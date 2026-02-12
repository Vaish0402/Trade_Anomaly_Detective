import pandas as pd
import json
import os
import sys

# Ensure local imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rule_engine import RuleEngine
from statistical_detector import StatisticalDetector
from llm_detector import LLMDetector, usage_tracker

class ReportGenerator:
    def __init__(self, data_dir='data', output_dir='output'):
        self.data_dir = data_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load all required DataFrames
        self.shipments = pd.read_csv(os.path.join(data_dir, 'shipments.csv'))
        self.catalog = pd.read_csv(os.path.join(data_dir, 'product_catalog.csv'))
        self.buyers = pd.read_csv(os.path.join(data_dir, 'buyers.csv'))
        
        # Load Ground Truth for Accuracy Reporting
        with open(os.path.join(data_dir, 'planted_anomalies.json'), 'r') as f:
            self.planted = json.load(f)

    def run_pipeline(self):
        print("Starting Detection Pipeline...")
        all_detected = []

        # Layer 1: Rule-Based
        print(" Running Layer 1 (Rules)...")
        re = RuleEngine(self.shipments)
        all_detected.extend(re.run_all_checks())

        # Layer 2: Statistical - FIXED: Now passing all 3 required arguments
        print(" Running Layer 2 (Statistical)...")
        sd = StatisticalDetector(self.shipments, self.catalog, self.buyers)
        all_detected.extend(sd.run_all_checks())

        # --- Layer 3: LLM reasoning ---
        print("Running Layer 3 (LLM Reasoning)...")
        ld = LLMDetector()
        
        # We only send suspicious rows to the LLM to remain token-efficient
        suspicious_ids = {a['shipment_id'] for a in all_detected}
        suspicious_data = self.shipments[self.shipments['shipment_id'].isin(suspicious_ids)].to_dict('records')
        
        # FIXED: Now passing both the data and the catalog
        llm_hits = ld.detect_hs_code_mismatch(suspicious_data, self.catalog)
        all_detected.extend(llm_hits)

        # 1. Save Anomaly Report
        report_path = os.path.join(self.output_dir, 'anomaly_report.json')
        with open(report_path, 'w') as f:
            json.dump(all_detected, f, indent=4)

        # 2. Generate Executive Summary
        summary = ld.generate_executive_summary(all_detected)
        with open(os.path.join(self.output_dir, 'executive_summary.md'), 'w') as f:
            f.write(summary)

        # 3. Save Accuracy Report
        self.calculate_accuracy(all_detected)

        # 4. Save Usage Report
        usage_tracker.save(os.path.join(self.output_dir, "llm_usage_report.json"))
        
        print(f"Analysis complete. Results in '{self.output_dir}/'")

    def calculate_accuracy(self, detected):
        """Compares detected results against the ground truth"""
        planted_ids = {a['shipment_id'] for a in self.planted}
        detected_ids = {a['shipment_id'] for a in detected}
        
        tp = len(planted_ids.intersection(detected_ids))
        fp = len(detected_ids - planted_ids)
        fn = len(planted_ids - detected_ids)
        
        metrics = {
            "precision": round(tp / (tp + fp), 2) if (tp + fp) > 0 else 0,
            "recall": round(tp / (tp + fn), 2) if (tp + fn) > 0 else 0,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn
        }
        with open(os.path.join(self.output_dir, 'accuracy_report.json'), 'w') as f:
            json.dump(metrics, f, indent=4)

if __name__ == "__main__":
    rg = ReportGenerator()
    rg.run_pipeline()