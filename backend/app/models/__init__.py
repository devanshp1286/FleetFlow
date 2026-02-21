import uuid
from datetime import date
from app import db


def gen_uuid():
    return str(uuid.uuid4())


# ─── USER ─────────────────────────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = "users"

    id            = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    username      = db.Column(db.String(50),  unique=True, nullable=False)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.String(20),  nullable=False, default="dispatcher")
    is_active     = db.Column(db.Boolean,     nullable=False, default=True)
    last_login    = db.Column(db.DateTime(timezone=True))
    created_at    = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at    = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            "id": self.id, "username": self.username, "email": self.email,
            "role": self.role, "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─── VEHICLE ──────────────────────────────────────────────────────────────────

class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id                   = db.Column(db.String(36),  primary_key=True, default=gen_uuid)
    registration_number  = db.Column(db.String(20),  unique=True, nullable=False)
    make                 = db.Column(db.String(50),  nullable=False)
    model                = db.Column(db.String(50),  nullable=False)
    type                 = db.Column(db.String(20),  nullable=False)
    capacity_kg          = db.Column(db.Numeric(10,2), nullable=False)
    odometer_km          = db.Column(db.Numeric(12,2), nullable=False, default=0)
    status               = db.Column(db.String(20),  nullable=False, default="available")
    fuel_efficiency_kmpl = db.Column(db.Numeric(5,2))
    last_service_date    = db.Column(db.Date)
    next_service_km      = db.Column(db.Numeric(12,2))
    created_by           = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at           = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at           = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    trips        = db.relationship("Trip",           backref="vehicle", lazy="dynamic")
    maintenance  = db.relationship("MaintenanceLog", backref="vehicle", lazy="dynamic")
    expenses     = db.relationship("Expense",        backref="vehicle", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "registration_number": self.registration_number,
            "make": self.make, "model": self.model, "type": self.type,
            "capacity_kg": float(self.capacity_kg),
            "odometer_km": float(self.odometer_km),
            "status": self.status,
            "fuel_efficiency_kmpl": float(self.fuel_efficiency_kmpl) if self.fuel_efficiency_kmpl else None,
            "last_service_date": self.last_service_date.isoformat() if self.last_service_date else None,
            "next_service_km": float(self.next_service_km) if self.next_service_km else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─── DRIVER ───────────────────────────────────────────────────────────────────

class Driver(db.Model):
    __tablename__ = "drivers"

    id              = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id         = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"))
    full_name       = db.Column(db.String(100), nullable=False)
    license_number  = db.Column(db.String(30),  unique=True, nullable=False)
    license_expiry  = db.Column(db.Date,        nullable=False)
    phone           = db.Column(db.String(15),  unique=True)
    safety_score    = db.Column(db.Numeric(4,1), nullable=False, default=100.0)
    duty_status     = db.Column(db.String(20),   nullable=False, default="available")
    total_trips     = db.Column(db.Integer,      nullable=False, default=0)
    total_km_driven = db.Column(db.Numeric(12,2), nullable=False, default=0)
    incidents_count = db.Column(db.Integer,      nullable=False, default=0)
    created_by      = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at      = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at      = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    trips = db.relationship("Trip", backref="driver", lazy="dynamic", foreign_keys="Trip.driver_id")

    @property
    def license_days_remaining(self):
        return (self.license_expiry - date.today()).days

    def to_dict(self):
        return {
            "id": self.id, "full_name": self.full_name,
            "license_number": self.license_number,
            "license_expiry": self.license_expiry.isoformat(),
            "license_days_remaining": self.license_days_remaining,
            "phone": self.phone,
            "safety_score": float(self.safety_score),
            "duty_status": self.duty_status,
            "total_trips": self.total_trips,
            "total_km_driven": float(self.total_km_driven),
            "incidents_count": self.incidents_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─── TRIP ─────────────────────────────────────────────────────────────────────

class Trip(db.Model):
    __tablename__ = "trips"

    id                   = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    vehicle_id           = db.Column(db.String(36), db.ForeignKey("vehicles.id", ondelete="RESTRICT"), nullable=False)
    driver_id            = db.Column(db.String(36), db.ForeignKey("drivers.id",  ondelete="RESTRICT"), nullable=False)
    cargo_weight_kg      = db.Column(db.Numeric(10,2), nullable=False)
    origin               = db.Column(db.String(255), nullable=False)
    destination          = db.Column(db.String(255), nullable=False)
    distance_km          = db.Column(db.Numeric(10,2))
    status               = db.Column(db.String(20), nullable=False, default="pending")
    scheduled_departure  = db.Column(db.DateTime(timezone=True), nullable=False)
    actual_departure     = db.Column(db.DateTime(timezone=True))
    actual_arrival       = db.Column(db.DateTime(timezone=True))
    estimated_fuel_cost  = db.Column(db.Numeric(10,2))
    actual_fuel_cost     = db.Column(db.Numeric(10,2))
    notes                = db.Column(db.Text)
    created_by           = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at           = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at           = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "driver_id":  self.driver_id,
            "vehicle_reg": self.vehicle.registration_number if self.vehicle else None,
            "driver_name": self.driver.full_name if self.driver else None,
            "cargo_weight_kg": float(self.cargo_weight_kg),
            "origin": self.origin, "destination": self.destination,
            "distance_km": float(self.distance_km) if self.distance_km else None,
            "status": self.status,
            "scheduled_departure": self.scheduled_departure.isoformat() if self.scheduled_departure else None,
            "actual_departure": self.actual_departure.isoformat() if self.actual_departure else None,
            "actual_arrival": self.actual_arrival.isoformat() if self.actual_arrival else None,
            "estimated_fuel_cost": float(self.estimated_fuel_cost) if self.estimated_fuel_cost else None,
            "actual_fuel_cost": float(self.actual_fuel_cost) if self.actual_fuel_cost else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─── MAINTENANCE LOG ──────────────────────────────────────────────────────────

class MaintenanceLog(db.Model):
    __tablename__ = "maintenance_logs"

    id                  = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    vehicle_id          = db.Column(db.String(36), db.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    service_type        = db.Column(db.String(100), nullable=False)
    description         = db.Column(db.Text)
    cost                = db.Column(db.Numeric(10,2), nullable=False)
    service_date        = db.Column(db.Date, nullable=False)
    odometer_at_service = db.Column(db.Numeric(12,2), nullable=False)
    next_service_km     = db.Column(db.Numeric(12,2))
    status              = db.Column(db.String(20), nullable=False, default="open")
    logged_by           = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at          = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at          = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        return {
            "id": self.id, "vehicle_id": self.vehicle_id,
            "vehicle_reg": self.vehicle.registration_number if self.vehicle else None,
            "service_type": self.service_type, "description": self.description,
            "cost": float(self.cost),
            "service_date": self.service_date.isoformat(),
            "odometer_at_service": float(self.odometer_at_service),
            "next_service_km": float(self.next_service_km) if self.next_service_km else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─── EXPENSE ──────────────────────────────────────────────────────────────────

class Expense(db.Model):
    __tablename__ = "expenses"

    id                   = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    trip_id              = db.Column(db.String(36), db.ForeignKey("trips.id", ondelete="SET NULL"))
    vehicle_id           = db.Column(db.String(36), db.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    driver_id            = db.Column(db.String(36), db.ForeignKey("drivers.id", ondelete="SET NULL"))
    expense_type         = db.Column(db.String(20), nullable=False)
    amount               = db.Column(db.Numeric(10,2), nullable=False)
    fuel_liters          = db.Column(db.Numeric(8,2))
    fuel_price_per_liter = db.Column(db.Numeric(6,2))
    expense_date         = db.Column(db.Date, nullable=False)
    receipt_url          = db.Column(db.String(500))
    notes                = db.Column(db.Text)
    logged_by            = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at           = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    driver  = db.relationship("Driver",  foreign_keys=[driver_id])

    def to_dict(self):
        return {
            "id": self.id, "trip_id": self.trip_id,
            "vehicle_id": self.vehicle_id,
            "vehicle_reg": self.vehicle.registration_number if self.vehicle else None,
            "driver_id": self.driver_id,
            "driver_name": self.driver.full_name if self.driver else None,
            "expense_type": self.expense_type,
            "amount": float(self.amount),
            "fuel_liters": float(self.fuel_liters) if self.fuel_liters else None,
            "fuel_price_per_liter": float(self.fuel_price_per_liter) if self.fuel_price_per_liter else None,
            "expense_date": self.expense_date.isoformat(),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
