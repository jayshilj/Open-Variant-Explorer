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

# --- LOG LOAD AND DATA PIPELINE ---
if file_to_parse is not None:
    try:
        # Load and clean
        df = load_and_clean_csv(file_to_parse, case_col, activity_col, timestamp_col)
        
        # Calculate stats
        variants = extract_variants(df)
        total_cases = df['case:concept:name'].nunique()
        total_activities = df['concept:name'].nunique()
        
        case_durations_df = get_case_durations(df)
        avg_lead_time_days = case_durations_df['duration_days'].mean()
        
        # Populate dynamic sidebar insights
        with st.sidebar:
            st.divider()
            with st.expander("📊 Event Log Statistics", expanded=True):
                st.write(f"**Total Events:** {len(df)}")
                st.write(f"**Date Range:** {df['time:timestamp'].min().strftime('%Y-%m-%d')} to {df['time:timestamp'].max().strftime('%Y-%m-%d')}")
                st.write(f"**Average Steps/Case:** {len(df) / total_cases:.1f}")
                st.divider()
                # Standardized download option
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Cleaned CSV",
                    data=csv_data,
                    file_name="standardized_event_log.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        # --- TITLE BLOCK ---
        st.markdown("<h1 style='margin-bottom: 5px;'>📊 Process Discovery & Variant Explorer</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#868e96; font-size: 1.1em; margin-bottom: 25px;'>Analyze operational deviations, discover process paths, and uncover execution bottlenecks.</p>", unsafe_allow_html=True)
        
        # --- METRICS ROW ---
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{total_cases}</div>
                    <div class="metric-label">Total Cases</div>
                </div>
            """, unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{total_activities}</div>
                    <div class="metric-label">Unique Activities</div>
                </div>
            """, unsafe_allow_html=True)
            
        with m3:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{avg_lead_time_days:.1f} Days</div>
                    <div class="metric-label">Avg Lead Time</div>
                </div>
            """, unsafe_allow_html=True)
            
        with m4:
            st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-value">{len(variants)}</div>
                    <div class="metric-label">Unique Variants</div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- TABS FOR MODULES ---
        tab_discovery, tab_variant, tab_lead_time = st.tabs([
            "📡 Process Map Explorer", 
            "🧬 Variant Explorer", 
            "⏱️ SLA & Lead Times"
        ])
        
        # MODULE 1: PROCESS MAP DISCOVERY
        with tab_discovery:
            st.subheader("📡 Directly-Follows Graph (Process Map)")
            st.markdown("Observe your process model as it is actually executed. Nodes represent activities; directed connections show transitions.")
            
            # Interactive Controls for Process Map
            c_metric, c_variant_filter = st.columns([1.5, 3])
            
            with c_metric:
                map_metric = st.radio(
                    "Select Process Metric:",
                    ["Frequency (Case Volume)", "Performance (Average Duration)"],
                    horizontal=True
                )
                
            with c_variant_filter:
                # Allow filtering DFG to only show specific variants
                variant_options = ["Show All Variants (Full Process)"] + [f"Variant {v['id']} ({v['case_count']} cases - {v['frequency']*100:.1f}%)" for v in variants]
                selected_var_str = st.selectbox(
                    "Filter map by Case Variant:",
                    variant_options
                )
                
            # Filter cases based on chosen variant
            filter_cases = None
            if selected_var_str != "Show All Variants (Full Process)":
                # Extract variant ID
                var_id = int(selected_var_str.split(" ")[1])
                matched_var = next(v for v in variants if v["id"] == var_id)
                filter_cases = matched_var["cases"]
                
            # Compute DFG data
            metric_type = "frequency" if "Frequency" in map_metric else "performance"
            dfg_freq, dfg_perf, activity_freq = compute_dfg_data(df, variant_cases=filter_cases)
            
            # Generate and Render Pyvis Map
            if activity_freq:
                with st.spinner("Discovering process models..."):
                    html_graph = generate_dfg_network(dfg_freq, dfg_perf, activity_freq, metric=metric_type)
                    st.components.v1.html(html_graph, height=620, scrolling=False)
            else:
                st.info("No transitions discovered for the selected filter.")
                
        # MODULE 2: VARIANT EXPLORER
        with tab_variant:
            st.subheader("🧬 Variant Explorer")
            st.markdown("Examine the exact sequences of activities that cases followed, ranked by their commonality.")
            
            # Display detailed list of variants
            for v in variants:
                freq_pct = v["frequency"] * 100
                st.markdown(f"""
                    <div class="variant-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <h4 style="margin:0; color:#2c3e50;">Variant #{v['id']}</h4>
                            <span style="background-color:#eef2ff; color:#3b5bdb; font-weight:700; font-size:13px; padding:3px 12px; border-radius:20px;">
                                📦 {v['case_count']} cases ({freq_pct:.1f}%)
                            </span>
                        </div>
                        <div style="margin-top:10px;">
                            {" ➡️ ".join([f"<span class='activity-badge'>{act}</span>" for act in v['activities']])}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
        # MODULE 3: LEAD TIME / Cycle time
        with tab_lead_time:
            st.subheader("⏱️ Throughput Time Distribution")
            st.markdown("Analyze how throughput times vary across your cases to identify latency patterns.")
            
            lt_col1, lt_col2 = st.columns([2, 1])
            
            with lt_col1:
                # Plotly Lead Time Histogram
                fig = px.histogram(
                    case_durations_df, 
                    x="duration_days",
                    nbins=15,
                    labels={"duration_days": "Lead Time (Days)", "count": "Case Count"},
                    title="Lead Time Distribution (Days)",
                    color_discrete_sequence=["#4dabf7"]
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(248,249,250,0.5)",
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=380
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with lt_col2:
                # High-level statistics
                min_days = case_durations_df['duration_days'].min()
                max_days = case_durations_df['duration_days'].max()
                med_days = case_durations_df['duration_days'].median()
                
                st.markdown(f"""
                    <div style="background-color: #f8f9fa; border:1px solid #e9ecef; border-radius:10px; padding:25px; height:100%; display:flex; flex-direction:column; justify-content:center;">
                        <h4 style="margin-top:0; color:#2c3e50; font-size:1.1rem; border-bottom:2px solid #dee2e6; padding-bottom:8px; margin-bottom:15px;">⏱️ Cycle Statistics</h4>
                        <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:0.95em;">
                            <span style="color:#868e96; font-weight:600;">Fastest Case:</span>
                            <span style="color:#2c3e50; font-weight:700;">{min_days:.2f} Days</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:0.95em;">
                            <span style="color:#868e96; font-weight:600;">Median Case:</span>
                            <span style="color:#2c3e50; font-weight:700;">{med_days:.2f} Days</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:0.95em;">
                            <span style="color:#868e96; font-weight:600;">Slowest Case:</span>
                            <span style="color:#2c3e50; font-weight:700; color:#fa5252;">{max_days:.2f} Days</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
            st.divider()
            
            st.subheader("📋 Case Detail Ledger")
            # Convert start and end times to clean readable strings
            display_durations = case_durations_df.copy()
            display_durations['start_time'] = display_durations['start_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
            display_durations['end_time'] = display_durations['end_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
            display_durations['duration_days'] = display_durations['duration_days'].round(2)
            
            st.dataframe(
                display_durations.rename(columns={
                    "case_id": "Case Identifier",
                    "start_time": "Process Start",
                    "end_time": "Process Complete",
                    "duration_days": "Duration (Days)",
                    "activities_count": "Steps Count"
                }), 
                hide_index=True,
                width="stretch"
            )

    except Exception as e:
        st.error(f"Failed to analyze event log. Details: {e}")
        st.info("Ensure that the column mappings in the sidebar correctly match your dataset's headers.")
else:
    # No file uploaded warning block
    st.info("💡 **Welcome to Open-Variant Explorer!** Please select 'Use Sample O2C Log' in the sidebar or upload a custom CSV event log to start discovering your processes.")
