import pandas as pd
import numpy as np
import random
import json
import os

# ==========================================================
# Trade Shipment Synthetic Data Generator
# Injects 12 anomalies across 6 categories (2 each)
# ==========================================================

np.random.seed(42)
random.seed(42)


def generate_data():

    # ------------------------------------------------------
    # 1️⃣ PRODUCT CATALOG
    # ------------------------------------------------------
    products = [
        {"product_id": "P001", "name": "Organic Cotton T-shirt 100% knitted", "hs_code": "610910", "avg_price": 5.50},
        {"product_id": "P002", "name": "Silk Scarf Premium", "hs_code": "621410", "avg_price": 22.00},
        {"product_id": "P003", "name": "Leather Handbag Genuine", "hs_code": "420221", "avg_price": 45.00},
        {"product_id": "P004", "name": "Decorative Ceramic Vase", "hs_code": "691310", "avg_price": 12.00},
        {"product_id": "P005", "name": "Basmati Rice 5kg Export Grade", "hs_code": "100630", "avg_price": 8.00},
    ]

    df_catalog = pd.DataFrame(products)

    # ------------------------------------------------------
    # 2️⃣ BUYERS
    # ------------------------------------------------------
    buyers = [
        {"buyer_id": "B_USA_01", "name": "Global Retail Corp", "country": "USA", "avg_payment_days": 30},
        {"buyer_id": "B_UAE_02", "name": "Desert Trading LLC", "country": "UAE", "avg_payment_days": 15},
        {"buyer_id": "B_GER_03", "name": "EuroGoods GmbH", "country": "Germany", "avg_payment_days": 45},
    ]

    df_buyers = pd.DataFrame(buyers)

    # ------------------------------------------------------
    # 3️⃣ GENERATE 250 BASE SHIPMENTS
    # ------------------------------------------------------
    data = []

    for i in range(250):
        prod = random.choice(products)
        buyer = random.choice(buyers)

        qty = random.randint(100, 1000)
        unit_price = round(prod["avg_price"] * np.random.uniform(0.95, 1.05), 2)
        total_fob = round(qty * unit_price, 2)

        row = {
            "shipment_id": f"SHIP_{1000 + i}",
            "buyer_id": buyer["buyer_id"],
            "product_id": prod["product_id"],
            "product_description": prod["name"],
            "hs_code": prod["hs_code"],
            "quantity": qty,
            "unit_price": unit_price,
            "total_fob": total_fob,
            "incoterm": random.choice(["FOB", "CIF", "EXW"]),
            "freight_cost": random.randint(500, 2000),
            "customs_status": "cleared",
            "drawback_amount": round(total_fob * 0.02, 2),
            "payment_status": "received",
            "days_to_payment": random.randint(10, 50),
            "transit_time_days": random.randint(15, 40)
        }

        data.append(row)

    df_shipments = pd.DataFrame(data)

    planted_anomalies = []

    # ==========================================================
    # 🔴 INJECT 12 ANOMALIES (2 PER CATEGORY)
    # ==========================================================

    # ------------------------------------------------------
    # 1️⃣ Math Inconsistency (Rule-Based)
    # ------------------------------------------------------
    for idx in [10, 20]:
        df_shipments.at[idx, "total_fob"] = 999.99
        planted_anomalies.append({
            "shipment_id": df_shipments.at[idx, "shipment_id"],
            "category": "Math Inconsistency",
            "description": "Total FOB does not equal quantity times unit_price"
        })

    # ------------------------------------------------------
    # 2️⃣ Incoterm Compliance Risk (Rule-Based)
    # ------------------------------------------------------
    # CIF with zero freight
    df_shipments.at[30, "incoterm"] = "CIF"
    df_shipments.at[30, "freight_cost"] = 0

    planted_anomalies.append({
        "shipment_id": df_shipments.at[30, "shipment_id"],
        "category": "Incoterm Violation",
        "description": "CIF shipment with zero freight cost"
    })

    # EXW but seller paid freight
    df_shipments.at[40, "incoterm"] = "EXW"
    df_shipments.at[40, "freight_cost"] = 1500

    planted_anomalies.append({
        "shipment_id": df_shipments.at[40, "shipment_id"],
        "category": "Incoterm Violation",
        "description": "EXW shipment with seller-paid freight"
    })

    # ------------------------------------------------------
    # 3️⃣ Duty Drawback Abuse (Rule-Based)
    # ------------------------------------------------------
    for idx in [50, 60]:
        df_shipments.at[idx, "customs_status"] = "rejected"
        df_shipments.at[idx, "drawback_amount"] = 500

        planted_anomalies.append({
            "shipment_id": df_shipments.at[idx, "shipment_id"],
            "category": "Drawback Fraud Risk",
            "description": "Drawback claimed on rejected shipment"
        })

    # ------------------------------------------------------
    # 4️⃣ Statistical Price Outliers (Z-Score)
    # ------------------------------------------------------
    # Extremely overpriced
    df_shipments.at[70, "unit_price"] = 250.00
    df_shipments.at[70, "total_fob"] = (
        df_shipments.at[70, "quantity"] * 250.00
    )

    planted_anomalies.append({
        "shipment_id": df_shipments.at[70, "shipment_id"],
        "category": "Price Anomaly",
        "description": "Extreme overpricing (Z-score > 3)"
    })

    # Extremely underpriced
    df_shipments.at[80, "unit_price"] = 0.50
    df_shipments.at[80, "total_fob"] = (
        df_shipments.at[80, "quantity"] * 0.50
    )

    planted_anomalies.append({
        "shipment_id": df_shipments.at[80, "shipment_id"],
        "category": "Price Anomaly",
        "description": "Extreme underpricing (Z-score < -3)"
    })

    # ------------------------------------------------------
    # 5️⃣ HS Code Mismatch (LLM Required)
    # ------------------------------------------------------
    # Assign laptop HS code to T-shirt
    df_shipments.at[90, "product_id"] = "P001"
    df_shipments.at[90, "product_description"] = "Organic Cotton T-shirt 100% knitted"
    df_shipments.at[90, "hs_code"] = "847130"

    planted_anomalies.append({
        "shipment_id": df_shipments.at[90, "shipment_id"],
        "category": "HS Code Mismatch",
        "description": "Laptop HS code assigned to cotton T-shirt"
    })

    # Assign rice HS code to handbag
    df_shipments.at[100, "product_id"] = "P003"
    df_shipments.at[100, "product_description"] = "Leather Handbag Genuine"
    df_shipments.at[100, "hs_code"] = "100630"

    planted_anomalies.append({
        "shipment_id": df_shipments.at[100, "shipment_id"],
        "category": "HS Code Mismatch",
        "description": "Rice HS code assigned to leather handbag"
    })

    # ------------------------------------------------------
    # 6️⃣ Cross-Shipment Buyer Pattern Anomaly
    # ------------------------------------------------------
    # Payment delay spike
    df_shipments.at[110, "buyer_id"] = "B_UAE_02"
    df_shipments.at[110, "days_to_payment"] = 120

    planted_anomalies.append({
        "shipment_id": df_shipments.at[110, "shipment_id"],
        "category": "Buyer Behavior Anomaly",
        "description": "Sudden payment delay spike"
    })

    # Transit time spike
    df_shipments.at[120, "transit_time_days"] = 90

    planted_anomalies.append({
        "shipment_id": df_shipments.at[120, "shipment_id"],
        "category": "Logistics Anomaly",
        "description": "Unusually high transit time"
    })

    # ==========================================================
    # SAVE FILES
    # ==========================================================

    os.makedirs("data", exist_ok=True)

    df_shipments.to_csv("data/shipments.csv", index=False)
    df_catalog.to_csv("data/product_catalog.csv", index=False)
    df_buyers.to_csv("data/buyers.csv", index=False)

    with open("data/planted_anomalies.json", "w") as f:
        json.dump(planted_anomalies, f, indent=4)

    print("✅ Synthetic dataset generated successfully.")
    print("📦 Total Shipments: 250")
    print("🚨 Total Injected Anomalies: 12 (6 categories)")


if __name__ == "__main__":
    generate_data()
