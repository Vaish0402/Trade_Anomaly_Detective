## Trade Shipment Anomaly Detection System
    A multi-layer anomaly detection pipeline for identifying trade compliance risks, financial irregularities, and behavioral deviations in shipment data.

    This project combines:
        •Rule-based validation
        •Statistical anomaly detection
        •LLM-powered semantic validation
        •Risk scoring & ranking
        •Executive reporting
        •Interactive dashboard visualization

## Architecture Overview
    The system is built in layered stages:
            Data Generation
                ↓
            Rule Engine (Layer 1)
                ↓
            Statistical Detector (Layer 2)
                ↓
            LLM Detector (Layer 3)
                ↓
            Report Generator (Layer 4)
                ↓
            Streamlit Dashboard (Layer 5)

## Project Structure
    Assignment
    │
    ├── data/
    │   ├── shipments.csv
    │   ├── buyers.csv
    │   ├── product_catalog.csv
    │   ├── routes.csv
    │   └── planted_anomalies.json
    │
    ├── src/
    │   ├── data_generator.py
    │   ├── rule_engine.py
    │   ├── statistical_detector.py
    │   ├── llm_detector.py
    │   ├── report_generator.py
    │   └── app.py                          
    │
    ├── output/
    │   ├── anomaly_report.json
    │   ├── executive_summary.md
    │   ├── accuracy_report.json
    │   └── llm_usage_report.json   
    │
    ├── DESIGN_DECISIONS.md
    ├── requirements.txt
    └── README.md                   


## Layer Descriptions

1️⃣ Rule Engine (Deterministic)
    Flags violations such as:
        •Invoice math mismatches
        •Illegal drawback claims
        •CIF freight violations
        •These are strict business-rule checks.

2️⃣ Statistical Detector (Behavioral)
     Z-score to detect:
        •Extreme unit price deviations
        •Buyer payment delay anomalies
        •Transit time spikes
        •Flags values exceeding ±3 standard deviations.

3️⃣ LLM Detector (Semantic)
    Validates HS code classifications by:
        •Comparing product description
        •Checking against expected HS code
        •Returning structured JSON output
        •Uses constrained schema for reliable automation.

4️⃣ Risk Scoring
    Each anomaly receives:
        •Base score from severity
        •Type-based bonus
        •Final risk score
        •Priority tier (P1–P4)
        •Enables ranking and triage.

5️⃣ Executive Reporting
    Generates:
        •Overall risk level
        •Summary insights
        •Recommended actions
        •LLM usage statistics
        •Model accuracy metrics

## How to Run
1️⃣ Install Dependencies
        pip install -r requirements.txt

2️⃣ Run the Dashboard
        streamlit run app.py

3️⃣ Click “Run Analysis”
    The system will:
        •Generate synthetic shipment data
        •Run full anomaly pipeline
        •Generate reports
        •Display dashboard results


Future Enhancements
    •Replace Z-score with adaptive detection (IQR / MAD)
    •Add model drift monitoring
    •Implement role-based authentication
    •Add export functionality
    •Convert to FastAPI + React production stack
    •Add machine learning–based risk scoring
