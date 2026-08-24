-- =============================================================
-- FloodShield Database Schema
-- Generated from SQLAlchemy models (Member 2 - Backend)
-- Target: PostgreSQL 14+
-- =============================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================
-- ENUMS
-- =============================================================

CREATE TYPE user_role AS ENUM (
    'admin', 'business_owner', 'warehouse_manager',
    'fleet_manager', 'analyst', 'responder'
);

CREATE TYPE business_type AS ENUM (
    'retail', 'warehouse', 'manufacturing',
    'pharmacy', 'food_storage', 'logistics', 'other'
);

CREATE TYPE business_status AS ENUM (
    'active', 'evacuating', 'evacuated', 'damaged', 'closed'
);

CREATE TYPE item_category AS ENUM (
    'essential_supplies', 'medicines', 'food',
    'electronics', 'machinery', 'documents', 'fuel', 'other'
);

CREATE TYPE warehouse_status AS ENUM (
    'available', 'partially_full', 'full', 'unsafe', 'closed'
);

CREATE TYPE vehicle_type AS ENUM (
    'truck', 'van', 'boat', 'helicopter',
    'forklift', 'ambulance', 'bus', 'other'
);

CREATE TYPE vehicle_status AS ENUM (
    'available', 'in_transit', 'loading', 'maintenance', 'unavailable'
);

CREATE TYPE route_status AS ENUM (
    'computed', 'active', 'completed', 'cancelled'
);

CREATE TYPE risk_level AS ENUM (
    'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
);

CREATE TYPE plan_status AS ENUM (
    'draft', 'active', 'in_progress', 'completed', 'cancelled'
);

CREATE TYPE plan_trigger AS ENUM (
    'manual', 'risk_threshold', 'weather_alert', 'government_order'
);

-- =============================================================
-- TABLES
-- =============================================================

CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    email               VARCHAR(255) UNIQUE NOT NULL,
    hashed_password     VARCHAR(255) NOT NULL,
    full_name           VARCHAR(120),
    phone               VARCHAR(20),
    role                user_role NOT NULL DEFAULT 'business_owner',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified         BOOLEAN NOT NULL DEFAULT FALSE,
    last_login_at       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS businesses (
    id                      SERIAL PRIMARY KEY,
    owner_id                INTEGER NOT NULL REFERENCES users(id),
    name                    VARCHAR(200) NOT NULL,
    registration_number     VARCHAR(100) UNIQUE,
    business_type           business_type NOT NULL DEFAULT 'other',
    description             TEXT,
    address                 VARCHAR(500) NOT NULL,
    city                    VARCHAR(100) NOT NULL,
    state                   VARCHAR(100) NOT NULL,
    pincode                 VARCHAR(10) NOT NULL,
    latitude                FLOAT,
    longitude               FLOAT,
    elevation_meters        FLOAT,
    status                  business_status NOT NULL DEFAULT 'active',
    contact_email           VARCHAR(255),
    contact_phone           VARCHAR(20),
    employee_count          INTEGER NOT NULL DEFAULT 0,
    estimated_asset_value   FLOAT NOT NULL DEFAULT 0.0,
    is_critical_infrastructure BOOLEAN NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventories (
    id                  SERIAL PRIMARY KEY,
    business_id         INTEGER NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    item_name           VARCHAR(200) NOT NULL,
    sku                 VARCHAR(100),
    category            item_category NOT NULL DEFAULT 'other',
    description         TEXT,
    quantity            FLOAT NOT NULL DEFAULT 0.0,
    unit                VARCHAR(50) NOT NULL DEFAULT 'units',
    unit_value          FLOAT NOT NULL DEFAULT 0.0,
    total_value         FLOAT NOT NULL DEFAULT 0.0,
    is_perishable       BOOLEAN NOT NULL DEFAULT FALSE,
    is_hazardous        BOOLEAN NOT NULL DEFAULT FALSE,
    evacuation_priority INTEGER NOT NULL DEFAULT 3,
    storage_location    VARCHAR(200),
    last_audited_at     TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS warehouses (
    id                      SERIAL PRIMARY KEY,
    name                    VARCHAR(200) NOT NULL,
    operator_name           VARCHAR(200),
    description             TEXT,
    address                 VARCHAR(500) NOT NULL,
    city                    VARCHAR(100) NOT NULL,
    state                   VARCHAR(100) NOT NULL,
    pincode                 VARCHAR(10) NOT NULL,
    latitude                FLOAT NOT NULL,
    longitude               FLOAT NOT NULL,
    elevation_meters        FLOAT NOT NULL DEFAULT 0.0,
    total_capacity_sqm      FLOAT NOT NULL DEFAULT 0.0,
    available_capacity_sqm  FLOAT NOT NULL DEFAULT 0.0,
    max_weight_tons         FLOAT,
    status                  warehouse_status NOT NULL DEFAULT 'available',
    is_flood_safe           BOOLEAN NOT NULL DEFAULT TRUE,
    has_power_backup        BOOLEAN NOT NULL DEFAULT FALSE,
    has_cold_storage        BOOLEAN NOT NULL DEFAULT FALSE,
    contact_phone           VARCHAR(20),
    contact_email           VARCHAR(255),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vehicles (
    id                      SERIAL PRIMARY KEY,
    registration_number     VARCHAR(50) UNIQUE NOT NULL,
    vehicle_type            vehicle_type NOT NULL,
    make                    VARCHAR(100),
    model                   VARCHAR(100),
    year                    INTEGER,
    payload_capacity_tons   FLOAT NOT NULL DEFAULT 0.0,
    passenger_capacity      INTEGER NOT NULL DEFAULT 0,
    volume_capacity_cbm     FLOAT,
    status                  vehicle_status NOT NULL DEFAULT 'available',
    current_latitude        FLOAT,
    current_longitude       FLOAT,
    last_location_update    TIMESTAMPTZ,
    driver_name             VARCHAR(120),
    driver_phone            VARCHAR(20),
    is_amphibious           BOOLEAN NOT NULL DEFAULT FALSE,
    fuel_level_pct          FLOAT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS routes (
    id                          SERIAL PRIMARY KEY,
    business_id                 INTEGER REFERENCES businesses(id),
    vehicle_id                  INTEGER REFERENCES vehicles(id),
    destination_warehouse_id    INTEGER REFERENCES warehouses(id),
    origin_address              VARCHAR(500) NOT NULL,
    origin_latitude             FLOAT NOT NULL,
    origin_longitude            FLOAT NOT NULL,
    destination_address         VARCHAR(500) NOT NULL,
    destination_latitude        FLOAT NOT NULL,
    destination_longitude       FLOAT NOT NULL,
    distance_km                 FLOAT,
    estimated_duration_min      INTEGER,
    waypoints                   JSONB,
    flood_risk_zones            JSONB,
    is_flood_safe               BOOLEAN NOT NULL DEFAULT TRUE,
    safety_score                FLOAT,
    status                      route_status NOT NULL DEFAULT 'computed',
    notes                       TEXT,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS risk_assessments (
    id                  SERIAL PRIMARY KEY,
    business_id         INTEGER NOT NULL REFERENCES businesses(id),
    risk_score          INTEGER NOT NULL DEFAULT 0,
    risk_level          risk_level NOT NULL DEFAULT 'LOW',
    safe_window_hours   INTEGER,
    rainfall_mm         FLOAT,
    river_level_m       FLOAT,
    flood_zone_overlap  FLOAT,
    elevation_risk      FLOAT,
    historical_flood    FLOAT,
    infrastructure_risk FLOAT,
    assessed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    assessed_by_user_id INTEGER REFERENCES users(id),
    source              VARCHAR(50) NOT NULL DEFAULT 'engine',
    notes               TEXT,
    raw_engine_response JSONB
);

CREATE TABLE IF NOT EXISTS action_plans (
    id                      SERIAL PRIMARY KEY,
    business_id             INTEGER NOT NULL REFERENCES businesses(id),
    created_by_user_id      INTEGER REFERENCES users(id),
    title                   VARCHAR(300) NOT NULL,
    description             TEXT,
    trigger                 plan_trigger NOT NULL DEFAULT 'manual',
    status                  plan_status NOT NULL DEFAULT 'draft',
    steps                   JSONB NOT NULL DEFAULT '[]',
    priority                INTEGER NOT NULL DEFAULT 3,
    target_completion_hours INTEGER,
    activated_at            TIMESTAMPTZ,
    completed_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============================================================
-- INDEXES
-- =============================================================

CREATE INDEX IF NOT EXISTS idx_businesses_owner   ON businesses(owner_id);
CREATE INDEX IF NOT EXISTS idx_businesses_city    ON businesses(city);
CREATE INDEX IF NOT EXISTS idx_inventories_biz    ON inventories(business_id);
CREATE INDEX IF NOT EXISTS idx_routes_business    ON routes(business_id);
CREATE INDEX IF NOT EXISTS idx_routes_vehicle     ON routes(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_risk_business      ON risk_assessments(business_id);
CREATE INDEX IF NOT EXISTS idx_risk_assessed_at   ON risk_assessments(assessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_plans_business     ON action_plans(business_id);
CREATE INDEX IF NOT EXISTS idx_vehicles_status    ON vehicles(status);
CREATE INDEX IF NOT EXISTS idx_warehouses_safe    ON warehouses(is_flood_safe, status);
