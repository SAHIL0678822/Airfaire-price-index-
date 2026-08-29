"""
APIx Dashboard -- run with: streamlit run dashboard.py

Shows:
1. The Airfare Price Index trend over time (line chart)
2. Sector-wise (route) fare heatmap across advance-purchase windows
3. Lead-time elasticity curve (how fare changes as you book closer to departure)
4. DGCA route weights (so judges can see the weighting methodology at a glance)
"""

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go

DB_CONFIG = "dbname=apix user=postgres password=yourpassword host=localhost"

st.set_page_config(page_title="APIx - Airfare Price Index", layout="wide")


@st.cache_data(ttl=300)  # refresh every 5 minutes
def load_data():
    conn = psycopg2.connect(DB_CONFIG)

    index_df = pd.read_sql(
        "SELECT index_date, index_value FROM daily_index "
        "WHERE frequency = 'daily' AND route_id IS NULL "
        "ORDER BY index_date;",
        conn,
    )

    fares_df = pd.read_sql(
        """
        SELECT r.origin, r.destination, r.dgca_weight,
               fq.advance_purchase_days, fq.total_fare, fq.search_date
        FROM fare_quotes fq
        JOIN routes r ON fq.route_id = r.route_id
        WHERE fq.is_outlier = FALSE;
        """,
        conn,
    )

    weights_df = pd.read_sql(
        "SELECT origin, destination, dgca_weight FROM routes "
        "WHERE dgca_weight IS NOT NULL ORDER BY dgca_weight DESC;",
        conn,
    )

    conn.close()
    return index_df, fares_df, weights_df


st.title("✈️ APIx — Real-Time Airfare Price Index")
st.caption(" Data: SerpApi (Google Flights) + DGCA")

index_df, fares_df, weights_df = load_data()

if fares_df.empty:
    st.warning("No data yet — run fetch_serpapi.py, clean_data.py, and "
               "calculate_index.py first.")
    st.stop()

# ---- Section 1: Index trend line ----
st.header("1. Airfare Price Index Trend")

if len(index_df) >= 2:
    fig_index = px.line(
        index_df, x="index_date", y="index_value",
        markers=True,
        labels={"index_date": "Date", "index_value": "Index Value (Base = 100)"},
        title="APIx Over Time",
    )
    fig_index.add_hline(y=100, line_dash="dash", line_color="gray",
                         annotation_text="Base period")
    st.plotly_chart(fig_index, use_container_width=True)
else:
    st.info(f"Only {len(index_df)} day(s) of index data so far. "
            "The trend line will become meaningful as you collect more days — "
            "keep running fetch_serpapi.py + clean_data.py + calculate_index.py daily.")
    st.dataframe(index_df, use_container_width=True)

# ---- Section 2: Sector-wise heatmap ----
st.header("2. Sector-wise Fare Heatmap")
st.caption("Average fare (₹) by route and advance-purchase window")

route_label = fares_df["origin"] + "-" + fares_df["destination"]
fares_df = fares_df.assign(route=route_label)

heatmap_data = (
    fares_df.groupby(["route", "advance_purchase_days"])["total_fare"]
    .mean()
    .reset_index()
    .pivot(index="route", columns="advance_purchase_days", values="total_fare")
)

fig_heatmap = go.Figure(data=go.Heatmap(
    z=heatmap_data.values,
    x=[f"T+{c}" for c in heatmap_data.columns],
    y=heatmap_data.index,
    colorscale="YlOrRd",
    text=heatmap_data.values.round(0),
    texttemplate="₹%{text}",
    colorbar_title="Avg Fare (₹)",
))
fig_heatmap.update_layout(title="Average Fare by Route and Booking Window")
st.plotly_chart(fig_heatmap, use_container_width=True)

# ---- Section 3: Lead-time elasticity curve ----
st.header("3. Lead-Time Elasticity Curve")
st.caption("How average fare changes as departure gets closer")

elasticity_data = (
    fares_df.groupby(["route", "advance_purchase_days"])["total_fare"]
    .mean()
    .reset_index()
)

fig_elasticity = px.line(
    elasticity_data, x="advance_purchase_days", y="total_fare", color="route",
    markers=True,
    labels={"advance_purchase_days": "Days Before Departure (Advance Purchase)",
            "total_fare": "Average Fare (₹)"},
    title="Fare vs. Booking Lead Time, by Route",
)
fig_elasticity.update_xaxes(autorange="reversed")  # T+1 (closest) on the right
st.plotly_chart(fig_elasticity, use_container_width=True)

# ---- Section 4: DGCA weights ----
st.header("4. Route Weights (DGCA Passenger Traffic-Based)")

col1, col2 = st.columns([1, 1])

with col1:
    weights_df["route"] = weights_df["origin"] + "-" + weights_df["destination"]
    fig_weights = px.bar(
        weights_df, x="route", y="dgca_weight",
        labels={"dgca_weight": "Weight (share of basket traffic)", "route": "Route"},
        title="Route Weights in the Index",
    )
    fig_weights.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig_weights, use_container_width=True)

with col2:
    st.dataframe(
        weights_df[["route", "dgca_weight"]].assign(
            dgca_weight=lambda d: (d["dgca_weight"] * 100).round(1).astype(str) + "%"
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Weights derived from DGCA's published city-pair passenger "
               "traffic data (most recent complete year). Source: DGCA, "
               "via github.com/Vonter/india-aviation-traffic (ODbL license).")

st.divider()
st.caption("Data attribution: DGCA, Ministry of Civil Aviation, Google Flights (via SerpApi)")
