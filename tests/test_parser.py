import unittest
import sys
import os
import pandas as pd
from io import StringIO

# Append parent directory to path so we can import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.parser import load_and_clean_csv, extract_variants, compute_dfg_data, format_duration

class TestParser(unittest.TestCase):

    def setUp(self):
        # Set up a mock CSV event log for testing
        self.mock_csv = """case_id,activity,timestamp,user
Case_1,Create Order,2026-05-01 09:00:00,Alice
Case_1,Approve Credit,2026-05-01 10:00:00,Bob
Case_1,Close Order,2026-05-01 11:00:00,Alice
Case_2,Create Order,2026-05-02 09:00:00,Alice
Case_2,Close Order,2026-05-02 10:00:00,Alice
"""
        self.df = load_and_clean_csv(
            StringIO(self.mock_csv), 
            case_col="case_id", 
            activity_col="activity", 
            timestamp_col="timestamp"
        )

    def test_load_and_clean_csv(self):
        """Test if columns are standard PM4Py format and clean."""
        self.assertIn('case:concept:name', self.df.columns)
        self.assertIn('concept:name', self.df.columns)
        self.assertIn('time:timestamp', self.df.columns)
        self.assertEqual(len(self.df), 5)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(self.df['time:timestamp']))

    def test_validate_csv_headers_missing(self):
        """Test if ValueError is correctly raised when columns are missing."""
        invalid_csv = StringIO("wrong_case,activity,timestamp\n1,ActA,2026-05-01 09:00:00")
        with self.assertRaises(ValueError) as context:
            load_and_clean_csv(
                invalid_csv,
                case_col="case_id",
                activity_col="activity",
                timestamp_col="timestamp"
            )
        self.assertIn("missing the following required columns: Case ID column 'case_id'", str(context.exception))

    def test_load_and_clean_json(self):
        """Test if hybrid loader correctly reads and standardizes JSON logs."""
        json_data = StringIO(
            '[{"case_id": "Case_X", "activity": "A", "timestamp": "2026-05-01 12:00:00"},'
            '{"case_id": "Case_X", "activity": "B", "timestamp": "2026-05-01 13:00:00"}]'
        )
        df_json = load_and_clean_csv(
            json_data,
            case_col="case_id",
            activity_col="activity",
            timestamp_col="timestamp"
        )
        self.assertEqual(len(df_json), 2)
        self.assertEqual(df_json.iloc[0]['concept:name'], 'A')
        self.assertEqual(df_json.iloc[1]['concept:name'], 'B')

    def test_extract_variants(self):
        """Test if unique process variants are correctly sequenced and ranked."""
        variants = extract_variants(self.df)
        self.assertEqual(len(variants), 2) # Variant 1: Create, Approve, Close. Variant 2: Create, Close
        
        # Variant 1 (most frequent)
        var_1 = next(v for v in variants if v["id"] == 1)
        self.assertEqual(var_1["activities"], ["Create Order", "Approve Credit", "Close Order"])
        self.assertEqual(var_1["case_count"], 1)
        self.assertEqual(var_1["cases"], ["Case_1"])

    def test_compute_dfg_data(self):
        """Test transition discovery in Directly-Follows Graph."""
        dfg_freq, dfg_perf, activity_freq = compute_dfg_data(self.df)
        
        # Discover transitions
        self.assertIn(("Create Order", "Approve Credit"), dfg_freq)
        self.assertEqual(dfg_freq[("Create Order", "Approve Credit")], 1)
        
        self.assertIn(("Create Order", "Close Order"), dfg_freq)
        self.assertEqual(dfg_freq[("Create Order", "Close Order")], 1)
        
        # Test performance (durations in seconds)
        # Create Order -> Approve Credit took exactly 1 hour (3600 seconds)
        self.assertEqual(dfg_perf[("Create Order", "Approve Credit")], 3600.0)

    def test_format_duration(self):
        """Test human-readable duration formatting helper."""
        self.assertEqual(format_duration(30), "30.0s")
        self.assertEqual(format_duration(120), "2.0m")
        self.assertEqual(format_duration(7200), "2.0h")
        self.assertEqual(format_duration(172800), "2.0d")

if __name__ == '__main__':
    unittest.main()
