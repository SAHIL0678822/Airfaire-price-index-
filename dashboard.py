"""
APIx Dashboard -- run with: streamlit run dashboard.py

Visual identity: modeled directly on the actual MoSPI (mospi.gov.in) website --
dark navy hero band with glowing radial background and orange stat callouts,
a floating white search/lookup card overlapping the hero, chip-style quick
filters, and light blue-gray card sections for content (matching MoSPI's
"Offerings" / "Themes" section pattern).
"""

import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go

DB_CONFIG = "dbname=apix user=postgres password=yourpassword host=localhost"

st.set_page_config(page_title="APIx - Airfare Price Index", layout="wide", page_icon="✈️")

# ---------------------------------------------------------------------------
# THEME -- tokens pulled from the real MoSPI site
# ---------------------------------------------------------------------------
PAGE_BG = "#EDF1F7"          # light blue-gray section background (Themes/Offerings)
CARD_BG = "#FFFFFF"
CARD_BORDER = "#DCE3ED"
NAVY_DARK = "#0A2647"        # deep hero navy
NAVY = "#0F3D73"
NAVY_MID = "#144D8F"
ORANGE = "#F5A300"           # stat-number orange
SAFFRON = "#FF9933"
GREEN = "#128807"
TEXT = "#1A2B45"
TEXT_MUTED = "#5C6B80"
RED = "#C0392B"
CHIP_BG = "#E4ECF7"
CHIP_TEXT = "#0F3D73"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}
.stApp {{
    background-color: {PAGE_BG};
    color: {TEXT};
}}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 1.2rem; max-width: 1200px; }}

/* ---------- Top utility strip (mimics GOI masthead) ---------- */
.gov-strip {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 4px 10px 4px;
    border-bottom: 1px solid {CARD_BORDER};
    margin-bottom: 0;
    font-size: 0.72rem;
    color: {TEXT_MUTED};
}}
.gov-strip .left {{ display:flex; align-items:center; gap:8px; }}
.gov-emblem {{
    width: 30px; height: 30px; border-radius: 50%;
    background: linear-gradient(135deg, {NAVY} 0%, {NAVY_MID} 100%);
    display:flex; align-items:center; justify-content:center;
    color:#fff; font-size:0.85rem; font-weight:700;
}}
.gov-strip .ministry-name {{
    font-weight: 700; color: {NAVY_DARK}; font-size: 0.82rem; line-height:1.2;
}}
.gov-strip .ministry-sub {{ font-size: 0.68rem; color: {TEXT_MUTED}; }}
.gov-badges {{ display:flex; gap:14px; font-size: 0.95rem; color:{NAVY}; }}

/* ---------- Ticker ---------- */
.ticker-bar {{
    background: {NAVY};
    color: #fff;
    padding: 7px 16px;
    font-size: 0.78rem;
    border-radius: 4px;
    margin: 10px 0 0 0;
    display:flex; align-items:center; gap:10px;
    overflow:hidden;
    white-space:nowrap;
}}
.ticker-label {{
    background: {ORANGE};
    color: {NAVY_DARK};
    font-weight: 800;
    font-size: 0.66rem;
    letter-spacing: 0.6px;
    padding: 3px 9px;
    border-radius: 3px;
    flex-shrink: 0;
}}
.ticker-text {{ font-size: 0.78rem; opacity: 0.95; }}

