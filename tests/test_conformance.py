import unittest
import sys
import os

# Append parent directory to path so we can import src modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.conformance import check_exact_match, calculate_alignment_fitness, analyze_deviations

class TestConformance(unittest.TestCase):

    def test_check_exact_match(self):
        ref = ["A", "B", "C"]
        self.assertTrue(check_exact_match(["A", "B", "C"], ref))
        self.assertFalse(check_exact_match(["A", "B"], ref))
        self.assertFalse(check_exact_match(["A", "B", "C", "D"], ref))
        self.assertFalse(check_exact_match(["B", "A", "C"], ref))

    def test_calculate_alignment_fitness(self):
        ref = ["A", "B", "C"]
        # Perfect fit
        self.assertEqual(calculate_alignment_fitness(["A", "B", "C"], ref), 1.0)
        # Empty sequences
        self.assertEqual(calculate_alignment_fitness([], []), 1.0)
        # Completely different
        self.assertEqual(calculate_alignment_fitness(["X", "Y", "Z"], ref), 0.0)
        # One deletion (distance = 1, max_len = 3, fitness = 1 - 1/3 = 0.6666...)
        self.assertAlmostEqual(calculate_alignment_fitness(["A", "C"], ref), 2/3)
        # One insertion (distance = 1, max_len = 4, fitness = 1 - 1/4 = 0.75)
        self.assertEqual(calculate_alignment_fitness(["A", "B", "X", "C"], ref), 0.75)

    def test_analyze_deviations_basic(self):
        ref = ["A", "B", "C"]
        # Compliant
        self.assertEqual(analyze_deviations(["A", "B", "C"], ref), [])
        # Missing B
        self.assertEqual(analyze_deviations(["A", "C"], ref), ["Missing: 'B'"])
        # Unexpected X
        self.assertEqual(analyze_deviations(["A", "X", "B", "C"], ref), ["Unexpected: 'X'"])
        # Missing B and unexpected Y
        self.assertEqual(sorted(analyze_deviations(["A", "Y", "C"], ref)), sorted(["Missing: 'B'", "Unexpected: 'Y'"]))

if __name__ == '__main__':
    unittest.main()
