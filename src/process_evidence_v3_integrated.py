#!/usr/bin/env python3
#
# src/process_evidence_v3_integrated.py
#
# Last Updated: June 24, 2025
# Status: PRODUCTION
#
# Core processing engine for the Mariupol Evidence Vault.
# This version is fully integrated with the Toponymic Intelligence Archive.
#

import pandas as pd
import json
import os
from datetime import datetime

# UPDATED: Import the entire module to avoid import errors.
import toponymic_db_fw

def process_evidence_file(input_csv, output_csv):
    """
    Reads a raw CSV of scraped data, applies toponymic analysis,
    and writes an enriched CSV file.
    """
    print(f"Processing {input_csv}...")
    df = pd.read_csv(input_csv)

    # UPDATED: Use the more comprehensive extraction function.
    def analyze_row(row_text):
        """Helper function to analyze text from a row."""
        if not isinstance(row_text, str):
            return {
                'verified_correlations': [],
                'ownership_claim_threats': [],
                'cultural_erasure_evidence': []
            }
        # Call the function from the imported module
        return toponymic_db_fw.extract_addresses_with_verified_toponymy(row_text)

    # Apply the intelligence function to the 'lemmatized_text' column
    intelligence_results = df['lemmatized_text'].apply(analyze_row)

    # Expand the results into new columns
    df['toponymic_intelligence'] = intelligence_results.apply(lambda x: json.dumps(x, ensure_ascii=False))
    df['is_flagged'] = intelligence_results.apply(lambda x: bool(x.get('ownership_claim_threats') or x.get('cultural_erasure_evidence')))
    df['threat_type'] = intelligence_results.apply(lambda x: x.get('ownership_claim_threats')[0]['manipulation_tactic'] if x.get('ownership_claim_threats') else None)
    df['erasure_type'] = intelligence_results.apply(lambda x: x.get('cultural_erasure_evidence')[0]['cultural_significance'] if x.get('cultural_erasure_evidence') else None)

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Enriched data saved to {output_csv}")
    print(f"Flagged {df['is_flagged'].sum()} records for high-level review.")
    return df

def update_chain_of_custody(log_file, processed_file):
    """
    Appends a new entry to the chain of custody log.
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    log_data = {"custody_chain": []}
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Custody log {log_file} is empty or corrupted. Starting a new log.")

    with open(log_file, 'w', encoding='utf-8') as f:
        new_entry = {
            "timestamp_utc": datetime.utcnow().isoformat(),
            "event": "DATA_ENRICHMENT",
            "script": "src/process_evidence_v3_integrated.py",
            "input_file": os.path.basename(processed_file),
            "output_file": os.path.basename(processed_file),
            "details": "Applied Toponymic Intelligence Correlation."
        }
        if "custody_chain" not in log_data:
            log_data["custody_chain"] = []
        log_data["custody_chain"].append(new_entry)
        json.dump(log_data, f, indent=4, ensure_ascii=False)

    print(f"Updated chain of custody log: {log_file}")


# CORRECTED CODE
if __name__ == "__main__":
    # File paths are now relative to the project root, where the script is run from.
    INPUT_FILE = 'data/telegram_scrape_results_lemmatized.csv'
    OUTPUT_FILE = 'output/Mariupol_Evidence_Locker_Processed_v3.csv'
    CUSTODY_LOG = 'output/evidence_custody_log.json'

    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found at {INPUT_FILE}")
        print("Please ensure the data files are in the 'data/' directory.")
    else:
        processed_df = process_evidence_file(INPUT_FILE, OUTPUT_FILE)
        update_chain_of_custody(CUSTODY_LOG, OUTPUT_FILE)