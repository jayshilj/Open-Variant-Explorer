import tempfile
import os
from pyvis.network import Network
from src.parser import format_duration

def generate_dfg_network(dfg_freq, dfg_perf, activity_freq, metric="frequency"):
    """
    Generate an interactive Directly-Follows Graph network using Pyvis.
    metric can be "frequency" or "performance".
    """
    net = Network(
        height="600px", 
        width="100%", 
        bgcolor="#f8f9fa", 
        font_color="#2c3e50", 
        directed=True,
        select_menu=False,
        cdn_resources='remote'
    )
    
    # Well-balanced, highly-stable physics layout
    net.force_atlas_2based(
        gravity=-45, 
        central_gravity=0.012, 
        spring_length=150, 
        spring_strength=0.055, 
        damping=0.5, 
        overlap=0.8
    )
    
    # 1. Add Nodes (Activities)
    if not activity_freq:
        return "<p style='color:red;'>No activity data found.</p>"
        
    max_freq = max(activity_freq.values()) if activity_freq.values() else 1
    
    for act, freq in activity_freq.items():
        # Scale size logarithmically/proportionally based on frequency
        size = int(max(15, min(45, 12 + (freq / max_freq) * 25)))
        
        # Build node title (tooltip)
        tooltip = f"<b>Activity:</b> {act}<br><b>Occurrences:</b> {freq}"
        
        # Aesthetic colors (Celonis-inspired blues/slates)
        bg_color = "#3b5bdb" if freq > (max_freq * 0.7) else "#4dabf7"
        border_color = "#1c7ed6"
        
        net.add_node(
            act,
            label=f"{act}\n({freq})",
            title=tooltip,
            shape="dot",
            size=size,
            color={"background": bg_color, "border": border_color,
                   "highlight": {"background": "#12b886", "border": "#0ca678"},
                   "hover": {"background": "#22b8cf", "border": "#15aabf"}},
            font={"size": 12, "face": "Segoe UI, sans-serif", "color": "#1a1b1f", "bold": True},
            borderWidth=2,
            shadow={"enabled": True, "color": "rgba(0,0,0,0.08)", "size": 4, "x": 2, "y": 2}
        )
        
    # 2. Add Edges (Transitions)
    if metric == "frequency":
        if not dfg_freq:
            return ""
        max_edge_val = max(dfg_freq.values()) if dfg_freq.values() else 1
        
        for (act_a, act_b), val in dfg_freq.items():
            # Scale edge width
            width = max(1.0, min(8.0, 1.0 + (val / max_edge_val) * 7))
            
            # Celonis-style slate/blue edge transitions
            color = "#a5d8ff" if val > (max_edge_val * 0.5) else "#ced4da"
            
            tooltip = f"<b>Transition:</b> {act_a} ➡️ {act_b}<br><b>Cases:</b> {val}"
            
            net.add_edge(
                act_a, act_b,
                label=f" {val}",
                title=tooltip,
                width=width,
                color={"color": color, "highlight": "#228be6", "hover": "#228be6"},
                arrows={"to": {"enabled": True, "scaleFactor": 0.55}},
                smooth={"type": "dynamic"}
            )
            
    else: # "performance"
        if not dfg_perf:
            return ""
        max_duration = max(dfg_perf.values()) if dfg_perf.values() else 1
        
        for (act_a, act_b), duration_sec in dfg_perf.items():
            # Scale edge width by frequency of that transition (if present in frequency map)
            freq_val = dfg_freq.get((act_a, act_b), 1)
            max_freq_val = max(dfg_freq.values()) if dfg_freq.values() else 1
            width = max(1.0, min(8.0, 1.0 + (freq_val / max_freq_val) * 7))
            
            # Color transition based on duration (longer = red/orange bottleneck)
            ratio = duration_sec / max_duration if max_duration > 0 else 0
            if ratio > 0.7:
                color = "#fa5252" # Red (Critical Bottleneck)
            elif ratio > 0.4:
                color = "#ff922b" # Orange (High Latency)
            else:
                color = "#adb5bd" # Neutral Grey
                
            formatted_time = format_duration(duration_sec)
            tooltip = f"<b>Transition:</b> {act_a} ➡️ {act_b}<br><b>Avg Duration:</b> {formatted_time}<br><b>Transitions:</b> {freq_val} cases"
            
            net.add_edge(
                act_a, act_b,
                label=f" {formatted_time}",
                title=tooltip,
                width=width,
                color={"color": color, "highlight": "#fa5252", "hover": "#fa5252"},
                arrows={"to": {"enabled": True, "scaleFactor": 0.55}},
                smooth={"type": "dynamic"}
            )
            
    # Save graph in a temp file and read into memory
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp:
        tmp_path = tmp.name
        
    net.save_graph(tmp_path)
    with open(tmp_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    try:
        os.remove(tmp_path)
    except OSError:
        pass
        
    return html_content
