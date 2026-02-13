import os
import json
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class UsageTracker:
    def __init__(self):
        self.total_calls = 0
        self.total_tokens = 0
        self.estimated_cost = 0.0

    def log(self, tokens):
        self.total_calls += 1
        self.total_tokens += tokens
        # Rough estimate for Llama 3 on Groq (usually free, but for report purposes)
        self.estimated_cost += (tokens / 1000) * 0.0001 

    def save(self, path):
        with open(path, 'w') as f:
            json.dump({
                "total_calls": self.total_calls,
                "total_tokens": self.total_tokens,
                "estimated_cost_usd": round(self.estimated_cost, 6)
            }, f, indent=4)

usage_tracker = UsageTracker()

class LLMDetector:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"  # Updated model for better reasoning

    def _validate_single_shipment(self, row: Dict, catalog_df) -> Dict:
        """Internal helper to validate one row; used for parallel execution."""
        product_desc = row.get('product_description', 'Unknown')
        hs_code = row.get('hs_code', 'Unknown')
        
        prompt = f"""
        Act as a Global Trade Compliance Expert. 
        Analyze if this HS Code is correct for the product description.
        
        Product: {product_desc}
        HS Code: {hs_code}
        
        Return ONLY a JSON object:
        {{
            "is_mismatch": true/false,
            "reason": "Short explanation",
            "severity": "Medium/High"
        }}
        """
        
        try:
            start_time = time.time()
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                response_format={"type": "json_object"}
            )
            
            # Track usage
            usage_tracker.log(completion.usage.total_tokens)
            
            res = json.loads(completion.choices[0].message.content)
            
            if res.get("is_mismatch"):
                return {
                    "shipment_id": row['shipment_id'],
                    "category": "HS Code Mismatch",
                    "type": "LLM Reasoning",
                    "severity": res.get("severity", "Medium"),
                    "evidence": res.get("reason"),
                    "recommendation": "Verify HS code against customs tariff schedule."
                }
        except Exception as e:
            print(f"LLM Error for {row['shipment_id']}: {e}")
        return None

    def detect_hs_code_mismatch(self, shipments_to_check: List[Dict], catalog_df) -> List[Dict]:
        """Runs validation in parallel to prevent the 'Stuck' issue."""
        if not shipments_to_check:
            return []

        # We use max_workers=5 to avoid hitting Groq's rate limits too fast
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda r: self._validate_single_shipment(r, catalog_df), shipments_to_check))
        
        # Filter out None results (where no mismatch was found or error occurred)
        return [r for r in results if r is not None]

    def generate_executive_summary(self, anomalies: List[Dict]) -> str:
        """Generates a markdown summary for the Operations Head."""
        prompt = f"""
        Generate a 1-page Executive Summary for a Head of Operations.
        Based on these detected anomalies: {json.dumps(anomalies[:15])}
        Include:
        1. Top 3 Urgent Issues
        2. Cost Implications
        3. Immediate Actions
        Format: Professional Markdown.
        """
        try:
            completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error generating summary: {e}"