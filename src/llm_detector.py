import json
import os
import time
from datetime import datetime
from groq import Groq
from typing import List, Dict

# --- TRACKER DEFINITION ---
class LLMUsageTracker:
    def __init__(self, provider="Groq", model="llama-3.3-70b-versatile"):
        self.data = {
            "provider": provider,
            "model": model,
            "total_calls": 0,
            "total_tokens": {"input": 0, "output": 0, "total": 0},
            "estimated_cost_usd": 0.0,
            "breakdown_by_task": {
                "hs_code_validation": {"calls": 0, "tokens": 0, "description": "Validating HS codes match product descriptions"},
                "executive_summary": {"calls": 0, "tokens": 0, "description": "Generating executive summary from anomaly report"}
            },
            "avg_latency_ms": 0,
            "timestamp": "",
            "notes": ""
        }
        self.latencies = []

    def log_call(self, task, response, latency_ms):
        usage = response.usage
        prompt_tokens = usage.prompt_tokens
        completion_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        self.data["total_calls"] += 1
        self.data["total_tokens"]["input"] += prompt_tokens
        self.data["total_tokens"]["output"] += completion_tokens
        self.data["total_tokens"]["total"] += total_tokens
        
        if task in self.data["breakdown_by_task"]:
            self.data["breakdown_by_task"][task]["calls"] += 1
            self.data["breakdown_by_task"][task]["tokens"] += total_tokens
        
        self.latencies.append(latency_ms)
        self.data["avg_latency_ms"] = sum(self.latencies) / len(self.latencies)
        self.data["estimated_cost_usd"] += (total_tokens / 1_000_000) * 0.59

    def save(self, path):
        self.data["timestamp"] = datetime.utcnow().isoformat() + "Z"
        with open(path, "w") as f:
            json.dump(self.data, f, indent=2)

# This makes usage_tracker available for import in report_generator.py
usage_tracker = LLMUsageTracker()

# --- DETECTOR DEFINITION ---
class LLMDetector:
    def __init__(self):
        # Fallback to a dummy key if env variable is missing to avoid crash
        api_key = os.environ.get("GROQ_API_KEY", "MISSING_KEY")
        self.client = Groq(api_key=api_key)
        self.tracker = usage_tracker

    def detect_hs_code_mismatch(self, shipments_to_check: List[Dict], catalog_df) -> List[Dict]:
        anomalies = []
        for row in shipments_to_check:
            start_time = time.time()
            
            # Enrich data using product_id to find the actual name
            product_info = catalog_df[catalog_df['product_id'] == row['product_id']]
            product_name = product_info['name'].values[0] if not product_info.empty else "Unknown Product"

            prompt = (f"Product: {product_name}. HS Code: {row['hs_code']}. "
                      f"Is this correct? Answer YES/NO with reasoning.")
            
            try:
                response = self.client.chat.completions.create(
                    model=self.tracker.data["model"],
                    messages=[{"role": "user", "content": prompt}]
                )
                latency = (time.time() - start_time) * 1000
                self.tracker.log_call("hs_code_validation", response, latency)

                content = response.choices[0].message.content
                if "NO" in content.upper():
                    anomalies.append({
                        "shipment_id": row["shipment_id"],
                        "layer": "llm",
                        "category": "Classification",
                        "description": "HS code mismatch",
                        "evidence": {
                            "product": product_name,
                            "hs_code": row['hs_code'],
                            "llm_reasoning": content.strip()
                        },
                        "severity": "High"
                    })
            except Exception as e:
                self.tracker.data["notes"] += f"Error ID {row['shipment_id']}: {str(e)}; "
        return anomalies

    def generate_executive_summary(self, anomalies: List[Dict]) -> str:
        start_time = time.time()
        prompt = f"Write a non-technical summary of these trade anomalies: {json.dumps(anomalies)}"
        try:
            response = self.client.chat.completions.create(
                model=self.tracker.data["model"],
                messages=[{"role": "user", "content": prompt}]
            )
            latency = (time.time() - start_time) * 1000
            self.tracker.log_call("executive_summary", response, latency)
            return response.choices[0].message.content
        except Exception as e:
            return f"Summary failed: {str(e)}"