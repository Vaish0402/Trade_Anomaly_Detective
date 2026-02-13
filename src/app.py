import streamlit as st
import pandas as pd
import json
import os
import subprocess
from datetime import datetime
import sys

# Page configuration for a professional look
st.set_page_config(page_title="Trade Anomaly Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- HELPER FUNCTIONS ---
def load_json(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

def load_markdown(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read()
    return "Click 'Run Analysis' to generate the executive summary."

# --- SIDEBAR: CONTROL PANEL ---
with st.sidebar:
    st.header("Pipeline Controls")
    st.info("Trigger the targeted 3-layer detection engine (Rules, Statistical, and LLM) for the 4 planted anomalies.")
    
    if st.button("Run Analysis", use_container_width=True):
        with st.spinner("Executing targeted pipeline layers..."):
            try:
                # Run the orchestrator script
                # Note: Ensure src/report_generator.py is the path to your script
                result = subprocess.run([sys.executable, "src/report_generator.py"], capture_output=True, text=True)
                
                if result.returncode == 0:
                    st.success("Analysis Complete!")
                    st.rerun()
                else:
                    st.error("Pipeline failed.")
                    st.code(result.stderr)
            except Exception as e:
                st.error(f"System error: {e}")

    st.divider()
    st.subheader("System Status")
    st.write(f"**Target Audit Mode:** `PLANTED_IDS ONLY`")
    st.write(f"**Last Sync:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- DATA LOADING ---
# Ensure these paths match your ReportGenerator output_dir
anomalies = load_json('output/anomaly_report.json')
accuracy = load_json('output/accuracy_report.json')
# usage is optional based on your recent change to remove it
usage = load_json('output/usage_report.json') 
summary_md = load_markdown('output/executive_summary.md')

# --- DASHBOARD HEADER ---
st.title("🛡️ Trade Shipment Anomaly Detective")
st.markdown("Automated surveillance focusing on **Planted Test Cases** for Pricing, Compliance, and HS Code risks.")

if anomalies:
    df = pd.DataFrame(anomalies)

    # --- KPI METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        # Total rows in the full dataset (as defined in your earlier prompt)
        st.metric("Total Shipments", "250") 
    with col2:
        st.metric("Anomalies Caught", len(df))
    with col3:
        # Filter for high severity
        high_sev = len(df[df['severity'].astype(str).str.upper() == 'HIGH'])
        st.metric("High Severity", high_sev)
    with col4:
        if accuracy:
            # Displays the recall from your accuracy_report.json
            st.metric("Audit Accuracy", f"{int(accuracy['recall'] * 100)}%")

    st.divider()

    # --- MAIN CONTENT TABS ---
    tab1, tab2, tab3 = st.tabs(["📊 Anomaly Explorer", "📝 Executive Summary", "⚙️ System Metrics"])

    with tab1:
        st.subheader("Targeted Anomaly Table")
        
        # Table Filters
        c1, c2 = st.columns([2, 1])
        with c1:
            search = st.text_input("Search Shipment ID (e.g., SHIP_1010)", "")
        with c2:
            cat_list = df['category'].unique().tolist()
            cat_filter = st.multiselect("Filter Category", cat_list, default=cat_list)
        
        # Filtering logic
        filtered_df = df[df['category'].isin(cat_filter)]
        if search:
            filtered_df = filtered_df[filtered_df['shipment_id'].str.contains(search, case=False)]

        # Display Sortable Table
        st.dataframe(filtered_df[['shipment_id', 'category', 'type', 'severity']], use_container_width=True, hide_index=True)

        # Expanding Details Section
        st.divider()
        st.subheader("Evidence Viewer")
        if not filtered_df.empty:
            selected_id = st.selectbox("Select Shipment for Forensic Details:", filtered_df['shipment_id'].unique())
            
            if selected_id:
                detail = df[df['shipment_id'] == selected_id].iloc[0]
                d_col1, d_col2 = st.columns(2)
                with d_col1:
                    st.write(f"**Category:** {detail['category']}")
                    st.write(f"**Anomaly Type:** {detail['type']}")
                    st.error(f"**Severity:** {detail['severity']}")
                with d_col2:
                    evidence = detail.get('evidence', "No evidence provided.")
                    st.write("**Evidence Detail:**")
                    if isinstance(evidence, dict):
                        st.json(evidence)
                    else:
                        st.info(evidence)
                
                # Recommendation logic
                rec = detail.get('recommendation', "Immediate audit of trade documents required.")
                st.markdown(f" **Recommendation:** {rec}")
        else:
            st.info("No anomalies match the current filters.")

    with tab2:
        st.subheader("Operational Briefing")
        st.markdown(summary_md)

    with tab3:
        st.subheader("Technical Performance")
        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            if accuracy:
                st.write("**Detection Accuracy (vs Ground Truth)**")
                st.json(accuracy)
        with col_acc2:
            if usage:
                st.write("**LLM Usage Tracking**")
                st.json(usage)
            else:
                st.info("Usage tracking is currently disabled in the pipeline.")

else:
    st.warning("⚠️ No analysis data found. Please click 'Run Analysis' in the sidebar to start the detection pipeline.")
    st.image("https://via.placeholder.com/800x200.png?text=Waiting+for+Pipeline+Execution", use_column_width=True)