/* ---------- Hero band ---------- */
.hero {{
    background:
        radial-gradient(circle at 15% 30%, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0) 45%),
        radial-gradient(circle at 85% 70%, rgba(245,163,0,0.10) 0%, rgba(245,163,0,0) 50%),
        linear-gradient(120deg, {NAVY_DARK} 0%, {NAVY} 55%, {NAVY_MID} 100%);
    border-radius: 16px;
    padding: 40px 40px 76px 40px;
    margin-top: 14px;
    position: relative;
    overflow: hidden;
}}
.hero-title {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    font-size: 2.3rem;
    color: #FFFFFF;
    margin: 0 0 6px 0;
    text-align: center;
}}
.hero-subtitle {{
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    color: #C9D8EE;
    text-align: center;
    margin: 0 0 34px 0;
}}
.hero-stats {{
    display: flex;
    justify-content: center;
    gap: 60px;
    flex-wrap: wrap;
}}
.hero-stat {{ text-align: center; min-width: 140px; }}
.hero-stat-icon {{ font-size: 1.4rem; margin-bottom: 6px; opacity: 0.9; }}
.hero-stat-value {{
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    font-size: 1.9rem;
    color: {ORANGE};
    line-height: 1.1;
}}
.hero-stat-value.red {{ color: #FF7A6E; }}
.hero-stat-value.green {{ color: #6FE39B; }}
.hero-stat-label {{
    font-size: 0.76rem;
    color: #DCE6F5;
    margin-top: 4px;
    line-height: 1.3;
}}

/* ---------- Floating lookup card ---------- */
.lookup-card {{
    background: {CARD_BG};
    border-radius: 14px;
    box-shadow: 0 10px 30px rgba(10, 38, 71, 0.18);
    padding: 20px 26px;
    margin: -52px 24px 26px 24px;
    position: relative;
    z-index: 5;
}}
.lookup-label {{
    font-size: 0.78rem;
    font-weight: 700;
    color: {TEXT_MUTED};
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.chip-row {{ display:flex; flex-wrap:wrap; gap:8px; margin-top: 12px; }}
.chip {{
    background: {CHIP_BG};
    color: {CHIP_TEXT};
    font-size: 0.78rem;
    font-weight: 600;
    padding: 6px 14px;
    border-radius: 20px;
    white-space: nowrap;
}}

/* ---------- Section headers (mimics "Themes" / "What's New") ---------- */
.section-block {{ margin-top: 8px; margin-bottom: 30px; }}
.section-head {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
}}
.section-head .icon {{
    font-size: 1.2rem;
    color: {NAVY};
}}
.section-head .label {{
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 1.15rem;
    color: {NAVY_DARK};
}}

/* ---------- Card panel ---------- */
.panel {{
    background: {CARD_BG};
    border: 1px solid {CARD_BORDER};
    border-radius: 14px;
    padding: 20px 22px;
    box-shadow: 0 2px 8px rgba(10,38,71,0.05);
}}

/* ---------- Tabs styled as nav pills ---------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
    border-bottom: none;
    background: {CARD_BG};
    padding: 6px;
    border-radius: 30px;
    border: 1px solid {CARD_BORDER};
    display: inline-flex;
}}
.stTabs [data-baseweb="tab"] {{
    background-color: transparent;
    color: {TEXT_MUTED};
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 8px 18px;
    border-radius: 24px;
}}
.stTabs [aria-selected="true"] {{
    color: #FFFFFF !important;
    background: {NAVY} !important;
}}

/* ---------- Dataframes ---------- */
[data-testid="stDataFrame"] {{
    border: 1px solid {CARD_BORDER};
    border-radius: 10px;
    overflow: hidden;
}}

/* ---------- Badges / route health cards ---------- */
.badge {{
    display: inline-block;
    padding: 3px 12px;
    border-radius: 14px;
    font-size: 0.72rem;
    font-weight: 700;
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
}}

.explain-box {{
    background: linear-gradient(135deg, #FFF6E8 0%, #FFFFFF 65%);
    border: 1px solid {CARD_BORDER};
    border-left: 4px solid {ORANGE};
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
    margin-top: 30px;
    text-align: center;
}}
</style>
""", unsafe_allow_html=True)


def themed_layout(fig, title):
    fig.update_layout(
        title=title,
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font=dict(family="Inter, sans-serif", color=TEXT, size=13),
        title_font=dict(family="Poppins, sans-serif", color=NAVY_DARK, size=16),
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
# TOP UTILITY STRIP (mimics GOI masthead)
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="gov-strip">
    <div class="left">
        <div class="gov-emblem">GoI</div>
        <div>
            <div class="ministry-name">Ministry of Statistics and Programme Implementation</div>
            <div class="ministry-sub">Prototype built for SIH26056 &middot; National Statistics Office</div>
        </div>
    </div>
    <div class="gov-badges">🔍 &nbsp; 🌐 &nbsp; ♿</div>
</div>
""", unsafe_allow_html=True)

index_df, fares_df, weights_df, route_metrics_df, confidence_df = load_data()

if fares_df.empty:
    st.warning("No data yet — run fetch_serpapi.py, clean_data.py, and calculate_index.py first.")
    st.stop()

# ---------------------------------------------------------------------------
# TICKER
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
<div class="ticker-bar">
    <span class="ticker-label">LIVE</span>
    <span class="ticker-text">
        Today's APIx: {latest_index:.1f} ({change_sign}{change_pct:.1f}% vs. previous day)
        &nbsp;•&nbsp; Tracking {routes_tracked} DGCA-weighted routes
        &nbsp;•&nbsp; {total_quotes:,} clean fare quotes collected
    </span>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# HERO BAND with stat callouts (mirrors MoSPI homepage stat grid)
# ---------------------------------------------------------------------------
confidence_stat_html = f"""
<div class="hero-stat">
    <div class="hero-stat-icon">✅</div>
    <div class="hero-stat-value">{latest_confidence:.0f}%</div>
    <div class="hero-stat-label">Data Confidence<br/>(today's collection)</div>
</div>
""" if latest_confidence is not None else ""

st.markdown(f"""
<div class="hero">
    <div class="hero-title">Real-Time Airfare Price Index</div>
    <div class="hero-subtitle">SIH26056 &middot; A DGCA-weighted, explainable index prototype for MoSPI</div>
    <div class="hero-stats">
        <div class="hero-stat">
            <div class="hero-stat-icon">📊</div>
            <div class="hero-stat-value">{latest_index:.1f}</div>
            <div class="hero-stat-label">Current Index<br/>(Base = 100)</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-icon">📈</div>
            <div class="hero-stat-value {change_class}">{change_sign}{change_pct:.1f}%</div>
            <div class="hero-stat-label">Day-over-day<br/>change</div>
        </div>
        <div class="hero-stat">
            <div class="hero-stat-icon">🗓️</div>
            <div class="hero-stat-value">{days_tracked}</div>
            <div class="hero-stat-label">Days Tracked<br/>since baseline</div>
        </div>
        {confidence_stat_html}
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# FLOATING LOOKUP CARD (mirrors MoSPI's floating search card)
# ---------------------------------------------------------------------------
route_options = ["All routes"] + sorted(
    (fares_df["origin"] + "–" + fares_df["destination"]).unique().tolist()
)
chip_html = "".join(
    f'<span class="chip">{r}</span>'
    for r in sorted((fares_df["origin"] + "-" + fares_df["destination"]).unique().tolist())
)

st.markdown('<div class="lookup-card">', unsafe_allow_html=True)
st.markdown('<div class="lookup-label">Quick Route Lookup</div>', unsafe_allow_html=True)
selected_route = st.selectbox(
    "Select a route to filter the views below",
    route_options,
    label_visibility="collapsed",
)
st.markdown(f'<div class="chip-row">{chip_html}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# Apply route filter where relevant
if selected_route != "All routes":
    o, d = selected_route.split("–")
    filtered_fares = fares_df[(fares_df["origin"] == o) & (fares_df["destination"] == d)]
else:
    filtered_fares = fares_df

# ---------------------------------------------------------------------------
# TABS (styled as nav pills)
# ---------------------------------------------------------------------------
tab_trend, tab_heatmap, tab_elasticity, tab_weights, tab_insights = st.tabs(
    ["Trend", "Heatmap", "Elasticity", "Weights", "Insights"]
)

with tab_trend:
    st.markdown('<div class="section-block">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><span class="icon">📈</span>'
                '<span class="label">Index Trend</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    if len(index_df) >= 2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=index_df["index_date"], y=index_df["index_value"],
            mode="lines+markers",
            line=dict(color=NAVY, width=2.5),
            marker=dict(size=7, color=ORANGE),
            fill="tozeroy",
            fillcolor="rgba(15, 61, 115, 0.06)",
        ))
        fig.add_hline(y=100, line_dash="dash", line_color=TEXT_MUTED,
                      annotation_text="Base", annotation_font_color=TEXT_MUTED)
        fig = themed_layout(fig, "APIx Over Time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"Only {len(index_df)} day(s) of index data so far. The trend line "
                "becomes meaningful as you collect more days.")
        st.dataframe(index_df, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

with tab_heatmap:
    st.markdown('<div class="section-block">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><span class="icon">🔥</span>'
                '<span class="label">Fare Heatmap</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)

    hm_source = filtered_fares if selected_route == "All routes" else fares_df
    route_label = hm_source["origin"] + "-" + hm_source["destination"]
    hm_source = hm_source.assign(route=route_label)

    heatmap_data = (
        hm_source.groupby(["route", "advance_purchase_days"])["total_fare"]
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
        colorscale=[[0, "#EAF1FB"], [0.5, "#8FB8E8"], [1, NAVY_DARK]],
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
    st.markdown('</div></div>', unsafe_allow_html=True)

with tab_elasticity:
    st.markdown('<div class="section-block">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><span class="icon">⏱</span>'
                '<span class="label">Fare Elasticity</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)

    el_source = fares_df.assign(route=fares_df["origin"] + "-" + fares_df["destination"])
    elasticity_data = (
        el_source.groupby(["route", "advance_purchase_days"])["total_fare"]
        .mean()
        .reset_index()
    )

    palette = [NAVY, ORANGE, GREEN, "#8B5CF6", "#C0392B", "#0EA5A5"]
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
    st.markdown('</div></div>', unsafe_allow_html=True)

with tab_weights:
    st.markdown('<div class="section-block">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><span class="icon">⚖️</span>'
                '<span class="label">DGCA Route Weights</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)

    col1, col2 = st.columns([1.3, 1])
    with col1:
        weights_df["route"] = weights_df["origin"] + "-" + weights_df["destination"]
        fig = px.bar(
            weights_df, x="route", y="dgca_weight",
            labels={"dgca_weight": "Weight", "route": "Route"},
            color_discrete_sequence=[ORANGE],
        )
        fig.update_yaxes(tickformat=".0%")
        fig = themed_layout(fig, "Route Weights (DGCA Traffic-Based)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="lookup-label">Weight Table</div>', unsafe_allow_html=True)
        st.dataframe(
            weights_df[["route", "dgca_weight"]].assign(
                dgca_weight=lambda d: (d["dgca_weight"] * 100).round(1).astype(str) + "%"
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Weights derived from DGCA's published city-pair passenger traffic "
            "data (most recent complete year). Source: DGCA, via github.com/"
            "Vonter/india-aviation-traffic (ODbL license)."
        )
    st.markdown('</div></div>', unsafe_allow_html=True)

with tab_insights:
    st.markdown('<div class="section-block">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><span class="icon">🧠</span>'
                '<span class="label">Explainable Index — Insights</span></div>',
                unsafe_allow_html=True)

    if route_metrics_df.empty:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.info("No innovation-layer data yet. Run innovation_engine.py after "
                "your usual fetch → clean → calculate_index steps.")
        st.markdown('</div>', unsafe_allow_html=True)
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
            st.info("Contribution analysis needs at least 2 days of collected data.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="lookup-label">Contribution to Today\'s Change</div>',
                        unsafe_allow_html=True)
            if not contrib_ranked.empty:
                fig = px.bar(
                    contrib_ranked, x="contribution_pct", y="route", orientation="h",
                    labels={"contribution_pct": "Contribution %", "route": "Route"},
                    color_discrete_sequence=[ORANGE],
                )
                fig.update_yaxes(categoryorder="total ascending")
                fig = themed_layout(fig, "Route Contribution — Latest Day")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("Not enough data yet.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown('<div class="lookup-label">Route Health Scores</div>',
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
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel" style="margin-top:16px;">', unsafe_allow_html=True)
        st.markdown('<div class="lookup-label">Confidence Trend</div>', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="footer-note">Data attribution: DGCA, Ministry of Civil Aviation · '
    'Google Flights (via SerpApi) · Prototype for SIH 2026</div>',
    unsafe_allow_html=True,
)
