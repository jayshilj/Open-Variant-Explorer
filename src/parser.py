import pandas as pd
import pm4py
from pm4py.objects.log.util import dataframe_utils
from datetime import timedelta
from typing import Union, List, Dict, Tuple, Optional, Any
import io
import os
import tempfile

def validate_csv_headers(
    df: pd.DataFrame, 
    case_col: str, 
    activity_col: str, 
    timestamp_col: str
) -> None:
    """
    Validate that the requested columns exist in the DataFrame.
    Raises ValueError with descriptive instructions if any column is missing.
    """
    missing = []
    if case_col not in df.columns:
        missing.append(f"Case ID column '{case_col}'")
    if activity_col not in df.columns:
        missing.append(f"Activity column '{activity_col}'")
    if timestamp_col not in df.columns:
        missing.append(f"Timestamp column '{timestamp_col}'")
        
    if missing:
        raise ValueError(
            f"CSV file is missing the following required columns: {', '.join(missing)}. "
            f"Available columns are: {list(df.columns)}"
        )

def load_and_clean_csv(
    file_path_or_buffer: Union[str, io.StringIO, io.BytesIO], 
    case_col: str, 
    activity_col: str, 
    timestamp_col: str
) -> pd.DataFrame:
    """
    Load a CSV event log and convert timestamps into a standard format.
    
    Args:
        file_path_or_buffer: Path to CSV or a file-like buffer object.
        case_col: Column name containing the case identifiers.
        activity_col: Column name containing the activity names.
        timestamp_col: Column name containing the timestamps.
        
    Returns:
        pd.DataFrame: Sorted, standardized event log dataframe.
    """
    # Support hybrid CSV/JSON/XES parsing with robust detection
    df = None
    is_xes = False
    
    if isinstance(file_path_or_buffer, str) and (file_path_or_buffer.lower().endswith('.xes') or file_path_or_buffer.lower().endswith('.xes.gz')):
        is_xes = True
    elif hasattr(file_path_or_buffer, 'name') and isinstance(file_path_or_buffer.name, str) and (file_path_or_buffer.name.lower().endswith('.xes') or file_path_or_buffer.name.lower().endswith('.xes.gz')):
        is_xes = True

    if is_xes:
        if not isinstance(file_path_or_buffer, str):
            suffix = ".xes.gz" if file_path_or_buffer.name.lower().endswith('.gz') else ".xes"
            # Read current position, write to temp file
            if hasattr(file_path_or_buffer, 'seek'):
                file_path_or_buffer.seek(0)
            content = file_path_or_buffer.read()
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                if isinstance(content, str):
                    content = content.encode('utf-8')
                tmp.write(content)
                tmp_path = tmp.name
            try:
                df = pm4py.read_xes(tmp_path)
            finally:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
        else:
            df = pm4py.read_xes(file_path_or_buffer)
            
        # Map standard XES columns back to mapped names if needed
        current_cols = df.columns.tolist()
        if case_col not in current_cols and 'case:concept:name' in current_cols:
            df = df.rename(columns={'case:concept:name': case_col})
        if activity_col not in current_cols and 'concept:name' in current_cols:
            df = df.rename(columns={'concept:name': activity_col})
        if timestamp_col not in current_cols and 'time:timestamp' in current_cols:
            df = df.rename(columns={'time:timestamp': timestamp_col})
    elif isinstance(file_path_or_buffer, str) and file_path_or_buffer.lower().endswith('.json'):
        df = pd.read_json(file_path_or_buffer)
    else:
        # Check if the buffer content looks like JSON
        looks_like_json = False
        if hasattr(file_path_or_buffer, 'read'):
            try:
                if hasattr(file_path_or_buffer, 'seek'):
                    file_path_or_buffer.seek(0)
                lead_chars = file_path_or_buffer.read(50).strip()
                file_path_or_buffer.seek(0)
                if isinstance(lead_chars, bytes):
                    lead_chars = lead_chars.decode('utf-8', errors='ignore')
                if lead_chars.startswith(('[', '{')):
                    looks_like_json = True
            except Exception:
                pass
                
        if looks_like_json:
            df = pd.read_json(file_path_or_buffer)
        else:
            try:
                df = pd.read_csv(file_path_or_buffer)
                # If columns are not found and it might be JSON, fallback
                if case_col not in df.columns and activity_col not in df.columns:
                    if hasattr(file_path_or_buffer, 'seek'):
                        file_path_or_buffer.seek(0)
                    df = pd.read_json(file_path_or_buffer)
            except Exception:
                if hasattr(file_path_or_buffer, 'seek'):
                    file_path_or_buffer.seek(0)
                df = pd.read_json(file_path_or_buffer)
            
    # Validate column mappings
    validate_csv_headers(df, case_col, activity_col, timestamp_col)
    
    # Clean the dataframe using PM4Py utility
    df = pm4py.format_dataframe(df, case_id=case_col, activity_key=activity_col, timestamp_key=timestamp_col)
    
    # Ensure correct types
    df['case:concept:name'] = df['case:concept:name'].astype(str)
    df['concept:name'] = df['concept:name'].astype(str)
    df['time:timestamp'] = pd.to_datetime(df['time:timestamp'], utc=True).dt.tz_localize(None)
    
    # Sort values to preserve process chronological order
    df = df.sort_values(by=['case:concept:name', 'time:timestamp'])
    return df

