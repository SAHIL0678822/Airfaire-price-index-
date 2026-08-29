"""
APIx Dashboard -- run with: streamlit run dashboard.py

Visual identity: clean, official light theme in the spirit of Digital India /
government portals -- white background, navy-blue headings, saffron and
green accents (tricolor-inspired), card-based layout.
"""

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go

DB_CONFIG = "dbname=apix user=postgres password=yourpassword host=localhost"

st.set_page_config(page_title="APIx - Airfare Price Index", layout="wide", page_icon="✈️")

# ---------------------------------------------------------------------------
# THEME
# ---------------------------------------------------------------------------
BG = "#F7F9FC"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#E1E8F0"
NAVY = "#0B3D91"
SAFFRON = "#FF9933"
GREEN = "#128807"
TEXT = "#1A2B45"
TEXT_MUTED = "#6B7A90"
RED = "#C0392B"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.stApp {{
    background-color: {BG};
    color: {TEXT};
}}

/* Header */
.apix-header {{
    display: flex;
    align-items: center;
    gap: 14px;
    border-bottom: 3px solid {SAFFRON};
    padding-bottom: 16px;
    margin-bottom: 28px;
}}
.apix-title {{
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 2.2rem;
    color: {NAVY};
    margin: 0;
}}
.apix-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: {TEXT_MUTED};
    margin: 0;
}}

/* KPI cards */
.kpi-row {{
    display: flex;
    gap: 16px;
    margin-bottom: 32px;
    flex-wrap: wrap;
}}
.kpi-tile {{
    background-color: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-left: 4px solid {NAVY};
    border-radius: 6px;
    padding: 16px 20px;
    flex: 1;
    min-width: 170px;
    box-shadow: 0 1px 3px rgba(11, 61, 145, 0.06);
}}
.kpi-tile.saffron {{ border-left-color: {SAFFRON}; }}
.kpi-tile.green {{ border-left-color: {GREEN}; }}
.kpi-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: {TEXT_MUTED};
    margin-bottom: 6px;
}}
.kpi-value {{
    font-family: 'Poppins', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: {NAVY};
}}
.kpi-value.green {{ color: {GREEN}; }}
.kpi-value.red {{ color: {RED}; }}
.kpi-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: {TEXT_MUTED};
    margin-top: 2px;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 1px solid {CARD_BORDER};
}}
.stTabs [data-baseweb="tab"] {{
    background-color: transparent;
    color: {TEXT_MUTED};
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.5px;
    padding: 10px 18px;
}}
.stTabs [aria-selected="true"] {{
    color: {NAVY} !important;
    border-bottom: 3px solid {SAFFRON} !important;
}}

/* Dataframes */
[data-testid="stDataFrame"] {{
    border: 1px solid {CARD_BORDER};
    border-radius: 6px;
}}

.footer-note {{
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: {TEXT_MUTED};
    border-top: 1px solid {CARD_BORDER};
    padding-top: 14px;
    margin-top: 40px;
}}
</style>
""", unsafe_allow_html=True)


def themed_layout(fig, title):
    """Applies the light theme to any Plotly figure."""
    fig.update_layout(
        title=title,
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(family="Inter, sans-serif", color=TEXT, size=13),
        title_font=dict(family="Poppins, sans-serif", color=NAVY, size=16),
        xaxis=dict(gridcolor=CARD_BORDER, zerolinecolor=CARD_BORDER),
        yaxis=dict(gridcolor=CARD_BORDER, zerolinecolor=CARD_BORDER),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=60, l=40, r=30, b=40),
    )
    return fig


@st.cache_data(ttl=300)
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


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="apix-header">
    <div class="apix-title">✈ APIx</div>
    <div class="apix-subtitle">Real-Time Airfare Price Index — SIH26056 · MoSPI</div>
</div>
""", unsafe_allow_html=True)

index_df, fares_df, weights_df = load_data()

