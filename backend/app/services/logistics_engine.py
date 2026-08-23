import json
import os

from route_engine import load_routes, find_best_route
from storage_engine import load_warehouses, find_best_storage
from transport_engine import load_vehicles, find_best_vehicle


def load_inventory():
    """
    Load inventory information from inventory.json.
    """

    current_file = os.path.dirname(os.path.abspath(__file__))

    data_file = os.path.join(
        current_file,
        "..",
        "data",
        "inventory.json"
    )

    with open(data_file, "r") as file:
        return json.load(file)


def generate_logistics_recommendation(inventory):
    """
    Generate a complete logistics recommendation
    for the given inventory.
    """

    required_capacity = inventory["quantity"]
    required_payload = inventory["quantity"]

    routes = load_routes()
    warehouses = load_warehouses()
    vehicles = load_vehicles()

    best_warehouse = find_best_storage(
        warehouses,
        required_capacity
    )

    if not best_warehouse:
        return {
            "inventory": inventory,
            "route": None,
            "warehouse": None,
            "vehicle": None
        }

    best_route = find_best_route(
        routes,
        destination=best_warehouse["id"]
    )

    best_vehicle = find_best_vehicle(
        vehicles,
        required_payload
    )

    return {
        "inventory": inventory,
        "route": best_route,
        "warehouse": best_warehouse,
        "vehicle": best_vehicle
    }


if __name__ == "__main__":

    inventories = load_inventory()

    inventory = inventories[0]

    recommendation = generate_logistics_recommendation(
        inventory
    )

    route = recommendation["route"]
    warehouse = recommendation["warehouse"]
    vehicle = recommendation["vehicle"]

    print()
    print("==========================================")
    print("          FLOODSHIELD LOGISTICS")
    print("==========================================")

    print()
    print("INVENTORY")
    print("------------------------------------------")
    print(f"Product: {inventory['product']}")
    print(f"Quantity: {inventory['quantity']} {inventory['unit']}")
    print(f"Value: ₹{inventory['value']}")
    print(f"Location: {inventory['location']}")
    print(f"Risk Level: {inventory['risk_level']}")
    print(f"Risk Score: {inventory['risk_score']}")

    print()
    print("SAFE STORAGE")
    print("------------------------------------------")

    if warehouse:
        print(f"Warehouse: {warehouse['id']}")
        print(f"Name: {warehouse['name']}")
        print(f"Location: {warehouse['location']}")
        print(f"Flood Risk: {warehouse['flood_risk']}")
        print(f"Available Capacity: {warehouse['available_capacity']} tons")
        print(f"Score: {warehouse['score']}")
    else:
        print("No suitable warehouse found.")

    print()
    print("SAFE ROUTE")
    print("------------------------------------------")

    if route:
        print(f"Route: {route['id']}")
        print(f"Start: {route['start']}")
        print(f"Destination: {route['destination']}")
        print(f"Distance: {route['distance']} km")
        print(f"ETA: {route['eta']} minutes")
        print(f"Flood Risk: {route['flood_risk']}")
        print(f"Score: {route['score']}")
    else:
        print("No suitable route found.")

    print()
    print("TRANSPORT")
    print("------------------------------------------")

    if vehicle:
        print(f"Vehicle: {vehicle['id']}")
        print(f"Type: {vehicle['type']}")
        print(f"Capacity: {vehicle['capacity']} tons")
        print(f"ETA: {vehicle['eta']} minutes")
        print(f"Score: {vehicle['score']}")
    else:
        print("No suitable vehicle found.")

    print()
    print("==========================================")
    print("          FINAL RECOMMENDATION")
    print("==========================================")

    if route and warehouse and vehicle:
        print(
            f"Move {inventory['product']} "
            f"using {vehicle['id']} "
            f"to {warehouse['id']} "
            f"via {route['id']}."
        )
    else:
        print("Incomplete logistics recommendation.")

    print("==========================================")