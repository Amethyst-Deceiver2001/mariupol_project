#!/usr/bin/env python3
"""
Enhanced Mariupol Property Geocoder
----------------------------------
This script geocodes property addresses using OpenStreetMap's Nominatim service
with improved performance, reliability, and user experience.
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Any, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable
from tqdm import tqdm
from shapely.geometry import Point
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('geocoding.log')
    ]
)
logger = logging.getLogger('geocoder')
logger = logging.getLogger('geocoder')

class RateLimitedGeocoder:
    """Handles rate limiting and retries for geocoding requests."""
    
    def __init__(self, max_retries: int = 3, requests_per_second: float = 0.5):
        self.geolocator = Nominatim(
            user_agent="mariupol_property_geocoder_enhanced",
            timeout=10,
            domain="nominatim.openstreetmap.org"
        )
        self.max_retries = max_retries
        self.requests_per_second = requests_per_second
        self.last_request_time = 0
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable)
        ),
        reraise=True
    )
    def geocode_with_retry(self, query: str, **kwargs) -> Optional[Any]:
        """Make a geocoding request with rate limiting and retries."""
        # Enforce rate limiting
        time_since_last = time.time() - self.last_request_time
        if time_since_last < (1.0 / self.requests_per_second):
            time.sleep((1.0 / self.requests_per_second) - time_since_last)
        
        try:
            self.last_request_time = time.time()
            return self.geolocator.geocode(query, **kwargs)
        except Exception as e:
            logger.warning(f"Geocoding failed for '{query}': {str(e)}")
            raise
class SeizedPropertyGeocoder:
    """Handles geocoding of seized properties with caching and batch processing."""
    
    def __init__(self, cache_file: str = "geocoding_cache.json"):
        """Initialize the geocoder with caching.
        
        Args:
            cache_file: Path to the JSON file for caching geocoding results
        """
        self.geocoder = RateLimitedGeocoder()
        self.cache_file = Path(cache_file)
        self.cache = self._load_cache()
        self.cache_hits = 0
        self.cache_misses = 0
        self.processed_count = 0
        logger.info(f"Initialized geocoder with cache: {self.cache_file}")
        
    def _load_cache(self) -> Dict[str, Optional[Tuple[float, float]]]:
        """Load cached geocoding results from file.
        
        Returns:
            Dictionary mapping addresses to (longitude, latitude) tuples
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    logger.info(f"Loaded {len(cache)} cached addresses from {self.cache_file}")
                    return {k: tuple(v) if v else None for k, v in cache.items()}
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
        return {}
    
    def _save_cache(self):
        """Save the current cache to disk."""
        try:
            # Create parent directories if they don't exist
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to a temporary file first
            temp_file = self.cache_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {k: list(v) if v else None for k, v in self.cache.items()},
                    f,
                    ensure_ascii=False,
                    indent=2
                )
            
            # Atomic rename
            temp_file.replace(self.cache_file)
            logger.debug(f"Saved {len(self.cache)} addresses to cache")
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    def _normalize_address(self, address: str, district: str = "") -> List[str]:
        """Generate multiple query variations for better geocoding success.
        
        Args:
            address: The raw address string
            district: Optional district name for context
            
        Returns:
            List of normalized address variations to try
        """
        if not isinstance(address, str) or not address.strip():
            return []
            
        # Common replacements and expansions
        replacements = {
            'пр-т': 'проспект',
            'бул.': 'бульвар',
            'ул.': 'улица',
            'пер.': 'переулок',
            'д.': 'дом',
            'кв.': 'квартира',
            'ЖРА': 'Жовтневий район',
            'КСР': 'Київський район',
            'ЛБ': 'Лівобережний район',
            'ПР': 'Приморський район',
            'ЦР': 'Центральний район',
            'Іллічівський': 'Іллічівський район',
            'Орджонікідзевський': 'Орджонікідзевський район'
        }
        
        # Basic cleaning
        address = ' '.join(str(address).split())
        
        # Generate variations
        variations = []
        
        # Original address
        variations.append(address)
        
        # Add city if not present
        if 'Мариуполь' not in address:
            variations.append(f"{address}, Мариуполь, Україна")
            
            # Add with district if available
            if district:
                variations.append(f"{address}, {district}, Мариуполь, Україна")
        
        # Add variations with common replacements
        replaced = address
        for short, long in replacements.items():
            if short in address:
                replaced = replaced.replace(short, long)
        
        if replaced != address:
            variations.append(replaced)
            if 'Мариуполь' not in replaced:
                variations.append(f"{replaced}, Мариуполь, Україна")
        
        return list(dict.fromkeys(variations))  # Remove duplicates while preserving order
    
    def _geocode_single_address(self, address: str, district: str = "") -> Optional[Tuple[float, float]]:
        """Geocode a single address with cache lookup and fallbacks.
        
        Args:
            address: The address to geocode
            district: Optional district for context
            
        Returns:
            Tuple of (longitude, latitude) or None if not found
        """
        # Check cache first
        if address in self.cache:
            self.cache_hits += 1
            return self.cache[address]
            
        self.cache_misses += 1
        
        # Generate query variations
        queries = self._normalize_address(address, district)
        if not queries:
            return None
        
        # Try each query variation
        for query in queries:
            try:
                location = self.geocoder.geocode_with_retry(
                    query, 
                    addressdetails=True, 
                    language='ru'
                )
                if location:
                    coords = (location.longitude, location.latitude)
                    self.cache[address] = coords
                    # Save cache periodically
                    if len(self.cache) % 10 == 0:
                        self._save_cache()
                    return coords
            except Exception as e:
                logger.debug(f"Query failed: {query} - {str(e)}")
                continue
        
        # If we get here, all queries failed
        self.cache[address] = None
        return None
    def process_batch(self, df_batch: pd.DataFrame) -> pd.DataFrame:
        """Process a batch of addresses in parallel.
        
        Args:
            df_batch: DataFrame containing address data with 'address' column
            
        Returns:
            DataFrame with added 'longitude' and 'latitude' columns
        """
        results = {}
        batch_size = len(df_batch)
        
        logger.info(f"Processing batch of {batch_size} addresses...")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_idx = {
                executor.submit(
                    self._geocode_single_address, 
                    row['address'], 
                    row.get('district', '')
                ): idx
                for idx, row in df_batch.iterrows()
            }
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    coords = future.result()
                    if coords:
                        results[idx] = {
                            'longitude': coords[0],
                            'latitude': coords[1]
                        }
                except Exception as e:
                    logger.error(f"Error processing address at index {idx}: {e}")
        
        # Update the batch with results
        for idx, coords in results.items():
            df_batch.at[idx, 'longitude'] = coords['longitude']
            df_batch.at[idx, 'latitude'] = coords['latitude']
            
        return df_batch
    
    def _save_geojson(self, df: pd.DataFrame, output_path: str) -> bool:
        """Save geocoded results to GeoJSON file.
        
        Args:
            df: DataFrame with geocoded results
            output_path: Path to save the GeoJSON file
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Filter out rows without coordinates
            valid_df = df.dropna(subset=['longitude', 'latitude']).copy()
            if valid_df.empty:
                logger.warning("No valid coordinates to save")
                return False
                
            # Convert to GeoDataFrame
            geometry = [Point(xy) for xy in zip(valid_df['longitude'], valid_df['latitude'])]
            gdf = gpd.GeoDataFrame(valid_df, geometry=geometry, crs="EPSG:4326")
            
            # Ensure output directory exists
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to temporary file first
            temp_path = output_path.with_suffix('.tmp')
            gdf.to_file(temp_path, driver='GeoJSON')
            
            # Atomic rename
            temp_path.replace(output_path)
            logger.info(f"Saved {len(gdf)} features to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving GeoJSON: {e}")
            return False
    def process_properties(
        self,
        input_file: str,
        output_file: str,
        batch_size: int = 50,
        resume_from: int = 0,
        output_format: str = 'geojson'
    ) -> bool:
        """Process all properties with progress tracking and checkpointing.
        
        Args:
            input_file: Path to input CSV file
            output_file: Path to save output file
            batch_size: Number of addresses to process in each batch
            resume_from: Row number to start from (for resuming)
            output_format: Output format ('geojson' or 'csv')
            
        Returns:
            True if processing completed successfully, False otherwise
        """
        try:
            # Load the input data
            logger.info(f"Loading data from {input_file}...")
            df = pd.read_csv(input_file, dtype=str)
            
            # Initialize coordinate columns if they don't exist
            if 'longitude' not in df.columns:
                df['longitude'] = None
            if 'latitude' not in df.columns:
                df['latitude'] = None
            
            # Filter out already processed rows if resuming
            if resume_from > 0:
                df = df.iloc[resume_from:]
                logger.info(f"Resuming from row {resume_from}")
            
            total = len(df)
            if total == 0:
                logger.info("No addresses to process.")
                return True
                
            logger.info(f"Processing {total} addresses in batches of {batch_size}...")
            
            # Process in batches
            start_time = time.time()
            processed = 0
            
            with tqdm(total=total, desc="Geocoding addresses", unit="addr") as pbar:
                for i in range(0, total, batch_size):
                    batch = df.iloc[i:i + batch_size].copy()
                    self.process_batch(batch)
                    processed += len(batch)
                    
                    # Save progress after each batch
                    if output_format.lower() == 'geojson':
                        self._save_geojson(df, output_file)
                    else:
                        df.to_csv(output_file, index=False)
                    
                    # Update progress
                    pbar.update(len(batch))
                    
                    # Log progress
                    elapsed = time.time() - start_time
                    rate = processed / max(elapsed, 1)  # addresses per second
                    logger.info(
                        f"Processed {processed}/{total} addresses "
                        f"({processed/total*100:.1f}%) | "
                        f"Rate: {rate*60:.1f} addresses/min | "
                        f"Cache hits: {self.cache_hits} | "
                        f"Cache misses: {self.cache_misses}"
                    )
            
            # Final save
            if output_format.lower() == 'geojson':
                success = self._save_geojson(df, output_file)
            else:
                df.to_csv(output_file, index=False)
                success = True
            
            # Save final cache
            self._save_cache()
            
            return success
            
        except KeyboardInterrupt:
            logger.info("Processing interrupted by user")
            # Try to save current progress
            if output_format.lower() == 'geojson':
                self._save_geojson(df, output_file)
            else:
                df.to_csv(output_file, index=False)
            self._save_cache()
            return False
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            return False


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Geocode property addresses using OpenStreetMap's Nominatim service."
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to input CSV file containing addresses'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=True,
        help='Path to save the geocoded results (GeoJSON or CSV)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of addresses to process in each batch (default: 50)'
    )
    parser.add_argument(
        '--cache',
        type=str,
        default='geocoding_cache.json',
        help='Path to cache file (default: geocoding_cache.json)'
    )
    parser.add_argument(
        '--format',
        type=str,
        choices=['geojson', 'csv'],
        default='geojson',
        help='Output format (geojson or csv, default: geojson)'
    )
    parser.add_argument(
        '--resume',
        type=int,
        default=0,
        help='Row number to start from (for resuming)'
    )
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_arguments()
    
    try:
        logger.info("Starting geocoding process...")
        geocoder = SeizedPropertyGeocoder(cache_file=args.cache)
        
        success = geocoder.process_properties(
            input_file=args.input,
            output_file=args.output,
            batch_size=args.batch_size,
            resume_from=args.resume,
            output_format=args.format
        )
        
        if success:
            logger.info("Geocoding completed successfully!")
            return 0
        else:
            logger.error("Geocoding completed with errors")
            return 1
            
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())                                            