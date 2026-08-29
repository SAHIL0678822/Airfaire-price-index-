
import psycopg2
from datetime import date, timedelta
from serpapi import GoogleSearch

API_KEY = "c137854973860ecebaaf6f451c5e3469106e73faf91bca1d31b06b175877a56a"
print(f"DEBUG - Using key: '{API_KEY}'")
# Your basket of DGCA-weighted routes (IATA airport codes)
ROUTES = [
    ("DEL", "BOM"), ("DEL", "BLR"), ("BOM", "BLR"),
    ("DEL", "CCU"), ("BLR", "HYD"), ("MAA", "DEL"),
]

# Advance-purchase windows to check, per the problem statement
ADVANCE_DAYS = [1, 7, 15, 30, 45]


def fetch_fares(origin, destination, travel_date):
    """Calls SerpApi's Google Flights engine for one route/date."""
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": travel_date.isoformat(),
        "currency": "INR",
        "hl": "en",
        "gl": "in",
        "type": "2",  # one-way
        "api_key": API_KEY,
    }
    search = GoogleSearch(params)
    return search.get_dict()


def parse_results(data, origin, destination, search_date, travel_date, advance_days):
    """Extracts fields your schema needs from SerpApi's response."""
    rows = []

    # IMPORTANT: catch API errors explicitly (quota exhausted, bad params, etc.)
    # instead of silently treating them as "0 flights found"
    if "error" in data:
        raise RuntimeError(f"SerpApi error: {data['error']}")

    # SerpApi returns 'best_flights' and 'other_flights' lists
    all_flights = data.get("best_flights", []) + data.get("other_flights", [])

    for flight_group in all_flights:
        price = flight_group.get("price")
        if price is None:
            continue

        flights = flight_group.get("flights", [])
        if not flights:
            continue

        first_leg = flights[0]
        carrier = first_leg.get("airline", "unknown")
        flight_number = first_leg.get("flight_number", "")

        # SerpApi's total price includes taxes; it doesn't always split
        # base fare vs taxes separately -- document this limitation in
        # your report, and estimate a typical tax proportion (~15-20%
        # for Indian domestic fares) if you need the breakdown for your
        # index formula, clearly labeled as an estimate.
        total_fare = float(price)

        rows.append({
            "origin": origin,
            "destination": destination,
            "search_date": search_date,
            "travel_date": travel_date,
            "advance_purchase_days": advance_days,
            "carrier": carrier,
            "flight_number": flight_number,
            "total_fare": total_fare,
            "source_site": "google_flights_via_serpapi",
        })

    return rows


def save_to_db(conn, row):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO routes (origin, destination) VALUES (%s, %s) "
            "ON CONFLICT (origin, destination) DO NOTHING;",
            (row["origin"], row["destination"]),
        )
        cur.execute(
            "SELECT route_id FROM routes WHERE origin=%s AND destination=%s;",
            (row["origin"], row["destination"]),
        )
        route_id = cur.fetchone()[0]

        cur.execute(
            """
            INSERT INTO fare_quotes
                (route_id, search_date, travel_date, advance_purchase_days,
                 carrier, flight_number, total_fare, source_site)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                route_id, row["search_date"], row["travel_date"], row["advance_purchase_days"],
                row["carrier"], row["flight_number"], row["total_fare"], row["source_site"],
            ),
        )
    conn.commit()


def main():
    conn = psycopg2.connect("dbname=apix user=postgres password=yourpassword host=localhost")
    search_date = date.today()

    for origin, destination in ROUTES:
        for advance_days in ADVANCE_DAYS:
            travel_date = search_date + timedelta(days=advance_days)
            try:
                data = fetch_fares(origin, destination, travel_date)
                rows = parse_results(data, origin, destination, search_date, travel_date, advance_days)
                for row in rows:
                    save_to_db(conn, row)
                print(f"Saved {len(rows)} fares for {origin}-{destination} (T+{advance_days})")
            except Exception as e:
                print(f"Failed for {origin}-{destination} T+{advance_days}: {e}")

    conn.close()


if __name__ == "__main__":
    main()
