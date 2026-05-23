import pandas as pd
import pm4py
from pm4py.objects.log.util import dataframe_utils
from datetime import timedelta

def load_and_clean_csv(file_path_or_buffer, case_col, activity_col, timestamp_col):
    """
    Load a CSV event log and convert timestamps.
    """
    df = pd.read_csv(file_path_or_buffer)
    # Clean the dataframe using PM4Py utility
    df = dataframe_utils.clean_double_col(df)
    
    # Rename columns to standard PM4Py format internally for ease of use
    df = df.rename(columns={
        case_col: 'case:concept:name',
        activity_col: 'concept:name',
        timestamp_col: 'time:timestamp'
    })
    
    # Ensure correct types
    df['case:concept:name'] = df['case:concept:name'].astype(str)
    df['concept:name'] = df['concept:name'].astype(str)
    df['time:timestamp'] = pd.to_datetime(df['time:timestamp'])
    
    # Sort values to preserve process chronological order
    df = df.sort_values(by=['case:concept:name', 'time:timestamp'])
    return df

def extract_variants(df):
    """
    Extract and calculate process variants (sequences of activities).
    Returns a sorted list of dictionaries with variant information:
    [
        {
            "id": 1,
            "activities": ["Create Order", "Approve Credit", ...],
            "case_count": 10,
            "frequency": 0.45,
            "cases": ["Case_1", "Case_3", ...]
        }
    ]
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
    dfg_freq = pm4py.discover_directly_follows_graph(df)
    
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
