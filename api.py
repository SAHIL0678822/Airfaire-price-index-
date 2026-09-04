"""
APIx API -- run with: uvicorn api:app --reload --port 8000

This is the piece the problem statement asks for explicitly: "an API that
the NSO and RBI can consume." Once running, interactive documentation is
auto-generated at http://localhost:8000/docs (Swagger UI) -- worth showing
judges directly, since it proves the API is real and usable, not just a
claim in a slide.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
from datetime import date
from typing import Optional

DB_CONFIG = "dbname=apix user=postgres password=yourpassword host=localhost"

app = FastAPI(
    title="APIx - Real-Time Airfare Price Index API",
    description=(
        "Prototype API for SIH26056 (MoSPI). Exposes a DGCA-weighted, "
        "daily Airfare Price Index computed from live scraped fare data. "
        "Built for consumption by NSO/RBI systems."
    ),
    version="1.0.0",
)

# Allow any frontend (dashboard, NSO/RBI systems, etc.) to call this API.
# For production, replace "*" with the specific allowed origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_connection():
    return psycopg2.connect(DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)


# ---------------------------------------------------------------------------
# Response models (these also power the auto-generated API docs)
# ---------------------------------------------------------------------------

class IndexPoint(BaseModel):
    index_date: date
    index_value: float


class LatestIndex(BaseModel):
    index_date: date
    index_value: float
    change_pct: Optional[float]
    previous_index_value: Optional[float]


class RouteWeight(BaseModel):
    origin: str
    destination: str
    dgca_weight: float


class RouteFareSummary(BaseModel):
    origin: str
    destination: str
    advance_purchase_days: int
    avg_fare: float
    quote_count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Info"])
def root():
    """Basic API info and links to documentation."""
    return {
        "name": "APIx - Real-Time Airfare Price Index",
        "docs": "/docs",
        "endpoints": ["/index/daily", "/index/latest", "/routes", "/fares/route/{origin}/{destination}"],
    }


@app.get("/health", tags=["Info"])
def health():
    """Health check -- confirms the API and database connection are working."""
    try:
        conn = get_connection()
        conn.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {e}")


@app.get("/index/daily", response_model=list[IndexPoint], tags=["Index"])
def get_daily_index():
    """
    Full daily Airfare Price Index history. Base period = 100; values above
    100 mean fares have risen since the baseline, below 100 means they've
    fallen, weighted by each route's DGCA-based traffic share.
    """
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT index_date, index_value FROM daily_index "
            "WHERE frequency = 'daily' AND route_id IS NULL "
            "ORDER BY index_date;"
        )
        rows = cur.fetchall()
    conn.close()
    return rows


@app.get("/index/latest", response_model=LatestIndex, tags=["Index"])
def get_latest_index():
    """The most recent index value, plus day-over-day percent change."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT index_date, index_value FROM daily_index "
            "WHERE frequency = 'daily' AND route_id IS NULL "
            "ORDER BY index_date DESC LIMIT 2;"
        )
        rows = cur.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No index data available yet.")

    latest = rows[0]
    previous = rows[1] if len(rows) > 1 else None

    change_pct = None
    if previous:
        change_pct = round(
            (latest["index_value"] - previous["index_value"]) / previous["index_value"] * 100,
            2,
        )

    return {
        "index_date": latest["index_date"],
        "index_value": latest["index_value"],
        "change_pct": change_pct,
        "previous_index_value": previous["index_value"] if previous else None,
    }


@app.get("/routes", response_model=list[RouteWeight], tags=["Routes"])
def get_routes():
    """
    The basket of routes tracked by the index, with their DGCA-based
    passenger-traffic weights (how much each route counts toward the
    overall index).
    """
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT origin, destination, dgca_weight FROM routes "
            "WHERE dgca_weight IS NOT NULL ORDER BY dgca_weight DESC;"
        )
        rows = cur.fetchall()
    conn.close()
    return rows


@app.get(
    "/fares/route/{origin}/{destination}",
    response_model=list[RouteFareSummary],
    tags=["Fares"],
)
def get_route_fares(origin: str, destination: str):
    """
    Average fare for a specific route, broken down by advance-purchase
    window (T+1, T+7, T+15, T+30, T+45). Route codes are IATA airport
    codes, e.g. /fares/route/DEL/BOM
    """
    origin, destination = origin.upper(), destination.upper()

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT r.origin, r.destination, fq.advance_purchase_days,
                   ROUND(AVG(fq.total_fare)::numeric, 2) AS avg_fare,
                   COUNT(*) AS quote_count
            FROM fare_quotes fq
            JOIN routes r ON fq.route_id = r.route_id
            WHERE r.origin = %s AND r.destination = %s AND fq.is_outlier = FALSE
            GROUP BY r.origin, r.destination, fq.advance_purchase_days
            ORDER BY fq.advance_purchase_days;
            """,
            (origin, destination),
        )
        rows = cur.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No fare data found for route {origin}-{destination}.",
        )
    return rows


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
