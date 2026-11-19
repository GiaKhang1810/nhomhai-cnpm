from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Librarian:
    """Staff profile and application actions assigned to the Librarian role."""

    staff_id: str
    user_id: int
    full_name: str
    phone: str | None = None

    @staticmethod
    def _dispatch(service: Any, actions: dict[str, str], action: str, *args: Any, **kwargs: Any):
        method_name = actions.get(action)
        if method_name is None:
            raise ValueError(f"Thao tác thủ thư không hợp lệ: {action}.")
        return getattr(service, method_name)(*args, **kwargs)

    def manage_books(self, service: Any, action: str, *args: Any, **kwargs: Any):
        return self._dispatch(service, {
            "search": "search_books", "details": "get_book_details", "create": "add_new_book",
            "update": "update_book", "deactivate": "deactivate_book", "activate": "activate_book",
        }, action, *args, **kwargs)

    def manage_readers(self, service: Any, action: str, *args: Any, **kwargs: Any):
        return self._dispatch(service, {
            "search": "search_readers", "create": "create_new_reader", "update": "update_reader",
            "deactivate": "deactivate_reader", "activate": "activate_reader",
        }, action, *args, **kwargs)

    def process_borrowing(self, service: Any, *args: Any, **kwargs: Any):
        return service.process_borrowing(*args, **kwargs)

    def process_returns(self, service: Any, *args: Any, **kwargs: Any):
        return service.process_returns(*args, **kwargs)

    def manage_fines(self, service: Any, action: str, *args: Any, **kwargs: Any):
        return self._dispatch(service, {
            "outstanding": "get_outstanding_charges", "payment": "record_payment",
        }, action, *args, **kwargs)
