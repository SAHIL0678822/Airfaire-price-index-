-- PostgreSQL schema for Airfare Price Index (APIx) project

CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,
    origin VARCHAR(3) NOT NULL,          -- e.g. 'DEL'
    destination VARCHAR(3) NOT NULL,     -- e.g. 'BOM'
    dgca_weight NUMERIC(6,4),            -- share of national passenger traffic, from DGCA data
    UNIQUE(origin, destination)
);

CREATE TABLE fare_quotes (
    quote_id BIGSERIAL PRIMARY KEY,
    route_id INT REFERENCES routes(route_id),
    search_date DATE NOT NULL,           -- the day you scraped
    travel_date DATE NOT NULL,           -- the day the flight departs
    advance_purchase_days INT NOT NULL,  -- travel_date - search_date
    carrier VARCHAR(50),
    flight_number VARCHAR(20),
    fare_class VARCHAR(20),
    base_fare NUMERIC(10,2),
    taxes_and_fees NUMERIC(10,2),
    total_fare NUMERIC(10,2),
    seat_status VARCHAR(20),             -- 'available' / 'sold_out'
    source_site VARCHAR(50),             -- 'indigo_direct', 'ixigo', etc.
    scraped_at TIMESTAMP DEFAULT NOW(),
    is_outlier BOOLEAN DEFAULT FALSE     -- flagged by cleaning pipeline
);

CREATE TABLE daily_index (
    index_id SERIAL PRIMARY KEY,
    index_date DATE NOT NULL,
    frequency VARCHAR(10),               -- 'daily' / 'weekly' / 'monthly'
    index_value NUMERIC(10,4),           -- normalized to base period = 100
    route_id INT REFERENCES routes(route_id), -- NULL for the overall composite index
    UNIQUE(index_date, frequency, route_id)
);

CREATE TABLE dgca_historical (
    id SERIAL PRIMARY KEY,
    month DATE NOT NULL,
    route_id INT REFERENCES routes(route_id),
    avg_fare NUMERIC(10,2),              -- for backtest comparison
    passenger_count INT                  -- for weighting
);

-- Indexes for the queries your dashboard will run constantly
CREATE INDEX idx_fare_quotes_search_date ON fare_quotes(search_date);
CREATE INDEX idx_fare_quotes_route ON fare_quotes(route_id);
