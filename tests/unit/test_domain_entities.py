import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

from source.domain.entities import (
    Administrator,
    Book,
    BookCopy,
    BorrowingDetail,
    BorrowingRecord,
    Librarian,
    Reader,
)


class BookEntityTests(unittest.TestCase):
    def setUp(self):
        self.book = Book(
            book_code="BK-0001",
            title="Clean Code",
            author="Robert C. Martin",
            listed_value=Decimal("250000.00"),
            total_quantity=3,
            available_quantity=2,
        )

    def test_update_book_accepts_valid_values(self):
        self.book.update_book(title="Clean Code: Updated", available_quantity=1)
        self.assertEqual(self.book.title, "Clean Code: Updated")
        self.assertEqual(self.book.available_quantity, 1)

    def test_update_book_rejects_available_quantity_above_total(self):
        with self.assertRaises(ValueError):
            self.book.update_book(available_quantity=4)

    def test_update_book_rejects_negative_listed_value(self):
        with self.assertRaises(ValueError):
            self.book.update_book(listed_value=Decimal("-1"))

    def test_book_can_be_deactivated_and_activated(self):
        self.book.deactivate()
        self.assertFalse(self.book.is_active)
        self.book.activate()
        self.assertTrue(self.book.is_active)


class BookCopyEntityTests(unittest.TestCase):
    def test_book_copy_status_update(self):
        copy = BookCopy("CP-0001", "BK-0001")
        copy.update_status("BORROWED")
        self.assertEqual(copy.status, "BORROWED")
        copy.update_status("DAMAGED", "DAMAGED")
        self.assertEqual((copy.status, copy.condition), ("DAMAGED", "DAMAGED"))

    def test_available_copy_must_be_normal(self):
        copy = BookCopy("CP-0001", "BK-0001", condition="DAMAGED", status="DAMAGED")
        with self.assertRaises(ValueError):
            copy.update_status("AVAILABLE")

    def test_rejects_unknown_copy_status(self):
        copy = BookCopy("CP-0001", "BK-0001")
        with self.assertRaises(ValueError):
            copy.update_status("IN_STOCK")


class BorrowingEntityTests(unittest.TestCase):
    def test_calculates_overdue_fine(self):
        detail = BorrowingDetail("CP-0001")
        total = detail.calculate_fine(
            date(2026, 11, 10), date(2026, 11, 13), listed_value=Decimal("100000")
        )
        self.assertEqual(detail.overdue_fine, Decimal("15000.00"))
        self.assertEqual(detail.compensation, Decimal("0.00"))
        self.assertEqual(total, Decimal("15000.00"))

    def test_calculates_compensation_for_lost_copy(self):
        detail = BorrowingDetail("CP-0001")
        total = detail.calculate_fine(
            date(2026, 11, 10), date(2026, 11, 13),
            condition="LOST", listed_value=Decimal("125000.00"),
        )
        self.assertEqual(detail.overdue_fine, Decimal("15000.00"))
        self.assertEqual(detail.compensation, Decimal("125000.00"))
        self.assertEqual(total, Decimal("140000.00"))

    def test_borrowing_record_rejects_duplicate_copy(self):
        record = BorrowingRecord("LN-0001", "RD-0001", date(2026, 11, 1), date(2026, 11, 15))
        record.add_detail(BorrowingDetail("CP-0001"))
        with self.assertRaises(ValueError):
            record.add_detail(BorrowingDetail("CP-0001"))

    def test_borrowing_record_tracks_full_return(self):
        record = BorrowingRecord("LN-0001", "RD-0001", date(2026, 11, 1), date(2026, 11, 15))
        first = BorrowingDetail("CP-0001")
        second = BorrowingDetail("CP-0002")
        record.add_detail(first)
        record.add_detail(second)
        self.assertFalse(record.is_fully_returned())
        first.return_date = date(2026, 11, 10)
        second.return_date = date(2026, 11, 11)
        self.assertTrue(record.is_fully_returned())


class ReaderEntityTests(unittest.TestCase):
    def setUp(self):
        self.reader = Reader(
            reader_id="RD-0001", user_id=12, full_name="Test Reader",
            identity_number="012345678901", card_issue_date=date(2026, 1, 1),
            card_expiry_date=date(2027, 1, 1), phone="0900000000",
        )

    def test_view_profile_does_not_expose_user_credentials(self):
        profile = self.reader.view_profile()
        self.assertEqual(profile["reader_id"], "RD-0001")
        self.assertNotIn("password", profile)
        self.assertNotIn("user_id", profile)

    def test_view_borrowing_history_is_scoped_to_reader_id(self):
        loader = Mock(return_value=[{"loan_id": "LN-0001"}])
        history = self.reader.view_borrowing_history(loader)
        loader.assert_called_once_with("RD-0001")
        self.assertEqual(history[0]["loan_id"], "LN-0001")


class RoleEntityTests(unittest.TestCase):
    def test_librarian_delegates_book_management(self):
        librarian = Librarian("ST-01", 3, "Test Librarian")
        service = Mock()
        service.add_new_book.return_value = (True, "created")
        result = librarian.manage_books(service, "create", {"title": "Book"})
        service.add_new_book.assert_called_once_with({"title": "Book"})
        self.assertEqual(result, (True, "created"))

    def test_librarian_rejects_unknown_action(self):
        librarian = Librarian("ST-01", 3, "Test Librarian")
        with self.assertRaises(ValueError):
            librarian.manage_books(Mock(), "drop_database")

    def test_librarian_delegates_borrowing_and_returns(self):
        librarian = Librarian("ST-01", 3, "Test Librarian")
        borrowing = Mock()
        returns = Mock()
        borrowing.process_borrowing.return_value = (True, "loan created")
        returns.process_returns.return_value = (True, "returned", Decimal("0.00"))
        self.assertEqual(librarian.process_borrowing(borrowing, "RD-1", ["CP-1"]), (True, "loan created"))
        self.assertEqual(librarian.process_returns(returns, "LN-1", []), (True, "returned", Decimal("0.00")))
        borrowing.process_borrowing.assert_called_once_with("RD-1", ["CP-1"])
        returns.process_returns.assert_called_once_with("LN-1", [])

    def test_librarian_manages_fine_payments(self):
        librarian = Librarian("ST-01", 3, "Test Librarian")
        service = Mock()
        service.record_payment.return_value = (True, "paid")
        result = librarian.manage_fines(service, "payment", {"detail_id": 1}, 3)
        service.record_payment.assert_called_once_with({"detail_id": 1}, 3)
        self.assertEqual(result, (True, "paid"))

    def test_administrator_delegates_staff_account_management(self):
        administrator = Administrator(admin_id=7)
        service = Mock()
        service.create_staff_account.return_value = (True, "created")
        result = administrator.manage_staff_accounts(service, "create", {"username": "staff"})
        service.create_staff_account.assert_called_once_with({"username": "staff"})
        self.assertEqual(result, (True, "created"))

    def test_administrator_generates_all_report_sections(self):
        administrator = Administrator(admin_id=7)
        repository = Mock()
        repository.get_dashboard_metrics.return_value = {"books": 4}
        repository.get_activity_stats.return_value = []
        repository.get_category_distribution.return_value = []
        repository.get_recent_transactions.return_value = []
        report = administrator.generate_reports(repository)
        self.assertEqual(report["metrics"], {"books": 4})
        repository.get_activity_stats.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
