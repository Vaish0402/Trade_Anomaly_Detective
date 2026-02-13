import pandas as pd
import numpy as np


class StatisticalDetector:
    """
    Z-Score based statistical detection.
    Computes distribution from full dataset,
    but applies anomaly detection ONLY to filtered rows.
    """

    def __init__(self, full_shipments_df, catalog_df, buyers_df):

        # Full dataset used ONLY for computing baselines
        self.full_df = full_shipments_df.copy()

        self.catalog = catalog_df
        self.buyers = buyers_df
        self.anomalies = []

        # ----------------------------------------------
        # FILTER TARGET ROWS (Only suspicious candidates)
        # ----------------------------------------------

        # 1️⃣ Potential price anomalies (extreme unit_price)
        self.price_candidates = self.full_df[
            (self.full_df["unit_price"] > self.full_df["unit_price"].quantile(0.99)) |
            (self.full_df["unit_price"] < self.full_df["unit_price"].quantile(0.01))
        ]

        # 2️⃣ Buyer payment delay spikes
        self.payment_candidates = self.full_df[
            self.full_df["days_to_payment"] > 90
        ]

        # 3️⃣ Transit time spikes
        self.transit_candidates = self.full_df[
            self.full_df["transit_time_days"] > 60
        ]

    # ======================================================
    # ENTRY POINT
    # ======================================================
    def run_all_checks(self):

        self.check_unit_price_outliers()
        self.check_buyer_payment_anomalies()
        self.check_transit_time_anomalies()

        return self.anomalies

    # ======================================================
    # 1️⃣ UNIT PRICE OUTLIERS
    # ======================================================
    def check_unit_price_outliers(self):

        if self.price_candidates.empty:
            return

        for _, row in self.price_candidates.iterrows():

            product_group = self.full_df[
                self.full_df["product_id"] == row["product_id"]
            ]

            mean_price = product_group["unit_price"].mean()
            std_price = product_group["unit_price"].std()

            if std_price == 0 or np.isnan(std_price):
                continue

            z_score = (row["unit_price"] - mean_price) / std_price

            if abs(z_score) > 3:

                self.anomalies.append({
                    "shipment_id": row["shipment_id"],
                    "category": "Statistical",
                    "type": "Unit Price Outlier",
                    "layer": "statistical",
                    "evidence": f"Z-score={round(z_score,2)} | mean={round(mean_price,2)} | std={round(std_price,2)}",
                    "severity": "High"
                })

    # ======================================================
    # 2️⃣ BUYER PAYMENT ANOMALY
    # ======================================================
    def check_buyer_payment_anomalies(self):

        if self.payment_candidates.empty:
            return

        for _, row in self.payment_candidates.iterrows():

            buyer_group = self.full_df[
                self.full_df["buyer_id"] == row["buyer_id"]
            ]

            mean_days = buyer_group["days_to_payment"].mean()
            std_days = buyer_group["days_to_payment"].std()

            if std_days == 0 or np.isnan(std_days):
                continue

            z_score = (row["days_to_payment"] - mean_days) / std_days

            if abs(z_score) > 3:

                self.anomalies.append({
                    "shipment_id": row["shipment_id"],
                    "category": "Statistical",
                    "type": "Buyer Payment Delay Anomaly",
                    "layer": "statistical",
                    "evidence": f"Z-score={round(z_score,2)} | buyer_avg={round(mean_days,2)} | std={round(std_days,2)}",
                    "severity": "Medium"
                })

    # ======================================================
    # 3️⃣ TRANSIT TIME ANOMALY
    # ======================================================
    def check_transit_time_anomalies(self):

        if self.transit_candidates.empty:
            return

        mean_transit = self.full_df["transit_time_days"].mean()
        std_transit = self.full_df["transit_time_days"].std()

        if std_transit == 0 or np.isnan(std_transit):
            return

        for _, row in self.transit_candidates.iterrows():

            z_score = (row["transit_time_days"] - mean_transit) / std_transit

            if abs(z_score) > 3:

                self.anomalies.append({
                    "shipment_id": row["shipment_id"],
                    "category": "Statistical",
                    "type": "Transit Time Anomaly",
                    "layer": "statistical",
                    "evidence": f"Z-score={round(z_score,2)} | global_avg={round(mean_transit,2)} | std={round(std_transit,2)}",
                    "severity": "Medium"
                })
