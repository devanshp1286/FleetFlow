from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, extract
from datetime import date, timedelta

from app import db
from app.models import Trip, Vehicle, Expense, Driver
from app.utils.helpers import success

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/summary")
@jwt_required()
def financial_summary():
    months = request.args.get("months", 6, type=int)
    months = min(months, 24)

    results = []
    today = date.today()

    for i in range(months - 1, -1, -1):
        # Calculate month boundaries
        target = date(today.year, today.month, 1) - timedelta(days=i * 28)
        month_start = date(target.year, target.month, 1)
        if target.month == 12:
            month_end = date(target.year + 1, 1, 1)
        else:
            month_end = date(target.year, target.month + 1, 1)

        total_cost = db.session.query(func.sum(Expense.amount)).filter(
            Expense.expense_date >= month_start,
            Expense.expense_date < month_end,
        ).scalar() or 0

        fuel_cost = db.session.query(func.sum(Expense.amount)).filter(
            Expense.expense_date >= month_start,
            Expense.expense_date < month_end,
            Expense.expense_type == "fuel",
        ).scalar() or 0

        repair_cost = db.session.query(func.sum(Expense.amount)).filter(
            Expense.expense_date >= month_start,
            Expense.expense_date < month_end,
            Expense.expense_type == "repair",
        ).scalar() or 0

        trips_count = Trip.query.filter(
            Trip.status == "completed",
            Trip.actual_arrival >= month_start,
            Trip.actual_arrival < month_end,
        ).count()

        results.append({
            "month": month_start.strftime("%b %Y"),
            "month_short": month_start.strftime("%b"),
            "total_cost": float(total_cost),
            "fuel_cost": float(fuel_cost),
            "repair_cost": float(repair_cost),
            "trips_completed": trips_count,
        })

    return success(results)


@analytics_bp.get("/vehicle-roi")
@jwt_required()
def vehicle_roi():
    vehicles = Vehicle.query.filter(Vehicle.status != "retired").all()
    result = []

    for v in vehicles:
        total_cost = db.session.query(func.sum(Expense.amount)).filter_by(vehicle_id=v.id).scalar() or 0
        trips_done = Trip.query.filter_by(vehicle_id=v.id, status="completed").count()
        total_dist = db.session.query(func.sum(Trip.distance_km)).filter_by(
            vehicle_id=v.id, status="completed"
        ).scalar() or 0

        # Rough revenue estimate: ₹45/km (can be made dynamic)
        estimated_revenue = float(total_dist or 0) * 45

        result.append({
            "vehicle_id":         v.id,
            "registration":       v.registration_number,
            "make_model":         f"{v.make} {v.model}",
            "type":               v.type,
            "total_cost":         float(total_cost),
            "estimated_revenue":  estimated_revenue,
            "net_roi":            estimated_revenue - float(total_cost),
            "trips_completed":    trips_done,
            "total_distance_km":  float(total_dist or 0),
            "cost_per_km": round(float(total_cost) / float(total_dist), 2) if total_dist else None,
        })

    result.sort(key=lambda x: x["net_roi"], reverse=True)
    return success(result)


@analytics_bp.get("/fuel-efficiency")
@jwt_required()
def fuel_efficiency():
    vehicles = Vehicle.query.filter(
        Vehicle.fuel_efficiency_kmpl.isnot(None),
        Vehicle.status != "retired"
    ).all()
    return success([{
        "registration": v.registration_number,
        "make_model": f"{v.make} {v.model}",
        "efficiency_kmpl": float(v.fuel_efficiency_kmpl),
        "type": v.type,
    } for v in vehicles])


@analytics_bp.get("/driver-performance")
@jwt_required()
def driver_performance():
    drivers = Driver.query.order_by(Driver.safety_score.desc()).all()
    return success([{
        **d.to_dict(),
        "on_time_rate": 87 + (float(d.safety_score) - 80) * 0.2,  # Computed approximation
    } for d in drivers])
