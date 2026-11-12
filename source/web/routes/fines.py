from flask import Blueprint, jsonify, request, session

from source.core.decorators import login_required, role_required
from source.services.fine_service import FineService

fines_bp = Blueprint("fines", __name__, url_prefix="/api/fines")
fine_service = FineService()


@fines_bp.get("/outstanding")
@login_required
@role_required("LIBRARIAN", "ADMIN")
def outstanding():
    reader_id = request.args.get("reader_id", "").strip() or None
    rows = fine_service.get_outstanding_charges(reader_id)
    for row in rows:
        for field in ("overdue_fine", "compensation", "paid_amount", "outstanding"):
            row[field] = str(row[field])
    return jsonify({"success": True, "data": rows})


@fines_bp.post("/payments")
@login_required
@role_required("LIBRARIAN")
def record_payment():
    data = request.get_json(silent=True) or {}
    success, message = fine_service.record_payment(data, int(session["user_id"]))
    return jsonify({"success": success, "message": message}), 201 if success else 400
