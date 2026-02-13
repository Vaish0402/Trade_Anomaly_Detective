import os
import json
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


# ==========================================================
# ADVANCED USAGE TRACKER
# ==========================================================

class AdvancedUsageTracker:
    def __init__(self):
        self.provider = "Groq"
        self.model = "llama-3.3-70b-versatile"
        self.total_calls = 0
        self.tokens = {"input": 0, "output": 0, "total": 0}
        self.breakdown = {
            "hs_code_validation": 0,
            "executive_summary": 0,
            "buyer_pattern_analysis": 0
        }
        self.latencies = []

    def log(self, task: str, input_tokens: int, output_tokens: int, latency_ms: float):
        self.total_calls += 1
        self.tokens["input"] += input_tokens
        self.tokens["output"] += output_tokens
        self.tokens["total"] += (input_tokens + output_tokens)

        if task in self.breakdown:
            self.breakdown[task] += 1
        else:
            self.breakdown[task] = 1

        self.latencies.append(latency_ms)

    # IMPORTANT:
    # This method will ONLY be called from report_generator.py
    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        avg_latency = (
            sum(self.latencies) / len(self.latencies)
            if self.latencies else 0
        )

        report = {
            "provider": self.provider,
            "model": self.model,
            "total_llm_calls": self.total_calls,
            "token_usage": self.tokens,
            "breakdown_by_task": self.breakdown,
            "average_latency_ms": round(avg_latency, 2),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "notes": "LLM only processes suspicious rows from Layer 1 & 2."
        }

        with open(path, "w") as f:
            json.dump(report, f, indent=4)


usage_tracker = AdvancedUsageTracker()


# ==========================================================
# LLM DETECTOR
# ==========================================================

class LLMDetector:

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    # ==========================================================
    # 1️⃣ HS CODE VALIDATION
    # ==========================================================

    def detect_hs_code_mismatch(self, suspicious_rows: List[Dict]) -> List[Dict]:

        results = []

        if not suspicious_rows:
            return results

        def validate(row):

            prompt = f"""
You are a global trade classification expert.

Question:
Does HS code {row['hs_code']} correctly classify the product:
"{row['product_description']}" ?

Respond strictly in JSON:

{{
  "is_mismatch": true/false,
  "reason": "short explanation",
  "severity": "Low/Medium/High"
}}
"""

            start = time.time()

            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "Respond ONLY in valid JSON."},
                        {"role": "user", "content": prompt}
                    ]
                )

                latency = (time.time() - start) * 1000

                usage_tracker.log(
                    task="hs_code_validation",
                    input_tokens=completion.usage.prompt_tokens,
                    output_tokens=completion.usage.completion_tokens,
                    latency_ms=latency
                )

                response = json.loads(completion.choices[0].message.content)

                if response.get("is_mismatch"):

                    return {
                        "shipment_id": row["shipment_id"],
                        "category": "LLM",
                        "type": "HS Code Mismatch",
                        "layer": "llm",
                        "evidence": response.get("reason"),
                        "severity": response.get("severity", "High")
                    }

            except Exception as e:
                print(f"LLM error for {row['shipment_id']}: {e}")

            return None

        # Parallel execution
        with ThreadPoolExecutor(max_workers=min(5, len(suspicious_rows))) as executor:
            responses = list(executor.map(validate, suspicious_rows))

        return [r for r in responses if r is not None]

    # ==========================================================
    # 2️⃣ BUYER PATTERN ANALYSIS
    # ==========================================================

    def analyze_buyer_pattern(self, buyer_shipments: List[Dict]):

        if not buyer_shipments:
            return None

        prompt = f"""
You are a trade risk analyst.

Here are recent shipments from one buyer:
{json.dumps(buyer_shipments, indent=2)}

Do you observe unusual behavioral patterns?

Respond strictly in JSON:

{{
  "is_risky_pattern": true/false,
  "reason": "brief explanation",
  "severity": "Low/Medium/High"
}}
"""

        start = time.time()

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Respond ONLY in valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )

            latency = (time.time() - start) * 1000

            usage_tracker.log(
                task="buyer_pattern_analysis",
                input_tokens=completion.usage.prompt_tokens,
                output_tokens=completion.usage.completion_tokens,
                latency_ms=latency
            )

            return json.loads(completion.choices[0].message.content)

        except Exception as e:
            print(f"Buyer pattern LLM error: {e}")

        return None

    # ==========================================================
    # 3️⃣ EXECUTIVE SUMMARY GENERATION
    # ==========================================================

    def generate_executive_summary(self, anomalies: List[Dict]) -> str:

        if not anomalies:
            return "No anomalies detected."

        prompt = f"""
You are a trade compliance executive advisor.

Summarize the following detected anomalies for senior leadership.

Focus on:
- Overall risk level
- High severity issues
- Financial exposure
- Compliance risks
- Recommended actions

Anomalies:
{json.dumps(anomalies, indent=2)}

Respond strictly in JSON:

{{
  "overall_risk_level": "Low/Medium/High",
  "summary": "concise executive explanation",
  "recommended_actions": ["action1", "action2"]
}}
"""

        start = time.time()

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Respond ONLY in valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )

            latency = (time.time() - start) * 1000

            usage_tracker.log(
                task="executive_summary",
                input_tokens=completion.usage.prompt_tokens,
                output_tokens=completion.usage.completion_tokens,
                latency_ms=latency
            )

            return completion.choices[0].message.content

        except Exception as e:
            return f"Executive summary generation failed: {e}"
