"""
APIx Dashboard -- run with: streamlit run dashboard.py

Visual identity: clean, official light theme in the spirit of Digital India /
government portals -- white background, navy-blue headings, saffron and
green accents (tricolor-inspired), card-based layout with a subtle gradient
header band and icon-led KPI tiles.
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
BG = "#F5F7FB"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#E4E9F1"
NAVY = "#0B3D91"
NAVY_DEEP = "#082B69"
SAFFRON = "#FF9933"
GREEN = "#128807"
TEXT = "#1A2B45"
TEXT_MUTED = "#6B7A90"
RED = "#C0392B"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.stApp {{
    background-color: {BG};
    color: {TEXT};
}}

#MainMenu, footer, header {{ visibility: hidden; }}

/* Header band */
.apix-header {{
    background: linear-gradient(120deg, {NAVY_DEEP} 0%, {NAVY} 55%, #1A56C4 100%);
    border-radius: 14px;
    padding: 26px 32px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 6px 18px rgba(11, 61, 145, 0.18);
    position: relative;
    overflow: hidden;
}}
.apix-header::after {{
    content: "";
    position: absolute;
    top: 0; right: 0; bottom: 0;
    width: 6px;
    background: linear-gradient(180deg, {SAFFRON} 0%, #FFFFFF 50%, {GREEN} 100%);
}}
.apix-title {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    font-size: 2.1rem;
    color: #FFFFFF;
    margin: 0;
    letter-spacing: 0.5px;
}}
.apix-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 0.85rem;
    color: #D7E2F7;
    margin: 4px 0 0 0;
}}
.apix-badge {{
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.25);
    color: #FFFFFF;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 6px 14px;
    border-radius: 20px;
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
    border-radius: 12px;
    padding: 18px 22px;
    flex: 1;
    min-width: 175px;
    box-shadow: 0 2px 10px rgba(11, 61, 145, 0.06);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    position: relative;
}}
.kpi-tile:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(11, 61, 145, 0.12);
}}
.kpi-tile::before {{
    content: "";
    position: absolute;
    left: 0; top: 14px; bottom: 14px;
    width: 4px;
    border-radius: 4px;
    background-color: {NAVY};
}}
.kpi-tile.saffron::before {{ background-color: {SAFFRON}; }}
.kpi-tile.green::before {{ background-color: {GREEN}; }}
.kpi-icon {{
    font-size: 1.1rem;
    margin-bottom: 6px;
    display: block;
}}
.kpi-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.7rem;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: {TEXT_MUTED};
    margin-bottom: 6px;
    padding-left: 8px;
}}
.kpi-value {{
    font-family: 'Poppins', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: {NAVY};
    padding-left: 8px;
}}
.kpi-value.green {{ color: {GREEN}; }}
.kpi-value.red {{ color: {RED}; }}
.kpi-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: {TEXT_MUTED};
    margin-top: 2px;
    padding-left: 8px;
}}

/* Section labels */
.section-label {{
    font-family: 'Inter', sans-serif;
    font-size: 0.72rem;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {NAVY};
    font-weight: 700;
    margin: 4px 0 10px 0;
    border-left: 3px solid {SAFFRON};
    padding-left: 8px;
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
    border-radius: 10px;
    overflow: hidden;
}}

/* Volatility badges */
.badge {{
    display: inline-block;
    padding: 3px 12px;
    border-radius: 14px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.3px;
    white-space: nowrap;
}}
.badge-stable {{ background-color: #E6F4EA; color: {GREEN}; }}
.badge-moderate {{ background-color: #FFF3E0; color: #B36B00; }}
.badge-high {{ background-color: #FDEDEB; color: {RED}; }}
.badge-extreme {{ background-color: #FBE2E1; color: #8B0000; }}
.badge-na {{ background-color: #EEF0F3; color: {TEXT_MUTED}; }}

.route-card {{
    display:flex; justify-content:space-between; align-items:center;
    padding:12px 16px; border:1px solid {CARD_BORDER}; border-radius:10px;
    margin-bottom:8px; background-color:{CARD_BG};
    box-shadow: 0 1px 4px rgba(11,61,145,0.04);
}}

.explain-box {{
    background: linear-gradient(135deg, #FFF8F0 0%, #FFFFFF 60%);
    border: 1px solid {CARD_BORDER};
    border-left: 4px solid {SAFFRON};
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 22px;
    font-size: 0.95rem;
    line-height: 1.65;
}}

.footer-note {{
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: {TEXT_MUTED};
    border-top: 1px solid {CARD_BORDER};
    padding-top: 14px;
    margin-top: 40px;
    text-align: center;
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


def badge_html(label):
    label = label or "N/A"
    cls_map = {
        "Stable": "badge-stable",
        "Moderately Volatile": "badge-moderate",
        "Highly Volatile": "badge-high",
        "Extreme": "badge-extreme",
    }
    cls = cls_map.get(label, "badge-na")
    return f'<span class="badge {cls}">{label}</span>'


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

    # --- Innovation layer tables (safe to be missing on first run) ---
    try:
        route_metrics_df = pd.read_sql(
            """
            SELECT rm.metric_date, r.origin, r.destination, rm.avg_fare,
                   rm.contribution_pct, rm.health_score, rm.volatility_label
            FROM route_metrics rm
            JOIN routes r ON rm.route_id = r.route_id
            ORDER BY rm.metric_date DESC;
            """,
            conn,
        )
    except Exception:
        route_metrics_df = pd.DataFrame()

    try:
        confidence_df = pd.read_sql(
            "SELECT index_date, confidence_score, expected_points, actual_points, reason "
            "FROM index_confidence ORDER BY index_date;",
            conn,
        )
    except Exception:
        confidence_df = pd.DataFrame()

    conn.close()
    return index_df, fares_df, weights_df, route_metrics_df, confidence_df


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="apix-header">
    <div>
        <div class="apix-title">✈ APIx</div>
        <div class="apix-subtitle">Real-Time Airfare Price Index — SIH26056 · Ministry of Statistics &amp; Programme Implementation</div>
    </div>
    <div class="apix-badge">Live Prototype</div>
</div>
""", unsafe_allow_html=True)

