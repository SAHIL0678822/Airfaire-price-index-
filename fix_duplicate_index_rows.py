"""
One-time fix: removes duplicate rows in daily_index caused by a Postgres
quirk (NULL values in route_id are never treated as equal for uniqueness
checks, so the ON CONFLICT clause in calculate_index.py silently failed to
catch duplicates on re-runs).

Keeps only the MOST RECENT row per index_date (the latest calculation is
the most accurate one, since it reflects the most up-to-date clean data).
"""

import psycopg2

DB_CONFIG = "dbname=apix user=postgres password=yourpassword host=localhost"


def main():
    conn = psycopg2.connect(DB_CONFIG)
    with conn.cursor() as cur:
        # Delete all but the most recent row (highest index_id) per
        # index_date, for the composite index (route_id IS NULL).
        cur.execute("""
            DELETE FROM daily_index a
            USING daily_index b
            WHERE a.index_date = b.index_date
              AND a.frequency = b.frequency
              AND a.route_id IS NULL
              AND b.route_id IS NULL
              AND a.index_id < b.index_id;
        """)
        deleted = cur.rowcount
    conn.commit()

    with conn.cursor() as cur:
        cur.execute(
            "SELECT index_date, index_value FROM daily_index "
            "WHERE frequency = 'daily' AND route_id IS NULL ORDER BY index_date;"
        )
        rows = cur.fetchall()

    conn.close()

    print(f"Removed {deleted} duplicate rows.")
    print("\nClean index data now:")
    for date, value in rows:
        print(f"  {date}: {value}")


if __name__ == "__main__":
    main()
