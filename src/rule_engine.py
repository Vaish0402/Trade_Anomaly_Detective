import pandas as pd


class RuleEngine:
    """
    Layer 1: Deterministic Rule-Based Detection
    No ML. No LLM. Pure business logic.
    """

    def __init__(self, shipments_df):
        """
        shipments_df: Can be full dataset or pre-filtered subset.
        """
        self.df = shipments_df.copy()
        self.anomalies = []

    # ==========================================================
    # ENTRY POINT
    # ==========================================================
    def run_all_checks(self):

        self.check_math_validation()
        self.check_drawback_violation()
        self.check_payment_integrity()
        self.check_cif_freight_logic()
        self.check_insurance_sanity()

        return self.anomalies

    # ==========================================================
    # 1️⃣ total_fob ≠ quantity × unit_price
    # ==========================================================
    def check_math_validation(self):

        tolerance = 0.01  # float tolerance

        mask = abs(
            self.df["total_fob"] -
            (self.df["quantity"] * self.df["unit_price"])
        ) > tolerance

        for _, row in self.df[mask].iterrows():
            self.anomalies.append({
                "shipment_id": row["shipment_id"],
                "category": "Rule-Based",
                "type": "Math Validation Error",
                "layer": "rule",
                "evidence": f"FOB={row['total_fob']} ≠ {row['quantity']}×{row['unit_price']}",
                "severity": "High",
                "impact": "Financial misstatement or invoice manipulation"
            })

    # ==========================================================
    # 2️⃣ drawback claimed when customs rejected
    # ==========================================================
    def check_drawback_violation(self):

        mask = (
            (self.df["customs_status"] == "rejected") &
            (self.df["drawback_amount"] > 0)
        )

        for _, row in self.df[mask].iterrows():
            self.anomalies.append({
                "shipment_id": row["shipment_id"],
                "category": "Rule-Based",
                "type": "Illegal Drawback Claim",
                "layer": "rule",
                "evidence": "Drawback claimed on rejected shipment",
                "severity": "High",
                "impact": "Regulatory violation and potential fraud"
            })

    # ==========================================================
    # 3️⃣ payment_status = received but days_to_payment is null
    # ==========================================================
    def check_payment_integrity(self):

        mask = (
            (self.df["payment_status"] == "received") &
            (self.df["days_to_payment"].isna())
        )

        for _, row in self.df[mask].iterrows():
            self.anomalies.append({
                "shipment_id": row["shipment_id"],
                "category": "Rule-Based",
                "type": "Payment Data Integrity Issue",
                "layer": "rule",
                "evidence": "Payment marked received but days_to_payment is NULL",
                "severity": "Medium",
                "impact": "Incomplete financial tracking"
            })

    # ==========================================================
    # 4️⃣ freight_cost = 0 when incoterm = CIF
    # ==========================================================
    def check_cif_freight_logic(self):

        mask = (
            (self.df["incoterm"] == "CIF") &
            (self.df["freight_cost"] <= 0)
        )

        for _, row in self.df[mask].iterrows():
            self.anomalies.append({
                "shipment_id": row["shipment_id"],
                "category": "Rule-Based",
                "type": "CIF Freight Violation",
                "layer": "rule",
                "evidence": "CIF requires seller-paid freight but freight_cost is 0",
                "severity": "Medium",
                "impact": "Contractual non-compliance"
            })

    # ==========================================================
    # 5️⃣ Insurance sanity check against FOB value
    #
    # Assumption:
    # Insurance should typically be between 0.5% and 5% of FOB
    # ==========================================================
    def check_insurance_sanity(self):

        if "insurance_amount" not in self.df.columns:
            return  # Skip if column not present

        lower_bound = 0.005
        upper_bound = 0.05

        for _, row in self.df.iterrows():

            if row["insurance_amount"] <= 0:
                continue

            ratio = row["insurance_amount"] / row["total_fob"]

            if ratio < lower_bound or ratio > upper_bound:

                self.anomalies.append({
                    "shipment_id": row["shipment_id"],
                    "category": "Rule-Based",
                    "type": "Insurance Value Anomaly",
                    "layer": "rule",
                    "evidence": f"Insurance ratio={round(ratio,4)} outside expected range (0.5%-5%)",
                    "severity": "Medium",
                    "impact": "Possible under/over insurance risk exposure"
                })
