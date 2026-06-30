import os
import sys
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import yfinance as yf

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.decision_agent import DecisionAgent
from agents.historical_agent import HistoricalAgent
from agents.moneycontrol_agent import MoneycontrolAgent
from agents.news_agent import NewsAgent
from agents.technical_agent import TechnicalAgent
from services.stock_service import StockService

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MarketMind AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #060d1a; }

/* Cards */
.card {
    background: #0d1f35;
    border: 1px solid #1e3a5f;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}

/* Decision badge */
.badge {
    display: inline-block;
    padding: 0.5rem 1.6rem;
    border-radius: 999px;
    font-size: 1.1rem;
    font-weight: 800;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.badge-buy  { background: rgba(16,185,129,.18); color:#10b981; border:1.5px solid #10b981; }
.badge-hold { background: rgba(245,158,11,.18);  color:#f59e0b; border:1.5px solid #f59e0b; }
.badge-sell { background: rgba(239,68,68,.18);   color:#ef4444; border:1.5px solid #ef4444; }

/* Metric tiles */
.metric-tile {
    background: #0a1628;
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    text-align: center;
}
.metric-tile .label { font-size: 0.72rem; color:#64748b; text-transform:uppercase; letter-spacing:1px; }
.metric-tile .value { font-size: 1.3rem; font-weight:700; color:#e2e8f0; margin-top:0.2rem; }
.metric-tile .value.green { color:#10b981; }
.metric-tile .value.red   { color:#ef4444; }
.metric-tile .value.amber { color:#f59e0b; }

/* Progress bar */
.conf-bar-bg { background:#1e3a5f; border-radius:999px; height:10px; margin-top:0.5rem; }
.conf-bar-fill { height:10px; border-radius:999px; background: linear-gradient(90deg,#3b82f6,#10b981); }

/* News item */
.news-item { border-left: 3px solid #3b82f6; padding: 0.6rem 0.9rem; margin-bottom: 0.8rem; background:#0a1628; border-radius:0 8px 8px 0; }
.news-item a { color:#93c5fd; text-decoration:none; font-weight:600; }
.news-item a:hover { text-decoration:underline; }
.news-meta { font-size:0.72rem; color:#475569; margin-top:0.2rem; }

/* SWOT */
.swot-box { border-radius:10px; padding:0.9rem; margin-bottom:0.6rem; }
.swot-s { background:rgba(16,185,129,.1); border:1px solid rgba(16,185,129,.3); }
.swot-w { background:rgba(239,68,68,.1);  border:1px solid rgba(239,68,68,.3);  }
.swot-o { background:rgba(59,130,246,.1); border:1px solid rgba(59,130,246,.3); }
.swot-t { background:rgba(245,158,11,.1); border:1px solid rgba(245,158,11,.3); }
.swot-label { font-size:0.78rem; font-weight:700; text-transform:uppercase; letter-spacing:1px; }
.swot-s .swot-label { color:#10b981; }
.swot-w .swot-label { color:#ef4444; }
.swot-o .swot-label { color:#3b82f6; }
.swot-t .swot-label { color:#f59e0b; }
.swot-count { font-size:2rem; font-weight:800; }

/* Section headers */
h2.section { font-size:1.1rem; font-weight:700; color:#94a3b8;
             text-transform:uppercase; letter-spacing:2px; margin:1.4rem 0 0.8rem; }

div[data-testid="stMetricValue"] { font-size:1.6rem; font-weight:700; color:#38bdf8; }
</style>
""", unsafe_allow_html=True)


# ── Init services ──────────────────────────────────────────────────────────────
@st.cache_resource
def load_services():
    return (
        StockService(),
        HistoricalAgent(),
        TechnicalAgent(),
        NewsAgent(),
        MoneycontrolAgent(),
        DecisionAgent(),
    )

stock_service, historical, technical, news, moneycontrol_agent, decision = load_services()


# ── Helpers ────────────────────────────────────────────────────────────────────
def color_val(v: str):
    v_lower = v.lower()
    if any(w in v_lower for w in ["bull", "positive", "strong"]):
        return "green"
    if any(w in v_lower for w in ["bear", "negative", "weak"]):
        return "red"
    return "amber"

def fmt_price(val, exchange):
    symbol = "₹" if exchange in ("NSE", "BSE") else "$"
    return f"{symbol}{val:,.2f}"

def get_live_prices(resolved_symbol, data):
    prices = {}
    if resolved_symbol.endswith((".NS", ".BO")):
        base = resolved_symbol[:-3]
        for suffix, key in [(".NS", "NSE"), (".BO", "BSE")]:
            try:
                d = yf.Ticker(f"{base}{suffix}").history(period="1d")
                if not d.empty:
                    prices[key] = round(float(d["Close"].iloc[-1]), 2)
            except Exception:
                pass
    # Fallback to the DataFrame's last close only if it is non-empty
    if not prices:
        try:
            if hasattr(data, "empty") and not data.empty:
                prices["Default"] = round(float(data["Close"].iloc[-1]), 2)
        except Exception:
            pass
    return prices


# ── Live price fragment ────────────────────────────────────────────────────────
@st.fragment(run_every=3)
def live_price_widget(resolved_symbol, fallback_prices):
    try:
        prices = get_live_prices(resolved_symbol, pd.DataFrame())
        if not prices:
            prices = fallback_prices
    except Exception:
        prices = fallback_prices

    cols = st.columns(len(prices))
    for idx, (exc, val) in enumerate(prices.items()):
        cols[idx].metric(
            label=f"🟢 Live · {exc}",
            value=fmt_price(val, exc),
        )


# ── Candlestick chart ──────────────────────────────────────────────────────────
def build_candlestick(data, tech_result):
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.72, 0.28],
        vertical_spacing=0.04,
    )

    # Candles
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["Open"], high=data["High"],
        low=data["Low"], close=data["Close"],
        name="Price",
        increasing_line_color="#10b981",
        decreasing_line_color="#ef4444",
    ), row=1, col=1)

    # SMA 20
    sma20_raw = tech_result.get("_sma20_series", [])
    if sma20_raw:
        fig.add_trace(go.Scatter(
            x=data.index, y=sma20_raw,
            name="SMA 20", line=dict(color="#f59e0b", width=1.5, dash="dot"),
        ), row=1, col=1)

    # SMA 50
    sma50_raw = tech_result.get("_sma50_series", [])
    if sma50_raw:
        fig.add_trace(go.Scatter(
            x=data.index, y=sma50_raw,
            name="SMA 50", line=dict(color="#a78bfa", width=1.5, dash="dot"),
        ), row=1, col=1)

    # Volume
    colors = ["#10b981" if c >= o else "#ef4444"
              for c, o in zip(data["Close"], data["Open"])]
    fig.add_trace(go.Bar(
        x=data.index, y=data["Volume"],
        name="Volume", marker_color=colors, opacity=0.6,
    ), row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#060d1a",
        plot_bgcolor="#060d1a",
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=520,
        font=dict(family="Inter"),
    )
    fig.update_xaxes(gridcolor="#1e3a5f", showgrid=True)
    fig.update_yaxes(gridcolor="#1e3a5f", showgrid=True)
    return fig


# ── Agent score bar chart ──────────────────────────────────────────────────────
def build_score_chart(agent_scores: dict):
    agents = list(agent_scores.keys())
    scores = list(agent_scores.values())
    bar_colors = [
        "#10b981" if s >= 63 else "#ef4444" if s <= 40 else "#f59e0b"
        for s in scores
    ]
    fig = go.Figure(go.Bar(
        x=agents, y=scores,
        marker_color=bar_colors,
        text=[f"{s}" for s in scores],
        textposition="outside",
        textfont=dict(color="#e2e8f0", size=13),
    ))
    fig.add_hline(y=63, line_dash="dot", line_color="#10b981", annotation_text="Buy zone", annotation_font_color="#10b981")
    fig.add_hline(y=40, line_dash="dot", line_color="#ef4444", annotation_text="Sell zone", annotation_font_color="#ef4444")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1f35",
        plot_bgcolor="#0d1f35",
        yaxis=dict(range=[0, 105], gridcolor="#1e3a5f"),
        xaxis=dict(gridcolor="#1e3a5f"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=340,
        font=dict(family="Inter"),
        showlegend=False,
    )
    return fig


# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 1.5rem 0 0.5rem;">
  <h1 style="font-size:2.8rem; font-weight:800; background:linear-gradient(135deg,#60a5fa,#34d399);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0;">
    📈 MarketMind AI
  </h1>
  <p style="color:#475569; margin:0.4rem 0 0; font-size:1rem;">
    Multi-agent analysis · yFinance · Moneycontrol · NewsAPI
  </p>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Stock Search")
    query = st.text_input("Ticker / Company Name", value="RELIANCE", label_visibility="collapsed",
                          placeholder="RELIANCE / HDFC / AAPL")
    run_btn = st.button("🚀 Run Analysis", use_container_width=True, type="primary")

    st.markdown("---")
    st.markdown("**What this app does:**")
    st.markdown("""
- 📊 Candlestick chart + SMA overlay
- 📰 Live news + sentiment
- 🏦 Moneycontrol SWOT & ratios
- 🤖 5 AI agents → Buy / Hold / Sell
- 💰 Live prices every 3 seconds
""")
    st.markdown("---")
    st.caption("Data: yFinance · NewsAPI · Moneycontrol")


# ── MAIN FLOW ──────────────────────────────────────────────────────────────────
if not (run_btn or query):
    st.markdown("""
    <div style="text-align:center; padding:4rem 0; color:#334155;">
      <p style="font-size:3rem;">📊</p>
      <p style="font-size:1.1rem;">Enter a stock name or ticker in the sidebar and click <strong>Run Analysis</strong></p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── RUN AGENTS ─────────────────────────────────────────────────────────────────
with st.spinner("🔄 Resolving symbol & fetching market data..."):
    data, resolved = stock_service.get_stock_data(query)

if data.empty:
    st.error(f"❌ Could not find stock data for **{query}**. Try a ticker like `RELIANCE.NS` or `AAPL`.")
    st.stop()

with st.spinner("🤖 Running AI agents (History · Technical · News · Moneycontrol)..."):
    hist_result  = historical.analyze(data)
    tech_result  = technical.analyze(data)
    news_result  = news.analyze(resolved)
    mc_result    = moneycontrol_agent.analyze(resolved)
    final        = decision.analyze(hist_result, tech_result, news_result, moneycontrol=mc_result)

agent_scores   = final["agent_scores"]
dec            = final["decision"]
confidence     = final["confidence"]
reasons        = final["reasons"]
initial_prices = get_live_prices(resolved, data)

st.success(f"✅ Resolved **{query}** → `{resolved}`")

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 1 — Decision + Live Prices
# ═══════════════════════════════════════════════════════════════════════════════
col_dec, col_price = st.columns([1, 2], gap="large")

with col_dec:
    badge_cls = dec.lower()
    st.markdown(f"""
    <div class="card" style="text-align:center;">
      <p style="color:#64748b; font-size:0.8rem; text-transform:uppercase; letter-spacing:2px; margin:0 0 0.6rem;">AI Recommendation</p>
      <span class="badge badge-{badge_cls}">{dec}</span>
      <p style="color:#94a3b8; margin:0.8rem 0 0.2rem; font-size:0.85rem;">Confidence Score</p>
      <p style="font-size:2rem; font-weight:800; color:#e2e8f0; margin:0;">{confidence:.1f}<span style="font-size:1rem;">/100</span></p>
      <div class="conf-bar-bg">
        <div class="conf-bar-fill" style="width:{min(confidence,100):.0f}%;"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with col_price:
    st.markdown('<h2 class="section">💰 Live Prices (auto-refresh every 3s)</h2>', unsafe_allow_html=True)
    live_price_widget(resolved, initial_prices)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 2 — Metrics Strip
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<h2 class="section">📊 Agent Signals</h2>', unsafe_allow_html=True)
m1, m2, m3, m4, m5 = st.columns(5)

trend = hist_result.get("trend", "Neutral")
change_pct = hist_result.get("change_pct", 0.0)
rsi = tech_result.get("RSI", 50.0)
sma_sig = tech_result.get("sma_signal", "Neutral")
macd_trend = tech_result.get("macd_trend", "Neutral")
news_sent = news_result.get("sentiment", "Neutral")

def metric_html(label, value, cls=""):
    return f"""<div class="metric-tile"><div class="label">{label}</div>
    <div class="value {cls}">{value}</div></div>"""

m1.markdown(metric_html("6M Trend", trend, color_val(trend)), unsafe_allow_html=True)
m2.markdown(metric_html("Change", f"{change_pct:+.1f}%", "green" if change_pct >= 0 else "red"), unsafe_allow_html=True)
m3.markdown(metric_html("RSI-14", f"{rsi:.1f}", "red" if rsi > 70 else "green" if rsi < 30 else "amber"), unsafe_allow_html=True)
m4.markdown(metric_html("MACD", macd_trend, color_val(macd_trend)), unsafe_allow_html=True)
m5.markdown(metric_html("News", news_sent, color_val(news_sent)), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 3 — Candlestick + Agent Scores
# ═══════════════════════════════════════════════════════════════════════════════
chart_col, score_col = st.columns([3, 2], gap="large")

with chart_col:
    st.markdown('<h2 class="section">📈 Candlestick Chart (6 Months)</h2>', unsafe_allow_html=True)
    st.plotly_chart(build_candlestick(data, tech_result), use_container_width=True)

with score_col:
    st.markdown('<h2 class="section">🤖 Agent Confidence Scores</h2>', unsafe_allow_html=True)
    st.plotly_chart(build_score_chart(agent_scores), use_container_width=True)

    st.markdown('<h2 class="section">🧠 Decision Reasons</h2>', unsafe_allow_html=True)
    for r in reasons:
        icon = "🟢" if any(w in r.lower() for w in ["bull", "positive", "healthy", "oversold", "strength", "above"]) else \
               "🔴" if any(w in r.lower() for w in ["bear", "negative", "overbought", "caution", "below", "risk"]) else "🟡"
        st.markdown(f"{icon} {r}")

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 4 — Technical Details
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<h2 class="section">⚙️ Technical Indicators</h2>', unsafe_allow_html=True)
t1, t2, t3, t4 = st.columns(4)
t1.markdown(metric_html("SMA 20", f"₹{tech_result.get('sma20') or 'N/A'}", ""), unsafe_allow_html=True)
t2.markdown(metric_html("SMA 50", f"₹{tech_result.get('sma50') or 'N/A'}", ""), unsafe_allow_html=True)
t3.markdown(metric_html("SMA Signal", sma_sig, color_val(sma_sig)), unsafe_allow_html=True)
t4.markdown(metric_html("Volatility", f"{hist_result.get('volatility', 0.0):.2f}% /day", ""), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 5 — Moneycontrol (SWOT + Metrics)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<h2 class="section">🏦 Moneycontrol Analysis</h2>', unsafe_allow_html=True)

if mc_result:
    company_name = mc_result.get("company_name") or resolved
    sector = mc_result.get("sector", "—")
    mc_url = mc_result.get("mc_url", "")
    metrics = mc_result.get("metrics") or {}
    swot = mc_result.get("swot") or {}
    mc_analysis = mc_result.get("analysis") or {}

    # Header
    link_html = f'<a href="{mc_url}" target="_blank" style="color:#60a5fa;">↗ View on Moneycontrol</a>' if mc_url else ""
    st.markdown(f"""
    <div class="card" style="display:flex; justify-content:space-between; align-items:center; padding:1rem 1.4rem;">
      <div>
        <p style="margin:0; font-size:1.2rem; font-weight:700; color:#e2e8f0;">{company_name}</p>
        <p style="margin:0; color:#64748b; font-size:0.85rem;">{sector}</p>
      </div>
      <div>{link_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # Valuation metrics
    if metrics:
        met_keys = [
            ("market_cap_cr", "Mkt Cap (Cr)"),
            ("pe", "P/E (TTM)"),
            ("sector_pe", "Sector P/E"),
            ("pb", "P/B"),
            ("eps", "EPS (TTM)"),
            ("book_value", "Book Value"),
            ("beta", "Beta"),
            ("dividend_yield", "Div Yield"),
            ("fifty_two_w_high", "52W High"),
            ("fifty_two_w_low", "52W Low"),
        ]
        available = [(k, l) for k, l in met_keys if metrics.get(k)]
        if available:
            mcols = st.columns(min(len(available), 5))
            for i, (k, label) in enumerate(available[:10]):
                mcols[i % 5].markdown(metric_html(label, metrics[k], ""), unsafe_allow_html=True)

    # SWOT
    if swot:
        st.markdown("**SWOT Analysis**")
        sc1, sc2, sc3, sc4 = st.columns(4)
        swot_defs = [
            (sc1, "swot-s", "💪 Strengths", "strength"),
            (sc2, "swot-w", "⚠️ Weaknesses", "weakness"),
            (sc3, "swot-o", "🚀 Opportunities", "opportunit"),
            (sc4, "swot-t", "🔥 Threats", "threat"),
        ]
        for col, cls, title, key in swot_defs:
            matched = next((v for k, v in swot.items() if key in k.lower()), [])
            count = mc_analysis.get(
                f"{'strengths' if 'strength' in key else 'weaknesses' if 'weakness' in key else 'opportunities' if 'opportunit' in key else 'threats'}_total",
                len(matched)
            )
            preview = matched[:2] if matched else []
            preview_html = "".join(f"<li style='font-size:0.78rem;color:#94a3b8;'>{item[:60]}{'…' if len(item)>60 else ''}</li>" for item in preview)
            col.markdown(f"""
            <div class="swot-box {cls}">
              <div class="swot-label">{title}</div>
              <div class="swot-count">{count}</div>
              <ul style="padding-left:1rem; margin:0.3rem 0 0;">{preview_html}</ul>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("⚠️ Moneycontrol data unavailable for this symbol (scraping may be blocked or symbol not found).")

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 6 — News
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<h2 class="section">📰 Recent News & Sentiment</h2>', unsafe_allow_html=True)

articles = news_result.get("articles", [])
news_count = news_result.get("news_count", 0)
sent_color = {"Positive": "#10b981", "Negative": "#ef4444"}.get(news_sent, "#f59e0b")

nc1, nc2 = st.columns([1, 4])
nc1.markdown(f"""
<div class="card" style="text-align:center;">
  <div class="label" style="font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Overall</div>
  <div style="font-size:1.8rem; font-weight:800; color:{sent_color}; margin:0.4rem 0;">{news_sent}</div>
  <div style="color:#64748b; font-size:0.85rem;">{news_count} articles analysed</div>
</div>
""", unsafe_allow_html=True)

with nc2:
    if articles:
        for art in articles:
            title = art.get("title", "No title")
            url = art.get("url", "#")
            pub = art.get("publishedAt", "")[:10] if art.get("publishedAt") else ""
            source = art.get("source", {}).get("name", "") if isinstance(art.get("source"), dict) else ""
            st.markdown(f"""
            <div class="news-item">
              <a href="{url}" target="_blank">{title}</a>
              <div class="news-meta">📅 {pub}{"  ·  " + source if source else ""}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent news articles found. Check your NewsAPI key in `.env`.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2rem 0 1rem; color:#334155; font-size:0.8rem;">
  MarketMind AI · Powered by yFinance · NewsAPI · Moneycontrol · Not financial advice
</div>
""", unsafe_allow_html=True)
