from datetime import date
from decimal import Decimal

OVERDUE_FINE_PER_DAY = Decimal("5000.00")


def calculate_overdue_fine(due_date: date, return_date: date) -> Decimal:
    """Calculate late fee per returned copy, following the project specification."""
    overdue_days = max((return_date - due_date).days, 0)
    return OVERDUE_FINE_PER_DAY * overdue_days
