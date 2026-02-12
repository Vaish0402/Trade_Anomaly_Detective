import pandas as pd
import numpy as np
import random
import json
import os

# Set seed for reproducibility
np.random.seed(42)

def generate_data():
    # 1. Setup Product Catalog
    products = [
        {"product_id": "P001", "name": "Organic Cotton Tee", "hs_code": "610910", "avg_price": 5.50},
        {"product_id": "P002", "name": "Silk Scarf", "hs_code": "621410", "avg_price": 22.00},
        {"product_id": "P003", "name": "Leather Handbag", "hs_code": "420221", "avg_price": 45.00},
        {"product_id": "P004", "name": "Ceramic Vase", "hs_code": "691310", "avg_price": 12.00},
        {"product_id": "P005", "name": "Basmati Rice 5kg", "hs_code": "100630", "avg_price": 8.00},
    ]
    df_catalog = pd.DataFrame(products)

    # 2. Setup Buyers
    buyers = [
        {"buyer_id": "B_USA_01", "name": "Global Retail Corp", "country": "USA", "avg_payment_days": 30},
        {"buyer_id": "B_UAE_02", "name": "Desert Trading", "country": "UAE", "avg_payment_days": 15},
        {"buyer_id": "B_GER_03", "name": "EuroGoods GmbH", "country": "Germany", "avg_payment_days": 45},
    ]
    df_buyers = pd.DataFrame(buyers)

    # 3. Generate 250 Base Shipments
    data = []
    for i in range(250):
        prod = random.choice(products)
        buyer = random.choice(buyers)
        qty = random.randint(100, 1000)
        unit_price = round(prod['avg_price'] * np.random.uniform(0.95, 1.05), 2)
        fob_value = round(qty * unit_price, 2)
        
        row = {
            "shipment_id": f"SHIP_{1000+i}",
            "buyer_id": buyer['buyer_id'],
            "product_id": prod['product_id'],
            "hs_code": prod['hs_code'],
            "quantity": qty,
            "unit_price": unit_price,
            "total_fob": fob_value,
            "incoterm": random.choice(["FOB", "CIF", "EXW"]),
            "freight_cost": random.randint(500, 2000),
            "customs_status": "cleared",
            "drawback_amount": round(fob_value * 0.02, 2),
            "payment_status": "received",
            "days_to_payment": random.randint(10, 50),
            "transit_time_days": random.randint(15, 40)
        }
        data.append(row)

    df_shipments = pd.DataFrame(data)

    # 4. INJECT ANOMALIES (The "Planted" Data)
    planted_anomalies = []

    # Category 1: Rule-Based - Math Error
    idx = 10
    df_shipments.at[idx, 'total_fob'] = 500.00  # Should be qty * unit_price
    planted_anomalies.append({
        "shipment_id": df_shipments.at[idx, 'shipment_id'],
        "category": "Math Inconsistency",
        "description": "Total FOB does not match quantity x unit price"
    })

    # Category 2: Rule-Based - CIF Freight Logic
    idx = 25
    df_shipments.at[idx, 'incoterm'] = "CIF"
    df_shipments.at[idx, 'freight_cost'] = 0  # CIF requires seller to pay freight
    planted_anomalies.append({
        "shipment_id": df_shipments.at[idx, 'shipment_id'],
        "category": "Compliance Risk",
        "description": "Freight cost is zero for CIF incoterm"
    })

    # Category 3: Statistical - Price Outlier
    idx = 50
    df_shipments.at[idx, 'unit_price'] = 250.00  # Massive outlier for a Tee
    df_shipments.at[idx, 'total_fob'] = 250.00 * df_shipments.at[idx, 'quantity']
    planted_anomalies.append({
        "shipment_id": df_shipments.at[idx, 'shipment_id'],
        "category": "Price Anomaly",
        "description": "Unit price is 50x the catalog average"
    })

    # Category 4: LLM - HS Code Mismatch
    idx = 75
    df_shipments.at[idx, 'product_id'] = "P001" # Organic Cotton Tee
    df_shipments.at[idx, 'hs_code'] = "847130" # HS Code for Laptops/Computers
    planted_anomalies.append({
        "shipment_id": df_shipments.at[idx, 'shipment_id'],
        "category": "Classification Error",
        "description": "HS Code for Laptops assigned to Cotton T-shirts"
    })

    # 5. Save Files
    os.makedirs('data', exist_ok=True)
    df_shipments.to_csv('data/shipments.csv', index=False)
    df_catalog.to_csv('data/product_catalog.csv', index=False)
    df_buyers.to_csv('data/buyers.csv', index=False)
    
    with open('data/planted_anomalies.json', 'w') as f:
        json.dump(planted_anomalies, f, indent=4)

    print("✅ Synthetic data generated with 4 sample anomalies.")

if __name__ == "__main__":
    generate_data()