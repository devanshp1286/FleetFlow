-- FleetFlow Database Schema
-- PostgreSQL 15 | 3NF Normalized | UUID Primary Keys

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─── ENUMS ────────────────────────────────────────────────────────────────────

CREATE TYPE user_role AS ENUM ('admin', 'dispatcher', 'driver', 'viewer');
CREATE TYPE vehicle_type AS ENUM ('truck', 'mini', 'van', 'tanker');
CREATE TYPE vehicle_status AS ENUM ('available', 'on_trip', 'in_shop', 'retired');
CREATE TYPE driver_status AS ENUM ('available', 'on_trip', 'on_break', 'suspended');
CREATE TYPE trip_status AS ENUM ('pending', 'dispatched', 'in_transit', 'completed', 'cancelled');
CREATE TYPE maintenance_status AS ENUM ('open', 'in_progress', 'completed');
CREATE TYPE expense_type AS ENUM ('fuel', 'toll', 'repair', 'insurance', 'other');

-- ─── USERS ───────────────────────────────────────────────────────────────────

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(50)  UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            user_role    NOT NULL DEFAULT 'dispatcher',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email    ON users(email);

-- ─── VEHICLES ────────────────────────────────────────────────────────────────

CREATE TABLE vehicles (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registration_number   VARCHAR(20)     UNIQUE NOT NULL,
    make                  VARCHAR(50)     NOT NULL,
    model                 VARCHAR(50)     NOT NULL,
    type                  vehicle_type    NOT NULL,
    capacity_kg           NUMERIC(10,2)   NOT NULL CHECK (capacity_kg > 0),
    odometer_km           NUMERIC(12,2)   NOT NULL DEFAULT 0,
    status                vehicle_status  NOT NULL DEFAULT 'available',
    fuel_efficiency_kmpl  NUMERIC(5,2),
    last_service_date     DATE,
    next_service_km       NUMERIC(12,2),
    created_by            UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_reg    ON vehicles(registration_number);

-- ─── DRIVERS ─────────────────────────────────────────────────────────────────

CREATE TABLE drivers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    full_name       VARCHAR(100)    NOT NULL,
    license_number  VARCHAR(30)     UNIQUE NOT NULL,
    license_expiry  DATE            NOT NULL,
    phone           VARCHAR(15)     UNIQUE,
    safety_score    NUMERIC(4,1)    NOT NULL DEFAULT 100.0 CHECK (safety_score BETWEEN 0 AND 100),
    duty_status     driver_status   NOT NULL DEFAULT 'available',
    total_trips     INTEGER         NOT NULL DEFAULT 0,
    total_km_driven NUMERIC(12,2)   NOT NULL DEFAULT 0,
    incidents_count INTEGER         NOT NULL DEFAULT 0,
    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_drivers_status          ON drivers(duty_status);
CREATE INDEX idx_drivers_license_expiry  ON drivers(license_expiry);

-- ─── TRIPS ───────────────────────────────────────────────────────────────────

CREATE TABLE trips (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id            UUID NOT NULL REFERENCES vehicles(id) ON DELETE RESTRICT,
    driver_id             UUID NOT NULL REFERENCES drivers(id)  ON DELETE RESTRICT,
    cargo_weight_kg       NUMERIC(10,2)   NOT NULL CHECK (cargo_weight_kg > 0),
    origin                VARCHAR(255)    NOT NULL,
    destination           VARCHAR(255)    NOT NULL,
    distance_km           NUMERIC(10,2),
    status                trip_status     NOT NULL DEFAULT 'pending',
    scheduled_departure   TIMESTAMPTZ     NOT NULL,
    actual_departure      TIMESTAMPTZ,
    actual_arrival        TIMESTAMPTZ,
    estimated_fuel_cost   NUMERIC(10,2),
    actual_fuel_cost      NUMERIC(10,2),
    notes                 TEXT,
    created_by            UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_trips_status       ON trips(status);
CREATE INDEX idx_trips_vehicle_id   ON trips(vehicle_id);
CREATE INDEX idx_trips_driver_id    ON trips(driver_id);
CREATE INDEX idx_trips_created_at   ON trips(created_at DESC);
CREATE INDEX idx_trips_departure    ON trips(scheduled_departure);

-- ─── MAINTENANCE LOGS ────────────────────────────────────────────────────────

CREATE TABLE maintenance_logs (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id           UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    service_type         VARCHAR(100)        NOT NULL,
    description          TEXT,
    cost                 NUMERIC(10,2)       NOT NULL CHECK (cost >= 0),
    service_date         DATE                NOT NULL,
    odometer_at_service  NUMERIC(12,2)       NOT NULL,
    next_service_km      NUMERIC(12,2),
    status               maintenance_status  NOT NULL DEFAULT 'open',
    logged_by            UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at           TIMESTAMPTZ         NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_maintenance_vehicle_id ON maintenance_logs(vehicle_id);
CREATE INDEX idx_maintenance_status     ON maintenance_logs(status);

-- ─── EXPENSES ────────────────────────────────────────────────────────────────

CREATE TABLE expenses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trip_id             UUID REFERENCES trips(id) ON DELETE SET NULL,
    vehicle_id          UUID NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    driver_id           UUID REFERENCES drivers(id) ON DELETE SET NULL,
    expense_type        expense_type    NOT NULL,
    amount              NUMERIC(10,2)   NOT NULL CHECK (amount >= 0),
    fuel_liters         NUMERIC(8,2),
    fuel_price_per_liter NUMERIC(6,2),
    expense_date        DATE            NOT NULL,
    receipt_url         VARCHAR(500),
    notes               TEXT,
    logged_by           UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_expenses_vehicle_id   ON expenses(vehicle_id);
CREATE INDEX idx_expenses_date         ON expenses(expense_date DESC);
CREATE INDEX idx_expenses_type         ON expenses(expense_type);

-- ─── REFRESH TOKENS ──────────────────────────────────────────────────────────

CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) UNIQUE NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_user ON refresh_tokens(user_id);

-- ─── UPDATED_AT TRIGGER ──────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at        BEFORE UPDATE ON users        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_vehicles_updated_at     BEFORE UPDATE ON vehicles     FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_drivers_updated_at      BEFORE UPDATE ON drivers      FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_trips_updated_at        BEFORE UPDATE ON trips        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_maintenance_updated_at  BEFORE UPDATE ON maintenance_logs FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─── SEED DATA ────────────────────────────────────────────────────────────────
-- Password: admin123 (argon2 hash)
INSERT INTO users (username, email, password_hash, role) VALUES
  ('admin',       'admin@fleetflow.in',       '$argon2id$v=19$m=65536,t=3,p=4$c2FsdHNhbHRzYWx0c2FsdA$placeholder_hash_admin', 'admin'),
  ('dispatcher1', 'dispatch@fleetflow.in',    '$argon2id$v=19$m=65536,t=3,p=4$c2FsdHNhbHRzYWx0c2FsdA$placeholder_hash_disp',  'dispatcher'),
  ('viewer1',     'viewer@fleetflow.in',      '$argon2id$v=19$m=65536,t=3,p=4$c2FsdHNhbHRzYWx0c2FsdA$placeholder_hash_view',  'viewer');

-- Note: Run `python -c "from app import create_app; create_app().app_context().push(); from app.utils.seed import seed_db; seed_db()"` for proper seeded data with correct password hashes.
