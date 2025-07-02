#!/usr/bin/env python3
"""
Enhanced geocoding script for Mariupol seized properties with caching and retries.
"""

import os
import sys
import re
import json
import logging
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple, Any, Set, Union
import time
import argparse
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pathlib import Path
import pandas as pd
import geopandas as gpd
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable
from shapely.geometry import Point
from tqdm import tqdm
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler('geocoding.log')]
)
logger = logging.getLogger(__name__)

class RateLimitedGeocoder:
    def __init__(self, user_agent="mariupol_property_geocoder", **kwargs):
        self.geocoder = Nominatim(
            user_agent=user_agent,
            timeout=30,
            **kwargs
        )
        # More conservative rate limiting (Nominatim's default is 1 request/second)
        self.min_delay = 1.1  # seconds between requests
        self.last_request = 0
        self.max_retries = 3
        
    def geocode(self, query, **kwargs):
        retries = 0
        last_exception = None
        
        while retries < self.max_retries:
            try:
                # Enforce rate limiting
                elapsed = time.time() - self.last_request
                if elapsed < self.min_delay:
                    time.sleep(self.min_delay - elapsed)
                
                # Make the request
                self.last_request = time.time()
                
                # Set default parameters
                params = {
                    'exactly_one': True,
                    'timeout': 30,
                    'addressdetails': True,
                    'country_codes': 'ua',
                    'language': 'ru',
                }
                params.update(kwargs)  # Allow overriding defaults
                
                return self.geocoder.geocode(query, **params)
                
            except (GeocoderTimedOut, GeocoderServiceError) as e:
                last_exception = e
                wait_time = (2 ** retries) + random.uniform(0, 1)
                logger.warning(f"Attempt {retries + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                retries += 1
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return None
        
        logger.error(f"All {self.max_retries} attempts failed for: {query}")
        return None

class SeizedPropertyGeocoder:
    def __init__(self, cache_file: str = None, user_agent: str = "mariupol_property_geocoder"):
        self.geocoder = RateLimitedGeocoder(user_agent=user_agent)
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.cache_hits = 0
        self.cache_misses = 0
        self.last_save = time.time()
        self.cache_modified = False
        self.save_interval = 300
        
        # Enhanced manual coordinates with more variations
        self.manual_coordinates = {
            # Bohdana Khmelnytskoho Boulevard variations
            'б-р Богдана Хмельницкого, д. 24': (37.5689, 47.1012),
            'б-р Богдана Хмельницкого, 24': (37.5689, 47.1012),
            'Богдана Хмельницкого, 24': (37.5689, 47.1012),
            'Хмельницкого, 24': (37.5689, 47.1012),
            'Khmelnytskoho, 24': (37.5689, 47.1012),
            
            # 50-летия СССР variations
            '50-летия СССР, 55, Октябрьский район': (37.5667, 47.1000),
            '50-летия СССР, 55': (37.5667, 47.1000),
            '50 let SSSR, 55': (37.5667, 47.1000),
            
            # Add more common addresses as needed
            'б-р Шевченко, 24': (37.5650, 47.0980),  # Example coordinates
            'Шевченко, 24': (37.5650, 47.0980),
            'Shevchenka, 24': (37.5650, 47.0980),
        }

    def _load_cache(self):
        if not self.cache_file or not os.path.exists(self.cache_file):
            return {}
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load cache file: {e}")
            return {}

    def _save_cache(self, force=False):
        if not self.cache_modified or not self.cache_file:
            return
            
        current_time = time.time()
        if not force and (current_time - self.last_save) < self.save_interval:
            return
            
        try:
            temp_file = f"{self.cache_file}.tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            
            if os.path.exists(self.cache_file):
                os.replace(temp_file, self.cache_file)
            else:
                os.rename(temp_file, self.cache_file)
                
            self.cache_modified = False
            self.last_save = current_time
            logger.debug(f"Cache saved with {len(self.cache)} entries")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def extract_building_address(self, full_address: str) -> str:
        """Extract just the building part of the address (without apartment number)."""
        # Remove apartment number and any trailing commas/spaces
        building_address = re.sub(r',?\s*кв\.?\s*\d+.*$', '', full_address).strip()
        return building_address

    def _clean_address(self, address: str) -> str:
        if not address or not isinstance(address, str):
            return ""

        # Convert to string and normalize
        cleaned = str(address).strip()
        
        # Handle special street names first
        cleaned = re.sub(
            r'(?i)(\d+)[-\s]*(?:год[ау]?|лет|рок[ів]?|рік)[-\s]*(ссср|срср|срс|сс|с\.?с\.?р\.?|с\.?р\.?с\.?р\.?)', 
            r'\1-летия СССР', 
            cleaned
        )
        
        # Standardize district abbreviations (both Russian and Ukrainian variants)
        district_mapping = {
            # Central District (Центральный район / Центральний район)
            r'(?i)\bц\.?\s*р\.?\b': 'Центральный район',
            r'(?i)\bцр\b': 'Центральный район',
            r'(?i)\bцентральний\b': 'Центральный',
            
            # Kalmius District (Кальмиусский район / Кальміуський район)
            r'(?i)\bк\.?\s*р\.?\b(?!ривой)': 'Кальмиусский район',
            r'(?i)\bкр\b(?!ривой)': 'Кальмиусский район',
            r'(?i)\bкальміуський\b': 'Кальмиусский',
            
            # October District (Октябрьский район / Жовтневий район)
            r'(?i)\bж\.?\s*р\.?\s*а\.?\b': 'Октябрьский район',
            r'(?i)\bжра\b': 'Октябрьский район',
            r'(?i)\bо\.?\s*р\.?\s*а\.?\b': 'Октябрьский район',
            r'(?i)\bора\b': 'Октябрьский район',
            r'(?i)\bжовтневий\b': 'Октябрьский',
            
            # Primorsky District (Приморский район / Приморський район)
            r'(?i)\bп\.?\s*р\.?\b(?!ортов)': 'Приморский район',
            r'(?i)\bпр\b(?!ортов)': 'Приморский район',
            r'(?i)\bприморський\b': 'Приморский',
            
            # Left Bank District (Левобережный район / Лівобережний район)
            r'(?i)\bл\.?\s*б\.?\s*р\.?\b': 'Левобережный район',
            r'(?i)\bлбр\b': 'Левобережный район',
            r'(?i)\bлівобережний\b': 'Левобережный',
            
            # Common street name variants
            r'(?i)\bпр-?кт\.?\s*металлургов\b': 'проспект Металлургов',
            r'(?i)\bпр-?кт\.?\s*ленина\b': 'проспект Ленина',
            r'(?i)\bпр-?кт\.?\s*мира\b': 'проспект Мира',
            r'(?i)\bпер\.?\s*нахимова\b': 'переулок Нахимова',
            r'(?i)\bул\.?\s*артема\b': 'улица Артема',
            r'(?i)\bул\.?\s*куприна\b': 'улица Куприна',
            
            # Special case for 50-летия СССР street
            r'(?i)\b(ул\.?|улица|вул\.?|вулиця)?\s*(\d+)[-\s]*(?:год[ау]?|лет|рок[ів]?|рік)[-\s]*(ссср|срср|срс|сс|с\.?с\.?р\.?|с\.?р\.?с\.?р\.?)\b': 
                'улица \2-летия СССР',
        }
        
        for pattern, replacement in district_mapping.items():
            cleaned = re.sub(pattern, replacement, cleaned)
        
        # Standardize street types and other address components
        replacements = {
            # Street types (Ukrainian -> Russian)
            r'(?i)\b(?:вул\.?|вулиц[яюи]|вулиці|vul\.?|vulytsya)\b': 'улица',
            r'(?i)\b(?:пров\.?|провулок|prov\.?|provulok)\b': 'переулок',
            r'(?i)\b(?:пр-?кт\.?|просп\.?|проспект|prosp\.?|prospekt)\b': 'проспект',
            r'(?i)\b(?:бул\.?|бульвар|bul\.?|bulvar)\b': 'бульвар',
            r'(?i)\b(?:пл\.?|площа|площадь|pl\.?|ploshcha|ploshchad)\b': 'площадь',
            r'(?i)\b(?:ш\.?|шосе|sh\.?|shose)\b': 'шоссе',
            r'(?i)\b(?:наб\.?|набережна|набережная|nab\.?|naberezhna|naberezhnaya)\b': 'набережная',
            r'(?i)\b(?:пр-?д\.?|проезд|proezd)\b': 'проезд',
            r'(?i)\b(?:туп\.?|тупик|tup\.?|tupik)\b': 'тупик',
            
            # Settlement types (Ukrainian -> Russian)
            r'(?i)\b(?:с\.?\s*с\.?|с/с|с-с|селище|selyshche|s/s|s-s|с\.?с\.?)\b': 'поселок',
            r'(?i)\b(?:пос\.?|поселение|поселок|pos\.?|poseleniye|posyolok|п\.?|п/п|п-п|п\.?п\.?)\b': 'поселок',
            r'(?i)\b(?:смт\b|с\.?м\.?т\.?|селище міського типу)\b': 'пгт',
            r'(?i)\b(?:с\.?|село|selo|s\.?)\b': 'село',
            r'(?i)\b(?:х\.?|хутор|khutor|kh\.?)\b': 'хутор',
            
            # Common address components
            r'(?i)\b(?:буд\.?|будинок|bud\.?|budynok)\b': 'д.',
            r'(?i)\b(?:корп\.?|корпус|korpus|kor\.?|korp\.?)\b': 'к.',
            
            # Only replace нко with улица when it's at the start of the address or after a comma
            r'(?i)(^|\s|,)(нко)(\s|$)': r'\1улица\3',
            r'(?i)\bн\.?\s*к\.?\s*о\.?\b': 'улица',
            
            # Handle numbered streets with ordinal suffixes (1-й, 2-я, etc.)
            r'(?i)\b(\d+)[-\s]*(?:й|я|го|му|ый|ой|ий|ая|ое|ье|ые|ых|ым|ими|х|м|го|му|ем|ом|ом)\b': r'\1-й',
            
            # Clean up special street names
            r'(?i)\b(\d+)\s*[-–—]?\s*(?:год[ау]?|лет|рок[ів]?|рік)?\s*(ссср|срср|срс|сс|с\.?с\.?р\.?|с\.?р\.?с\.?р\.?)\b': r'\1-летия СССР',
            
            # Clean up punctuation and whitespace
            r'\s+': ' ',
            r'\s*,\s*': ', ',
            r'\s*\.\s*': '.',
            r'\s*\/\s*': '/',
            r'\s*-\s*': '-',
        }
        
        for pattern, repl in replacements.items():
            cleaned = re.sub(pattern, repl, cleaned)
        
        # Handle building numbers with letters (e.g., 123а)
        cleaned = re.sub(r'(\d+)([а-яА-Я])\b', r'\1\2', cleaned, flags=re.IGNORECASE)
        
        # Clean up any remaining multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Remove any trailing commas or periods
        cleaned = re.sub(r'[\s,.]*$', '', cleaned)
        
        return cleaned

    def _generate_address_variations(self, address: str, district: str = "") -> List[str]:
        if not address or not isinstance(address, str):
            return []
            
        cleaned_address = self._clean_address(address)
        if not cleaned_address:
            return []
            
        variations = set()
        
        # Base variation - just the cleaned address
        variations.add(cleaned_address)
        
        # Common street name mappings (common misspellings and variations)
        street_name_mappings = {
            'металлургов': ['металургов'],
            'артема': ['артёма'],
            'нахимова': ['нахимова', 'нахимова переулок'],
            '50-летия СССР': [
                '50 лет СССР', 
                '50 лет ССР', 
                '50-летия ССР',
                '50-летия СССР',
                '50 років СРСР',
                '50 летия СССР',
                '50-річчя СРСР',
                '50-річчя СССР'
            ],
            '2-й Кальчик': ['2-й Кальчик', '2-й Кальчикский', '2-я Кальчикская'],
            # Add more street name variations here
            'Кирова': ['Кірова'],
            'Чернышевского': ['Чернишевського'],
            'Щорса': ['Щорса', 'Щорса улица', 'улица Щорса'],
            'Луначарского': ['Луначарського'],
            'Куйбышева': ['Куйбишева'],
            'Фрунзе': ['Фрунзе', 'Фрунзе улица', 'улица Фрунзе'],
            'Дзержинского': ['Дзержинського'],
            'Куприна': ['Куприна', 'Купріна'],
            'Лермонтова': ['Лермонтова', 'Лермонтовська'],
            'Гагарина': ['Гагаріна'],
            'Горького': ['Горького', 'Горького улица', 'улица Горького'],
        }
        
        # Generate variations with common street name alternatives
        for standard, alts in street_name_mappings.items():
            if standard.lower() in cleaned_address.lower():
                for alt in alts:
                    variations.add(cleaned_address.replace(standard, alt))
                    variations.add(cleaned_address.lower().replace(standard.lower(), alt))
        
        # Add variations with different levels of context
        if district:
            cleaned_district = self._clean_address(district)
            if cleaned_district and cleaned_district.lower() not in cleaned_address.lower():
                variations.add(f"{cleaned_address}, {cleaned_district}")
        
        # Check if we already have regional context
        has_regional_context = any(x in cleaned_address.lower() for x in 
                                 ['мариуполь', 'донецк', 'донецкая', 'украин'])
        
        # Add regional context if not present
        if not has_regional_context:
            for var in list(variations):  # Create a copy to avoid modifying during iteration
                variations.add(f"{var}, Мариуполь, Донецкая область, Украина")
                variations.add(f"{var}, Мариуполь, Донецкая область")
        
        # Handle district variations (Russian/Ukrainian)
        district_variations = {
            'Октябрьский район': 'Жовтневий район',
            'Ильичёвский район': 'Іллічівський район',
            'Портовский район': 'Портівський район',
            'Центральный район': 'Центральний район',
            'Кальмиусский район': 'Кальміуський район',
            'Приморский район': 'Приморський район',
            'Левобережный район': 'Лівобережний район',
        }
        
        # Add variations with alternate district names
        for ru_district, uk_district in district_variations.items():
            for var in list(variations):
                if ru_district.lower() in var.lower():
                    variations.add(var.replace(ru_district, uk_district))
                    variations.add(var.replace(ru_district, uk_district).title())
                elif uk_district.lower() in var.lower():
                    variations.add(var.replace(uk_district, ru_district))
                    variations.add(var.replace(uk_district, ru_district).title())
        
        # Add variations with and without street type (ул., проспект, etc.)
        street_type_variations = []
        for var in variations:
            # Remove street type
            no_type = re.sub(r'\b(?:улица|ул\.?|проспект|пр-?кт\.?|бульвар|б-р|переулок|пер\.?|площадь|пл\.?|шоссе|ш\.?|набережная|наб\.?|проезд|пр-?д\.?|тупик|туп\.?)\s+', 
                            '', var, flags=re.IGNORECASE)
            if no_type != var:
                street_type_variations.append(no_type)
            
            # Add short form of street type
            short_type = re.sub(r'\b(улица|проспект|бульвар|переулок|площадь|шоссе|набережная|проезд|тупик)\b', 
                              lambda m: {
                                  'улица': 'ул.',
                                  'проспект': 'пр-т',
                                  'бульвар': 'б-р',
                                  'переулок': 'пер.',
                                  'площадь': 'пл.',
                                  'шоссе': 'ш.',
                                  'набережная': 'наб.',
                                  'проезд': 'пр-д',
                                  'тупик': 'туп.'
                              }[m.group(0)], var, flags=re.IGNORECASE)
            if short_type != var:
                street_type_variations.append(short_type)
        
        variations.update(street_type_variations)
        
        # Convert to list and clean up
        variations = list(variations)
        
        # Remove any empty strings and normalize whitespace
        variations = [' '.join(v.split()) for v in variations if v and v.strip()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_variations = []
        for var in variations:
            norm_var = ' '.join(var.split())  # Normalize whitespace
            if norm_var.lower() not in seen:
                seen.add(norm_var.lower())
                unique_variations.append(norm_var)
        
        # Log the variations for debugging
        if len(unique_variations) > 1:
            logger.debug(f"Generated {len(unique_variations)} variations for '{cleaned_address}': {unique_variations}")
        
        return unique_variations

    def _generate_soviet_street_variations(self, address: str, district: str = "") -> List[str]:
        """Generate specific variations for 50-летия СССР street."""
        variations = set()
        
        # Extract house number if present
        house_match = re.search(r'д\.?\s*(\d+[а-яА-Я]?)\b', address)
        house_num = house_match.group(1) if house_match else ""
        
        # Base variations
        base_variants = [
            f"улица 50-летия СССР, {house_num}, Мариуполь, Донецкая область, Украина",
            f"50-летия СССР ул., {house_num}, Мариуполь, Донецкая область, Украина",
            f"50-летия СССР, {house_num}, Мариуполь, Донецкая область, Украина",
            f"50 лет СССР, {house_num}, Мариуполь, Донецкая область, Украина",
            f"50-летия СССР, {house_num}, Октябрьский район, Мариуполь, Донецкая область, Украина",
            f"50-летия СССР, {house_num}, Мариуполь, Украина",
        ]
        
        # Add variations with different street type formats
        street_variants = [
            '50-летия СССР',
            '50 лет СССР',
            '50-летия ССР',
            '50 лет ССР',
            '50 років СРСР',
        ]
        
        for street in street_variants:
            variations.update([
                f"улица {street}, {house_num}, Мариуполь, Донецкая область, Украина",
                f"ул. {street}, {house_num}, Мариуполь, Донецкая область, Украина",
                f"{street} ул., {house_num}, Мариуполь, Донецкая область, Украина",
                f"{street}, {house_num}, Мариуполь, Донецкая область, Украина",
            ])
        
        # Add variations with district
        if district:
            cleaned_district = self._clean_address(district)
            if cleaned_district:
                variations.update([
                    f"50-летия СССР, {house_num}, {cleaned_district}, Мариуполь, Донецкая область, Украина",
                    f"50 лет СССР, {house_num}, {cleaned_district}, Мариуполь, Донецкая область, Украина",
                ])
        
        # Add the base variations
        variations.update(base_variants)
        
        # Clean and deduplicate
        variations = [v for v in variations if v]
        variations = list(dict.fromkeys(variations))  # Preserve order
        
        logger.debug(f"Generated {len(variations)} Soviet street variations for '{address}': {variations}")
        return variations

    def _geocode_single_address(self, address: str, district: str = "") -> Optional[Tuple[float, float]]:
        """Geocode a single address with improved reliability and caching."""
        if not address or not isinstance(address, str):
            return None
            
        # Clean and normalize the address
        cleaned = self._clean_address(address)
        if not cleaned:
            return None
            
        cache_key = f"{cleaned}|{district}".lower()
        
        # Check cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if isinstance(cached, (tuple, list)) and len(cached) == 2:
                self.cache_hits += 1
                return tuple(cached)
            elif cached is None:  # Cache negative results
                return None
        
        self.cache_misses += 1
        
        # Check manual coordinates with more precise matching
        manual_key = f"{cleaned}, {district}" if district else cleaned
        manual_key = manual_key.lower().strip()
        
        # Try exact matches first
        if manual_key in (k.lower() for k in self.manual_coordinates.keys()):
            coords = self.manual_coordinates[manual_key]
            logger.info(f"Exact manual match: {manual_key} -> {coords}")
            self.cache[cache_key] = coords
            self.cache_modified = True
            return coords
            
        # Then try partial matches but be more strict
        for key, coords in self.manual_coordinates.items():
            key_lower = key.lower()
            # Only match if the address starts with the key (to avoid partial matches)
            if manual_key.startswith(key_lower):
                logger.info(f"Partial manual match: {manual_key} -> {coords} (matched on {key})")
                self.cache[cache_key] = coords
                self.cache_modified = True
                return coords
        
        # If no manual match found, try online geocoding with limited variations
        logger.info(f"No manual match found, trying online geocoding for: {cleaned}")
        
        # Generate address variations (limit to 5 most relevant ones)
        variations = self._generate_address_variations(cleaned, district)[:5]
        
        # Add district to variations if not already included
        if district and not any(district.lower() in v.lower() for v in variations):
            variations.append(f"{cleaned}, {district}")
        
        # Add city and country to variations (limit to 2 variations with region)
        variations_with_region = []
        for var in variations[:2]:  # Only take first 2 variations for region addition
            if 'мариуполь' not in var.lower():
                variations_with_region.append(f"{var}, Мариуполь, Донецкая область, Украина")
                variations_with_region.append(f"{var}, Мариуполь")
        
        variations = variations + variations_with_region
        
        # Add the original cleaned address as the last resort
        if cleaned not in variations:
            variations.append(cleaned)
        
        # Limit total variations to 8
        variations = variations[:8]
        
        logger.debug(f"Trying {len(variations)} variations for: {cleaned}")
        
        # Try each variation until we get a valid result
        for i, variation in enumerate(variations, 1):
            try:
                # Check cache for this variation
                var_key = f"{variation}|{district}".lower()
                if var_key in self.cache:
                    cached = self.cache[var_key]
                    if isinstance(cached, (tuple, list)) and len(cached) == 2:
                        self.cache[cache_key] = cached  # Cache under the original key too
                        logger.debug(f"Cache hit for variation {i}/{len(variations)}")
                        return tuple(cached)
                
                # Try to geocode
                logger.debug(f"Trying to geocode ({i}/{len(variations)}): {variation}")
                location = self.geocoder.geocode(variation, exactly_one=True)
                
                if location and hasattr(location, 'longitude') and hasattr(location, 'latitude'):
                    lon, lat = location.longitude, location.latitude
                    
                    # Verify the location is in the Mariupol region
                    if self._is_in_mariupol_region(lon, lat):
                        logger.info(f"Successfully geocoded: {variation} -> ({lon}, {lat})")
                        self.cache[cache_key] = (lon, lat)  # Cache under original key
                        self.cache[var_key] = (lon, lat)     # Cache under variation key
                        self.cache_modified = True
                        return (lon, lat)
                    else:
                        logger.warning(f"Geocoded location outside Mariupol region: {variation} -> ({lon}, {lat})")
                
            except Exception as e:
                logger.warning(f"Error geocoding variation {i}/{len(variations)} '{variation}': {str(e)}")
                continue
        
        # If we get here, all variations failed
        logger.warning(f"Failed to geocode address after {len(variations)} attempts: {cleaned}")
        self.cache[cache_key] = None  # Cache the failure
        self.cache_modified = True
        return None

    def _is_in_mariupol_region(self, lon: float, lat: float) -> bool:
        min_lon, max_lon = 37.4, 37.7
        min_lat, max_lat = 47.0, 47.2
        return (min_lon <= lon <= max_lon) and (min_lat <= lat <= max_lat)

    def process_properties(self, input_file: str, output_file: str, output_format: str = 'geojson', 
                          batch_size: int = 50, resume: bool = False) -> bool:
        """Process properties with optimized geocoding of unique buildings."""
        try:
            logger.info(f"Reading input file: {input_file}")
            df = pd.read_csv(input_file)
            
            # Extract building addresses
            logger.info("Extracting building addresses...")
            df['building_address'] = df['address'].apply(self.extract_building_address)
            
            # Process unique buildings first
            buildings = df[['district', 'building_address']].drop_duplicates()
            logger.info(f"Found {len(buildings)} unique buildings to geocode")
            
            # Geocode each unique building
            buildings['coordinates'] = buildings.apply(
                lambda x: self._geocode_single_address(x['building_address'], x['district']), 
                axis=1
            )
            
            # Map coordinates back to all apartments
            building_coords = dict(zip(
                buildings['building_address'], 
                buildings['coordinates']
            ))
            df['coordinates'] = df['building_address'].map(building_coords)
            
            # Split coordinates into separate columns
            df[['longitude', 'latitude']] = pd.DataFrame(
                df['coordinates'].tolist(), 
                index=df.index
            )
            
            # Save results
            self._save_output(df, output_file, output_format)
            logger.info(f"Successfully processed {len(df)} properties")
            return True
            
        except Exception as e:
            logger.error(f"Error processing properties: {e}", exc_info=True)
            return False

    def _save_output(self, df: pd.DataFrame, output_file: str, output_format: str):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            if output_format.lower() == 'geojson':
                gdf = gpd.GeoDataFrame(
                    df,
                    geometry=gpd.points_from_xy(df.longitude, df.latitude),
                    crs="EPSG:4326"
                )
                gdf.to_file(output_file, driver='GeoJSON')
            else:
                df.to_csv(output_file, index=False)
                
            logger.info(f"Saved {len(df)} features to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save output: {e}", exc_info=True)
            raise

def parse_arguments():
    parser = argparse.ArgumentParser(description='Geocode Mariupol seized properties')
    parser.add_argument('--input', default='data/processed/properties_structured.csv',
                      help='Input CSV file with addresses')
    parser.add_argument('--output', default='data/processed/geocoded_properties.geojson',
                      help='Output file path')
    parser.add_argument('--cache', default='data/geocoding_cache.json', 
                      help='Cache file path')
    parser.add_argument('--batch-size', type=int, default=25, 
                      help='Number of addresses to process in each batch')
    parser.add_argument('--format', choices=['geojson', 'csv'], default='geojson',
                      help='Output format')
    parser.add_argument('--resume', action='store_true',
                      help='Resume from existing output file')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug logging')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    else:
        logger.setLevel(logging.INFO)
    
    try:
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            return 1
            
        logger.info(f"Initializing geocoder with cache: {args.cache}")
        geocoder = SeizedPropertyGeocoder(cache_file=args.cache)
        
        logger.info(f"Starting geocoding from {args.input} to {args.output}")
        success = geocoder.process_properties(
            input_file=args.input,
            output_file=args.output,
            output_format=args.format,
            batch_size=args.batch_size,
            resume=args.resume
        )
        
        if success:
            logger.info("Geocoding completed successfully")
            return 0
        else:
            logger.error("Geocoding failed")
            return 1
            
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())