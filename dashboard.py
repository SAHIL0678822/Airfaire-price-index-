"""
APIx — Real-Time Airfare Price Index
Modern light data-dashboard UI for Streamlit.

Run:
    streamlit run dashboard_modern.py

Keeps the existing APIx PostgreSQL data model and analytics, but redesigns
the interface as a professional, light-first data product:
- collapsible Streamlit sidebar for navigation + data information
- light glass / elevated cards with subtle 3D depth
- all major analytics visible on one structured page
- responsive columns
- no heavy dark/purple visual treatment
"""

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

DB_CONFIG = "dbname=apix user=postgres password=yourpassword host=localhost"

st.set_page_config(
    page_title="APIx — Airfare Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# LIGHT PROFESSIONAL DESIGN SYSTEM
# ---------------------------------------------------------------------------

BG = "#F6F8FB"
SURFACE = "#FFFFFF"
SURFACE_SOFT = "#F9FBFD"
BORDER = "#E3E8EF"
TEXT = "#172033"
TEXT_2 = "#4E5D73"
TEXT_3 = "#7B8798"

BLUE = "#1769E0"
BLUE_SOFT = "#EAF2FF"
TEAL = "#0B8F87"
TEAL_SOFT = "#E8F7F5"
GREEN = "#168447"
GREEN_SOFT = "#EAF7EF"
AMBER = "#B77900"
AMBER_SOFT = "#FFF5DD"
RED = "#D14343"
RED_SOFT = "#FDECEC"

SHADOW = "0 8px 28px rgba(30, 45, 70, 0.07)"
SHADOW_HOVER = "0 14px 35px rgba(30, 45, 70, 0.11)"

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');

:root {{
    --bg: {BG};
    --surface: {SURFACE};
    --border: {BORDER};
    --text: {TEXT};
    --text2: {TEXT_2};
    --text3: {TEXT_3};
    --blue: {BLUE};
}}

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
}}

.stApp {{
    background: {BG};
    color: {TEXT};
}}

.block-container {{
    max-width: 1440px;
    padding: 1.25rem 2rem 3rem 2rem;
}}

#MainMenu, footer {{
    visibility: hidden;
}}

header[data-testid="stHeader"] {{
    background: rgba(246, 248, 251, 0.88);
}}

h1, h2, h3 {{
    font-family: 'Manrope', sans-serif !important;
    color: {TEXT};
    letter-spacing: -0.02em;
}}

[data-testid="stSidebar"] {{
    background: #FFFFFF;
    border-right: 1px solid {BORDER};
}}

[data-testid="stSidebar"] > div:first-child {{
    padding-top: 1.2rem;
}}

[data-testid="stSidebar"] .stMarkdown {{
    color: {TEXT};
}}

.stButton > button {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    background: #FFFFFF;
    color: {TEXT};
    font-weight: 600;
}}

.stButton > button:hover {{
    border-color: #B8C7DB;
    color: {BLUE};
}}

div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {{
    border-radius: 10px !important;
    border-color: {BORDER} !important;
    background: #FFFFFF !important;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: transparent;
    border-bottom: 1px solid {BORDER};
}}

.stTabs [data-baseweb="tab"] {{
    color: {TEXT_2};
    font-weight: 600;
}}

.stTabs [aria-selected="true"] {{
    color: {BLUE} !important;
}}

[data-testid="stDataFrame"] {{
    border: 1px solid {BORDER};
    border-radius: 12px;
    overflow: hidden;
}}

div[data-testid="stMetric"] {{
    background: transparent;
}}

.app-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 18px;
    margin: 2px 0 18px 0;
}}

.brand {{
    display: flex;
    align-items: center;
    gap: 13px;
}}

.brand-mark {{
    width: 44px;
    height: 44px;
    border-radius: 13px;
    background: linear-gradient(145deg, #1F78FF, #1255C7);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 21px;
    box-shadow: 0 8px 18px rgba(23, 105, 224, .22);
}}

.brand-title {{
    font-family: 'Manrope', sans-serif;
    font-size: 1.34rem;
    font-weight: 800;
    color: {TEXT};
    line-height: 1.1;
}}

.brand-sub {{
    color: {TEXT_3};
    font-size: .78rem;
    margin-top: 3px;
}}

.status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 7px 11px;
    border-radius: 999px;
    background: {GREEN_SOFT};
    color: {GREEN};
    border: 1px solid #D5EBDD;
    font-size: .75rem;
    font-weight: 700;
}}

