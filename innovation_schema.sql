-- Run this once to add the innovation-layer tables.
-- Does NOT touch your existing tables (routes, fare_quotes, daily_index, dgca_historical).

CREATE TABLE IF NOT EXISTS route_metrics (
    metric_id           SERIAL PRIMARY KEY,
    metric_date         DATE NOT NULL,
    route_id            INTEGER REFERENCES routes(route_id),
    avg_fare            NUMERIC(10,2),
    contribution_pct    NUMERIC(6,2),
    health_score        NUMERIC(5,2),
    volatility_label    VARCHAR(30),
    UNIQUE(metric_date, route_id)
);

CREATE TABLE IF NOT EXISTS index_confidence (
    confidence_id       SERIAL PRIMARY KEY,
    index_date          DATE NOT NULL UNIQUE,
    confidence_score    NUMERIC(5,2),
    expected_points     INTEGER,
    actual_points       INTEGER,
    reason              TEXT
);

CREATE INDEX IF NOT EXISTS idx_route_metrics_date ON route_metrics(metric_date);
CREATE INDEX IF NOT EXISTS idx_confidence_date ON index_confidence(index_date);
