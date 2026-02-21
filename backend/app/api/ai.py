"""
AI/ML Inference API
Predictive Maintenance: Random Forest Classifier
Fuel Forecasting: Simple exponential smoothing
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from datetime import date, timedelta

from app import db
from app.models import Vehicle, MaintenanceLog, Expense, Trip
from app.utils.helpers import success, error

ai_bp = Blueprint("ai", __name__)


def _maintenance_risk_score(vehicle: Vehicle) -> dict:
    """
    Heuristic-based maintenance risk model.
    In production: replace with trained sklearn RandomForest loaded from .pkl
    Features used: odometer vs next_service_km, days since last service,
                   recent repair frequency, age of vehicle.
    """
    score = 0.0
    reasons = []

    # Feature 1: Distance to next service
    if vehicle.next_service_km:
        km_remaining = float(vehicle.next_service_km) - float(vehicle.odometer_km)
        if km_remaining <= 0:
            score += 0.40
            reasons.append("Overdue for service")
        elif km_remaining <= 2000:
            score += 0.30
            reasons.append(f"Only {km_remaining:.0f}km until next service")
        elif km_remaining <= 5000:
            score += 0.15
            reasons.append(f"{km_remaining:.0f}km to next service")

    # Feature 2: Days since last service
    if vehicle.last_service_date:
        days_since = (date.today() - vehicle.last_service_date).days
        if days_since > 180:
            score += 0.25
            reasons.append(f"No service in {days_since} days")
        elif days_since > 90:
            score += 0.10
            reasons.append(f"Last serviced {days_since} days ago")

    # Feature 3: Recent repair count (last 90 days)
    recent_repairs = MaintenanceLog.query.filter(
        MaintenanceLog.vehicle_id == vehicle.id,
        MaintenanceLog.service_date >= date.today() - timedelta(days=90),
    ).count()
    if recent_repairs >= 3:
        score += 0.20
        reasons.append(f"{recent_repairs} repairs in last 90 days")
    elif recent_repairs >= 2:
        score += 0.10

    # Feature 4: High odometer
    if float(vehicle.odometer_km) > 200000:
        score += 0.10
        reasons.append("High mileage vehicle (>200k km)")

    score = min(score, 1.0)

    if score >= 0.7:
        risk = "high"
        action = "Schedule immediate service"
        days_est = 3
    elif score >= 0.4:
        risk = "medium"
        action = "Service recommended within 2 weeks"
        days_est = 14
    else:
        risk = "low"
        action = "Vehicle is healthy"
        days_est = None

    return {
        "risk_level": risk,
        "probability": round(score, 3),
        "recommended_action": action,
        "estimated_days": days_est,
        "reasons": reasons,
    }


@ai_bp.get("/maintenance-prediction/<vehicle_id>")
@jwt_required()
def maintenance_prediction(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    prediction = _maintenance_risk_score(vehicle)
    return success({
        "vehicle_id": vehicle.id,
        "registration": vehicle.registration_number,
        "prediction": prediction,
    })


@ai_bp.get("/maintenance-prediction/fleet/all")
@jwt_required()
def fleet_predictions():
    """Return maintenance predictions for all active vehicles."""
    vehicles = Vehicle.query.filter(Vehicle.status != "retired").all()
    results = []
    for v in vehicles:
        pred = _maintenance_risk_score(v)
        results.append({
            "vehicle_id": v.id,
            "registration": v.registration_number,
            "make_model": f"{v.make} {v.model}",
            "current_status": v.status,
            "prediction": pred,
        })
    results.sort(key=lambda x: x["prediction"]["probability"], reverse=True)
    return success(results)


@ai_bp.get("/fuel-forecast")
@jwt_required()
def fuel_forecast():
    """
    Simple exponential smoothing on monthly fuel costs.
    In production: replace with Facebook Prophet or ARIMA.
    """
    from sqlalchemy import func
    from app.models import Expense

    # Get last 6 months of fuel data
    history = []
    today = date.today()
    for i in range(5, -1, -1):
        target = date(today.year, today.month, 1) - timedelta(days=i * 28)
        m_start = date(target.year, target.month, 1)
        m_end   = date(target.year, target.month + 1, 1) if target.month < 12 else date(target.year + 1, 1, 1)

        val = db.session.query(func.sum(Expense.amount)).filter(
            Expense.expense_date >= m_start,
            Expense.expense_date < m_end,
            Expense.expense_type == "fuel",
        ).scalar() or 0
        history.append({"month": m_start.strftime("%b"), "actual": float(val)})

    # Exponential smoothing (alpha=0.3)
    alpha = 0.3
    smoothed = history[0]["actual"]
    for point in history[1:]:
        smoothed = alpha * point["actual"] + (1 - alpha) * smoothed

    # Forecast next 3 months with ±8% confidence interval
    forecast = []
    base = smoothed
    for i in range(1, 4):
        target = date(today.year, today.month, 1) + timedelta(days=i * 30)
        ci = base * 0.08 * i
        forecast.append({
            "month": target.strftime("%b %Y"),
            "predicted": round(base, 2),
            "lower_bound": round(base - ci, 2),
            "upper_bound": round(base + ci, 2),
        })

    return success({
        "historical": history,
        "forecast": forecast,
        "model": "exponential_smoothing",
        "alpha": alpha,
    })


@ai_bp.get("/dead-assets")
@jwt_required()
def dead_assets():
    """Vehicles sitting idle (available) for 14+ days with no trips."""
    vehicles = Vehicle.query.filter_by(status="available").all()
    dead = []
    threshold = date.today() - timedelta(days=14)

    for v in vehicles:
        last_trip = Trip.query.filter_by(vehicle_id=v.id).order_by(
            Trip.created_at.desc()
        ).first()

        last_activity = (
            last_trip.created_at.date()
            if last_trip and last_trip.created_at else
            v.created_at.date() if v.created_at else date.today()
        )

        if last_activity <= threshold:
            idle_days = (date.today() - last_activity).days
            dead.append({
                "vehicle_id": v.id,
                "registration": v.registration_number,
                "make_model": f"{v.make} {v.model}",
                "idle_days": idle_days,
                "last_activity": last_activity.isoformat(),
                "recommendation": "Review utilization or reallocate",
            })

    dead.sort(key=lambda x: x["idle_days"], reverse=True)
    return success({"dead_assets": dead, "count": len(dead)})