.status-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: {GREEN};
}}

.hero {{
    position: relative;
    overflow: hidden;
    background:
        radial-gradient(circle at 92% 12%, rgba(31,120,255,.13), transparent 31%),
        radial-gradient(circle at 12% 100%, rgba(11,143,135,.09), transparent 30%),
        #FFFFFF;
    border: 1px solid {BORDER};
    border-radius: 22px;
    padding: 30px 32px;
    box-shadow: {SHADOW};
    margin-bottom: 18px;
}}

.hero::after {{
    content: "";
    position: absolute;
    width: 260px;
    height: 260px;
    right: -100px;
    bottom: -150px;
    border-radius: 50%;
    border: 1px solid rgba(23,105,224,.10);
}}

.hero-kicker {{
    color: {BLUE};
    text-transform: uppercase;
    letter-spacing: .11em;
    font-size: .68rem;
    font-weight: 800;
    margin-bottom: 8px;
}}

.hero-title {{
    font-family: 'Manrope', sans-serif;
    font-size: 2.35rem;
    font-weight: 800;
    letter-spacing: -.045em;
    margin: 0;
    color: {TEXT};
}}

.hero-desc {{
    color: {TEXT_2};
    max-width: 760px;
    line-height: 1.55;
    margin-top: 8px;
    font-size: .92rem;
}}

.hero-mini {{
    display: flex;
    gap: 9px;
    flex-wrap: wrap;
    margin-top: 18px;
}}

.mini-chip {{
    padding: 6px 10px;
    border-radius: 8px;
    background: {SURFACE_SOFT};
    border: 1px solid {BORDER};
    color: {TEXT_2};
    font-size: .72rem;
    font-weight: 600;
}}

.section {{
    margin-top: 25px;
}}

.section-head {{
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 15px;
    margin-bottom: 11px;
}}

.section-title {{
    font-family: 'Manrope', sans-serif;
    font-size: 1.06rem;
    font-weight: 800;
    color: {TEXT};
}}

.section-caption {{
    color: {TEXT_3};
    font-size: .75rem;
    margin-top: 3px;
}}

.card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 16px;
    padding: 18px 19px;
    box-shadow: {SHADOW};
    transition: transform .18s ease, box-shadow .18s ease;
}}

.card:hover {{
    transform: translateY(-2px);
    box-shadow: {SHADOW_HOVER};
}}

.card-title {{
    font-size: .73rem;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: {TEXT_3};
    font-weight: 800;
}}

.card-value {{
    font-family: 'Manrope', sans-serif;
    font-size: 1.75rem;
    font-weight: 800;
    color: {TEXT};
    margin-top: 6px;
    letter-spacing: -.035em;
}}

.card-meta {{
    font-size: .72rem;
    color: {TEXT_2};
    margin-top: 4px;
}}

.metric-up {{
    color: {RED};
    font-weight: 700;
}}

.metric-down {{
    color: {GREEN};
    font-weight: 700;
}}

.metric-neutral {{
    color: {TEXT_2};
    font-weight: 700;
}}

.insight {{
    border-left: 4px solid {BLUE};
    background: {BLUE_SOFT};
    border-radius: 12px;
    padding: 15px 17px;
    color: {TEXT_2};
    line-height: 1.55;
    font-size: .84rem;
}}

.insight strong {{
    color: {TEXT};
}}

.side-brand {{
    display:flex;
    align-items:center;
    gap:10px;
    margin-bottom:22px;
}}

