# src/toponymic_db_fw.py
# Last Updated: June 24, 2025
# This version contains all necessary functions for the processing script.

import re
import asyncio

# --- Database Section ---
MARIUPOL_COMPREHENSIVE_TOPONYMIC_DATABASE = {
    'CENTRAL_DISTRICT_VERIFIED': {
        'площадь_свободы': {
            'ukrainian_name': 'Площа Свободи', 'ukrainian_transliteration': 'Freedom Square',
            'occupation_name': 'площадь Ленина', 'occupation_transliteration': 'Lenin Square',
            'renaming_date': '2023-08', 'renaming_authority': 'Denis Pushilin (DPR Head)',
            'cultural_significance': 'DEMOCRATIC_VALUES_ERASURE', 'strategic_importance': 'CRITICAL_SYMBOLIC_CENTER'
        },
        'проспект_нахимова_82': {
            'ukrainian_name': 'проспект Нахімова, 82', 'demolition_status': 'BUILDING_DEMOLISHED_2022',
            'new_construction_address': 'Черноморский переулок 1б', 'address_manipulation_tactic': 'OWNERSHIP_CLAIM_PREVENTION',
            'legal_impact': 'COMPENSATION_DENIAL_MECHANISM', 'war_crimes_evidence': 'SYSTEMATIC_PROPERTY_APPROPRIATION'
        }
    },
    'INDUSTRIAL_DISTRICT_VERIFIED': {
        'азовстальська_вулиця': {
            'ukrainian_name': 'Азовсталь вулиця', 'ukrainian_transliteration': 'Azovstalska Street',
            'occupation_name': 'улица Тульская', 'occupation_transliteration': 'Tula Street',
            'renaming_date': '2023-08', 'renaming_authority': 'Denis Pushilin (DPR Head)',
            'cultural_significance': 'RESISTANCE_SYMBOL_ERASURE', 'strategic_importance': 'INDUSTRIAL_HERITAGE_ELIMINATION'
        }
    }
}

# --- Function Definitions ---

def find_verified_toponymic_correlation(street_name, house_number=None):
    """
    Finds correlations using verified intelligence from the comprehensive database.
    """
    street_name_normalized = street_name.lower().strip()

    for district_data in MARIUPOL_COMPREHENSIVE_TOPONYMIC_DATABASE.values():
        for street_key, street_data in district_data.items():
            search_terms = [
                street_data.get('occupation_name', '').lower(),
                street_data.get('new_construction_address', '').lower(),
                street_data.get('ukrainian_name').lower()
            ]
            search_terms = [term for term in search_terms if term]

            for term in search_terms:
                if street_name_normalized in term or term in street_name_normalized:
                    return street_data
    return None

def extract_addresses_with_verified_toponymy(text):
    """
    Enhanced address extraction using documented systematic renaming intelligence.
    This is the function that was missing from your file.
    """
    extracted_addresses = {
        'verified_correlations': [],
        'ownership_claim_threats': [],
        'cultural_erasure_evidence': []
    }
    comprehensive_patterns = [
        r'(?:ул\.|улица|пр\.|проспект|пл\.|площадь|пер\.|переулок)\s*([А-Яа-я\s\-]+)\s*,?\s*(\d+[А-Яа-я]*)',
        r'([А-Яа-я]+ский\s+переулок)\s+(\d+[а-я])',
    ]

    for pattern in comprehensive_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            street_name, house_number = match[0].strip(), match[1].strip()
            full_address_text = f"{street_name}, {house_number}"
            correlation = find_verified_toponymic_correlation(street_name, house_number)

            if correlation:
                if correlation.get('address_manipulation_tactic'):
                    extracted_addresses['ownership_claim_threats'].append({
                        'current_address': full_address_text,
                        'original_ukrainian_address': correlation.get('ukrainian_name'),
                        'manipulation_tactic': correlation.get('address_manipulation_tactic'),
                        'legal_impact': correlation.get('legal_impact'),
                        'evidence_type': 'VERIFIED_ADDRESS_MANIPULATION'
                    })
                elif correlation.get('cultural_significance'):
                    extracted_addresses['cultural_erasure_evidence'].append({
                        'current_name': street_name,
                        'ukrainian_name': correlation.get('ukrainian_name'),
                        'cultural_significance': correlation.get('cultural_significance'),
                        'renaming_authority': correlation.get('renaming_authority'),
                        'evidence_type': 'SYSTEMATIC_CULTURAL_ERASURE'
                    })
                extracted_addresses['verified_correlations'].append({
                    'occupation_address': full_address_text,
                    'ukrainian_correlation': correlation.get('ukrainian_name'),
                    'verification_status': 'DOCUMENTED_INTELLIGENCE',
                    'strategic_importance': correlation.get('strategic_importance')
                })

    return extracted_addresses