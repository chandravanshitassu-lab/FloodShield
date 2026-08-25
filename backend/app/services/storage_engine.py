import json
import os


def calculate_storage_score(
    flood_risk,
    distance,
    available_capacity,
    required_capacity
):
    """
    Calculate warehouse suitability score.

    Lower score = better warehouse.
    """

    capacity_utilization = (
        required_capacity / available_capacity
    ) * 100

    score = (
        flood_risk * 0.50
        + distance * 0.30
        + capacity_utilization * 0.20
    )

    return round(score, 2)


def find_best_storage(warehouses, required_capacity):
    """
    Find the best available warehouse.
    """

    suitable_warehouses = []

    for warehouse in warehouses:

        if not warehouse["available"]:
            continue

        if warehouse["available_capacity"] < required_capacity:
            continue

        warehouse["score"] = calculate_storage_score(
            warehouse["flood_risk"],
            warehouse["distance"],
            warehouse["available_capacity"],
            required_capacity
        )

        suitable_warehouses.append(warehouse)

    if not suitable_warehouses:
        return None

    return min(
        suitable_warehouses,
        key=lambda warehouse: warehouse["score"]
    )


def load_warehouses():
    """
    Load warehouse information from warehouses.json.
    """

    current_file = os.path.dirname(os.path.abspath(__file__))

    data_file = os.path.join(
        current_file,
        "..",
        "data",
        "warehouses.json"
    )

    with open(data_file, "r") as file:
        return json.load(file)


if __name__ == "__main__":

    required_capacity = 3

    warehouses = load_warehouses()

    best_warehouse = find_best_storage(
        warehouses,
        required_capacity
    )

    print("Storage Analysis")
    print("--------------------")

    for warehouse in warehouses:
        if "score" in warehouse:
            print(
                f'{warehouse["id"]} → '
                f'Score: {warehouse["score"]}'
            )

    print("--------------------")

    if best_warehouse:
        print(
            f'Recommended Warehouse: '
            f'{best_warehouse["id"]}'
        )
    else:
        print("No suitable warehouse found.")