.side-logo {{
    width:35px;
    height:35px;
    border-radius:10px;
    background: linear-gradient(145deg, #1F78FF, #1255C7);
    color:#fff;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:800;
}}

.side-name {{
    font-family:'Manrope', sans-serif;
    font-weight:800;
    color:{TEXT};
}}

.side-label {{
    font-size:.67rem;
    color:{TEXT_3};
    text-transform:uppercase;
    letter-spacing:.1em;
    font-weight:800;
    margin:18px 0 7px;
}}

.info-box {{
    background: {SURFACE_SOFT};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 12px 13px;
    color: {TEXT_2};
    font-size: .74rem;
    line-height: 1.5;
}}

.legend {{
    display:flex;
    gap:12px;
    flex-wrap:wrap;
    margin-top:8px;
}}

.legend-item {{
    display:flex;
    align-items:center;
    gap:6px;
    font-size:.7rem;
    color:{TEXT_2};
}}

.legend-dot {{
    width:8px;
    height:8px;
    border-radius:50%;
}}

.footer {{
    border-top: 1px solid {BORDER};
    margin-top: 34px;
    padding-top: 14px;
    color: {TEXT_3};
    font-size: .7rem;
    text-align:center;
}}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def themed_layout(fig, title=None, height=None):
    fig.update_layout(
        title=dict(
            text=title or "",
            font=dict(family="Manrope, sans-serif", size=16, color=TEXT),
            x=0,
            xanchor="left",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(family="DM Sans, sans-serif", color=TEXT_2, size=12),
        xaxis=dict(
            gridcolor="#EEF1F5",
            zerolinecolor="#EEF1F5",
            linecolor="#E5EAF0",
        ),
        yaxis=dict(
            gridcolor="#EEF1F5",
            zerolinecolor="#EEF1F5",
            linecolor="#E5EAF0",
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,.85)",
            bordercolor=BORDER,
            borderwidth=1,
        ),
        margin=dict(t=55 if title else 25, l=15, r=15, b=35),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor=BORDER,
            font=dict(color=TEXT),
        ),
        height=height,
    )
    return fig


def safe_pct(value):
    try:
        return float(value)
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def load_data():
    conn = psycopg2.connect(DB_CONFIG)

    index_df = pd.read_sql(
        """
        SELECT index_date, index_value
        FROM daily_index
        WHERE frequency = 'daily' AND route_id IS NULL
        ORDER BY index_date;
        """,
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
        """
        SELECT origin, destination, dgca_weight
        FROM routes
        WHERE dgca_weight IS NOT NULL
        ORDER BY dgca_weight DESC;
        """,
        conn,
    )

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
            """
            SELECT index_date, confidence_score, expected_points,
                   actual_points, reason
            FROM index_confidence
            ORDER BY index_date;
            """,
            conn,
        )
    except Exception:
        confidence_df = pd.DataFrame()

    conn.close()
    return index_df, fares_df, weights_df, route_metrics_df, confidence_df


