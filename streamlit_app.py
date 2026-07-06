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
from agents.fundamental_agent import FundamentalAgent
from agents.sentiment_agent import SentimentAgent
from agents.insider_agent import InsiderAgent
from agents.sector_agent import SectorAgent
from agents.risk_agent import RiskAgent
from agents.backtesting_agent import BacktestingAgent
from agents.prediction_agent import PredictionAgent
from agents.pattern_agent import PatternAgent
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
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4, h5, h6 { font-family: 'Outfit', sans-serif !important; }

/* Background & Core */
.stApp { 
    background: radial-gradient(circle at top, #0b172a 0%, #040914 100%); 
}

/* Premium Glassmorphism Cards */
.card {
    background: rgba(13, 31, 53, 0.4);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    padding: 1.6rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px 0 rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.2);
}

/* Decision badge with Glow */
.badge {
    display: inline-block;
    padding: 0.5rem 1.8rem;
    border-radius: 999px;
    font-size: 1.15rem;
    font-weight: 800;
    font-family: 'Outfit', sans-serif;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    box-shadow: 0 0 20px rgba(0,0,0,0.5);
}
.badge-buy  { background: rgba(16,185,129,.15); color:#10b981; border:1.5px solid rgba(16,185,129,.6); box-shadow: 0 0 15px rgba(16,185,129, 0.3); }
.badge-hold { background: rgba(245,158,11,.15);  color:#f59e0b; border:1.5px solid rgba(245,158,11,.6); box-shadow: 0 0 15px rgba(245,158,11, 0.3); }
.badge-sell { background: rgba(239,68,68,.15);   color:#ef4444; border:1.5px solid rgba(239,68,68,.6); box-shadow: 0 0 15px rgba(239,68,68, 0.3); }

/* Metric tiles */
.metric-tile {
    background: linear-gradient(145deg, rgba(15, 23, 42, 0.6), rgba(11, 17, 32, 0.8));
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    padding: 1.1rem;
    text-align: center;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), 0 4px 15px rgba(0,0,0,0.2);
    transition: all 0.2s ease-in-out;
}
.metric-tile:hover {
    border-color: rgba(56, 189, 248, 0.3);
    transform: translateY(-2px);
}
.metric-tile .label { font-size: 0.75rem; color:#94a3b8; text-transform:uppercase; letter-spacing:1.5px; font-weight:600; }
.metric-tile .value { font-size: 1.35rem; font-weight:800; font-family:'Outfit', sans-serif; color:#f8fafc; margin-top:0.4rem; }
.metric-tile .value.green { color:#34d399; text-shadow: 0 0 10px rgba(52,211,153,0.3); }
.metric-tile .value.red   { color:#f87171; text-shadow: 0 0 10px rgba(248,113,113,0.3); }
.metric-tile .value.amber { color:#fbbf24; text-shadow: 0 0 10px rgba(251,191,36,0.3); }

/* Progress bar (Score Builder) */
.conf-bar-bg { background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255,255,255,0.05); border-radius:999px; height:12px; margin-top:0.6rem; overflow:hidden; }
.conf-bar-fill { height:100%; border-radius:999px; background: linear-gradient(90deg, #0ea5e9, #10b981, #f59e0b); background-size: 200% 100%; animation: shimmer 3s infinite linear; }
@keyframes shimmer { 0% {background-position: 100% 0;} 100% {background-position: -100% 0;} }

/* News item */
.news-item { 
    border-left: 3px solid #38bdf8; 
    padding: 0.8rem 1rem; 
    margin-bottom: 0.8rem; 
    background: rgba(15, 23, 42, 0.4); 
    border-radius: 0 8px 8px 0; 
    transition: background 0.2s;
}
.news-item:hover { background: rgba(15, 23, 42, 0.8); border-left-color: #818cf8; }
.news-item a { color:#e0f2fe; text-decoration:none; font-weight:600; font-size: 0.95rem; line-height: 1.4; }
.news-item a:hover { color: #38bdf8; }
.news-meta { font-size:0.75rem; color:#64748b; margin-top:0.4rem; }

/* SWOT styling */
.swot-box { border-radius:12px; padding:1.2rem; margin-bottom:0.8rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
.swot-s { background:linear-gradient(145deg, rgba(16,185,129,.1), rgba(4,9,20,0.4)); border:1px solid rgba(16,185,129,.2); }
.swot-w { background:linear-gradient(145deg, rgba(239,68,68,.1), rgba(4,9,20,0.4));  border:1px solid rgba(239,68,68,.2);  }
.swot-o { background:linear-gradient(145deg, rgba(59,130,246,.1), rgba(4,9,20,0.4)); border:1px solid rgba(59,130,246,.2); }
.swot-t { background:linear-gradient(145deg, rgba(245,158,11,.1), rgba(4,9,20,0.4)); border:1px solid rgba(245,158,11,.2); }
.swot-label { font-size:0.8rem; font-weight:800; text-transform:uppercase; letter-spacing:1.5px; font-family:'Outfit'; }
.swot-s .swot-label { color:#34d399; }
.swot-w .swot-label { color:#f87171; }
.swot-o .swot-label { color:#60a5fa; }
.swot-t .swot-label { color:#fbbf24; }
.swot-count { font-size:2.4rem; font-weight:800; font-family:'Outfit'; color:#f8fafc; line-height:1.2; }

/* Section headers */
h2.section { font-size:1.15rem; font-family:'Outfit', sans-serif; font-weight:800; color:#cbd5e1;
             text-transform:uppercase; letter-spacing:3px; margin:2rem 0 1rem; 
             display: flex; align-items: center; gap: 8px;}
h2.section::before { content: ""; display: inline-block; width: 8px; height: 8px; background: #38bdf8; border-radius: 50%; box-shadow: 0 0 10px #38bdf8; }

/* Streamlit Native overrides */
div[data-testid="stMetricValue"] { font-size:1.8rem !important; font-weight:800 !important; font-family:'Outfit' !important; color:#38bdf8 !important; }
div[data-testid="stMetricLabel"] { font-weight: 600 !important; color: #94a3b8 !important; letter-spacing: 1px; text-transform: uppercase; font-size: 0.8rem !important; }
hr { border-color: rgba(255,255,255,0.05); margin: 2rem 0; }
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
        FundamentalAgent(),
        SentimentAgent(),
        InsiderAgent(),
        SectorAgent(),
        RiskAgent(),
        BacktestingAgent(),
        PredictionAgent(),
        PatternAgent(),
        DecisionAgent(),
    )

stock_service, historical, technical, news, moneycontrol_agent, fundamental, sentiment, insider, sector, risk, backtesting, prediction, pattern, decision = load_services()


# ── Helpers ────────────────────────────────────────────────────────────────────
def metric_html(label, value, cls=""):
    return f"""<div class="metric-tile"><div class="label">{label}</div>
    <div class="value {cls}">{value}</div></div>"""

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


# ── Agent score waterfall chart ────────────────────────────────────────────────
def build_waterfall_chart(agent_scores, final_score):
    weights = {
        "Historical": 0.05,
        "Technical": 0.20,
        "News": 0.10,
        "Moneycontrol": 0.10,
        "Fundamental": 0.20,
        "Sentiment": 0.10,
        "Insider": 0.05,
        "Sector": 0.10,
    }
    
    x = ["Base"]
    y = [0]
    measure = ["relative"]
    text = ["0"]
    
    for k, w in weights.items():
        if k in agent_scores:
            val = agent_scores[k] * w
            x.append(k)
            y.append(val)
            measure.append("relative")
            text.append(f"+{val:.1f}")
            
    if "Risk Penalty" in agent_scores:
        x.append("Risk Penalty")
        y.append(agent_scores["Risk Penalty"])
        measure.append("relative")
        text.append(f"{agent_scores['Risk Penalty']:.1f}")
        
    x.append("Total AI Score")
    y.append(final_score)
    measure.append("total")
    text.append(f"{final_score:.1f}")
    
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measure,
        x=x,
        y=y,
        text=text,
        textposition="outside",
        decreasing={"marker": {"color": "#ef4444"}},
        increasing={"marker": {"color": "#10b981"}},
        totals={"marker": {"color": "#38bdf8"}}
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1f35",
        plot_bgcolor="#0d1f35",
        margin=dict(l=10, r=10, t=30, b=10),
        height=340,
        font=dict(family="Inter")
    )
    return fig


# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 1.5rem 0 0.5rem;">
  <div style="display: inline-block; padding: 6px 16px; margin-bottom: 16px; border-radius: 24px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); color: #7dd3fc; font-size: 0.85rem; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15); backdrop-filter: blur(4px);">
    ✨ Crafted by <span style="color: #e0f2fe; font-weight: 800;">Mr. Walia</span>
  </div>
  <h1 style="font-size:2.8rem; font-weight:800; background:linear-gradient(135deg,#60a5fa,#34d399);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:0;">
    📈 MarketMind AI
  </h1>
  <p style="color:#64748b; margin:0.4rem 0 0; font-size:1.05rem; font-family:'Outfit', sans-serif; letter-spacing:1px; text-transform:uppercase;">
    Advanced AI Portfolio & Market Analyst
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
    st.markdown("**⚡ System Capabilities**")
    st.markdown("""
- 🧠 **11-Agent AI Architecture**
- 🔮 **Predictive ML Modeling**
- 🛡️ **Automated Risk Assessment**
- 📊 **Explainable AI Score Builder**
- ⏳ **Historical Strategy Backtesting**
- 🕯️ **Candlestick Pattern Detection**
""")
    st.markdown("---")
    st.caption("🚀 Enterprise-Grade Investment Intelligence")


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

with st.spinner("🤖 Running AI agents..."):
    hist_result  = historical.analyze(data)
    tech_result  = technical.analyze(data)
    news_result  = news.analyze(resolved)
    mc_result    = moneycontrol_agent.analyze(resolved)
    
    # New Agents
    fund_result  = fundamental.analyze(resolved)
    sentiment_result = sentiment.analyze(resolved)
    insider_result = insider.analyze(resolved)
    sector_result = sector.analyze(resolved)
    risk_result = risk.analyze(resolved)
    backtest_result = backtesting.analyze(data)
    pred_result = prediction.analyze(data)
    pattern_result = pattern.analyze(data)

    final = decision.analyze(
        hist_result,
        tech_result,
        news_result,
        moneycontrol=mc_result,
        fundamentals=fund_result,
        sentiment=sentiment_result,
        insider=insider_result,
        sector=sector_result,
        risk=risk_result
    )

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
      <p style="color:#94a3b8; margin:0.8rem 0 0.2rem; font-size:0.85rem;">Total AI Score</p>
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
# ROW 1.5 — Prediction & Risk Meter
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<h2 class="section">🔮 AI Price Prediction & Risk Level</h2>', unsafe_allow_html=True)
p0, p1, p2, p3, p4 = st.columns(5)

if pred_result:
    p0.markdown(metric_html("Today Range", f"₹{pred_result.get('today_low', 'N/A')} - {pred_result.get('today_high', 'N/A')}", ""), unsafe_allow_html=True)
    p1.markdown(metric_html("Tomorrow Range", f"₹{pred_result['tomorrow_low']} - {pred_result['tomorrow_high']}", ""), unsafe_allow_html=True)
    p2.markdown(metric_html("Next Week Range", f"₹{pred_result['next_week_low']} - {pred_result['next_week_high']}", ""), unsafe_allow_html=True)
    p3.markdown(metric_html("Prediction Probability", pred_result['probability'], "green"), unsafe_allow_html=True)

risk_level = risk_result.get("signal", "Unknown") if risk_result else "Unknown"
risk_color = "green" if "Low" in risk_level else "amber" if "Moderate" in risk_level else "red"
p4.markdown(metric_html("AI Risk Meter", risk_level, risk_color), unsafe_allow_html=True)

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

m1.markdown(metric_html("2Y Trend", trend, color_val(trend)), unsafe_allow_html=True)
m2.markdown(metric_html("Change", f"{change_pct:+.1f}%", "green" if change_pct >= 0 else "red"), unsafe_allow_html=True)
m3.markdown(metric_html("RSI-14", f"{rsi:.1f}", "red" if rsi > 70 else "green" if rsi < 30 else "amber"), unsafe_allow_html=True)
m4.markdown(metric_html("MACD", macd_trend, color_val(macd_trend)), unsafe_allow_html=True)
m5.markdown(metric_html("News", news_sent, color_val(news_sent)), unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 3 — Candlestick + Agent Scores
# ═══════════════════════════════════════════════════════════════════════════════
chart_col, score_col = st.columns([3, 2], gap="large")

with chart_col:
    st.markdown('<h2 class="section">📈 Candlestick Chart (2 Years)</h2>', unsafe_allow_html=True)
    if pattern_result and pattern_result.get("pattern") != "None":
        pat_color = "#10b981" if "Bullish" in pattern_result.get("signal", "") else "#ef4444"
        st.markdown(f"**Candlestick Pattern Detected**: <span style='color:{pat_color}'>{pattern_result['pattern']}</span> (Confidence: {pattern_result['confidence']})", unsafe_allow_html=True)
    st.plotly_chart(build_candlestick(data, tech_result), use_container_width=True)

with score_col:
    st.markdown('<h2 class="section">🤖 Explainable AI Score Builder</h2>', unsafe_allow_html=True)
    st.plotly_chart(build_waterfall_chart(agent_scores, confidence), use_container_width=True)

    st.markdown('<h2 class="section">🧠 Why this decision?</h2>', unsafe_allow_html=True)
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

# ═══════════════════════════════════════════════════════════════════════════════
# ROW 7 — Backtesting (New Feature)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown('<h2 class="section">⏳ Historical Strategy Backtesting (2-5 Years)</h2>', unsafe_allow_html=True)

if backtest_result:
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    b_col1.markdown(f"""
    <div class="metric-tile">
      <div class="label">Total Return</div>
      <div class="value green">{backtest_result.get('total_return', 'N/A')}</div>
    </div>
    """, unsafe_allow_html=True)
    b_col2.markdown(f"""
    <div class="metric-tile">
      <div class="label">Annualized</div>
      <div class="value green">{backtest_result.get('annualized_return', 'N/A')}</div>
    </div>
    """, unsafe_allow_html=True)
    b_col3.markdown(f"""
    <div class="metric-tile">
      <div class="label">Win Rate</div>
      <div class="value">{backtest_result.get('win_rate', 'N/A')}</div>
    </div>
    """, unsafe_allow_html=True)
    b_col4.markdown(f"""
    <div class="metric-tile">
      <div class="label">Max Drawdown</div>
      <div class="value red">{backtest_result.get('max_drawdown', 'N/A')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.caption(f"Strategy: {backtest_result.get('strategy', '')} | Signal: {backtest_result.get('signal', '')}")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2rem 0 1rem; color:#64748b; font-size:0.85rem; font-family:'Outfit', sans-serif; letter-spacing:1px; text-transform:uppercase;">
  MarketMind AI v2.0 · Proprietary 11-Agent Architecture · Advanced Market Intelligence<br>
  Created by <strong>Mr. Walia</strong><br>
  <span style="font-size:0.7rem; color:#475569;">For Informational and Research Purposes Only. Not Financial Advice.</span>
</div>
""", unsafe_allow_html=True)
