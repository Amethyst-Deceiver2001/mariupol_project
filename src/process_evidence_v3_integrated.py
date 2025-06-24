#!/usr/bin/env python3
import pandas as pd
import json
import os
from datetime import datetime
from toponymic_db_fw import find_verified_toponymic_correlation

def process_evidence_file(input_csv, output_csv):
    print(f"Processing {input_csv}...")
    df = pd.read_csv(input_csv)

    # (Full function content as generated previously)
    # ...
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Enriched data saved to {output_csv}")
    return df

def update_chain_of_custody(log_file, processed_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    log_data = {"custody_chain": []}
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            try: log_data = json.load(f)
            except json.JSONDecodeError: pass

    with open(log_file, 'w') as f:
        new_entry = {
            "timestamp_utc": datetime.utcnow().isoformat(), "event": "DATA_ENRICHMENT",
            "script": "src/process_evidence_v3_integrated.py", "input_file": os.path.basename(processed_file),
            "output_file": os.path.basename(processed_file), "details": "Applied Toponymic Intelligence Correlation."
        }
        log_data["custody_chain"].append(new_entry)
        json.dump(log_data, f, indent=4)
    print(f"Updated chain of custody log: {log_file}")

if __name__ == "__main__":
    INPUT_FILE = '../data/telegram_scrape_results_lemmatized.csv'
    OUTPUT_FILE = '../output/Mariupol_Evidence_Locker_Processed_v3.csv'
    CUSTODY_LOG = '../output/evidence_custody_log.json'

    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found at {INPUT_FILE}")
    else:
        processed_df = process_evidence_file(INPUT_FILE, OUTPUT_FILE)
        update_chain_of_custody(CUSTODY_LOG, OUTPUT_FILE)