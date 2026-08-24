-- =============================================================
-- FloodShield Seed Data
-- Sample data for development and testing
-- =============================================================

-- Admin User (password: Admin@123)
INSERT INTO users (email, hashed_password, full_name, phone, role, is_active, is_verified)
VALUES (
    'admin@floodshield.in',
    '$2b$12$placeholderHashReplaceWithActualBcryptHash',
    'FloodShield Admin',
    '+91-9000000001',
    'admin',
    TRUE, TRUE
) ON CONFLICT (email) DO NOTHING;

-- Sample Warehouses (flood-safe)
INSERT INTO warehouses (name, operator_name, address, city, state, pincode, latitude, longitude, elevation_meters, total_capacity_sqm, available_capacity_sqm, max_weight_tons, status, is_flood_safe, has_power_backup)
VALUES
    ('Central Safe Storage - Mumbai', 'NDRF Logistics', 'Andheri East, MIDC', 'Mumbai', 'Maharashtra', '400093', 19.1136, 72.8697, 12.0, 5000.0, 4000.0, 500.0, 'available', TRUE, TRUE),
    ('Northern Relief Hub - Pune',   'State Disaster Mgmt', 'Hadapsar Industrial Area', 'Pune', 'Maharashtra', '411028', 18.5018, 73.9252, 45.0, 3000.0, 2500.0, 300.0, 'available', TRUE, TRUE),
    ('Southern Depot - Chennai',     'Tamil Nadu SDMA', 'Ambattur Industrial Estate', 'Chennai', 'Tamil Nadu', '600058', 13.1143, 80.1548, 8.0, 4000.0, 3200.0, 400.0, 'available', TRUE, FALSE)
ON CONFLICT DO NOTHING;

-- Sample Vehicles
INSERT INTO vehicles (registration_number, vehicle_type, make, model, year, payload_capacity_tons, passenger_capacity, status, current_latitude, current_longitude, driver_name, driver_phone)
VALUES
    ('MH-01-AB-1234', 'truck',       'Tata',     'Prima 4028.S', 2022, 25.0, 2,  'available', 19.0760, 72.8777, 'Ravi Kumar',   '+91-9811111111'),
    ('MH-02-CD-5678', 'van',         'Force',    'Traveller',    2021,  2.0, 12, 'available', 18.5204, 73.8567, 'Amit Singh',   '+91-9822222222'),
    ('TN-09-EF-9999', 'truck',       'Ashok Leyland', 'Captain', 2023, 16.0, 2, 'available', 13.0827, 80.2707, 'Suresh Babu',  '+91-9833333333'),
    ('MH-03-GH-4321', 'boat',        'Yamaha',   'FB700',        2022,  1.5, 8,  'available', 19.2183, 72.9781, 'Deepak Patil', '+91-9844444444')
ON CONFLICT (registration_number) DO NOTHING;
