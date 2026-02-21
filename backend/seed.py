"""
Run: python seed.py
Seeds the database with realistic test data.
All users have password: FleetFlow@123
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from argon2 import PasswordHasher
from datetime import date, datetime, timezone, timedelta

ph = PasswordHasher()
DEFAULT_PASSWORD = "FleetFlow@123"


def seed_db():
    from app import create_app, db
    from app.models import User, Vehicle, Driver, Trip, MaintenanceLog, Expense

    app = create_app("development")
    with app.app_context():
        # Clear existing data (in order to respect FK constraints)
        Expense.query.delete()
        MaintenanceLog.query.delete()
        Trip.query.delete()
        Driver.query.delete()
        Vehicle.query.delete()
        User.query.delete()
        db.session.commit()

        # ── Users ─────────────────────────────────────────────────────────────
        hashed = ph.hash(DEFAULT_PASSWORD)
        admin  = User(username="admin",       email="admin@fleetflow.in",    password_hash=hashed, role="admin")
        disp   = User(username="dispatcher1", email="dispatch@fleetflow.in", password_hash=hashed, role="dispatcher")
        viewer = User(username="viewer1",     email="viewer@fleetflow.in",   password_hash=hashed, role="viewer")
        db.session.add_all([admin, disp, viewer])
        db.session.flush()

        # ── Vehicles ──────────────────────────────────────────────────────────
        v1 = Vehicle(registration_number="GJ05AB1234", make="Tata",         model="407",        type="truck", capacity_kg=4000, odometer_km=87450,  status="available", fuel_efficiency_kmpl=8.2,  last_service_date=date(2025,12,10), next_service_km=90000,  created_by=admin.id)
        v2 = Vehicle(registration_number="GJ05CD5678", make="Ashok Leyland",model="Viking",      type="truck", capacity_kg=7500, odometer_km=124300, status="on_trip",   fuel_efficiency_kmpl=6.8,  last_service_date=date(2025,11,22), next_service_km=130000, created_by=admin.id)
        v3 = Vehicle(registration_number="MH12EF9012", make="Mahindra",     model="Bolero Pickup",type="mini", capacity_kg=1200, odometer_km=43200,  status="in_shop",   fuel_efficiency_kmpl=12.4, last_service_date=date(2026,1,5),   next_service_km=50000,  created_by=admin.id)
        v4 = Vehicle(registration_number="GJ01GH3456", make="Tata",         model="Ace",         type="mini", capacity_kg=750,  odometer_km=65100,  status="available", fuel_efficiency_kmpl=14.1, last_service_date=date(2025,10,30), next_service_km=70000,  created_by=admin.id)
        v5 = Vehicle(registration_number="RJ14IJ7890", make="Eicher",       model="Pro 2095",    type="truck", capacity_kg=9000, odometer_km=198700, status="on_trip",   fuel_efficiency_kmpl=5.9,  last_service_date=date(2025,12,28), next_service_km=205000, created_by=admin.id)
        v6 = Vehicle(registration_number="GJ06KL1122", make="Force",        model="Traveller",   type="van",  capacity_kg=2000, odometer_km=56800,  status="available", fuel_efficiency_kmpl=10.3, last_service_date=date(2026,1,15),  next_service_km=65000,  created_by=admin.id)
        db.session.add_all([v1, v2, v3, v4, v5, v6])
        db.session.flush()

        # ── Drivers ───────────────────────────────────────────────────────────
        d1 = Driver(full_name="Rajan Patel",  license_number="GJ0520190012345", license_expiry=date(2027,6,30),  phone="9876543210", safety_score=94, duty_status="available", total_trips=187, total_km_driven=89400,  incidents_count=0, created_by=admin.id)
        d2 = Driver(full_name="Suresh Kumar", license_number="MH1220180056789", license_expiry=date(2026,3,15),  phone="9812345678", safety_score=78, duty_status="on_trip",   total_trips=243, total_km_driven=134200, incidents_count=2, created_by=admin.id)
        d3 = Driver(full_name="Arjun Singh",  license_number="RJ1420210098765", license_expiry=date(2026,4,20),  phone="9898765432", safety_score=88, duty_status="on_trip",   total_trips=112, total_km_driven=54300,  incidents_count=1, created_by=admin.id)
        d4 = Driver(full_name="Mohd. Iqbal",  license_number="GJ0520220011223", license_expiry=date(2028,8,12),  phone="9754321098", safety_score=97, duty_status="available", total_trips=89,  total_km_driven=41200,  incidents_count=0, created_by=admin.id)
        d5 = Driver(full_name="Vikram Desai", license_number="GJ0520160034567", license_expiry=date(2026,2,28),  phone="9687654321", safety_score=62, duty_status="suspended", total_trips=321, total_km_driven=178900, incidents_count=5, created_by=admin.id)
        db.session.add_all([d1, d2, d3, d4, d5])
        db.session.flush()

        # ── Trips ─────────────────────────────────────────────────────────────
        t1 = Trip(vehicle_id=v2.id, driver_id=d2.id, cargo_weight_kg=5200, origin="Surat",     destination="Mumbai",  distance_km=280, status="in_transit", scheduled_departure=datetime(2026,2,21,6,30,tzinfo=timezone.utc),  estimated_fuel_cost=3920, created_by=disp.id)
        t2 = Trip(vehicle_id=v5.id, driver_id=d3.id, cargo_weight_kg=8100, origin="Ahmedabad", destination="Delhi",   distance_km=940, status="in_transit", scheduled_departure=datetime(2026,2,20,22,0,tzinfo=timezone.utc),  estimated_fuel_cost=15980, created_by=disp.id)
        t3 = Trip(vehicle_id=v1.id, driver_id=d1.id, cargo_weight_kg=3200, origin="Surat",     destination="Pune",    distance_km=350, status="completed",  scheduled_departure=datetime(2026,2,19,8,0,tzinfo=timezone.utc),   estimated_fuel_cost=4270, actual_fuel_cost=4180, actual_arrival=datetime(2026,2,19,20,0,tzinfo=timezone.utc), created_by=disp.id)
        t4 = Trip(vehicle_id=v4.id, driver_id=d4.id, cargo_weight_kg=600,  origin="Surat",     destination="Vadodara",distance_km=110, status="completed",  scheduled_departure=datetime(2026,2,18,10,0,tzinfo=timezone.utc),  estimated_fuel_cost=780,  actual_fuel_cost=820,  actual_arrival=datetime(2026,2,18,14,0,tzinfo=timezone.utc), created_by=disp.id)
        t5 = Trip(vehicle_id=v6.id, driver_id=d1.id, cargo_weight_kg=1800, origin="Surat",     destination="Rajkot",  distance_km=220, status="pending",    scheduled_departure=datetime(2026,2,22,7,0,tzinfo=timezone.utc),   estimated_fuel_cost=2134, created_by=disp.id)
        db.session.add_all([t1, t2, t3, t4, t5])
        db.session.flush()

        # ── Maintenance ───────────────────────────────────────────────────────
        m1 = MaintenanceLog(vehicle_id=v3.id, service_type="Engine Overhaul",      description="Major engine repair", cost=28500, service_date=date(2026,2,18), odometer_at_service=43100, status="in_progress", logged_by=disp.id)
        m2 = MaintenanceLog(vehicle_id=v2.id, service_type="Tyre Replacement",     description="All 6 tyres",         cost=18000, service_date=date(2025,11,22),odometer_at_service=119800,status="completed",   logged_by=disp.id)
        m3 = MaintenanceLog(vehicle_id=v1.id, service_type="Oil Change + Filter",  description="Routine 80k service", cost=3200,  service_date=date(2025,12,10),odometer_at_service=80000, status="completed",   logged_by=disp.id)
        m4 = MaintenanceLog(vehicle_id=v5.id, service_type="Brake Pad Replacement",description="Front + rear brakes", cost=7800,  service_date=date(2025,12,28),odometer_at_service=195000,status="completed",   logged_by=disp.id)
        db.session.add_all([m1, m2, m3, m4])
        db.session.flush()

        # ── Expenses ──────────────────────────────────────────────────────────
        expenses = [
            Expense(vehicle_id=v2.id, trip_id=t1.id, driver_id=d2.id, expense_type="fuel",   amount=3920,  fuel_liters=57.6, fuel_price_per_liter=68.1, expense_date=date(2026,2,21), logged_by=disp.id),
            Expense(vehicle_id=v1.id, trip_id=t3.id, driver_id=d1.id, expense_type="fuel",   amount=4180,  fuel_liters=61.4, fuel_price_per_liter=68.1, expense_date=date(2026,2,19), logged_by=disp.id),
            Expense(vehicle_id=v3.id, trip_id=None,  driver_id=None,   expense_type="repair", amount=28500, fuel_liters=None, expense_date=date(2026,2,18), logged_by=disp.id),
            Expense(vehicle_id=v4.id, trip_id=t4.id, driver_id=d4.id, expense_type="fuel",   amount=820,   fuel_liters=12.0, fuel_price_per_liter=68.3, expense_date=date(2026,2,18), logged_by=disp.id),
            Expense(vehicle_id=v5.id, trip_id=None,  driver_id=None,   expense_type="toll",   amount=1240,  fuel_liters=None, expense_date=date(2026,2,20), logged_by=disp.id),
        ]
        db.session.add_all(expenses)
        db.session.commit()

        print("✅ Database seeded successfully!")
        print(f"   Users:       {User.query.count()}")
        print(f"   Vehicles:    {Vehicle.query.count()}")
        print(f"   Drivers:     {Driver.query.count()}")
        print(f"   Trips:       {Trip.query.count()}")
        print(f"   Maintenance: {MaintenanceLog.query.count()}")
        print(f"   Expenses:    {Expense.query.count()}")
        print(f"\n   Login credentials: admin / FleetFlow@123")


if __name__ == "__main__":
    seed_db()
