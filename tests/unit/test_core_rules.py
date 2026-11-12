import unittest
from datetime import date
from decimal import Decimal

from source.core.money import calculate_overdue_fine
from source.web.validators.borrowing_validator import validate_borrowing_request


class OverdueFineTests(unittest.TestCase):
    def test_no_fine_when_returned_on_due_date(self):
        self.assertEqual(
            calculate_overdue_fine(date(2026, 11, 10), date(2026, 11, 10)),
            Decimal("0.00"),
        )

    def test_no_fine_when_returned_early(self):
        self.assertEqual(
            calculate_overdue_fine(date(2026, 11, 10), date(2026, 11, 8)),
            Decimal("0.00"),
        )

    def test_fine_is_per_day_per_copy(self):
        self.assertEqual(
            calculate_overdue_fine(date(2026, 11, 10), date(2026, 11, 13)),
            Decimal("15000.00"),
        )


class BorrowingValidationTests(unittest.TestCase):
    def test_valid_request(self):
        valid, _ = validate_borrowing_request({
            "reader_id": "RD-0001",
            "copy_ids": ["CP-0001", "CP-0002"],
        })
        self.assertTrue(valid)

    def test_rejects_missing_reader(self):
        valid, message = validate_borrowing_request({"copy_ids": ["CP-0001"]})
        self.assertFalse(valid)
        self.assertIn("độc giả", message.lower())

    def test_rejects_more_than_five_copies(self):
        valid, _ = validate_borrowing_request({
            "reader_id": "RD-0001",
            "copy_ids": [f"CP-{index}" for index in range(6)],
        })
        self.assertFalse(valid)

    def test_rejects_duplicate_copy_ids(self):
        valid, message = validate_borrowing_request({
            "reader_id": "RD-0001",
            "copy_ids": ["CP-0001", "CP-0001"],
        })
        self.assertFalse(valid)
        self.assertIn("trùng lặp", message.lower())

    def test_rejects_invalid_copy_id_type(self):
        valid, _ = validate_borrowing_request({
            "reader_id": "RD-0001",
            "copy_ids": [None],
        })
        self.assertFalse(valid)


if __name__ == "__main__":
    unittest.main()
