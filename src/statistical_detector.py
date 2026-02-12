import pandas as pd
import numpy as np

class StatisticalDetector:
    def __init__(self, shipments_df, catalog_df, buyers_df):
        self.df = shipments_df
        self.catalog = catalog_df
        self.buyers = buyers_df
        self.anomalies = []

    def detect_iqr_outliers(self, group_col, target_col, severity="Medium"):
        """
        Identifies outliers using the 1.5 * IQR rule within specific groups.
        Useful for catching price spikes per product or transit delays per route.
        """
        # Group by category (e.g., product_id) to ensure context-aware detection
        for name, group in self.df.groupby(group_col):
            if len(group) < 5:
                continue  # Skip groups with insufficient data for statistical significance

            q1 = group[target_col].quantile(0.25)
            q3 = group[target_col].quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            # Filter rows outside the statistical 'normal' range
            outliers = group[(group[target_col] < lower_bound) | (group[target_col] > upper_bound)]

            for _, row in outliers.iterrows():
                self.anomalies.append({
                    "shipment_id": row['shipment_id'],
                    "category": "Statistical",
                    "type": f"{target_col.replace('_', ' ').title()} Outlier",
                    "evidence": f"Value {row[target_col]} is outside bounds [{lower_bound:.2f}, {upper_bound:.2f}] for {name}",
                    "severity": severity,
                    "impact": f"Significant deviation in {target_col.replace('_', ' ')} may indicate fraud or inefficiency."
                })

    def check_payment_behavior(self):
        """
        Detects shifts in buyer behavior by comparing current payment days 
        against the historical average in the buyers table.
        """
        # Merge to get historical 'avg_payment_days' per buyer
        merged = self.df.merge(self.buyers[['buyer_id', 'avg_payment_days']], on='buyer_id')
        
        # Flag if payment took significantly longer (e.g., > 50% increase) than historical average
        late_mask = merged['days_to_payment'] > (merged['avg_payment_days'] * 1.5)
        late_payments = merged[late_mask]
        
        for _, row in late_payments.iterrows():
            self.anomalies.append({
                "shipment_id": row['shipment_id'],
                "category": "Statistical",
                "type": "Payment Behavior Shift",
                "evidence": f"Payment took {row['days_to_payment']} days (Buyer historical avg: {row['avg_payment_days']})",
                "severity": "Medium",
                "impact": "Potential liquidity issues or deteriorating relationship with buyer."
            })

    def run_all_checks(self):
        """Execute all Layer 2 statistical detections."""
        # 1. Price outliers per product (Required: catches unit price spikes)
        self.detect_iqr_outliers('product_id', 'unit_price', severity="High")
        
        # 2. Transit time outliers (Required: catches route inefficiencies)
        self.detect_iqr_outliers('product_id', 'transit_time_days', severity="Medium")
        
        # 3. Freight cost outliers per Incoterm (Required: catches cost spikes)
        self.detect_iqr_outliers('incoterm', 'freight_cost', severity="Medium")
        
        # 4. Buyer payment behavior (Required: catches trend changes)
        self.check_payment_behavior()
        
        return self.anomalies