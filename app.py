import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.parser import load_and_clean_csv, extract_variants, compute_dfg_data, get_case_durations
from src.visualizer import generate_dfg_network

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Open-Variant Explorer | Process Mining Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR SLEEK MODERN DESIGN (Celonis Inspired) ---
st.markdown("""
    <style>
    .metric-container {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.05);
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #3b5bdb;
        margin-bottom: 2px;
    }
    .metric-label {
        font-size: 13px;
        font-weight: 600;
        color: #868e96;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .variant-card {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        border-left: 5px solid #3b5bdb;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.01);
    }
    .activity-badge {
        display: inline-block;
        background-color: #f1f3f5;
        color: #495057;
        font-weight: 600;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 20px;
        margin-right: 5px;
        margin-bottom: 5px;
        border: 1px solid #dee2e6;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/process.png", width=65)
    st.markdown("<h2 style='margin:0; padding-top:5px; font-size:1.8em;'>Open-Variant</h2><div style='color:#868e96; font-size:0.85em; margin-top:-5px; font-weight:600; margin-bottom: 20px;'>Process Mining Dashboard</div>", unsafe_allow_html=True)
    
    st.subheader("📁 Event Log Ingestion")
    data_source = st.radio("Select Data Source:", ["Use Sample O2C Log", "Upload CSV Log"])
    
    uploaded_file = None
    if data_source == "Upload CSV Log":
        uploaded_file = st.file_uploader("Upload CSV Event Log:", type=["csv"])
        
    st.divider()
    
    # Define Column Mappings (Reactive based on uploaded/sample data headers)
    st.subheader("⚙️ Column Mapping")
    
    # Pre-load headers
    if data_source == "Use Sample O2C Log":
        sample_path = "datasets/sample_o2c.csv"
        preview_df = pd.read_csv(sample_path, nrows=5)
        headers = preview_df.columns.tolist()
        
        default_case = "case_id" if "case_id" in headers else headers[0]
        default_act = "activity" if "activity" in headers else headers[0]
        default_time = "timestamp" if "timestamp" in headers else headers[0]
        
        file_to_parse = sample_path
    else:
        if uploaded_file is not None:
            preview_df = pd.read_csv(uploaded_file, nrows=5)
            headers = preview_df.columns.tolist()
            
            default_case = headers[0]
            default_act = headers[1] if len(headers) > 1 else headers[0]
            default_time = headers[2] if len(headers) > 2 else headers[0]
            
            file_to_parse = uploaded_file
            # Reset buffer pointer for full read later
            uploaded_file.seek(0)
        else:
            headers = ["No File Loaded"]
            default_case = default_act = default_time = "No File Loaded"
            file_to_parse = None
            
    case_col = st.selectbox("Case ID Column:", headers, index=headers.index(default_case) if default_case in headers else 0)
    activity_col = st.selectbox("Activity Column:", headers, index=headers.index(default_act) if default_act in headers else 0)
    timestamp_col = st.selectbox("Timestamp Column:", headers, index=headers.index(default_time) if default_time in headers else 0)

    st.markdown("""
        <div style="margin-top: 25px; padding: 12px; border-radius: 8px; background-color: #f8f9fa; border: 1px solid #e9ecef;">
            <p style="margin-bottom: 5px; font-size: 0.8em; color: #868e96; font-weight: 700;">DEVELOPMENT ENGINE</p>
            <p style="margin-bottom: 5px; font-size: 0.9em; font-weight: 600; color: #3b5bdb;">PM4Py Open-Source Core</p>
            <p style="margin: 0; font-size: 0.75em; color: #868e96; line-height: 1.3;">Designed for operational excellence and strategic throughput auditing.</p>
        </div>
    """, unsafe_allow_html=True)

# Placeholder for main app code
if file_to_parse is not None:
    st.success("Log loaded successfully! Start discovering your process flow in the next version.")
else:
    st.info("💡 **Welcome to Open-Variant Explorer!** Please select 'Use Sample O2C Log' in the sidebar or upload a custom CSV event log to start discovering your processes.")
