import json
import os


def calculate_route_score(
    flood_risk,
    blockage,
    traffic,
    distance
):
    """
    Calculate route safety score.

    Lower score = better route.
    """

    score = (
        flood_risk * 0.40
        + blockage * 0.30
        + traffic * 0.15
        + distance * 0.15
    )

    return round(score, 2)


def find_best_route(routes, destination=None):
    """
    Find the safest route.

    If destination is provided, only routes
    going to that destination are considered.
    """

    if destination:
        routes = [
            route
            for route in routes
            if route["destination"] == destination
        ]

    if not routes:
        return None

    for route in routes:
        route["score"] = calculate_route_score(
            route["flood_risk"],
            route["blockage"],
            route["traffic"],
            route["distance"]
        )

    return min(
        routes,
        key=lambda route: route["score"]
    )


def load_routes():
    """
    Load route data from routes.json.
    """

    current_file = os.path.dirname(
        os.path.abspath(__file__)
    )

    data_file = os.path.join(
        current_file,
        "..",
        "data",
        "routes.json"
    )

    with open(data_file, "r") as file:
        return json.load(file)


if __name__ == "__main__":

    routes = load_routes()

    best_route = find_best_route(routes)

    print()
    print("Route Analysis")
    print("--------------------")

    for route in routes:
        print(
            f'{route["id"]} → '
            f'Score: {route["score"]}'
        )

    print("--------------------")

    if best_route:
        print(
            f'Recommended Route: '
            f'{best_route["id"]}'
        )
    else:
        print("No suitable route found.")