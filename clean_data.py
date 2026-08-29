"""
Cleans the fare_quotes table:
1. Removes exact duplicate rows (same route, date, carrier, flight number, fare)
   that happen because SerpApi lists the same flight in both 'best_flights'
   and 'other_flights', or across repeated scrape runs on the same day.
2. Flags statistical outliers (using IQR method) per route+advance_purchase_days
   group, so a glitched ₹50,000 fare doesn't skew your index later.

Run this AFTER each fetch_serpapi.py run, or once daily after all scraping
for the day is done.
"""

import psycopg2
import pandas as pd

DB_CONFIG = "dbname=apix user=postgres password=yourpassword host=localhost"


def remove_exact_duplicates(conn):
    """
    Keeps only the earliest-scraped copy of each truly identical fare
    (same route, search_date, travel_date, carrier, flight_number, total_fare).
    """
    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM fare_quotes a
            USING fare_quotes b
            WHERE a.quote_id > b.quote_id
              AND a.route_id = b.route_id
              AND a.search_date = b.search_date
              AND a.travel_date = b.travel_date
              AND a.carrier = b.carrier
              AND a.flight_number = b.flight_number
              AND a.total_fare = b.total_fare;
        """)
        deleted = cur.rowcount
    conn.commit()
    print(f"Removed {deleted} exact duplicate rows.")


def flag_outliers(conn):
    """
    For each route + advance_purchase_days group, flags fares that fall
    outside 1.5x the IQR (standard outlier detection) as is_outlier = TRUE.
    These stay in the table for transparency but get excluded from index
    calculations later.
    """
    df = pd.read_sql(
        "SELECT quote_id, route_id, advance_purchase_days, total_fare FROM fare_quotes;",
        conn,
    )

    outlier_ids = []

    for (route_id, adv_days), group in df.groupby(["route_id", "advance_purchase_days"]):
        q1 = group["total_fare"].quantile(0.25)
        q3 = group["total_fare"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = group[(group["total_fare"] < lower) | (group["total_fare"] > upper)]
        outlier_ids.extend(outliers["quote_id"].tolist())

    if outlier_ids:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE fare_quotes SET is_outlier = TRUE WHERE quote_id = ANY(%s);",
                (outlier_ids,),
            )
        conn.commit()

    print(f"Flagged {len(outlier_ids)} outlier rows out of {len(df)} total.")


def summary(conn):
    """Prints a quick summary so you can see the cleaning results."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM fare_quotes;")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fare_quotes WHERE is_outlier = TRUE;")
        outliers = cur.fetchone()[0]
    print(f"\nFinal state: {total} total rows, {outliers} flagged as outliers, "
          f"{total - outliers} clean usable rows for index calculation.")


def main():
    conn = psycopg2.connect(DB_CONFIG)
    remove_exact_duplicates(conn)
    flag_outliers(conn)
    summary(conn)
    conn.close()


if __name__ == "__main__":
    main()
