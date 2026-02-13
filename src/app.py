import streamlit as st
import pandas as pd
import json
import os
from report_generator import ReportGenerator

OUTPUT_DIR = "output"

st.set_page_config(
    page_title="Trade Anomaly Dashboard",
    layout="wide"
)

# ==========================================================
# RUN ANALYSIS BUTTON
# ==========================================================

st.sidebar.title("Controls")

if st.sidebar.button("🚀 Run Analysis"):

    progress_bar = st.progress(0)
    status_text = st.empty()

    def progress_callback(percent, message):
        progress_bar.progress(percent)
        status_text.text(message)

    rg = ReportGenerator()

    rg.run_pipeline_with_progress(progress_callback)

    progress_bar.progress(100)
    status_text.text("✅ Analysis Completed")

    st.success("Pipeline execution finished.")


# ==========================================================
# LOAD DATA
# ==========================================================

def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


anomaly_report = load_json(os.path.join(OUTPUT_DIR, "anomaly_report.json"))
accuracy_report = load_json(os.path.join(OUTPUT_DIR, "accuracy_report.json"))
usage_report = load_json(os.path.join(OUTPUT_DIR, "llm_usage_report.json"))

# ==========================================================
# DASHBOARD HEADER
# ==========================================================

st.title("📦 Trade Shipment Anomaly Dashboard")

if not anomaly_report:
    st.warning("Run analysis to generate results.")
    st.stop()

anomalies = anomaly_report.get("anomalies", [])

df = pd.DataFrame(anomalies)

# ==========================================================
# SUMMARY STATS
# ==========================================================

st.subheader("📊 Summary Overview")

col1, col2, col3, col4 = st.columns(4)

shipments_path = os.path.join("data", "shipments.csv")

if os.path.exists(shipments_path):
    total_shipments = len(pd.read_csv(shipments_path))
else:
    total_shipments = 0
  
total_anomalies = len(df)

severity_counts = df["severity"].value_counts().to_dict() if not df.empty else {}
category_counts = df["category"].value_counts().to_dict() if not df.empty else {}

col1.metric("Total Shipments", total_shipments)
col2.metric("Total Anomalies", total_anomalies)
col3.metric("Highest Risk Score", anomaly_report.get("highest_risk_score", 0))
col4.metric("LLM Calls", usage_report.get("total_llm_calls", 0) if usage_report else 0)


import altair as alt
# ==========================================================
# SEVERITY BREAKDOWN
# ==========================================================

st.subheader("⚠ Severity Breakdown")

if not df.empty:
    severity_df = df["severity"].value_counts().reset_index()
    severity_df.columns = ["severity", "count"]

    chart = (
        alt.Chart(severity_df)
        .mark_bar(color="#4c78a8", cornerRadiusTopLeft=9, cornerRadiusTopRight=9)
        .encode(
            x=alt.X("severity:N", title="Severity Level"),
            y=alt.Y("count:Q", title="Number of Anomalies"),
            tooltip=["severity", "count"]
        )
        .properties(width=600, height=400)
    )

    st.altair_chart(chart, use_container_width=True)




# ==========================================================
# CATEGORY BREAKDOWN (Pie Chart)
# ==========================================================
import altair as alt
st.subheader("📂 Anomalies by Category")

if not df.empty:
    category_df = df["category"].value_counts().reset_index()
    category_df.columns = ["category", "count"]

    chart = (
        alt.Chart(category_df)
        .mark_arc(innerRadius=0)
        .encode(
            theta=alt.Theta(field="count", type="quantitative"),
            color=alt.Color(field="category", type="nominal", legend=alt.Legend(title="Category")),
            tooltip=["category", "count"]
        )
        .properties(width=400, height=400)
    )

    st.altair_chart(chart, use_container_width=True)


# ==========================================================
# ANOMALY TABLE
# ==========================================================

st.subheader("📋 Anomaly Table")

if not df.empty:

    filter_severity = st.selectbox(
        "Filter by Severity",
        ["All"] + sorted(df["severity"].unique())
    )

    filtered_df = df.copy()

    if filter_severity != "All":
        filtered_df = filtered_df[filtered_df["severity"] == filter_severity]

    st.dataframe(
        filtered_df.sort_values(by="risk_score", ascending=False),
        use_container_width=True
    )

    # ======================================================
    # CLICK TO VIEW DETAILS
    # ======================================================

    st.subheader("🔍 View Anomaly Details")

    selected_id = st.selectbox(
        "Select Shipment ID",
        filtered_df["shipment_id"].unique()
    )

    selected_row = filtered_df[filtered_df["shipment_id"] == selected_id].iloc[0]

    st.markdown(f"""
### Shipment ID: {selected_row['shipment_id']}

**Type:** {selected_row['type']}  
**Category:** {selected_row['category']}  
**Severity:** {selected_row['severity']}  
**Risk Score:** {selected_row['risk_score']}  
**Priority:** {selected_row['priority']}  

---

### Evidence
{selected_row['evidence']}
""")

# ==========================================================
# EXECUTIVE SUMMARY
# ==========================================================

st.subheader("📄 Executive Summary")

summary_path = os.path.join(OUTPUT_DIR, "executive_summary.md")

if os.path.exists(summary_path):
    with open(summary_path, "r") as f:
        st.markdown(f.read())
else:
    st.info("No summary generated yet.")

# ==========================================================
# ACCURACY REPORT
# ==========================================================

st.subheader("🎯 Detection Accuracy")

if accuracy_report:
    st.json(accuracy_report)

# ==========================================================
# LLM USAGE REPORT
# ==========================================================

st.subheader("🤖 LLM Usage Report")

if usage_report:
    st.json(usage_report)
