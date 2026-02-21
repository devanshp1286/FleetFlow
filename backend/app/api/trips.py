from datetime import datetime, timezone
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Trip, Vehicle, Driver
from app.utils.helpers import success, error, require_role, paginate

trips_bp = Blueprint("trips", __name__)


def _validate_dispatch(vehicle: Vehicle, driver: Driver, cargo_kg: float):
    """Core dispatch validation. Returns list of validation errors."""
    errors = []

    if vehicle.status == "in_shop":
        errors.append({
            "code": "VEHICLE_IN_SHOP",
            "message": f"Vehicle {vehicle.registration_number} is currently in the shop for maintenance."
        })
    elif vehicle.status == "on_trip":
        errors.append({
            "code": "VEHICLE_ON_TRIP",
            "message": f"Vehicle {vehicle.registration_number} is already on an active trip."
        })
    elif vehicle.status == "retired":
        errors.append({
            "code": "VEHICLE_RETIRED",
            "message": f"Vehicle {vehicle.registration_number} is retired."
        })

    if cargo_kg > float(vehicle.capacity_kg):
        excess = cargo_kg - float(vehicle.capacity_kg)
        errors.append({
            "code": "TRIP_WEIGHT_EXCEEDED",
            "message": f"Cargo {cargo_kg}kg exceeds vehicle capacity {float(vehicle.capacity_kg)}kg by {excess:.1f}kg.",
            "detail": {
                "capacity_kg": float(vehicle.capacity_kg),
                "requested_kg": cargo_kg,
                "excess_kg": round(excess, 2),
            }
        })

    if driver.duty_status == "on_trip":
        errors.append({
            "code": "DRIVER_ON_TRIP",
            "message": f"Driver {driver.full_name} is already assigned to an active trip."
        })
    elif driver.duty_status == "suspended":
        errors.append({
            "code": "DRIVER_SUSPENDED",
            "message": f"Driver {driver.full_name} is currently suspended."
        })

    from datetime import date
    if driver.license_expiry < date.today():
        errors.append({
            "code": "LICENSE_EXPIRED",
            "message": f"Driver {driver.full_name}'s license expired on {driver.license_expiry}."
        })

    return errors


@trips_bp.get("/")
@jwt_required()
def list_trips():
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status   = request.args.get("status")
    search   = request.args.get("search", "").strip()

    q = Trip.query
    if status and status != "all":
        q = q.filter_by(status=status)
    if search:
        q = q.filter(
            db.or_(
                Trip.origin.ilike(f"%{search}%"),
                Trip.destination.ilike(f"%{search}%"),
            )
        )
    q = q.order_by(Trip.created_at.desc())
    items, meta = paginate(q, page, per_page)
    return success([t.to_dict() for t in items], meta=meta)


@trips_bp.post("/")
@require_role("admin", "dispatcher")
def create_trip():
    body = request.get_json(silent=True) or {}

    required = ["vehicle_id", "driver_id", "cargo_weight_kg", "origin", "destination", "scheduled_departure"]
    missing  = [f for f in required if not body.get(f)]
    if missing:
        return error(f"Missing required fields: {', '.join(missing)}", 422)

    vehicle = Vehicle.query.get(body["vehicle_id"])
    driver  = Driver.query.get(body["driver_id"])
    if not vehicle:
        return error("Vehicle not found.", 404)
    if not driver:
        return error("Driver not found.", 404)

    cargo_kg = float(body["cargo_weight_kg"])
    validation_errors = _validate_dispatch(vehicle, driver, cargo_kg)
    if validation_errors:
        return error(
            validation_errors[0]["message"], 422,
            error_code=validation_errors[0]["code"]
        ) if len(validation_errors) == 1 else (
            db.session.rollback(),
            error("Multiple validation errors.", 422)
        )[1]

    trip = Trip(
        vehicle_id           = vehicle.id,
        driver_id            = driver.id,
        cargo_weight_kg      = cargo_kg,
        origin               = body["origin"],
        destination          = body["destination"],
        scheduled_departure  = datetime.fromisoformat(body["scheduled_departure"]),
        estimated_fuel_cost  = float(body["estimated_fuel_cost"]) if body.get("estimated_fuel_cost") else None,
        distance_km          = float(body["distance_km"]) if body.get("distance_km") else None,
        notes                = body.get("notes"),
        status               = "dispatched",
        actual_departure     = datetime.now(timezone.utc),
        created_by           = get_jwt_identity(),
    )

    # Lock vehicle and driver
    vehicle.status      = "on_trip"
    driver.duty_status  = "on_trip"

    db.session.add(trip)
    db.session.commit()

    return success({
        "trip": trip.to_dict(),
        "validation": {"weight_ok": True, "license_ok": True, "vehicle_ok": True},
    }, 201)


@trips_bp.patch("/<trip_id>/status")
@require_role("admin", "dispatcher")
def update_status(trip_id):
    trip    = Trip.query.get_or_404(trip_id)
    body    = request.get_json(silent=True) or {}
    new_status = body.get("status")

    valid_transitions = {
        "pending":    ["dispatched", "cancelled"],
        "dispatched": ["in_transit", "completed", "cancelled"],
        "in_transit": ["completed", "cancelled"],
    }
    if trip.status not in valid_transitions or new_status not in valid_transitions.get(trip.status, []):
        return error(f"Cannot transition from '{trip.status}' to '{new_status}'.", 422)

    trip.status = new_status

    if new_status in ("completed", "cancelled"):
        trip.actual_arrival = datetime.now(timezone.utc)
        # Unlock vehicle and driver
        vehicle = Vehicle.query.get(trip.vehicle_id)
        driver  = Driver.query.get(trip.driver_id)
        if vehicle:
            vehicle.status = "available"
            if body.get("final_odometer"):
                vehicle.odometer_km = float(body["final_odometer"])
        if driver:
            driver.duty_status  = "available"
            driver.total_trips += 1
            if trip.distance_km:
                driver.total_km_driven = float(driver.total_km_driven) + float(trip.distance_km)

        if body.get("actual_fuel_cost"):
            trip.actual_fuel_cost = float(body["actual_fuel_cost"])

    db.session.commit()
    return success(trip.to_dict())


@trips_bp.get("/<trip_id>")
@jwt_required()
def get_trip(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    return success(trip.to_dict())