if fares_df.empty:
    st.warning("No data yet — run fetch_serpapi.py, clean_data.py, and calculate_index.py first.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------------------------
latest_index = index_df.iloc[-1]["index_value"] if not index_df.empty else 100.0
prev_index = index_df.iloc[-2]["index_value"] if len(index_df) >= 2 else latest_index
change_pct = ((latest_index - prev_index) / prev_index * 100) if prev_index else 0
change_class = "red" if change_pct > 0 else "green"
change_sign = "+" if change_pct >= 0 else ""

days_tracked = len(index_df)
routes_tracked = fares_df[["origin", "destination"]].drop_duplicates().shape[0]
total_quotes = len(fares_df)

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-tile">
        <div class="kpi-label">Current Index</div>
        <div class="kpi-value">{latest_index:.1f}</div>
        <div class="kpi-sub">Base period = 100</div>
    </div>
    <div class="kpi-tile saffron">
        <div class="kpi-label">Day-over-day</div>
        <div class="kpi-value {change_class}">{change_sign}{change_pct:.1f}%</div>
        <div class="kpi-sub">vs. previous day</div>
    </div>
    <div class="kpi-tile green">
        <div class="kpi-label">Days Tracked</div>
        <div class="kpi-value green">{days_tracked}</div>
        <div class="kpi-sub">since baseline</div>
    </div>
    <div class="kpi-tile">
        <div class="kpi-label">Clean Fare Quotes</div>
        <div class="kpi-value">{total_quotes:,}</div>
        <div class="kpi-sub">across {routes_tracked} routes</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------
tab_trend, tab_heatmap, tab_elasticity, tab_weights = st.tabs(
    ["Trend", "Heatmap", "Elasticity", "Weights"]
)

with tab_trend:
    if len(index_df) >= 2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=index_df["index_date"], y=index_df["index_value"],
            mode="lines+markers",
            line=dict(color=NAVY, width=2.5),
            marker=dict(size=7, color=SAFFRON),
        ))
        fig.add_hline(y=100, line_dash="dash", line_color=TEXT_MUTED,
                      annotation_text="Base", annotation_font_color=TEXT_MUTED)
        fig = themed_layout(fig, "APIx Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"Only {len(index_df)} day(s) of index data so far. The trend line "
                "becomes meaningful as you collect more days — keep running the "
                "daily pipeline.")
        st.dataframe(index_df, use_container_width=True)

with tab_heatmap:
    route_label = fares_df["origin"] + "-" + fares_df["destination"]
    fares_df = fares_df.assign(route=route_label)

    heatmap_data = (
        fares_df.groupby(["route", "advance_purchase_days"])["total_fare"]
        .mean()
        .reset_index()
        .pivot(index="route", columns="advance_purchase_days", values="total_fare")
    )

    z = heatmap_data.values
    z_min, z_max = z.min(), z.max()
    z_norm = (z - z_min) / (z_max - z_min) if z_max > z_min else z * 0

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=[f"T+{c}" for c in heatmap_data.columns],
        y=heatmap_data.index,
        colorscale=[[0, "#EAF1FB"], [0.5, "#8FB8E8"], [1, NAVY]],
        colorbar=dict(title="₹", tickfont=dict(color=TEXT)),
        showscale=True,
    ))
    fig = themed_layout(fig, "Average Fare by Route and Booking Window")

    # Per-cell adaptive text color so labels stay readable across the
    # whole colorscale (light cells get dark text, dark cells get light text).
    for i, route in enumerate(heatmap_data.index):
        for j, col in enumerate(heatmap_data.columns):
            value = z[i][j]
            norm = z_norm[i][j]
            text_color = "#FFFFFF" if norm > 0.55 else TEXT
            fig.add_annotation(
                x=f"T+{col}", y=route,
                text=f"₹{value:,.0f}",
                showarrow=False,
                font=dict(family="Inter, sans-serif", size=13, color=text_color),
            )

    st.plotly_chart(fig, use_container_width=True)

with tab_elasticity:
    elasticity_data = (
        fares_df.groupby(["route", "advance_purchase_days"])["total_fare"]
        .mean()
        .reset_index()
    )

    palette = [NAVY, SAFFRON, GREEN, "#8B5CF6", "#C0392B", "#0EA5A5"]
    fig = px.line(
        elasticity_data, x="advance_purchase_days", y="total_fare", color="route",
        markers=True,
        color_discrete_sequence=palette,
        labels={"advance_purchase_days": "Days Before Departure",
                "total_fare": "Average Fare (₹)"},
    )
    fig.update_xaxes(autorange="reversed")
    fig = themed_layout(fig, "Fare vs. Booking Lead Time, by Route")
    st.plotly_chart(fig, use_container_width=True)

with tab_weights:
    col1, col2 = st.columns([1.3, 1])

    with col1:
        weights_df["route"] = weights_df["origin"] + "-" + weights_df["destination"]
        fig = px.bar(
            weights_df, x="route", y="dgca_weight",
            labels={"dgca_weight": "Weight", "route": "Route"},
            color_discrete_sequence=[SAFFRON],
        )
        fig.update_yaxes(tickformat=".0%")
        fig = themed_layout(fig, "Route Weights (DGCA Traffic-Based)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="kpi-label" style="margin-top:8px;">Weight Table</div>',
                    unsafe_allow_html=True)
        st.dataframe(
            weights_df[["route", "dgca_weight"]].assign(
                dgca_weight=lambda d: (d["dgca_weight"] * 100).round(1).astype(str) + "%"
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.markdown(
            '<div class="kpi-sub" style="margin-top:10px;">Weights derived from '
            'DGCA\'s published city-pair passenger traffic data (most recent '
            'complete year). Source: DGCA, via github.com/Vonter/'
            'india-aviation-traffic (ODbL license).</div>',
            unsafe_allow_html=True,
        )

st.markdown(
    '<div class="footer-note">Data attribution: DGCA, Ministry of Civil Aviation · '
    'Google Flights (via SerpApi)</div>',
    unsafe_allow_html=True,
)
