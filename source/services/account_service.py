from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from flask import current_app

from source.core.security import hash_password
from source.database.connection import get_db_connection


class AccountService:
    def create_staff_account(self, data: dict[str, Any]) -> tuple[bool, str]:
        username = str(data.get("username", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        full_name = str(data.get("full_name", "")).strip()
        role = str(data.get("role", "LIBRARIAN")).upper()
        if not all((username, email, password)):
            return False, "Vui lòng điền đầy đủ tên đăng nhập, email và mật khẩu."
        if role == "LIBRARIAN" and not full_name:
            return False, "Họ tên thủ thư không được để trống."
        if len(password) < 8:
            return False, "Mật khẩu phải có ít nhất 8 ký tự."
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            return False, "Địa chỉ email không hợp lệ."
        if role not in {"LIBRARIAN", "ADMIN"}:
            return False, "Vai trò nhân viên không hợp lệ."

        db = get_db_connection()
        cursor = db.cursor()
        staff_id = f"STF-{uuid4().hex[:10].upper()}"
        try:
            db.start_transaction()
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role, account_status) VALUES (%s, %s, %s, %s, 'ACTIVE')",
                (username, email, hash_password(password), role),
            )
            user_id = cursor.lastrowid
            if role == "LIBRARIAN":
                cursor.execute(
                    "INSERT INTO librarians (staff_id, user_id, full_name, phone) VALUES (%s, %s, %s, %s)",
                    (staff_id, user_id, full_name, str(data.get("phone", "")).strip() or None),
                )
            db.commit()
            description = "thủ thư" if role == "LIBRARIAN" else "quản trị viên"
            suffix = f" Mã nhân viên: {staff_id}" if role == "LIBRARIAN" else ""
            return True, f"Tạo tài khoản {description} thành công.{suffix}"
        except Exception:
            db.rollback()
            current_app.logger.exception("Tạo tài khoản nhân viên thất bại")
            return False, "Không thể tạo tài khoản. Username hoặc email có thể đã tồn tại."
        finally:
            cursor.close()

    def list_staff_accounts(self) -> list[dict[str, Any]]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT u.user_id, u.username, u.email, u.role, u.account_status,
                          l.staff_id, l.full_name, l.phone, u.created_at
                   FROM users u LEFT JOIN librarians l ON l.user_id=u.user_id
                   WHERE u.role IN ('LIBRARIAN', 'ADMIN')
                   ORDER BY u.created_at DESC"""
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def update_staff_account(self, user_id: int, data: dict[str, Any]) -> tuple[bool, str]:
        role = str(data.get("role", "")).upper() if data.get("role") else None
        if role and role not in {"LIBRARIAN", "ADMIN"}:
            return False, "Vai trò nhân viên không hợp lệ."
        if "username" in data and not str(data["username"]).strip():
            return False, "Tên đăng nhập không được để trống."
        if "email" in data and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(data["email"]).strip()):
            return False, "Địa chỉ email không hợp lệ."
        if "full_name" in data and not str(data["full_name"]).strip():
            return False, "Họ tên không được để trống."

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            db.start_transaction()
            cursor.execute(
                "SELECT user_id, role, username, email FROM users WHERE user_id=%s FOR UPDATE",
                (user_id,),
            )
            account = cursor.fetchone()
            if not account or account["role"] not in {"LIBRARIAN", "ADMIN"}:
                db.rollback()
                return False, "Không tìm thấy tài khoản nhân viên."

            target_role = role or account["role"]
            if "username" in data or "email" in data:
                cursor.execute(
                    "UPDATE users SET username=%s, email=%s WHERE user_id=%s",
                    (
                        str(data.get("username", account["username"])).strip(),
                        str(data.get("email", account["email"])).strip().lower(),
                        user_id,
                    ),
                )

            cursor.execute(
                "SELECT staff_id, full_name, phone FROM librarians WHERE user_id=%s FOR UPDATE",
                (user_id,),
            )
            staff = cursor.fetchone()
            if staff:
                if "full_name" in data or "phone" in data:
                    cursor.execute(
                        "UPDATE librarians SET full_name=%s, phone=%s WHERE user_id=%s",
                        (
                            str(data.get("full_name", staff["full_name"])).strip(),
                            str(data.get("phone", staff["phone"] or "")).strip() or None,
                            user_id,
                        ),
                    )
            elif target_role == "LIBRARIAN":
                full_name = str(data.get("full_name", "")).strip()
                if not full_name:
                    db.rollback()
                    return False, "Cần nhập họ tên khi chuyển tài khoản sang vai trò Thủ thư."
                cursor.execute(
                    "INSERT INTO librarians (staff_id, user_id, full_name, phone) VALUES (%s, %s, %s, %s)",
                    (
                        f"STF-{uuid4().hex[:10].upper()}",
                        user_id,
                        full_name,
                        str(data.get("phone", "")).strip() or None,
                    ),
                )

            if role:
                cursor.execute("UPDATE users SET role=%s WHERE user_id=%s", (role, user_id))

            db.commit()
            return True, "Cập nhật tài khoản nhân viên thành công."
        except Exception:
            db.rollback()
            current_app.logger.exception("Cập nhật tài khoản nhân viên thất bại")
            return False, "Không thể cập nhật tài khoản. Hãy kiểm tra username/email có bị trùng hoặc dữ liệu có hợp lệ không."
        finally:
            cursor.close()

    def deactivate_staff_account(self, user_id: int, current_user_id: int) -> tuple[bool, str]:
        if user_id == current_user_id:
            return False, "Bạn không thể tự khóa tài khoản đang sử dụng."
        db = get_db_connection()
        cursor = db.cursor()
        try:
            db.start_transaction()
            cursor.execute("UPDATE users SET account_status='INACTIVE' WHERE user_id=%s AND role IN ('LIBRARIAN', 'ADMIN')", (user_id,))
            if cursor.rowcount != 1:
                db.rollback()
                return False, "Không tìm thấy tài khoản nhân viên."
            db.commit()
            return True, "Đã khóa tài khoản nhân viên."
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()


    def activate_staff_account(self, user_id: int) -> tuple[bool, str]:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            db.start_transaction()
            cursor.execute(
                "SELECT user_id, role, account_status FROM users WHERE user_id=%s FOR UPDATE",
                (user_id,),
            )
            account = cursor.fetchone()
            if not account or account["role"] not in {"LIBRARIAN", "ADMIN"}:
                db.rollback()
                return False, "Không tìm thấy tài khoản nhân viên."
            if account["account_status"] == "ACTIVE":
                db.rollback()
                return True, "Tài khoản nhân viên đang hoạt động."
            cursor.execute(
                "UPDATE users SET account_status='ACTIVE' WHERE user_id=%s",
                (user_id,),
            )
            db.commit()
            return True, "Đã mở khóa tài khoản nhân viên."
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()

    def delete_staff_account(self, user_id: int, current_user_id: int) -> tuple[bool, str]:
        if user_id == current_user_id:
            return False, "Bạn không thể xóa tài khoản đang sử dụng."

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        try:
            db.start_transaction()
            cursor.execute(
                "SELECT user_id, role, account_status FROM users WHERE user_id=%s FOR UPDATE",
                (user_id,),
            )
            account = cursor.fetchone()
            if not account or account["role"] not in {"LIBRARIAN", "ADMIN"}:
                db.rollback()
                return False, "Không tìm thấy tài khoản nhân viên."

            if account["role"] == "ADMIN" and account["account_status"] == "ACTIVE":
                cursor.execute(
                    "SELECT user_id FROM users WHERE role='ADMIN' AND account_status='ACTIVE' FOR UPDATE"
                )
                active_admins = cursor.fetchall()
                if len(active_admins) <= 1:
                    db.rollback()
                    return False, "Không thể xóa quản trị viên đang hoạt động cuối cùng."

            cursor.execute(
                "SELECT COUNT(*) AS total FROM fine_payments WHERE received_by=%s",
                (user_id,),
            )
            if int(cursor.fetchone()["total"]) > 0:
                db.rollback()
                return False, "Tài khoản đã ghi nhận thanh toán. Không thể xóa để bảo toàn lịch sử; hãy khóa tài khoản thay thế."

            cursor.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
            if cursor.rowcount != 1:
                db.rollback()
                return False, "Không thể xóa tài khoản nhân viên."
            db.commit()
            return True, "Đã xóa tài khoản nhân viên."
        except Exception:
            db.rollback()
            raise
        finally:
            cursor.close()
