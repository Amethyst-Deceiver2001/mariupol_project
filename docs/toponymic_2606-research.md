### **`Deep_Research_Mission_Protocol_v3.0.md`**

```markdown
# Deep Research Mission Protocol v3.0

**Last Updated**: June 24, 2025 at 5:47 PM CEST
**Status**: ACTIVE - AWAITING EXECUTION
**Mission Objective**: To perform a comprehensive intelligence gathering and analysis iteration to support the technical expansion of the Mariupol Evidence Vault, and to serve as the single, self-contained source of truth for the project's current state.

---

## **1.0 Strategic & Legal Context**

### **1.1 Mission Overview**
The core mission is the legal-grade documentation of systematic property seizures in occupied Mariupol, Ukraine. The project's methodology is to produce evidence suitable for command responsibility cases in international courts by correlating administrative actions with property crimes, with a specific focus on "bureaucratic war crimes" operating through legal frameworks.

### **1.2 Legal Framework**
* **Standard**: The project adheres to the **Berkeley Protocol** for digital evidence collection to ensure court admissibility.
* **Licensing**: The project's source code is protected under the **GNU General Public License v3.0 (GPLv3)**. A `LICENSE` file containing the full text should be in the project root.

---

## **2.0 Project Architecture (Self-Contained)**

This section contains the complete codebase and configuration required to replicate the project.

### **2.1 Directory Structure**
The project must be organized using the following directory structure:
```

mariupol\_project/
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── data/
│   └── telegram\_scrape\_results\_lemmatized.csv
├── docs/
│   └── (All .md documentation files)
├── mariupol\_env/
│   └── (Python virtual environment)
├── output/
│   └── (Generated analysis files)
├── references/
│   └── (Supporting research materials)
└── src/
├── toponymic\_db\_fw.py
└── process\_evidence\_v3\_integrated.py

```

### **2.2 Configuration Files**

#### **`requirements.txt`**
```

numpy==2.3.1
pandas==2.3.0
python-dateutil==2.9.0.post0
pytz==2025.2
six==1.17.0
tzdata==2025.2

````

#### **`.gitignore`**
```gitignore
# Python
__pycache__/
mariupol_env/
.venv/
*.pyc

# Output & Data
output/
*.csv
*.json

# Credentials
.env
*.env.local

# OS-specific
.DS_Store
Thumbs.db
````

### **2.3 Core Source Code**

#### **`src/toponymic_db_fw.py`**

This file contains the core intelligence database and functions for analysis. The database has been updated with the latest intelligence from `toponymic_2606.md`.

```python
# src/toponymic_db_fw.py
import re
import asyncio

# Updated with intelligence from toponymic_2606.md
MARIUPOL_COMPREHENSIVE_TOPONYMIC_DATABASE = {
    'CENTRAL_DISTRICT_VERIFIED': {
        'площадь_свободы': {
            'ukrainian_name': 'Площа Свободи', 'occupation_name': 'площадь Ленина',
            'tactic': 'CULTURAL_ERASURE', 'mechanism': 'IDEOLOGICAL_REVERSAL'
        },
        'проспект_нахимова_82': {
            'ukrainian_name': 'проспект Нахімова, 82', 'occupation_name': 'Черноморский переулок 1б',
            'tactic': 'RECONSTRUCTION_FRAUD', 'mechanism': 'ADDRESS_MANIPULATION_POST_DEMOLITION'
        }
    },
    'LEFT_BANK_DISTRICT': {
        'азовстальська_вулиця': {
            'ukrainian_name': 'Азовсталь вулиця', 'occupation_name': 'улица Тульская',
            'tactic': 'CULTURAL_ERASURE', 'mechanism': 'RUSSIAN_GEOGRAPHIC_APPROPRIATION'
        },
        'улица_киевская': {
            'ukrainian_name': 'вулиця Київська', 'occupation_name': 'улица Киевская',
            'tactic': 'ADMINISTRATIVE_LIMBO', 'mechanism': 'OWNER_REGISTRATION_FAILURE'
        }
    }
}

def find_verified_toponymic_correlation(text):
    """
    Finds correlations using the verified intelligence database.
    """
    text_lower = text.lower()
    for district, streets in MARIUPOL_COMPREHENSIVE_TOPONYMIC_DATABASE.items():
        for key, data in streets.items():
            search_terms = [
                data.get('ukrainian_name', '').lower(),
                data.get('occupation_name', '').lower(),
                key.lower() # Search by the dictionary key itself
            ]
            search_terms = [term for term in search_terms if term]
            for term in search_terms:
                if term in text_lower:
                    return data # Return the entire data dictionary on match
    return None

def extract_addresses_with_verified_toponymy(text):
    """
    Enhanced address extraction using documented systematic renaming intelligence.
    """
    findings = {'flags': [], 'details': []}
    if not isinstance(text, str):
        return findings

    correlation = find_verified_toponymic_correlation(text)
    if correlation:
        findings['flags'].append(correlation.get('tactic', 'GENERIC_FLAG'))
        findings['details'].append(correlation)
    return findings
