"""
Calculates the Airfare Price Index (APIx) -- a Laspeyres-style fixed-basket
index, the same methodology MoSPI uses for CPI sub-indices.

How it works:
1. For each day you've collected data, compute the AVERAGE fare per route
   (using only clean, non-outlier rows).
2. Weight each route's average fare by its DGCA-based traffic share
   (calculated earlier in get_dgca_weights.py).
3. Sum the weighted fares to get one "basket value" per day.
4. Normalize every day's basket value against the BASE PERIOD (the very
   first day you collected data) = 100. This means:
     - Index = 100 on day 1 (by definition)
     - Index = 110 means "fares are 10% higher than day 1, on average,
       weighted by route importance"
     - Index = 95 means "fares are 5% lower than day 1"

This is exactly the logic MoSPI's own CPI uses (fixed basket, base-period
normalization) -- just applied to airfares instead of a shopping basket.

Run this daily, AFTER fetch_serpapi.py and clean_data.py.
"""

import psycopg2
import pandas as pd

DB_CONFIG = "dbname=apix user=postgres password=yourpassword host=localhost"


def load_clean_data(conn):
    """
    Pulls all non-outlier fare quotes, joined with each route's DGCA weight.
    """
    query = """
        SELECT
            fq.search_date,
            fq.route_id,
            r.origin,
            r.destination,
            r.dgca_weight,
            fq.total_fare
        FROM fare_quotes fq
        JOIN routes r ON fq.route_id = r.route_id
        WHERE fq.is_outlier = FALSE
          AND r.dgca_weight IS NOT NULL;
    """
    return pd.read_sql(query, conn)


def calculate_daily_route_averages(df):
    """
    Step 1: average fare per route, per day.
    (Later you can also compute this per advance_purchase_days window if
    you want a more granular index -- this version gives the overall
    composite index across all booking windows combined.)
    """
    daily_avg = (
        df.groupby(["search_date", "route_id", "origin", "destination", "dgca_weight"])
        ["total_fare"].mean()
        .reset_index()
        .rename(columns={"total_fare": "avg_fare"})
    )
    return daily_avg


def calculate_weighted_basket_value(daily_avg):
    """
    Step 2 & 3: weight each route's average fare by its DGCA weight,
    sum across all routes, per day -- this is your "basket value" per day.
    """
    daily_avg["weighted_fare"] = daily_avg["avg_fare"] * daily_avg["dgca_weight"]

    basket_value = (
        daily_avg.groupby("search_date")["weighted_fare"]
        .sum()
        .reset_index()
        .rename(columns={"weighted_fare": "basket_value"})
    )
    return basket_value.sort_values("search_date")


def normalize_to_index(basket_value):
    """
    Step 4: normalize every day against the base period (first day of data)
    = 100.
    """
    base_value = basket_value.iloc[0]["basket_value"]
    basket_value["index_value"] = (basket_value["basket_value"] / base_value) * 100
    return basket_value


def save_index_to_db(conn, basket_value):
    """
    Uses DELETE + INSERT instead of ON CONFLICT, because Postgres never
    treats NULL values (our route_id for the composite index) as equal for
    uniqueness checks -- ON CONFLICT silently fails to catch duplicates in
    that case, which is what caused the duplicate-row bug.
    """
    with conn.cursor() as cur:
        for _, row in basket_value.iterrows():
            cur.execute(
                """
                DELETE FROM daily_index
                WHERE index_date = %s AND frequency = 'daily' AND route_id IS NULL;
                """,
                (row["search_date"],),
            )
            cur.execute(
                """
                INSERT INTO daily_index (index_date, frequency, index_value, route_id)
                VALUES (%s, 'daily', %s, NULL);
                """,
                (row["search_date"], float(row["index_value"])),
            )
    conn.commit()


def main():
    conn = psycopg2.connect(DB_CONFIG)

    df = load_clean_data(conn)
    if df.empty:
        print("No clean data with DGCA weights found. "
              "Make sure fetch_serpapi.py, clean_data.py, and "
              "get_dgca_weights.py have all been run first.")
        return

    daily_avg = calculate_daily_route_averages(df)
    basket_value = calculate_weighted_basket_value(daily_avg)
    indexed = normalize_to_index(basket_value)

    print("\nYour Airfare Price Index (APIx), by day:")
    print(indexed[["search_date", "basket_value", "index_value"]].to_string(index=False))

    save_index_to_db(conn, indexed)
    print(f"\nSaved {len(indexed)} daily index values to daily_index table.")

    conn.close()


if __name__ == "__main__":
    main()