index_df, fares_df, weights_df, route_metrics_df, confidence_df = load_data()

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

latest_confidence = None
if not confidence_df.empty:
    latest_confidence = confidence_df.iloc[-1]["confidence_score"]

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-tile">
        <span class="kpi-icon">📊</span>
        <div class="kpi-label">Current Index</div>
        <div class="kpi-value">{latest_index:.1f}</div>
        <div class="kpi-sub">Base period = 100</div>
    </div>
    <div class="kpi-tile saffron">
        <span class="kpi-icon">📈</span>
        <div class="kpi-label">Day-over-day</div>
        <div class="kpi-value {change_class}">{change_sign}{change_pct:.1f}%</div>
        <div class="kpi-sub">vs. previous day</div>
    </div>
    <div class="kpi-tile green">
        <span class="kpi-icon">🗓️</span>
        <div class="kpi-label">Days Tracked</div>
        <div class="kpi-value green">{days_tracked}</div>
        <div class="kpi-sub">since baseline</div>
    </div>
    <div class="kpi-tile">
        <span class="kpi-icon">🧾</span>
        <div class="kpi-label">Clean Fare Quotes</div>
        <div class="kpi-value">{total_quotes:,}</div>
        <div class="kpi-sub">across {routes_tracked} routes</div>
    </div>
    {f'''<div class="kpi-tile saffron">
        <span class="kpi-icon">✅</span>
        <div class="kpi-label">Data Confidence</div>
        <div class="kpi-value">{latest_confidence:.0f}%</div>
        <div class="kpi-sub">today's collection completeness</div>
    </div>''' if latest_confidence is not None else ""}
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TABS
# ---------------------------------------------------------------------------
tab_trend, tab_heatmap, tab_elasticity, tab_weights, tab_insights = st.tabs(
    ["📈 Trend", "🔥 Heatmap", "⏱ Elasticity", "⚖️ Weights", "🧠 Insights"]
)

