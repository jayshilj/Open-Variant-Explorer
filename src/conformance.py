from typing import List, Dict, Tuple, Any, Union, Optional

# Type definition for case sequence dictionary
# Maps case_id to list of activity names
CaseSequences = Dict[str, List[str]]

# Type definition for deviation info
Deviation = Dict[str, Any]

# Type definition for conformance analysis result
ConformanceResult = Dict[str, Any]

def check_exact_match(case_path: List[str], reference_path: List[str]) -> bool:
    """
    Check if the executed case path conforms exactly to the reference path.
    """
    return case_path == reference_path

def compute_levenshtein_distance(seq1: List[str], seq2: List[str]) -> int:
    """
    Compute Levenshtein distance between two lists of activity strings.
    """
    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
        
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = min(
                    dp[i - 1][j] + 1,    # Deletion
                    dp[i][j - 1] + 1,    # Insertion
                    dp[i - 1][j - 1] + 1  # Substitution
                )
    return dp[m][n]

def calculate_alignment_fitness(case_path: List[str], reference_path: List[str]) -> float:
    """
    Calculate a normalized alignment fitness score between 0.0 and 1.0.
    1.0 means perfect fit, 0.0 means completely different.
    """
    if not case_path and not reference_path:
        return 1.0
    if not case_path or not reference_path:
        return 0.0
        
    max_len = max(len(case_path), len(reference_path))
    dist = compute_levenshtein_distance(case_path, reference_path)
    
    # Normalize distance to get fitness
    return 1.0 - (dist / max_len)

def analyze_deviations(case_path: List[str], reference_path: List[str]) -> List[str]:
    """
    Analyze step-by-step deviations of the case path against the reference path.
    Detects missing, unexpected, and out-of-order steps.
    """
    deviations = []
    
    # Set representations for quick membership check
    ref_set = set(reference_path)
    case_set = set(case_path)
    
    # 1. Detect Missing Steps (in reference, but not in case)
    for act in reference_path:
        if act not in case_set:
            deviations.append(f"Missing: '{act}'")
            
    # 2. Detect Unexpected Steps (in case, but not in reference)
    for act in case_path:
        if act not in ref_set:
            deviations.append(f"Unexpected: '{act}'")
            
    # 3. Detect Out-of-Order Steps (occurring in different relative order)
    common_activities = [act for act in case_path if act in ref_set]
    if len(common_activities) > 1:
        ref_indices = [reference_path.index(act) for act in common_activities]
        # Check if the ref_indices are sorted
        for k in range(len(ref_indices) - 1):
            if ref_indices[k] > ref_indices[k + 1]:
                act_curr = common_activities[k]
                act_next = common_activities[k + 1]
                deviations.append(f"Out of Order: '{act_curr}' executed before '{act_next}'")
            
    return deviations
