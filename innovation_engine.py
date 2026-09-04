"""
AIx Innovation Engine
---------------------
Reads data already sitting in your database (fare_quotes, routes, daily_index)
and computes four things, per day:

1. Contribution % — which route drove today's index change, and by how much
2. Route Health Score (0-100) — how volatile each route currently is
3. Volatility Label — Stable / Moderately Volatile / Highly Volatile / Extreme
4. Confidence Score — how complete today's data collection was

Does NOT touch your scraper, cleaner, or index calculation — this is a
read-only analysis layer that writes its output into two new tables:
route_metrics and index_confidence (see innovation_schema.sql).

Run this AFTER calculate_index.py each day, since it uses that day's
clean fare data.
"""

import pandas as pd
import numpy as np
import psycopg2

# ---- UPDATE THIS with your Docker Postgres password ----
DB_CONFIG = {
    "dbname": "apix",
    "user": "postgres",
    "password": "yourpassword",
    "host": "localhost",
}

EXPECTED_ROUTES = 6          # how many routes you're tracking
EXPECTED_WINDOWS = 5         # T+1, T+7, T+15, T+30, T+45
EXPECTED_POINTS_PER_DAY = EXPECTED_ROUTES * EXPECTED_WINDOWS


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def load_clean_fares(conn):
    """Load clean (non-outlier) fares joined with route info and DGCA weight."""
    query = """
        SELECT fq.search_date, fq.route_id, fq.advance_purchase_days,
               fq.total_fare, r.origin, r.destination, r.dgca_weight
        FROM fare_quotes fq
        JOIN routes r ON fq.route_id = r.route_id
        WHERE fq.is_outlier IS NOT TRUE
    """
    return pd.read_sql(query, conn)


def compute_daily_route_avg(df):
    """Average fare per route per day."""
    return (
        df.groupby(["search_date", "route_id", "origin", "destination", "dgca_weight"])
        ["total_fare"].mean().reset_index().rename(columns={"total_fare": "avg_fare"})
    )


def compute_contribution(daily_route_avg):
    """
    For each day (after the first), work out how much each route's
    weighted fare change contributed to the overall index movement.
    """
    daily_route_avg = daily_route_avg.sort_values(["route_id", "search_date"])
    daily_route_avg["weighted_fare"] = (
        daily_route_avg["avg_fare"] * daily_route_avg["dgca_weight"] / 100
    )
    daily_route_avg["prev_weighted_fare"] = daily_route_avg.groupby("route_id")["weighted_fare"].shift(1)
    daily_route_avg["weighted_change"] = (
        daily_route_avg["weighted_fare"] - daily_route_avg["prev_weighted_fare"]
    )

    results = []
    for date, group in daily_route_avg.groupby("search_date"):
        total_change = group["weighted_change"].abs().sum()
        for _, row in group.iterrows():
            if pd.isna(row["weighted_change"]) or total_change == 0:
                contribution_pct = None
            else:
                contribution_pct = round(abs(row["weighted_change"]) / total_change * 100, 2)
            results.append({
                "metric_date": date,
                "route_id": row["route_id"],
                "origin": row["origin"],
                "destination": row["destination"],
                "avg_fare": round(row["avg_fare"], 2),
                "contribution_pct": contribution_pct,
            })
    return pd.DataFrame(results)


def compute_health_scores(daily_route_avg):
    """
    Volatility per route = coefficient of variation (std / mean) across
    all days collected so far. Lower volatility -> higher health score.
    """
    scores = []
    for route_id, group in daily_route_avg.groupby("route_id"):
        if len(group) < 2:
            # Not enough days yet to judge volatility
            scores.append({
                "route_id": route_id,
                "origin": group["origin"].iloc[0],
                "destination": group["destination"].iloc[0],
                "health_score": None,
                "volatility_label": "Insufficient data",
            })
            continue

        mean_fare = group["avg_fare"].mean()
        std_fare = group["avg_fare"].std()
        cv = (std_fare / mean_fare) if mean_fare else 0

        # Map coefficient of variation to a 0-100 health score.
        # cv of 0 -> 100 (perfectly stable). cv of 0.3+ -> near 0.
        health_score = max(0, round(100 - (cv * 300), 1))

        if health_score >= 80:
            label = "Stable"
        elif health_score >= 55:
            label = "Moderately Volatile"
        elif health_score >= 30:
            label = "Highly Volatile"
        else:
            label = "Extreme"

        scores.append({
            "route_id": route_id,
            "origin": group["origin"].iloc[0],
            "destination": group["destination"].iloc[0],
            "health_score": health_score,
            "volatility_label": label,
        })
    return pd.DataFrame(scores)


