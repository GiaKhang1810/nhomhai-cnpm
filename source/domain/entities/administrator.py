from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Administrator:
    """Administrator identity. The current schema uses users.user_id as admin_id."""

    admin_id: int

    @property
    def user_id(self) -> int:
        """The schema stores administrators directly in users.user_id."""
        return self.admin_id

    def manage_staff_accounts(self, service: Any, action: str, *args: Any, **kwargs: Any):
        actions = {
            "create": "create_staff_account",
            "list": "list_staff_accounts",
            "update": "update_staff_account",
            "deactivate": "deactivate_staff_account",
            "activate": "activate_staff_account",
            "delete": "delete_staff_account",
        }
        method_name = actions.get(action)
        if method_name is None:
            raise ValueError(f"Thao tác quản lý tài khoản không hợp lệ: {action}.")
        return getattr(service, method_name)(*args, **kwargs)

    def generate_reports(self, repository: Any) -> dict[str, Any]:
        return {
            "metrics": repository.get_dashboard_metrics(),
            "activity": repository.get_activity_stats(),
            "categories": repository.get_category_distribution(),
            "recent_transactions": repository.get_recent_transactions(),
        }