```

#### **`src/process_evidence_v3_integrated.py`**

This is the main processing engine script, with all previous bugs resolved.

```python
#!/usr/bin/env python3
# src/process_evidence_v3_integrated.py
import pandas as pd
import json
import os
from datetime import datetime
import toponymic_db_fw

def process_evidence_file(input_csv, output_csv):
    """
    Reads a raw CSV of scraped data, applies toponymic analysis,
    and writes an enriched CSV file.
    """
    print(f"Processing {input_csv}...")
    df = pd.read_csv(input_csv)

    def analyze_row(row_text):
        """Helper function to analyze text from a row."""
        return toponymic_db_fw.extract_addresses_with_verified_toponymy(row_text)

    intelligence_results = df['lemmatized_text'].apply(analyze_row)

    df['toponymic_intelligence'] = intelligence_results.apply(lambda x: json.dumps(x, ensure_ascii=False))
    df['is_flagged'] = intelligence_results.apply(lambda x: bool(x.get('flags')))
    df['flag_type'] = intelligence_results.apply(lambda x: x['flags'][0] if x.get('flags') else None)

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Enriched data saved to {output_csv}")
    print(f"Flagged {df['is_flagged'].sum()} records for high-level review.")
    return df

def update_chain_of_custody(log_file, processed_file):
    """Appends a new entry to the chain of custody log."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    log_data = {"custody_chain": []}
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            try: log_data = json.load(f)
            except json.JSONDecodeError: print(f"Warning: Custody log corrupt. Starting new log.")

    with open(log_file, 'w', encoding='utf-8') as f:
        new_entry = {
            "timestamp_utc": datetime.utcnow().isoformat(), "event": "DATA_ENRICHMENT",
            "script": "src/process_evidence_v3_integrated.py", "input_file": os.path.basename(processed_file),
            "details": "Applied Toponymic Intelligence Correlation."
        }
        if "custody_chain" not in log_data: log_data["custody_chain"] = []
        log_data["custody_chain"].append(new_entry)
        json.dump(log_data, f, indent=4, ensure_ascii=False)
    print(f"Updated chain of custody log: {log_file}")

if __name__ == "__main__":
    INPUT_FILE = 'data/telegram_scrape_results_lemmatized.csv'
    OUTPUT_FILE = 'output/Mariupol_Evidence_Locker_Processed_v3.csv'
    CUSTODY_LOG = 'output/evidence_custody_log.json'

    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found at {INPUT_FILE}")
    else:
        processed_df = process_evidence_file(INPUT_FILE, OUTPUT_FILE)
        update_chain_of_custody(CUSTODY_LOG, OUTPUT_FILE)
```

-----

## **3.0 Deep Research Mission Directives**

### **3.1 Primary Objective**

To gather and structure foundational intelligence that will inform the development of the `youtube_collector.py` and the cross-platform correlation engine. This involves researching legal frameworks and documenting media patterns.

### **3.2 Research Prompts**

1.  **Investigate Legal Frameworks:**

      * **Action:** Conduct a detailed search for the full text and analyses of **"Law No. 66-RZ"** of the self-proclaimed "Donetsk People's Republic".
      * **Objective:** Extract clauses defining the process for declaring property "ownerless" (`бесхозное жилье`).
      * **Output:** A point-by-point summary of the legal mechanism.

2.  **Investigate Tactic Terminology (Based on `toponymic_2606.md`)**:

      * **Action:** Conduct searches for official announcements or news reports (text or video) from Mariupol occupation authorities that use or describe the concepts of **"administrative limbo"** and **"reconstruction fraud"** in relation to property.
      * **Objective:** Find real-world examples and the specific terminology used by officials to describe these tactics.
      * **Output:** A list of key phrases and links to 1-3 examples.

3.  **Analyze Video Documentation Patterns:**

      * **Action:** Search video platforms for reports on new construction or "compensation housing" in Mariupol.
      * **Objective:** Document the **metadata and textual patterns** from 5-10 distinct examples (video titles, channel names/affiliations, description language, location descriptions).
      * **Output:** A structured list of these metadata patterns.

### **3.3 Ambiguity & Data Unavailability Protocol**

This protocol must be strictly adhered to.

1.  **Resolve Ambiguity:** If information is ambiguous, first attempt to resolve it by conducting a targeted, secondary search using the `Google Search` tool.
2.  **Handle Unavailability:** If a primary source is unreachable (e.g., requires a VPN), you must **not** infer its contents. Document the source and mark the data point as **`DATA_UNAVAILABLE`**.
3.  **Refer for Clarification:** If critical ambiguity persists or critical data is unavailable, halt that specific research line and present the issue in a structured `REQUEST FOR CLARIFICATION` section, referring back to me (Alexey Kovalev).
4.  **Acknowledge Gaps:** Do not fill gaps with unsourced information. Explicitly state where information is missing.

### **3.4 Final Deliverable**

Synthesize all outputs from the research prompts into a single markdown document titled **`Deep_Research_Findings_v2.md`**.