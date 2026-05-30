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
