"""
Fetches DGCA's real city-pair passenger traffic data (via the Vonter/
india-aviation-traffic GitHub mirror, which sources it from DGCA directly)
and calculates DGCA-based weights for your 6 routes.

Data source: https://github.com/Vonter/india-aviation-traffic
License: ODbL -- attribute DGCA and Ministry of Civil Aviation in your
project documentation/report.
"""

import pandas as pd
import psycopg2
import requests
from io import StringIO

DB_CONFIG = "dbname=apix user=postgres password=yourpassword host=localhost"

DGCA_CITY_CSV_URL = (
    "https://raw.githubusercontent.com/Vonter/india-aviation-traffic/"
    "main/aggregated/domestic/city.csv"
)

# Map your route airport codes to the full city names DGCA uses
CITY_NAME_MAP = {
    "DEL": "DELHI",
    "BOM": "MUMBAI",
    "BLR": "BENGALURU",
    "CCU": "KOLKATA",
    "HYD": "HYDERABAD",
    "MAA": "CHENNAI",
}

ROUTES = [
    ("DEL", "BOM"), ("DEL", "BLR"), ("BOM", "BLR"),
    ("DEL", "CCU"), ("BLR", "HYD"), ("MAA", "DEL"),
]


def fetch_dgca_data():
    print("Downloading DGCA city-pair traffic data...")
    resp = requests.get(DGCA_CITY_CSV_URL)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))
    print(f"Loaded {len(df)} rows of DGCA data.")
    return df


def calculate_route_weights(df, reference_year=None):
    """
    For each of your 6 routes, sums recent passenger traffic (both
    directions) and calculates each route's share of the TOTAL traffic
    across your basket -- this becomes its DGCA-based weight in the index
    formula.

    reference_year: if None, auto-picks the most recent year that has
    complete data for ALL routes in your basket (some cities may have
    reporting gaps in the very latest year -- e.g. Mumbai's 2026 data
    wasn't available at the time this was built, so 2025 was used instead).
    """
    if reference_year is None:
        # Find the most recent year where every city in our basket has data
        all_needed_cities = set(CITY_NAME_MAP.values())
        for year in sorted(df["Year"].unique(), reverse=True):
            year_cities = set(df[df["Year"] == year]["City1"]) | set(df[df["Year"] == year]["City2"])
            if all_needed_cities.issubset(year_cities):
                reference_year = year
                break
        print(f"Auto-selected {reference_year} as the most recent year with "
              f"complete data for all 6 routes.")

    recent = df[df["Year"] == reference_year]

    route_traffic = {}

    for origin, destination in ROUTES:
        city1 = CITY_NAME_MAP[origin]
        city2 = CITY_NAME_MAP[destination]

        # Traffic is recorded per city pair in one direction per row;
        # match both City1->City2 and City2->City1 to capture the full route
        match = recent[
            ((recent["City1"] == city1) & (recent["City2"] == city2)) |
            ((recent["City1"] == city2) & (recent["City2"] == city1))
        ]

        total_pax = match["PaxToCity2"].sum() + match["PaxFromCity2"].sum()
        route_traffic[(origin, destination)] = total_pax
        print(f"{origin}-{destination}: {total_pax:,.0f} passengers ({reference_year})")

    total_basket_traffic = sum(route_traffic.values())

    if total_basket_traffic == 0:
        print("\nWARNING: No matching traffic found for any route. "
              "Check CITY_NAME_MAP spelling against DGCA's exact city names.")
        return {}

    weights = {
        route: traffic / total_basket_traffic
        for route, traffic in route_traffic.items()
    }

    print("\nCalculated DGCA-based route weights:")
    for route, weight in weights.items():
        print(f"  {route[0]}-{route[1]}: {weight:.4f} ({weight*100:.1f}%)")

    return weights


def save_weights_to_db(weights):
    conn = psycopg2.connect(DB_CONFIG)
    with conn.cursor() as cur:
        for (origin, destination), weight in weights.items():
            cur.execute(
                "UPDATE routes SET dgca_weight = %s WHERE origin = %s AND destination = %s;",
                (float(weight), origin, destination),
            )
    conn.commit()
    conn.close()
    print("\nSaved weights to your routes table.")


def main():
    df = fetch_dgca_data()
    weights = calculate_route_weights(df)
    if weights:
        save_weights_to_db(weights)


if __name__ == "__main__":
    main()
