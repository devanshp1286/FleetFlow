from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date

from app import db
from app.models import Driver, MaintenanceLog, Vehicle, Expense
from app.utils.helpers import success, error, require_role, paginate

drivers_bp    = Blueprint("drivers",     __name__)
maintenance_bp = Blueprint("maintenance", __name__)
expenses_bp    = Blueprint("expenses",    __name__)

# ═══════════════════════════════════════════════════════════════════════════════
# DRIVERS
# ═══════════════════════════════════════════════════════════════════════════════

@drivers_bp.get("/")
@jwt_required()
def list_drivers():
    page   = request.args.get("page", 1, type=int)
    status = request.args.get("status")
    search = request.args.get("search", "").strip()

    q = Driver.query
    if status and status != "all":
        q = q.filter_by(duty_status=status)
    if search:
        q = q.filter(
            db.or_(Driver.full_name.ilike(f"%{search}%"),
                   Driver.license_number.ilike(f"%{search}%"))
        )
    q = q.order_by(Driver.created_at.desc())
    items, meta = paginate(q, page)
    return success([d.to_dict() for d in items], meta=meta)


@drivers_bp.post("/")
@require_role("admin", "dispatcher")
def create_driver():
    body = request.get_json(silent=True) or {}
    required = ["full_name", "license_number", "license_expiry"]
    missing  = [f for f in required if not body.get(f)]
    if missing:
        return error(f"Missing: {', '.join(missing)}", 422)
    if Driver.query.filter_by(license_number=body["license_number"]).first():
        return error("License number already registered.", 409)

    d = Driver(
        full_name      = body["full_name"],
        license_number = body["license_number"],
        license_expiry = date.fromisoformat(body["license_expiry"]),
        phone          = body.get("phone"),
        created_by     = get_jwt_identity(),
    )
    db.session.add(d)
    db.session.commit()
    return success(d.to_dict(), 201)


@drivers_bp.get("/<driver_id>")
@jwt_required()
def get_driver(driver_id):
    d    = Driver.query.get_or_404(driver_id)
    data = d.to_dict()
    recent = d.trips.order_by(db.desc("created_at")).limit(10).all()
    data["recent_trips"] = [t.to_dict() for t in recent]
    return success(data)


@drivers_bp.put("/<driver_id>")
@require_role("admin", "dispatcher")
def update_driver(driver_id):
    d    = Driver.query.get_or_404(driver_id)
    body = request.get_json(silent=True) or {}
    for field in ["full_name", "phone", "license_expiry", "duty_status", "incidents_count"]:
        if field in body:
            if field == "license_expiry":
                d.license_expiry = date.fromisoformat(body[field])
            else:
                setattr(d, field, body[field])
    # Recompute safety score
    score = max(0, 100 - (d.incidents_count * 15))
    d.safety_score = score
    db.session.commit()
    return success(d.to_dict())


# ═══════════════════════════════════════════════════════════════════════════════
# MAINTENANCE
# ═══════════════════════════════════════════════════════════════════════════════

@maintenance_bp.get("/")
@jwt_required()
def list_maintenance():
    page       = request.args.get("page", 1, type=int)
    vehicle_id = request.args.get("vehicle_id")
    status     = request.args.get("status")

    q = MaintenanceLog.query
    if vehicle_id:
        q = q.filter_by(vehicle_id=vehicle_id)
    if status and status != "all":
        q = q.filter_by(status=status)
    q = q.order_by(MaintenanceLog.service_date.desc())
    items, meta = paginate(q, page)
    return success([m.to_dict() for m in items], meta=meta)


@maintenance_bp.post("/")
@require_role("admin", "dispatcher")
def create_maintenance():
    body = request.get_json(silent=True) or {}
    required = ["vehicle_id", "service_type", "cost", "service_date", "odometer_at_service"]
    missing  = [f for f in required if body.get(f) is None]
    if missing:
        return error(f"Missing: {', '.join(missing)}", 422)

    vehicle = Vehicle.query.get(body["vehicle_id"])
    if not vehicle:
        return error("Vehicle not found.", 404)

    log = MaintenanceLog(
        vehicle_id          = vehicle.id,
        service_type        = body["service_type"],
        description         = body.get("description"),
        cost                = float(body["cost"]),
        service_date        = date.fromisoformat(body["service_date"]),
        odometer_at_service = float(body["odometer_at_service"]),
        next_service_km     = float(body["next_service_km"]) if body.get("next_service_km") else None,
        status              = "in_progress",
        logged_by           = get_jwt_identity(),
    )
    # Auto-lock vehicle
    vehicle.status = "in_shop"
    if log.next_service_km:
        vehicle.next_service_km = log.next_service_km

    db.session.add(log)
    db.session.commit()
    return success({**log.to_dict(), "vehicle_locked": True}, 201)


@maintenance_bp.patch("/<log_id>/complete")
@require_role("admin", "dispatcher")
def complete_maintenance(log_id):
    log = MaintenanceLog.query.get_or_404(log_id)
    log.status = "completed"
    vehicle = Vehicle.query.get(log.vehicle_id)
    if vehicle and vehicle.status == "in_shop":
        vehicle.status = "available"
        vehicle.last_service_date = log.service_date
    db.session.commit()
    return success({**log.to_dict(), "vehicle_unlocked": True})


# ═══════════════════════════════════════════════════════════════════════════════
# EXPENSES
# ═══════════════════════════════════════════════════════════════════════════════

@expenses_bp.get("/")
@jwt_required()
def list_expenses():
    page       = request.args.get("page", 1, type=int)
    vehicle_id = request.args.get("vehicle_id")
    etype      = request.args.get("type")
    start      = request.args.get("start_date")
    end        = request.args.get("end_date")

    q = Expense.query
    if vehicle_id:
        q = q.filter_by(vehicle_id=vehicle_id)
    if etype:
        q = q.filter_by(expense_type=etype)
    if start:
        q = q.filter(Expense.expense_date >= date.fromisoformat(start))
    if end:
        q = q.filter(Expense.expense_date <= date.fromisoformat(end))
    q = q.order_by(Expense.expense_date.desc())
    items, meta = paginate(q, page)
    return success([e.to_dict() for e in items], meta=meta)


@expenses_bp.post("/")
@require_role("admin", "dispatcher")
def create_expense():
    body = request.get_json(silent=True) or {}
    required = ["vehicle_id", "expense_type", "amount", "expense_date"]
    missing  = [f for f in required if not body.get(f)]
    if missing:
        return error(f"Missing: {', '.join(missing)}", 422)

    if body["expense_type"] not in ("fuel", "toll", "repair", "insurance", "other"):
        return error("Invalid expense type.", 422)

    e = Expense(
        trip_id              = body.get("trip_id"),
        vehicle_id           = body["vehicle_id"],
        driver_id            = body.get("driver_id"),
        expense_type         = body["expense_type"],
        amount               = float(body["amount"]),
        fuel_liters          = float(body["fuel_liters"]) if body.get("fuel_liters") else None,
        fuel_price_per_liter = float(body["fuel_price_per_liter"]) if body.get("fuel_price_per_liter") else None,
        expense_date         = date.fromisoformat(body["expense_date"]),
        notes                = body.get("notes"),
        logged_by            = get_jwt_identity(),
    )
    db.session.add(e)
    db.session.commit()
    return success(e.to_dict(), 201)