def extract_variants(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract and calculate process variants (sequences of activities).
    
    Args:
        df: Standardized event log DataFrame.
        
    Returns:
        List[Dict[str, Any]]: List of sorted dictionaries with variant details.
    """
    # Group by Case ID and get chronological list of activities
    case_groups = df.groupby('case:concept:name')
    case_variants = {}
    
    for case_id, group in case_groups:
        activities = tuple(group['concept:name'].tolist())
        if activities not in case_variants:
            case_variants[activities] = []
        case_variants[activities].append(case_id)
        
    total_cases = len(case_groups)
    sorted_variants = sorted(
        case_variants.items(), 
        key=lambda x: len(x[1]), 
        reverse=True
    )
    
    variants_info = []
    for idx, (activities, cases) in enumerate(sorted_variants, 1):
        variants_info.append({
            "id": idx,
            "activities": list(activities),
            "case_count": len(cases),
            "frequency": len(cases) / total_cases if total_cases > 0 else 0,
            "cases": cases
        })
        
    return variants_info

def compute_dfg_data(df, variant_cases=None):
    """
    Compute Directly-Follows Graph (DFG) data.
    If variant_cases is specified, filters the DFG only for those cases.
    Returns:
        dfg_freq: dict of ((act_a, act_b), count)
        dfg_perf: dict of ((act_a, act_b), avg_duration_seconds)
        activity_freq: dict of (activity, count)
    """
    # Filter by specific cases if requested (e.g. when selecting a single variant)
    if variant_cases is not None:
        df = df[df['case:concept:name'].isin(variant_cases)]
        
    # Get Activity Frequencies
    activity_freq = df['concept:name'].value_counts().to_dict()
    
    # Get DFG with frequencies
    dfg_freq, _, _ = pm4py.discover_directly_follows_graph(df)
    
    # Calculate DFG with performance (durations)
    dfg_perf = {}
    # We group by case, iterate over transitions, and calculate time diffs
    case_groups = df.groupby('case:concept:name')
    transition_times = {} # ((act_a, act_b), [durations])
    
    for case_id, group in case_groups:
        sorted_group = group.sort_values(by='time:timestamp')
        activities = sorted_group['concept:name'].tolist()
        timestamps = sorted_group['time:timestamp'].tolist()
        
        for i in range(len(activities) - 1):
            act_a = activities[i]
            act_b = activities[i+1]
            time_a = timestamps[i]
            time_b = timestamps[i+1]
            
            duration = (time_b - time_a).total_seconds()
            pair = (act_a, act_b)
            
            if pair not in transition_times:
                transition_times[pair] = []
            transition_times[pair].append(duration)
            
    for pair, durations in transition_times.items():
        # Calculate average duration for the transition
        dfg_perf[pair] = sum(durations) / len(durations) if durations else 0
        
    return dfg_freq, dfg_perf, activity_freq

def get_case_durations(df):
    """
    Calculate the throughput time (duration) for each case.
    """
    case_durations = []
    case_groups = df.groupby('case:concept:name')
    
    for case_id, group in case_groups:
        start_time = group['time:timestamp'].min()
        end_time = group['time:timestamp'].max()
        duration_seconds = (end_time - start_time).total_seconds()
        
        case_durations.append({
            "case_id": case_id,
            "start_time": start_time,
            "end_time": end_time,
            "duration_days": duration_seconds / (24 * 3600),
            "activities_count": len(group)
        })
        
    return pd.DataFrame(case_durations)

def format_duration(seconds):
    """Format duration in seconds to a human-readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f}h"
    days = hours / 24
    return f"{days:.1f}d"

def compute_activity_durations(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate the average outbound transition latency in seconds for each activity.
    Helps isolate which activity points trigger the largest operational delay.
    """
    transition_times = []
    case_groups = df.groupby('case:concept:name')
    for case_id, group in case_groups:
        sorted_group = group.sort_values(by='time:timestamp')
        activities = sorted_group['concept:name'].tolist()
        timestamps = sorted_group['time:timestamp'].tolist()
        for i in range(len(activities) - 1):
            act_a = activities[i]
            duration = (timestamps[i+1] - timestamps[i]).total_seconds()
            transition_times.append({'activity': act_a, 'duration': duration})
            
    if not transition_times:
        return {}
    df_trans = pd.DataFrame(transition_times)
    return df_trans.groupby('activity')['duration'].mean().to_dict()

def compute_case_step_stats(df: pd.DataFrame) -> Dict[str, Union[int, float]]:
    """
    Calculate statistical metrics of steps per case.
    Returns:
        Dict with keys: "min", "max", "median", "mean", "std"
    """
    if df.empty:
        return {"min": 0, "max": 0, "median": 0.0, "mean": 0.0, "std": 0.0}
    
    case_sizes = df.groupby('case:concept:name').size()
    return {
        "min": int(case_sizes.min()),
        "max": int(case_sizes.max()),
        "median": float(case_sizes.median()),
        "mean": float(case_sizes.mean()),
        "std": float(case_sizes.std()) if len(case_sizes) > 1 else 0.0
    }