with tab_trend:
    if len(index_df) >= 2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=index_df["index_date"], y=index_df["index_value"],
            mode="lines+markers",
            line=dict(color=NAVY, width=2.5),
            marker=dict(size=7, color=SAFFRON),
            fill="tozeroy",
            fillcolor="rgba(11, 61, 145, 0.05)",
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

with tab_insights:
    if route_metrics_df.empty:
        st.info(
            "No innovation-layer data yet. Run innovation_engine.py after your "
            "usual fetch → clean → calculate_index steps to populate this tab."
        )
    else:
        latest_date = route_metrics_df["metric_date"].max()
        latest_metrics = route_metrics_df[route_metrics_df["metric_date"] == latest_date].copy()
        latest_metrics["route"] = latest_metrics["origin"] + "-" + latest_metrics["destination"]

        contrib_ranked = latest_metrics.dropna(subset=["contribution_pct"]).sort_values(
            "contribution_pct", ascending=False
        )
        conf_row = confidence_df[confidence_df["index_date"] == latest_date] if not confidence_df.empty else pd.DataFrame()

        if not contrib_ranked.empty:
            top = contrib_ranked.iloc[0]
            summary_lines = [
                f"<b>🧠 Why did the index move on {latest_date}?</b><br>",
                f"Top contributor: <b>{top['route']}</b> "
                f"({top['contribution_pct']:.1f}% of today's movement).",
            ]
            if not conf_row.empty:
                c = conf_row.iloc[0]
                summary_lines.append(
                    f"<br>Data confidence: <b>{c['confidence_score']:.0f}%</b> "
                    f"({int(c['actual_points'])}/{int(c['expected_points'])} expected data points collected)."
                )
            st.markdown(f'<div class="explain-box">{"".join(summary_lines)}</div>',
                        unsafe_allow_html=True)
        else:
            st.info("Contribution analysis needs at least 2 days of collected data to compare against.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="section-label">Contribution to Today\'s Index Change</div>',
                        unsafe_allow_html=True)
            if not contrib_ranked.empty:
                fig = px.bar(
                    contrib_ranked, x="contribution_pct", y="route", orientation="h",
                    labels={"contribution_pct": "Contribution %", "route": "Route"},
                    color_discrete_sequence=[SAFFRON],
                )
                fig.update_yaxes(categoryorder="total ascending")
                fig = themed_layout(fig, "Route Contribution — Latest Day")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("Not enough data yet.")

        with col2:
            st.markdown('<div class="section-label">Route Health Scores</div>',
                        unsafe_allow_html=True)
            health_display = latest_metrics.dropna(subset=["health_score"]).sort_values(
                "health_score", ascending=False
            )
            for _, row in health_display.iterrows():
                st.markdown(
                    f"""
                    <div class="route-card">
                        <div>
                            <b>{row['route']}</b><br>
                            <span style="font-size:0.8rem; color:{TEXT_MUTED};">
                                Health Score: {row['health_score']:.0f}/100
                            </span>
                        </div>
                        {badge_html(row['volatility_label'])}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            if health_display.empty:
                st.write("Health scores need at least 2 days of data per route.")

        st.markdown('<div class="section-label" style="margin-top:20px;">Confidence Trend</div>',
                    unsafe_allow_html=True)
        if not confidence_df.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=confidence_df["index_date"], y=confidence_df["confidence_score"],
                mode="lines+markers",
                line=dict(color=GREEN, width=2.5),
                marker=dict(size=7, color=NAVY),
                fill="tozeroy",
                fillcolor="rgba(18, 136, 7, 0.06)",
            ))
            fig.update_yaxes(range=[0, 105])
            fig = themed_layout(fig, "Data Collection Confidence Over Time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No confidence data yet.")

st.markdown(
    '<div class="footer-note">Data attribution: DGCA, Ministry of Civil Aviation · '
    'Google Flights (via SerpApi) · Prototype for SIH 2026</div>',
    unsafe_allow_html=True,
)
