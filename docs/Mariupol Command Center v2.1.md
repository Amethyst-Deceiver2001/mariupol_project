# Mariupol Command Center v2.1

**Last Updated**: June 24, 2025
**Status**: ACTIVE - PHASE 3 (LEGAL-GRADE EVIDENCE PRODUCTION)
**Source**: Integrated Red Team Handover Protocol v3.0
**Depends On**: Toponymic_Command_Center_v1.0.md

### 1.0 CORE MISSION DIRECTIVE

To develop and operate a legally compliant, Berkeley Protocol-standard evidence collection and analysis system for documenting systematic property seizures and reconstruction profiteering in occupied Mariupol, Ukraine. This system is designed to produce evidence suitable for legal proceedings and command responsibility cases.

### 2.0 TACTICAL PROJECT STATUS

**Project Stream**: Mariupol Evidence Vault (Priority: ACTIVE)
**Current Phase**: Phase 3 - Legal-Grade Evidence Production
**Objective**: Execute comprehensive analysis on the existing dataset, prepare legal documentation, and strategically expand evidence collection by correlating property seizures with toponymic manipulation.

**Immediate Actionable Priorities (72-hour window)**:
1.  **Reprocess Dataset**: Execute the updated `process_evidence_v3_integrated.py` script on the full dataset to enrich it with toponymic intelligence, identifying cases of address manipulation.
2.  **Cross-Verification Protocol**: Correlate satellite imagery coordinates with locations flagged for "OWNERSHIP_CLAIM_PREVENTION" to build a timeline of systematic demolition and reconstruction fraud.
3.  **Legal Documentation Preparation**: Begin drafting methodology documentation focusing on the systematic link between administrative toponymic changes and property crimes, as required for expert witness qualification.

### 3.0 TECHNICAL & DATA ASSETS

**3.1 Production-Ready Systems**
* **Collection Tool**: `telegram_scraper.py`
* **Processing Engine**: `process_evidence_v3_integrated.py`

**3.2 Critical Setup Requirement: Python Virtual Environment**
* **Activation Command**: `source mariupol_env/bin/activate`
* **Security Protocol**: Credentials must be set as environment variables before running the tools.
    ```bash
    export TELEGRAM_API_ID='YOUR_API_ID'
    export TELEGRAM_API_HASH='YOUR_API_HASH'
    ```

**3.3 Primary Data Assets**
* **Evidence Locker**: `Mariupol_Evidence_Locker_Processed_v3.csv`
* **Chain of Custody Log**: `evidence_custody_log.json`
* **Intelligence Dependency**: `toponymic_db_fw.py` (via Toponymic Command Center)

### 4.0 OPERATIONAL PROCEDURES & COMMANDS

**4.1 Standard Evidence Collection & Processing Cycle**
```bash
# 1. Activate environment
source mariupol_env/bin/activate

# 2. Set credentials (if not permanent)
export TELEGRAM_API_ID='YOUR_API_ID'
export TELEGRAM_API_HASH='YOUR_API_HASH'

# 3. Execute collection & processing (from project root)
python3 src/telegram_scraper.py
python3 src/process_evidence_v3_integrated.py