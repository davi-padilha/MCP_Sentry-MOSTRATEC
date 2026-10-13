import unittest
from apurar_tempos import review_timing


class TimingTests(unittest.TestCase):
    def test_separates_turns_gaps_and_accounting_difference(self):
        result=review_timing([{"started_at":100,"completed_at":110,"duration_ms":10000},
                              {"started_at":125,"completed_at":130,"duration_ms":4800}])
        self.assertEqual(result["turn_duration_seconds"],14.8)
        self.assertEqual(result["between_turns_seconds"],15)
        self.assertEqual(result["observed_interval_seconds"],30)
        self.assertAlmostEqual(result["clock_or_accounting_difference_seconds"],0.2)

    def test_missing_invalid_and_overlapping_turns_are_unavailable(self):
        for turns in ([],[{}],[{"started_at":0,"completed_at":1,"duration_ms":float('nan')}],
                      [{"started_at":0,"completed_at":3,"duration_ms":3000},{"started_at":2,"completed_at":4,"duration_ms":2000}]):
            with self.subTest(turns=turns):self.assertFalse(review_timing(turns)["available"])


if __name__=='__main__':unittest.main()