def compute_confidence(df):
    """
    Confidence = how many of the expected (route x booking-window) data
    points actually came in today, vs how many we expect on a normal day.
    """
    results = []
    for date, group in df.groupby("search_date"):
        actual_points = group[["route_id", "advance_purchase_days"]].drop_duplicates().shape[0]
        confidence = round(min(actual_points / EXPECTED_POINTS_PER_DAY, 1.0) * 100, 1)

        if confidence >= 90:
            reason = "Full data collection across all routes and windows."
        else:
            missing = EXPECTED_POINTS_PER_DAY - actual_points
            reason = f"Missing {missing} of {EXPECTED_POINTS_PER_DAY} expected data points — check scraper logs."

        results.append({
            "index_date": date,
            "confidence_score": confidence,
            "expected_points": EXPECTED_POINTS_PER_DAY,
            "actual_points": actual_points,
            "reason": reason,
        })
    return pd.DataFrame(results)


def save_route_metrics(conn, contribution_df, health_df):
    merged = contribution_df.merge(health_df[["route_id", "health_score", "volatility_label"]],
                                    on="route_id", how="left")
    cur = conn.cursor()
    for _, row in merged.iterrows():
        cur.execute("""
            INSERT INTO route_metrics (metric_date, route_id, avg_fare, contribution_pct,
                                        health_score, volatility_label)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (metric_date, route_id)
            DO UPDATE SET avg_fare = EXCLUDED.avg_fare,
                          contribution_pct = EXCLUDED.contribution_pct,
                          health_score = EXCLUDED.health_score,
                          volatility_label = EXCLUDED.volatility_label
        """, (row["metric_date"], row["route_id"], row["avg_fare"],
              row["contribution_pct"], row["health_score"], row["volatility_label"]))
    conn.commit()
    cur.close()


def save_confidence(conn, confidence_df):
    cur = conn.cursor()
    for _, row in confidence_df.iterrows():
        cur.execute("""
            INSERT INTO index_confidence (index_date, confidence_score, expected_points,
                                           actual_points, reason)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (index_date)
            DO UPDATE SET confidence_score = EXCLUDED.confidence_score,
                          expected_points = EXCLUDED.expected_points,
                          actual_points = EXCLUDED.actual_points,
                          reason = EXCLUDED.reason
        """, (row["index_date"], row["confidence_score"], row["expected_points"],
              row["actual_points"], row["reason"]))
    conn.commit()
    cur.close()


def print_explainable_summary(contribution_df, confidence_df):
    """Plain-English printout — the 'Explainable Index' layer."""
    if contribution_df.empty:
        print("No contribution data yet — need at least 2 days of collection.")
        return

    latest_date = contribution_df["metric_date"].max()
    latest = contribution_df[contribution_df["metric_date"] == latest_date].dropna(subset=["contribution_pct"])
    latest = latest.sort_values("contribution_pct", ascending=False)

    conf_row = confidence_df[confidence_df["index_date"] == latest_date]
    conf_val = conf_row["confidence_score"].values[0] if not conf_row.empty else None

    print(f"\n--- Explainable Index Summary for {latest_date} ---")
    if conf_val is not None:
        print(f"Confidence: {conf_val}%")
    if not latest.empty:
        top = latest.iloc[0]
        print(f"Top contributor: {top['origin']}-{top['destination']} "
              f"({top['contribution_pct']}% of today's movement)")
        for _, row in latest.iterrows():
            print(f"  {row['origin']}-{row['destination']}: {row['contribution_pct']}%")
    else:
        print("Not enough historical data yet to calculate contributions.")


def main():
    conn = get_conn()
    df = load_clean_fares(conn)

    if df.empty:
        print("No clean fare data found — run fetch_serpapi.py and clean_data.py first.")
        return

    daily_route_avg = compute_daily_route_avg(df)
    contribution_df = compute_contribution(daily_route_avg)
    health_df = compute_health_scores(daily_route_avg)
    confidence_df = compute_confidence(df)

    save_route_metrics(conn, contribution_df, health_df)
    save_confidence(conn, confidence_df)

    print("Route Health Scores:")
    print(health_df[["origin", "destination", "health_score", "volatility_label"]]
          .sort_values("health_score", ascending=False).to_string(index=False))

    print_explainable_summary(contribution_df, confidence_df)

    conn.close()
    print("\nSaved to route_metrics and index_confidence tables.")


if __name__ == "__main__":
    main()
