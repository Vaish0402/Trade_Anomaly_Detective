import pandas as pd

class RuleEngine:
    def __init__(self, shipments_df):
        self.df = shipments_df
        self.anomalies = []

    def run_all_checks(self):
        self.check_math_consistency()
        self.check_cif_freight()
        self.check_drawback_status()
        self.check_payment_logic()
        return self.anomalies

    def check_math_consistency(self):
        """Total FOB must equal Quantity x Unit Price."""
        # Using a small tolerance for floating point math
        mask = abs(self.df['total_fob'] - (self.df['quantity'] * self.df['unit_price'])) > 0.01
        inconsistent = self.df[mask]
        for _, row in inconsistent.iterrows():
            self.anomalies.append({
                "shipment_id": row['shipment_id'],
                "category": "Rule-Based",
                "type": "Math Error",
                "evidence": f"FOB {row['total_fob']} != {row['quantity']} * {row['unit_price']}",
                "severity": "High"
            })

    def check_cif_freight(self):
        """CIF means Cost, Insurance, and Freight; Seller MUST pay freight."""
        mask = (self.df['incoterm'] == 'CIF') & (self.df['freight_cost'] <= 0)
        violations = self.df[mask]
        for _, row in violations.iterrows():
            self.anomalies.append({
                "shipment_id": row['shipment_id'],
                "category": "Rule-Based",
                "type": "Incoterm Violation",
                "evidence": "Incoterm is CIF but freight_cost is 0",
                "severity": "Medium"
            })

    def check_drawback_status(self):
        """Duty drawback cannot be claimed if customs rejected the shipment."""
        mask = (self.df['customs_status'] == 'rejected') & (self.df['drawback_amount'] > 0)
        violations = self.df[mask]
        for _, row in violations.iterrows():
            self.anomalies.append({
                "shipment_id": row['shipment_id'],
                "category": "Rule-Based",
                "type": "Compliance Risk",
                "evidence": "Drawback claimed on rejected shipment",
                "severity": "High"
            })

    def check_payment_logic(self):
        """Payment received status requires a valid 'days_to_payment' value."""
        mask = (self.df['payment_status'] == 'received') & (self.df['days_to_payment'].isna())
        violations = self.df[mask]
        for _, row in violations.iterrows():
            self.anomalies.append({
                "shipment_id": row['shipment_id'],
                "category": "Rule-Based",
                "type": "Data Integrity",
                "evidence": "Status is 'received' but days_to_payment is null",
                "severity": "Low"
            })