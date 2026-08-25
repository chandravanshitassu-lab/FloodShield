import json
import os


def calculate_transport_score(
    distance,
    eta,
    capacity,
    required_payload
):
    """
    Calculate vehicle suitability score.

    Lower score = better vehicle.
    """

    capacity_utilization = (
        required_payload / capacity
    ) * 100

    score = (
        eta * 0.40
        + distance * 0.30
        + capacity_utilization * 0.30
    )

    return round(score, 2)


def find_best_vehicle(vehicles, required_payload):
    """
    Find the best available vehicle.
    """

    suitable_vehicles = []

    for vehicle in vehicles:

        if not vehicle["available"]:
            continue

        if vehicle["capacity"] < required_payload:
            continue

        vehicle["score"] = calculate_transport_score(
            vehicle["distance"],
            vehicle["eta"],
            vehicle["capacity"],
            required_payload
        )

        suitable_vehicles.append(vehicle)

    if not suitable_vehicles:
        return None

    return min(
        suitable_vehicles,
        key=lambda vehicle: vehicle["score"]
    )


def load_vehicles():
    """
    Load vehicle information from vehicles.json.
    """

    current_file = os.path.dirname(os.path.abspath(__file__))

    data_file = os.path.join(
        current_file,
        "..",
        "data",
        "vehicles.json"
    )

    with open(data_file, "r") as file:
        return json.load(file)


if __name__ == "__main__":

    required_payload = 3

    vehicles = load_vehicles()

    best_vehicle = find_best_vehicle(
        vehicles,
        required_payload
    )

    print("Transport Analysis")
    print("--------------------")

    for vehicle in vehicles:
        if "score" in vehicle:
            print(
                f'{vehicle["id"]} → '
                f'Score: {vehicle["score"]}'
            )

    print("--------------------")

    if best_vehicle:
        print(
            f'Recommended Vehicle: '
            f'{best_vehicle["id"]}'
        )
    else:
        print("No suitable vehicle found.")