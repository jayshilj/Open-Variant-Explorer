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
