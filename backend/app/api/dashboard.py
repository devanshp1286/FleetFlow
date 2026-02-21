import json
from datetime import date, timedelta
from flask import Blueprint, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from app import db
from app.models import Vehicle, Driver, Trip, Expense, MaintenanceLog
from app.utils.helpers import success

dashboard_bp = Blueprint("dashboard", __name__)


def _get_redis():
    import redis
    return redis.from_url(current_app.config["REDIS_URL"], decode_responses=True)


def _compute_kpis():
    today = date.today()
    expiry_threshold = today + timedelta(days=30)

    # Fleet counts
    total_vehicles    = Vehicle.query.filter(Vehicle.status != "retired").count()
    active_vehicles   = Vehicle.query.filter_by(status="on_trip").count()
    in_shop           = Vehicle.query.filter_by(status="in_shop").count()
    available         = Vehicle.query.filter_by(status="available").count()

    # Driver alerts
    license_expiring  = Driver.query.filter(
        Driver.license_expiry <= expiry_threshold,
        Driver.license_expiry >= today
    ).count()
    license_expired   = Driver.query.filter(Driver.license_expiry < today).count()

    # Trips
    pending_trips     = Trip.query.filter_by(status="pending").count()
    in_transit        = Trip.query.filter(Trip.status.in_(["dispatched", "in_transit"])).count()
    completed_today   = Trip.query.filter(
        Trip.status == "completed",
        func.date(Trip.actual_arrival) == today
    ).count()

    # Financial (current month)
    month_start = today.replace(day=1)
    monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.expense_date >= month_start
    ).scalar() or 0

    fuel_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.expense_date >= month_start,
        Expense.expense_type == "fuel"
    ).scalar() or 0

    # Utilization
    utilization = round((active_vehicles / total_vehicles * 100), 1) if total_vehicles else 0

    # Maintenance alerts
    maintenance_alerts = in_shop + license_expiring + license_expired

    # Vehicles near service (within 5000 km)
    service_due = Vehicle.query.filter(
        Vehicle.next_service_km.isnot(None),
        Vehicle.odometer_km >= Vehicle.next_service_km - 5000
    ).count()

    return {
        "fleet": {
            "total": total_vehicles,
            "active": active_vehicles,
            "available": available,
            "in_shop": in_shop,
            "utilization_pct": utilization,
        },
        "alerts": {
            "total": maintenance_alerts + service_due,
            "in_shop": in_shop,
            "license_expiring": license_expiring,
            "license_expired": license_expired,
            "service_due": service_due,
        },
        "trips": {
            "pending": pending_trips,
            "in_transit": in_transit,
            "completed_today": completed_today,
        },
        "financials": {
            "monthly_expenses": float(monthly_expenses),
            "monthly_fuel": float(fuel_expenses),
        },
    }


@dashboard_bp.get("/kpis")
@jwt_required()
def kpis():
    cache_key = "dashboard:kpis"
    try:
        r = _get_redis()
        cached = r.get(cache_key)
        if cached:
            return success(json.loads(cached))
    except Exception:
        pass  # Redis unavailable — compute fresh

    data = _compute_kpis()

    try:
        r.setex(cache_key, 30, json.dumps(data))
    except Exception:
        pass

    return success(data)


@dashboard_bp.get("/live-trips")
@jwt_required()
def live_trips():
    trips = Trip.query.filter(
        Trip.status.in_(["pending", "dispatched", "in_transit"])
    ).order_by(Trip.created_at.desc()).limit(20).all()
    return success([t.to_dict() for t in trips])


@dashboard_bp.get("/recent-activity")
@jwt_required()
def recent_activity():
    trips = Trip.query.order_by(Trip.created_at.desc()).limit(10).all()
    maintenance = MaintenanceLog.query.order_by(MaintenanceLog.created_at.desc()).limit(5).all()
    return success({
        "recent_trips": [t.to_dict() for t in trips],
        "recent_maintenance": [m.to_dict() for m in maintenance],
    })
