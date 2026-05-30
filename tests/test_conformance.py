import unittest
import sys
import os

# Append parent directory to path so we can import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.conformance import check_exact_match

class TestConformance(unittest.TestCase):

    def test_check_exact_match(self):
        ref = ["A", "B", "C"]
        self.assertTrue(check_exact_match(["A", "B", "C"], ref))
        self.assertFalse(check_exact_match(["A", "B"], ref))
        self.assertFalse(check_exact_match(["A", "B", "C", "D"], ref))
        self.assertFalse(check_exact_match(["B", "A", "C"], ref))

if __name__ == '__main__':
    unittest.main()
