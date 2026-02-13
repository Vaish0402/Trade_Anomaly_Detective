import pandas as pd
import json
import os
from datetime import datetime, timezone

from rule_engine import RuleEngine
from statistical_detector import StatisticalDetector
from llm_detector import LLMDetector, usage_tracker


class ReportGenerator:

    def __init__(self, data_dir="data", output_dir="output"):

        self.data_dir = data_dir
        self.output_dir = output_dir

        os.makedirs(self.output_dir, exist_ok=True)

        self.shipments = pd.read_csv(os.path.join(data_dir, "shipments.csv"))
        self.catalog = pd.read_csv(os.path.join(data_dir, "product_catalog.csv"))
        self.buyers = pd.read_csv(os.path.join(data_dir, "buyers.csv"))

        with open(os.path.join(data_dir, "planted_anomalies.json"), "r") as f:
            self.planted = json.load(f)

    # ==========================================================
    # MAIN PIPELINE
    # ==========================================================

    def run_pipeline(self):

        print("🔍 Running Layer 1: Rule Engine...")
        rule_engine = RuleEngine(self.shipments)
        rule_hits = rule_engine.run_all_checks()

        print("📊 Running Layer 2: Statistical Detector...")
        statistical_detector = StatisticalDetector(
            self.shipments, self.catalog, self.buyers
        )
        statistical_hits = statistical_detector.run_all_checks()

        all_layer12_hits = rule_hits + statistical_hits
        print(f"Layer 1 + 2 detected {len(all_layer12_hits)} anomalies.")

        # ======================================================
        # Layer 3 — LLM (Only Suspicious HS)
        # ======================================================

        llm_detector = LLMDetector()
        suspicious_hs = []

        for _, row in self.shipments.iterrows():
            catalog_row = self.catalog[
                self.catalog["product_id"] == row["product_id"]
            ]

            if not catalog_row.empty:
                correct_hs = str(catalog_row.iloc[0]["hs_code"])
                if str(row["hs_code"]) != correct_hs:
                    suspicious_hs.append(row.to_dict())

        print(f"Sending {len(suspicious_hs)} HS cases to LLM...")

        llm_hits = llm_detector.detect_hs_code_mismatch(suspicious_hs)

        # ======================================================
        # Combine & Deduplicate
        # ======================================================

        combined = all_layer12_hits + llm_hits

        unique = {}
        for a in combined:
            key = (a.get("shipment_id"), a.get("type"))
            unique[key] = a

        final_anomalies = list(unique.values())

        # 🔥 Always rank BEFORE saving
        final_anomalies = self.rank_anomalies(final_anomalies)

        # Save reports
        self.save_anomaly_report(final_anomalies)
        self.generate_summary(final_anomalies, llm_detector)
        self.calculate_accuracy(final_anomalies)
        usage_tracker.save(os.path.join(self.output_dir, "llm_usage_report.json"))

        print("✅ All reports generated successfully.")

    # ==========================================================
    # RISK SCORING
    # ==========================================================

    def rank_anomalies(self, anomalies):

        severity_map = {
            "Critical": 80,
            "High": 60,
            "Medium": 40,
            "Low": 20
        }

        ranked = []

        for anomaly in anomalies:

            severity = anomaly.get("severity", "Medium")
            base = severity_map.get(severity, 40)

            # Financial boost
            financial_boost = 0
            evidence = str(anomaly.get("evidence", ""))

            amount = 0
            for token in evidence.replace(",", "").split():
                try:
                    val = float(token)
                    if val > amount:
                        amount = val
                except:
                    continue

            if amount > 1_000_000:
                financial_boost = 20
            elif amount > 100_000:
                financial_boost = 10
            elif amount > 0:
                financial_boost = 5

            # Type bonus
            type_bonus = 0
            t = anomaly.get("type", "")

            if "FOB" in t:
                type_bonus += 10
            if "Payment" in t:
                type_bonus += 15
            if "HS" in t:
                type_bonus += 10
            if "Behavioral" in t:
                type_bonus += 20

            risk_score = min(100, base + financial_boost + type_bonus)

            anomaly["risk_score"] = risk_score

            if risk_score >= 85:
                anomaly["priority"] = "P1 - Immediate"
            elif risk_score >= 70:
                anomaly["priority"] = "P2 - High"
            elif risk_score >= 50:
                anomaly["priority"] = "P3 - Medium"
            else:
                anomaly["priority"] = "P4 - Low"

            ranked.append(anomaly)

        # Safe sort
        ranked.sort(key=lambda x: x.get("risk_score", 0), reverse=True)

        return ranked

    # ==========================================================
    # OUTPUT 1 — ANOMALY REPORT
    # ==========================================================

    def save_anomaly_report(self, anomalies):

        output_path = os.path.join(self.output_dir, "anomaly_report.json")

        highest = max(
            [a.get("risk_score", 0) for a in anomalies],
            default=0
        )

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_anomalies": len(anomalies),
            "highest_risk_score": highest,
            "anomalies": anomalies
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=4)

    # ==========================================================
    # OUTPUT 2 — EXECUTIVE SUMMARY
    # ==========================================================

    def generate_summary(self, anomalies, llm_detector):

        summary_json = llm_detector.generate_executive_summary(anomalies)

        try:
            summary_data = json.loads(summary_json)

            md_content = f"""
# Executive Summary

**Overall Risk Level:** {summary_data.get("overall_risk_level")}

## Summary
{summary_data.get("summary")}

## Recommended Immediate Actions
"""

            for action in summary_data.get("recommended_actions", []):
                md_content += f"- {action}\n"

        except Exception:
            md_content = summary_json

        with open(os.path.join(self.output_dir, "executive_summary.md"), "w") as f:
            f.write(md_content)

    # ==========================================================
    # OUTPUT 3 — ACCURACY
    # ==========================================================

    def calculate_accuracy(self, detected):

        planted_ids = {a["shipment_id"] for a in self.planted}
        detected_ids = {a["shipment_id"] for a in detected}

        tp = len(planted_ids & detected_ids)
        fp = len(detected_ids - planted_ids)
        fn = len(planted_ids - detected_ids)

        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0

        accuracy_report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "status": "Perfect Match" if fn == 0 else "Review Required"
        }

        with open(os.path.join(self.output_dir, "accuracy_report.json"), "w") as f:
            json.dump(accuracy_report, f, indent=4)

    def run_pipeline_with_progress(self, progress_callback=None):

        def update(progress, message):
            if progress_callback:
                progress_callback(progress, message)

    # Layer 1
        update(10, "Running Rule Engine...")
        rule_engine = RuleEngine(self.shipments)
        rule_hits = rule_engine.run_all_checks()

    # Layer 2
        update(30, "Running Statistical Detector...")
        statistical_detector = StatisticalDetector(
            self.shipments, self.catalog, self.buyers
        )
        statistical_hits = statistical_detector.run_all_checks()

        all_layer12_hits = rule_hits + statistical_hits

    # Layer 3
        update(55, "Running LLM HS Code Validation...")
        llm_detector = LLMDetector()

        suspicious_hs = []
        for _, row in self.shipments.iterrows():
            catalog_row = self.catalog[
                self.catalog["product_id"] == row["product_id"]
            ]
            if not catalog_row.empty:
                correct_hs = str(catalog_row.iloc[0]["hs_code"])
                if str(row["hs_code"]) != correct_hs:
                    suspicious_hs.append(row.to_dict())

        llm_hits = llm_detector.detect_hs_code_mismatch(suspicious_hs)

    # Combine
        update(75, "Ranking anomalies...")
        combined = all_layer12_hits + llm_hits
        unique = {(a["shipment_id"], a["type"]): a for a in combined}
        final_anomalies = self.rank_anomalies(list(unique.values()))

    # Save
        update(85, "Saving reports...")
        self.save_anomaly_report(final_anomalies)
        self.generate_summary(final_anomalies, llm_detector)
        self.calculate_accuracy(final_anomalies)
        usage_tracker.save(os.path.join(self.output_dir, "llm_usage_report.json"))

        update(100, "Analysis Complete.")

        return final_anomalies

if __name__ == "__main__":
    rg = ReportGenerator()
    rg.run_pipeline()
