import streamlit as st
import pandas as pd
import json
import os
import subprocess
from datetime import datetime
import sys

# Page configuration for a professional look
st.set_page_config(page_title="Trade Anomaly Dashboard", layout="wide", initial_sidebar_state="expanded")

# Helper functions to load output files
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
    st.header(" Pipeline Controls")
    st.info("Trigger the 3-layer detection engine (Rules, Statistical, and LLM).")
    
    if st.button(" Run Analysis", use_container_width=True):
        with st.spinner("Executing pipeline layers..."):
            # Execute the orchestrator script
            try:
                result = subprocess.run([sys.executable, "src/report_generator.py"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("Analysis Complete!")
                    st.rerun()
                else:
                    st.error(f"Error: {result.stderr}")
            except Exception as e:
                st.error(f"system error: {e}")

    st.divider()
    st.subheader("System Status")
    st.write(f"**Last Sync:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- DATA LOADING ---
anomalies = load_json('output/anomaly_report.json')
accuracy = load_json('output/accuracy_report.json')
usage = load_json('output/llm_usage_report.json')
summary_md = load_markdown('output/executive_summary.md')

# --- DASHBOARD HEADER ---
st.title(" Trade Shipment Anomaly Detective")
st.markdown("Automated surveillance for pricing, compliance, and payment risks.")

if anomalies:
    df = pd.DataFrame(anomalies)

    # --- KPI METRICS (Summary Stats) ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Shipments", "250") 
    with col2:
        st.metric("Detected Anomalies", len(df))
    with col3:
        high_sev = len(df[df['severity'].str.upper() == 'HIGH'])
        st.metric("High Severity", high_sev, delta_color="inverse")
    with col4:
        if accuracy:
            st.metric("System Recall", f"{int(accuracy['recall'] * 100)}%")

    st.divider()

    # --- MAIN CONTENT TABS ---
    tab1, tab2, tab3 = st.tabs(["Anomaly Explorer", " Executive Summary", " LLM Usage"])

    with tab1:
        st.subheader("Filterable Anomaly Table")
        
        # Table Filters
        c1, c2 = st.columns([2, 1])
        with c1:
            search = st.text_input("Search Shipment ID", "")
        with c2:
            cat_filter = st.multiselect("Filter Category", df['category'].unique(), default=df['category'].unique())
        
        # Filtering logic
        filtered_df = df[df['category'].isin(cat_filter)]
        if search:
            filtered_df = filtered_df[filtered_df['shipment_id'].str.contains(search, case=False)]

        # Display Sortable Table
        st.dataframe(filtered_df[['shipment_id', 'category', 'type', 'severity']], use_container_width=True, hide_index=True)

        # Expanding Details Section
        st.subheader("Detailed Evidence Viewer")
        selected_id = st.selectbox("Select a Shipment ID to see full details:", filtered_df['shipment_id'].unique())
        
        if selected_id:
            detail = df[df['shipment_id'] == selected_id].iloc[0]
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.write(f"**Category:** {detail['category']}")
                st.write(f"**Anomaly Type:** {detail['type']}")
                st.warning(f"**Severity:** {detail['severity']}")
            with d_col2:
                # Handle nested dictionary or string for evidence
                evidence = detail['evidence']
                st.write("**Evidence:**")
                st.json(evidence) if isinstance(evidence, dict) else st.info(evidence)
            
            # Show Impact and Recommendation
            st.markdown(f"**Recommendation:** {detail.get('recommendation', 'Immediate audit of trade documents required.')}")

    with tab2:
        st.markdown(summary_md)

    with tab3:
        if usage:
            st.subheader("LLM Token & Cost Tracking")
            st.json(usage)

else:
    st.warning(" No analysis data found. Please click 'Run Analysis' in the sidebar to start the detection pipeline.")