# ---------------------------------------------------------------------------
# SIDEBAR — MENU + IMPORTANT DATA INFORMATION
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="side-brand">
            <div class="side-logo">A</div>
            <div>
                <div class="side-name">APIx</div>
                <div style="font-size:.68rem;color:#7B8798;">Airfare Intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-label">Dashboard</div>', unsafe_allow_html=True)

    menu = st.radio(
        "Navigation",
        ["Overview", "Market Analytics", "Route Intelligence", "Methodology"],
        label_visibility="collapsed",
    )

    st.markdown('<div class="side-label">Data filters</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------

try:
    index_df, fares_df, weights_df, route_metrics_df, confidence_df = load_data()
except Exception as e:
    st.error("Could not connect to the APIx PostgreSQL database.")
    st.code(str(e))
    st.stop()

if fares_df.empty:
    st.warning(
        "No fare data yet. Run fetch_serpapi.py → clean_data.py → "
        "calculate_index.py first."
    )
    st.stop()

route_options = ["All routes"] + sorted(
    (fares_df["origin"] + "–" + fares_df["destination"]).dropna().unique().tolist()
)

with st.sidebar:
    selected_route = st.selectbox(
        "Route",
        route_options,
        help="Filter route-specific analytics.",
    )

    advance_options = sorted(
        fares_df["advance_purchase_days"].dropna().unique().tolist()
    )

    # "All days" acts like "All routes": when selected, every available
    # booking window is included in the analytics.
    booking_window_options = ["All days"] + advance_options
    selected_windows_ui = st.multiselect(
        "Booking windows",
        booking_window_options,
        default=["All days"],
        format_func=lambda x: (
            x if x == "All days" else f"T+{int(x)} days"
        ),
    )

    selected_windows = (
        advance_options
        if "All days" in selected_windows_ui or not selected_windows_ui
        else selected_windows_ui
    )

    st.markdown('<div class="side-label">System</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="info-box">
        <b>Source pipeline</b><br>
        Google Flights / SerpApi<br>
        Airline data where available<br>
        PostgreSQL analytics store<br><br>
        <b>Refresh</b><br>
        Cached for 5 minutes
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# FILTER DATA
# ---------------------------------------------------------------------------

if selected_route != "All routes":
    o, d = selected_route.split("–")
    filtered_fares = fares_df[
        (fares_df["origin"] == o) & (fares_df["destination"] == d)
    ].copy()
else:
    filtered_fares = fares_df.copy()

if selected_windows:
    filtered_fares = filtered_fares[
        filtered_fares["advance_purchase_days"].isin(selected_windows)
    ].copy()

# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------

latest_index = float(index_df.iloc[-1]["index_value"]) if not index_df.empty else 100.0
prev_index = (
    float(index_df.iloc[-2]["index_value"])
    if len(index_df) >= 2
    else latest_index
)
change_pct = ((latest_index - prev_index) / prev_index * 100) if prev_index else 0
change_sign = "+" if change_pct >= 0 else ""

days_tracked = len(index_df)
routes_tracked = fares_df[["origin", "destination"]].drop_duplicates().shape[0]
total_quotes = len(fares_df)

latest_confidence = None
if not confidence_df.empty:
    latest_confidence = safe_pct(confidence_df.iloc[-1]["confidence_score"])

st.markdown(
    f"""
    <div class="app-header">
        <div class="brand">
            <div class="brand-mark">✈</div>
            <div>
                <div class="brand-title">APIx · Airfare Intelligence</div>
                <div class="brand-sub">
                    Real-time Airfare Price Index · SIH26056 · MoSPI prototype
                </div>
            </div>
        </div>
        <div class="status-pill">
            <span class="status-dot"></span>
            Data pipeline active
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# HERO
# ---------------------------------------------------------------------------

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-kicker">National airfare price intelligence</div>
        <div class="hero-title">Real-Time Airfare Price Index</div>
        <div class="hero-desc">
            A DGCA-weighted, explainable view of domestic airfare movement,
            designed to make price changes measurable, comparable and easier
            to understand.
        </div>
        <div class="hero-mini">
            <span class="mini-chip">Base = 100</span>
            <span class="mini-chip">{routes_tracked} tracked routes</span>
            <span class="mini-chip">{total_quotes:,} clean fare observations</span>
            <span class="mini-chip">DGCA-weighted basket</span>
            <span class="mini-chip">Daily frequency</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# KPI STRIP
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="section-head">
        <div>
            <div class="section-title">Market snapshot</div>
            <div class="section-caption">Latest available APIx observations</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)

change_class = "metric-up" if change_pct > 0 else "metric-down" if change_pct < 0 else "metric-neutral"
confidence_text = f"{latest_confidence:.0f}%" if latest_confidence is not None else "—"

with k1:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">Current index</div>
            <div class="card-value">{latest_index:.1f}</div>
            <div class="card-meta">Base period = 100</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k2:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">Day-over-day</div>
            <div class="card-value">{change_sign}{change_pct:.1f}%</div>
            <div class="card-meta {change_class}">
                {'Upward movement' if change_pct > 0 else 'Downward movement' if change_pct < 0 else 'No change'}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k3:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">Data confidence</div>
            <div class="card-value">{confidence_text}</div>
            <div class="card-meta">Completeness of today's collection</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k4:
    st.markdown(
        f"""
        <div class="card">
            <div class="card-title">Coverage</div>
            <div class="card-value">{days_tracked}</div>
            <div class="card-meta">Days tracked since baseline</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# OVERVIEW
# ---------------------------------------------------------------------------

if menu == "Overview":
    st.markdown(
        """
        <div class="section">
            <div class="section-head">
                <div>
                    <div class="section-title">Index movement</div>
                    <div class="section-caption">
                        How the airfare index has changed over time
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_col, insight_col = st.columns([2.25, 1])

    with chart_col:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        if len(index_df) >= 2:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=index_df["index_date"],
                    y=index_df["index_value"],
                    mode="lines+markers",
                    name="APIx",
                    line=dict(color=BLUE, width=3),
                    marker=dict(size=6, color=BLUE),
                    fill="tozeroy",
                    fillcolor="rgba(23,105,224,.06)",
                    hovertemplate="Date: %{x}<br>Index: %{y:.2f}<extra></extra>",
                )
            )
            fig.add_hline(
                y=100,
                line_dash="dot",
                line_color="#9AA6B5",
                annotation_text="Base 100",
                annotation_position="top left",
            )
            fig = themed_layout(fig, "APIx over time", 420)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Collect more daily observations to build the index trend.")
            st.dataframe(index_df, use_container_width=True, hide_index=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with insight_col:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">Quick read</div>
                <div style="font-family:Manrope;font-size:1.15rem;font-weight:800;margin-top:8px;">
                    Index at {latest_index:.1f}
                </div>
                <div style="color:{TEXT_2};font-size:.82rem;line-height:1.6;margin-top:10px;">
                    The index is currently
                    <b>{'above' if latest_index > 100 else 'below' if latest_index < 100 else 'at'}</b>
                    the base-period level.
                </div>
                <div class="insight" style="margin-top:15px;">
                    <strong>Today's movement</strong><br>
                    {change_sign}{change_pct:.1f}% compared with the previous
                    available day.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if latest_confidence is not None:
            st.markdown(
                f"""
                <div class="card" style="margin-top:12px;">
                    <div class="card-title">Collection quality</div>
                    <div class="card-value">{latest_confidence:.0f}%</div>
                    <div class="card-meta">
                        Confidence in today's collected observations
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Fare heatmap
    st.markdown(
        """
        <div class="section">
            <div class="section-head">
                <div>
                    <div class="section-title">Fare landscape</div>
                    <div class="section-caption">
                        Average fare by route and booking window
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    hm_source = filtered_fares.copy()
    hm_source["route"] = hm_source["origin"] + "-" + hm_source["destination"]

    if not hm_source.empty:
        heatmap_data = (
            hm_source.groupby(["route", "advance_purchase_days"])["total_fare"]
            .mean()
            .reset_index()
            .pivot(
                index="route",
                columns="advance_purchase_days",
                values="total_fare",
            )
        )

        fig = go.Figure(
            data=go.Heatmap(
                z=heatmap_data.values,
                x=[f"T+{int(c)}" for c in heatmap_data.columns],
                y=heatmap_data.index,
                colorscale=[
                    [0, "#EEF5FF"],
                    [0.5, "#8BB5F1"],
                    [1, "#1769E0"],
                ],
                colorbar=dict(title="₹"),
                hovertemplate="Route: %{y}<br>%{x}<br>Average fare: ₹%{z:,.0f}<extra></extra>",
            )
        )
        fig = themed_layout(fig, "Average fare by route × booking window", 460)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# MARKET ANALYTICS
# ---------------------------------------------------------------------------

elif menu == "Market Analytics":
    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Market analytics</div>
                <div class="section-caption">
                    Booking-window behaviour and route-level fare patterns
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    source = fares_df.copy()
    source["route"] = source["origin"] + "-" + source["destination"]

    if selected_windows:
        source = source[source["advance_purchase_days"].isin(selected_windows)]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        elasticity_data = (
            source.groupby(["route", "advance_purchase_days"])["total_fare"]
            .mean()
            .reset_index()
        )

        if not elasticity_data.empty:
            fig = px.line(
                elasticity_data,
                x="advance_purchase_days",
                y="total_fare",
                color="route",
                markers=True,
                labels={
                    "advance_purchase_days": "Days before departure",
                    "total_fare": "Average fare (₹)",
                },
            )
            fig.update_xaxes(autorange="reversed")
            fig = themed_layout(fig, "Fare vs booking lead time", 430)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No fare observations for the selected filters.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        route_avg = (
            source.groupby("route")["total_fare"]
            .mean()
            .sort_values(ascending=False)
            .reset_index()
        )

        if not route_avg.empty:
            fig = px.bar(
                route_avg,
                x="route",
                y="total_fare",
                labels={"route": "Route", "total_fare": "Average fare (₹)"},
            )
            fig.update_traces(marker_color=BLUE)
            fig = themed_layout(fig, "Average fare by route", 430)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No route data for the selected filters.")

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="section">
            <div class="section-head">
                <div>
                    <div class="section-title">Route weights</div>
                    <div class="section-caption">
                        DGCA traffic-based importance used in the index basket
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    w1, w2 = st.columns([1.55, 1])

    with w1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if not weights_df.empty:
            w = weights_df.copy()
            w["route"] = w["origin"] + "-" + w["destination"]

            fig = px.bar(
                w.sort_values("dgca_weight"),
                x="dgca_weight",
                y="route",
                orientation="h",
                labels={"dgca_weight": "Weight", "route": "Route"},
            )
            fig.update_traces(marker_color=TEAL)
            fig.update_xaxes(tickformat=".0%")
            fig = themed_layout(fig, "DGCA traffic-based route weights", 430)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with w2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if not weights_df.empty:
            display_weights = weights_df.copy()
            display_weights["route"] = (
                display_weights["origin"] + "-" + display_weights["destination"]
            )
            display_weights["Weight"] = (
                display_weights["dgca_weight"] * 100
            ).round(1).astype(str) + "%"

            st.dataframe(
                display_weights[["route", "Weight"]],
                use_container_width=True,
                hide_index=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ROUTE INTELLIGENCE
# ---------------------------------------------------------------------------

elif menu == "Route Intelligence":
    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Route intelligence</div>
                <div class="section-caption">
                    Explain which routes are driving movement and how stable they are
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if route_metrics_df.empty:
        st.info(
            "No innovation-layer data yet. Run innovation_engine.py after "
            "the normal fetch → clean → calculate_index pipeline."
        )
    else:
        latest_date = route_metrics_df["metric_date"].max()
        latest_metrics = route_metrics_df[
            route_metrics_df["metric_date"] == latest_date
        ].copy()
        latest_metrics["route"] = (
            latest_metrics["origin"] + "-" + latest_metrics["destination"]
        )

        if selected_route != "All routes":
            latest_metrics = latest_metrics[
                latest_metrics["route"] == selected_route.replace("–", "-")
            ]

        contrib_ranked = latest_metrics.dropna(
            subset=["contribution_pct"]
        ).sort_values("contribution_pct", ascending=False)

        c1, c2 = st.columns([1.45, 1])

        with c1:
            st.markdown('<div class="card">', unsafe_allow_html=True)

            if not contrib_ranked.empty:
                top = contrib_ranked.iloc[0]

                st.markdown(
                    f"""
                    <div class="card-title">Explainability signal</div>
                    <div style="font-family:Manrope;font-size:1.25rem;font-weight:800;margin-top:7px;">
                        {top['route']} is the leading contributor
                    </div>
                    <div style="font-size:.82rem;color:{TEXT_2};margin-top:7px;">
                        Contribution to the latest measured movement:
                        <b>{top['contribution_pct']:.1f}%</b>
                    </div>
                    <div class="insight" style="margin-top:14px;">
                        APIx does not only report that the index moved.
                        The innovation layer helps identify which routes
                        contributed to that movement.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                fig = px.bar(
                    contrib_ranked,
                    x="contribution_pct",
                    y="route",
                    orientation="h",
                    labels={
                        "contribution_pct": "Contribution %",
                        "route": "Route",
                    },
                )
                fig.update_traces(marker_color=BLUE)
                fig.update_yaxes(categoryorder="total ascending")
                fig = themed_layout(fig, "Route contribution — latest day", 360)
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.info("Contribution analysis needs sufficient daily history.")

            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(
                '<div class="card-title">Route health</div>',
                unsafe_allow_html=True,
            )

            health_display = latest_metrics.dropna(
                subset=["health_score"]
            ).sort_values("health_score", ascending=False)

            if health_display.empty:
                st.info("Health scores need sufficient historical data.")
            else:
                for _, row in health_display.iterrows():
                    score = float(row["health_score"])
                    label = row.get("volatility_label", "N/A")

                    if label == "Stable":
                        bg, fg = GREEN_SOFT, GREEN
                    elif label == "Moderately Volatile":
                        bg, fg = AMBER_SOFT, AMBER
                    elif label in ("Highly Volatile", "Extreme"):
                        bg, fg = RED_SOFT, RED
                    else:
                        bg, fg = "#F0F2F5", TEXT_2

                    st.markdown(
                        f"""
                        <div style="
                            display:flex;
                            justify-content:space-between;
                            align-items:center;
                            padding:12px 0;
                            border-bottom:1px solid {BORDER};
                        ">
                            <div>
                                <b style="font-size:.84rem;">{row['route']}</b>
                                <div style="font-size:.7rem;color:{TEXT_3};margin-top:2px;">
                                    Health score {score:.0f}/100
                                </div>
                            </div>
                            <span style="
                                padding:5px 9px;
                                border-radius:999px;
                                background:{bg};
                                color:{fg};
                                font-size:.66rem;
                                font-weight:800;
                            ">{label}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown("</div>", unsafe_allow_html=True)

        # Confidence trend
        st.markdown(
            """
            <div class="section">
                <div class="section-head">
                    <div>
                        <div class="section-title">Data confidence</div>
                        <div class="section-caption">
                            Collection completeness over time
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="card">', unsafe_allow_html=True)

        if not confidence_df.empty:
            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=confidence_df["index_date"],
                    y=confidence_df["confidence_score"],
                    mode="lines+markers",
                    line=dict(color=TEAL, width=3),
                    marker=dict(size=6, color=TEAL),
                    fill="tozeroy",
                    fillcolor="rgba(11,143,135,.06)",
                    hovertemplate="Date: %{x}<br>Confidence: %{y:.1f}%<extra></extra>",
                )
            )
            fig.update_yaxes(range=[0, 105], ticksuffix="%")
            fig = themed_layout(fig, "Collection confidence over time", 370)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No confidence data available yet.")

        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# METHODOLOGY
# ---------------------------------------------------------------------------

else:
    st.markdown(
        """
        <div class="section-head">
            <div>
                <div class="section-title">Methodology & data dictionary</div>
                <div class="section-caption">
                    Understand how the dashboard's main indicators are constructed
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    m1, m2 = st.columns(2)

    with m1:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">1 · Collection</div>
                <div style="margin-top:8px;color:{TEXT_2};font-size:.84rem;line-height:1.65;">
                    Fare observations are collected across selected domestic
                    routes and booking lead-time windows. The pipeline stores
                    cleaned fare observations for subsequent index calculation.
                </div>
            </div>

            <div class="card" style="margin-top:12px;">
                <div class="card-title">2 · Cleaning</div>
                <div style="margin-top:8px;color:{TEXT_2};font-size:.84rem;line-height:1.65;">
                    Outlier observations are excluded before the dashboard
                    analytics are calculated. This reduces the impact of
                    abnormal fare observations on the index.
                </div>
            </div>

            <div class="card" style="margin-top:12px;">
                <div class="card-title">3 · Route weighting</div>
                <div style="margin-top:8px;color:{TEXT_2};font-size:.84rem;line-height:1.65;">
                    Routes receive DGCA passenger-traffic-based weights so
                    higher-volume city pairs have proportionally greater
                    influence on the aggregate index.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">4 · Index</div>
                <div style="margin-top:8px;color:{TEXT_2};font-size:.84rem;line-height:1.65;">
                    APIx is presented as a base-100 index. A value of 100
                    represents the selected base-period level; movements away
                    from 100 indicate relative fare movement.
                </div>
            </div>

            <div class="card" style="margin-top:12px;">
                <div class="card-title">5 · Explainability</div>
                <div style="margin-top:8px;color:{TEXT_2};font-size:.84rem;line-height:1.65;">
                    The innovation layer surfaces route contribution,
                    route health / volatility and collection confidence,
                    making the aggregate number easier to interpret.
                </div>
            </div>

            <div class="card" style="margin-top:12px;">
                <div class="card-title">6 · Dashboard</div>
                <div style="margin-top:8px;color:{TEXT_2};font-size:.84rem;line-height:1.65;">
                    Streamlit provides the application layer, Plotly provides
                    interactive analytics, and PostgreSQL stores the underlying
                    observations and calculated metrics.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="section">
            <div class="section-head">
                <div>
                    <div class="section-title">Current data coverage</div>
                    <div class="section-caption">
                        Live values from the APIx database
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)

    coverage = pd.DataFrame(
        {
            "Indicator": [
                "Index observations",
                "Clean fare observations",
                "Tracked routes",
                "Booking windows",
                "Confidence observations",
            ],
            "Value": [
                len(index_df),
                len(fares_df),
                routes_tracked,
                fares_df["advance_purchase_days"].nunique(),
                len(confidence_df),
            ],
        }
    )

    st.dataframe(coverage, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------

st.markdown(
    """
    <div class="footer">
        APIx · Adaptive Airfare Intelligence Platform · Prototype for SIH 2026
        <br>
        Data attribution: DGCA · Google Flights via SerpApi · PostgreSQL analytics
    </div>
    """,
    unsafe_allow_html=True,
)
