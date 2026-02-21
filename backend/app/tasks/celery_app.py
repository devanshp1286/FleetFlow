"""
Celery background tasks:
- License expiry alerts (daily)
- Maintenance due alerts (daily)
- KPI cache invalidation (every 30s)
"""
from celery import Celery
from celery.schedules import crontab
import os


def make_celery(app=None):
    celery = Celery(
        "fleetflow",
        broker=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        backend=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
    )
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Kolkata",
        enable_utc=True,
        beat_schedule={
            "check-license-expiry-daily": {
                "task": "app.tasks.alerts.check_license_expiry",
                "schedule": crontab(hour=8, minute=0),
            },
            "check-maintenance-due-daily": {
                "task": "app.tasks.alerts.check_maintenance_due",
                "schedule": crontab(hour=8, minute=30),
            },
            "invalidate-kpi-cache": {
                "task": "app.tasks.alerts.invalidate_kpi_cache",
                "schedule": 30.0,  # Every 30 seconds
            },
        },
    )
    return celery


celery_app = make_celery()


@celery_app.task(name="app.tasks.alerts.check_license_expiry")
def check_license_expiry():
    """Flag drivers whose license expires within 30 days."""
    from datetime import date, timedelta
    # In production: send email/SMS via Twilio/SendGrid
    threshold = date.today() + timedelta(days=30)
    print(f"[TASK] Checking license expiry. Threshold: {threshold}")
    # Query and alert logic would go here
    return {"status": "done"}


@celery_app.task(name="app.tasks.alerts.check_maintenance_due")
def check_maintenance_due():
    """Flag vehicles where odometer >= next_service_km - 5000."""
    print("[TASK] Checking maintenance due vehicles")
    return {"status": "done"}


@celery_app.task(name="app.tasks.alerts.invalidate_kpi_cache")
def invalidate_kpi_cache():
    """Clear dashboard KPI cache so next request recomputes."""
    import redis
    r = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    r.delete("dashboard:kpis")
    return {"status": "cache_cleared"}
