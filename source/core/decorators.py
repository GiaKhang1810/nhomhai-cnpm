from functools import wraps
from typing import Callable, TypeVar, Any

from flask import abort, flash, redirect, request, session, url_for

F = TypeVar("F", bound=Callable[..., Any])


def login_required(function: F) -> F:
    @wraps(function)
    def decorated_function(*args: Any, **kwargs: Any):
        if "user_id" not in session:
            if request.path.startswith("/api/") or request.is_json:
                abort(401)
            flash("Vui lòng đăng nhập để tiếp tục.", "warning")
            return redirect(url_for("auth.login"))
        return function(*args, **kwargs)
    return decorated_function  # type: ignore[return-value]


def role_required(*roles: str):
    def decorator(function: F) -> F:
        @wraps(function)
        def decorated_function(*args: Any, **kwargs: Any):
            if "user_id" not in session:
                if request.path.startswith("/api/") or request.is_json:
                    abort(401)
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
                abort(403)
            return function(*args, **kwargs)
        return decorated_function  # type: ignore[return-value]
    return decorator
