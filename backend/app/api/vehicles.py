from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Vehicle
from app.utils.helpers import success, error, require_role, paginate

vehicles_bp = Blueprint("vehicles", __name__)


@vehicles_bp.get("/")
@jwt_required()
def list_vehicles():
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status   = request.args.get("status")
    search   = request.args.get("search", "").strip()
    vtype    = request.args.get("type")

    q = Vehicle.query
    if status and status != "all":
        q = q.filter_by(status=status)
    if vtype:
        q = q.filter_by(type=vtype)
    if search:
        q = q.filter(
            db.or_(
                Vehicle.registration_number.ilike(f"%{search}%"),
                Vehicle.make.ilike(f"%{search}%"),
                Vehicle.model.ilike(f"%{search}%"),
            )
        )
    q = q.order_by(Vehicle.created_at.desc())
    items, meta = paginate(q, page, per_page)
    return success([v.to_dict() for v in items], meta=meta)


@vehicles_bp.post("/")
@require_role("admin", "dispatcher")
def create_vehicle():
    body = request.get_json(silent=True) or {}

    required = ["registration_number", "make", "model", "type", "capacity_kg"]
    missing  = [f for f in required if not body.get(f)]
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 422)

    if body["type"] not in ("truck", "mini", "van", "tanker"):
        return error("Invalid vehicle type.", 422)

    if Vehicle.query.filter_by(registration_number=body["registration_number"]).first():
        return error("Registration number already exists.", 409, "REG_DUPLICATE")

    v = Vehicle(
        registration_number  = body["registration_number"].upper().strip(),
        make                 = body["make"],
        model                = body["model"],
        type                 = body["type"],
        capacity_kg          = float(body["capacity_kg"]),
        odometer_km          = float(body.get("odometer_km", 0)),
        fuel_efficiency_kmpl = float(body["fuel_efficiency_kmpl"]) if body.get("fuel_efficiency_kmpl") else None,
        next_service_km      = float(body["next_service_km"]) if body.get("next_service_km") else None,
        created_by           = get_jwt_identity(),
    )
    db.session.add(v)
    db.session.commit()
    return success(v.to_dict(), 201)


@vehicles_bp.get("/<vehicle_id>")
@jwt_required()
def get_vehicle(vehicle_id):
    v = Vehicle.query.get_or_404(vehicle_id)
    data = v.to_dict()
    data["maintenance_history"] = [m.to_dict() for m in v.maintenance.order_by(db.desc("service_date")).limit(10)]
    data["recent_trips"] = [t.to_dict() for t in v.trips.order_by(db.desc("created_at")).limit(5)]
    return success(data)


@vehicles_bp.put("/<vehicle_id>")
@require_role("admin", "dispatcher")
def update_vehicle(vehicle_id):
    v    = Vehicle.query.get_or_404(vehicle_id)
    body = request.get_json(silent=True) or {}

    allowed = ["make", "model", "type", "capacity_kg", "odometer_km",
               "fuel_efficiency_kmpl", "last_service_date", "next_service_km", "status"]
    for field in allowed:
        if field in body:
            setattr(v, field, body[field])

    db.session.commit()
    return success(v.to_dict())


@vehicles_bp.delete("/<vehicle_id>")
@require_role("admin")
def delete_vehicle(vehicle_id):
    v = Vehicle.query.get_or_404(vehicle_id)
    if v.trips.filter(Vehicle.status.in_(["dispatched", "in_transit"])).count():
        return error("Cannot retire vehicle with active trips.", 409)
    v.status = "retired"
    db.session.commit()
    return success({"message": "Vehicle retired successfully."})
