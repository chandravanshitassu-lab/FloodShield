from backend.app.services.route_engine import (
    calculate_route_score,
    find_best_route
)

from backend.app.services.storage_engine import (
    calculate_storage_score,
    find_best_storage
)

from backend.app.services.transport_engine import (
    calculate_transport_score,
    find_best_vehicle
)


def test_route_score():
    score = calculate_route_score(
        flood_risk=20,
        blockage=10,
        traffic=30,
        distance=5
    )

    assert score == 16.25


def test_best_route():
    routes = [
        {
            "id": "R01",
            "start": "Business Area",
            "destination": "W01",
            "distance": 5,
            "eta": 20,
            "flood_risk": 20,
            "blockage": 10,
            "traffic": 30
        },
        {
            "id": "R02",
            "start": "Business Area",
            "destination": "W01",
            "distance": 3,
            "eta": 15,
            "flood_risk": 80,
            "blockage": 60,
            "traffic": 20
        }
    ]

    result = find_best_route(
        routes,
        destination="W01"
    )

    assert result["id"] == "R01"


def test_best_warehouse():
    warehouses = [
        {
            "id": "W01",
            "name": "Safe Warehouse A",
            "distance": 4,
            "flood_risk": 15,
            "available_capacity": 8,
            "available": True
        },
        {
            "id": "W02",
            "name": "Warehouse B",
            "distance": 2,
            "flood_risk": 75,
            "available_capacity": 10,
            "available": True
        }
    ]

    result = find_best_storage(
        warehouses,
        required_capacity=3
    )

    assert result["id"] == "W01"


def test_best_vehicle():
    vehicles = [
        {
            "id": "V01",
            "type": "Truck",
            "capacity": 5,
            "distance": 2,
            "eta": 20,
            "available": True
        },
        {
            "id": "V02",
            "type": "Large Truck",
            "capacity": 8,
            "distance": 6,
            "eta": 45,
            "available": True
        },
        {
            "id": "V03",
            "type": "Mini Truck",
            "capacity": 2,
            "distance": 1,
            "eta": 10,
            "available": True
        }
    ]

    result = find_best_vehicle(
        vehicles,
        required_payload=3
    )

    assert result["id"] == "V01"


def test_no_vehicle_for_large_payload():
    vehicles = [
        {
            "id": "V01",
            "type": "Truck",
            "capacity": 5,
            "distance": 2,
            "eta": 20,
            "available": True
        }
    ]

    result = find_best_vehicle(
        vehicles,
        required_payload=20
    )

    assert result is None


def test_no_warehouse_for_large_capacity():
    warehouses = [
        {
            "id": "W01",
            "name": "Warehouse A",
            "distance": 4,
            "flood_risk": 15,
            "available_capacity": 8,
            "available": True
        }
    ]

    result = find_best_storage(
        warehouses,
        required_capacity=20
    )

    assert result is None