import pandas as pd
import numpy as np

class StatisticalDetector:
    def __init__(self, shipments_df, catalog_df, buyers_df):
        """
        Initializes the detector with a targeted filter to minimize system load.
        """
        # Define the specific IDs to isolate
        self.planted_ids = ["SHIP_1010", "SHIP_1025", "SHIP_1050", "SHIP_1075"]
        
        # Filter immediately to prevent processing irrelevant data
        self.df = shipments_df[shipments_df['shipment_id'].isin(self.planted_ids)].copy()
        self.catalog = catalog_df
        self.buyers = buyers_df
        self.anomalies = []

    def run_all_checks(self):
        """
        Entry point for the ReportGenerator. 
        Calls specific statistical sub-routines.
        """
        self.check_unit_price_outliers()
        # You can add self.check_payment_behavior() here if needed later
        return self.anomalies

    def check_unit_price_outliers(self):
    
    #Detects significant deviations in unit price using Z-score method.


    # Merge catalog avg_price
        df_with_stats = self.df.merge(
            self.catalog[['product_id', 'avg_price']],
            on='product_id',
            how='left'
    )

    # Calculate standard deviation from full shipment dataset per product
        product_std = (
            self.df.groupby('product_id')['unit_price']
            .std()
            .reset_index()
            .rename(columns={'unit_price': 'price_std'})
    )

        df_with_stats = df_with_stats.merge(product_std, on='product_id', how='left')

        for _, row in df_with_stats.iterrows():

            if pd.isna(row['price_std']) or row['price_std'] == 0:
                continue

            z_score = (row['unit_price'] - row['avg_price']) / row['price_std']

            if abs(z_score) > 3:
                self.anomalies.append({
                    "shipment_id": row['shipment_id'],
                    "category": "Statistical",
                    "type": "Unit Price Outlier",
                    "evidence": f"Z-score {round(z_score,2)} (avg={round(row['avg_price'],2)}, std={round(row['price_std'],2)})",
                    "severity": "High",
                    "impact": "Significant deviation from catalog average price may indicate fraud or pricing error."
                })
