import os
import sys
import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# Ensure local imports are resolved correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.decision_agent import DecisionAgent
from agents.historical_agent import HistoricalAgent
from agents.news_agent import NewsAgent
from agents.technical_agent import TechnicalAgent
from services.stock_service import StockService

# Set Streamlit Page Config
st.set_page_config(
    page_title="Walia Mind AI Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom styling for Dark Theme matching React app
st.markdown(
    """
    <style>
    .reportview-container {
        background: #0f172a;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: bold;
        color: #38bdf8;
    }
    .decision-badge {
        padding: 8px 16px;
        border-radius: 9999px;
        font-weight: bold;
        text-align: center;
        display: inline-block;
    }
    .buy {
        background-color: #10b981;
        color: white;
    }
    .hold {
        background-color: #f59e0b;
        color: white;
    }
    .avoid {
        background-color: #ef4444;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Services & Agents
stock_service = StockService()
historical = HistoricalAgent()
technical = TechnicalAgent()
news = NewsAgent()
decision = DecisionAgent()


# Fragment function for real-time price updates (runs every 2 seconds)
@st.fragment(run_every=2)
def render_live_price(resolved_symbol, initial_prices):
    prices = {}
    if resolved_symbol.endswith((".NS", ".BO")):
        base_symbol = resolved_symbol[:-3]
        try:
            nse_data = yf.Ticker(f"{base_symbol}.NS").history(period="1d")
            if not nse_data.empty:
                prices["NSE"] = round(float(nse_data["Close"].iloc[-1]), 2)
        except Exception:
            pass
        try:
            bse_data = yf.Ticker(f"{base_symbol}.BO").history(period="1d")
            if not bse_data.empty:
                prices["BSE"] = round(float(bse_data["Close"].iloc[-1]), 2)
        except Exception:
            pass
    if not prices:
        try:
            ticker_data = yf.Ticker(resolved_symbol).history(period="1d")
            if not ticker_data.empty:
                prices["Default"] = round(
                    float(ticker_data["Close"].iloc[-1]), 2
                )
        except Exception:
            pass

    if not prices:
        prices = initial_prices

    # Render metrics in side-by-side columns
    cols = st.columns(len(prices))
    for idx, (exchange, val) in enumerate(prices.items()):
        cols[idx].metric(
            label=f"💰 Live Price ({exchange})", value=f"₹{val}" if exchange in ["NSE", "BSE"] else f"${val}"
        )


# Header
st.title("🧠 MarketMind AI Dashboard")
st.subheader("Multi-agent stock analysis powered by AI Agents")

# Sidebar search
with st.sidebar:
    st.header("Search Parameters")
    search_query = st.text_input("Enter Stock Name or Ticker", "HDFC")
    analyze_button = st.button("Run Analysis", use_container_width=True)

# Main Execution Flow
if search_query:
    # 1. Fetch stock data & resolve ticker
    with st.spinner("Resolving symbol and fetching market datasets..."):
        data, resolved_symbol = stock_service.get_stock_data(search_query)

    if data.empty:
        st.error(f"❌ Stock not found for query: '{search_query}'")
    else:
        st.success(
            f"✅ Resolved '{search_query}' to ticker **{resolved_symbol}**"
        )

        # 2. Run Agents
        with st.spinner("AI Agents analyzing trends, technicals & news..."):
            history_result = historical.analyze(data)
            technical_result = technical.analyze(data)
            news_result = news.analyze(resolved_symbol)
            final_decision = decision.analyze(
                history_result,
                technical_result,
                news_result,
            )

        # Extract initial prices for the fragment
        initial_prices = {}
        if resolved_symbol.endswith((".NS", ".BO")):
            base_symbol = resolved_symbol[:-3]
            try:
                initial_prices["NSE"] = round(
                    float(
                        yf.Ticker(f"{base_symbol}.NS")
                        .history(period="1d")["Close"]
                        .iloc[-1]
                    ),
                    2,
                )
            except Exception:
                pass
            try:
                initial_prices["BSE"] = round(
                    float(
                        yf.Ticker(f"{base_symbol}.BO")
                        .history(period="1d")["Close"]
                        .iloc[-1]
                    ),
                    2,
                )
            except Exception:
                pass
        if not initial_prices:
            initial_prices["Default"] = round(
                float(data["Close"].iloc[-1]), 2
            )

        # 3. Layout: Row 1 - Live Prices & Decision Badge
        col_badge, col_price = st.columns([1, 2])

        with col_badge:
            st.markdown("### AI Recommendation")
            rec = final_decision.get("decision", "Hold")
            badge_class = rec.lower()
            st.markdown(
                f'<span class="decision-badge {badge_class}">{rec.upper()}</span>',
                unsafe_allow_html=True,
            )
            st.write(f"**Confidence:** {final_decision.get('confidence', 66.67)}%")

        with col_price:
            st.markdown("### Live Prices (Updating real-time every 2s)")
            render_live_price(resolved_symbol, initial_prices)

        st.divider()

        # 4. Layout: Row 2 - Metrics
        st.markdown("### Agent Analysis Metrics")
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Historical Trend", history_result.get("trend", "Neutral"))
        m_col2.metric("Technical RSI", f"{technical_result.get('RSI', 50.0):.2f}")
        m_col3.metric("News Sentiment", news_result.get("sentiment", "Neutral"))

        # Reasons list
        st.markdown("#### Decision Rationale:")
        reasons = final_decision.get("reasons", [])
        if reasons:
            for r in reasons:
                st.write(f"- {r}")
        else:
            st.write("- No strong signals detected")

        st.divider()

        # 5. Layout: Row 3 - Charts
        chart_col1, chart_col2 = st.columns([2, 1])

        with chart_col1:
            st.markdown("### 📈 Candlestick Chart (6-Months)")
            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=data.index,
                        open=data["Open"],
                        high=data["High"],
                        low=data["Low"],
                        close=data["Close"],
                        name="Candles",
                    )
                ]
            )
            fig.update_layout(
                template="plotly_dark",
                xaxis_rangeslider_visible=False,
                margin=dict(l=20, r=20, t=20, b=20),
                height=450,
            )
            st.plotly_chart(fig, use_container_width=True)

        with chart_col2:
            st.markdown("### 📊 Agent Scores")
            agent_scores = {
                "Historical": 75,
                "Technical": 85,
                "News": 70,
                "Candlestick": 80,
                "Risk": 65,
            }
            score_df = pd.DataFrame(
                {
                    "Agent": list(agent_scores.keys()),
                    "Confidence Score": list(agent_scores.values()),
                }
            )
            fig_bar = go.Figure(
                data=[
                    go.Bar(
                        x=score_df["Agent"],
                        y=score_df["Confidence Score"],
                        marker_color="#38bdf8",
                    )
                ]
            )
            fig_bar.update_layout(
                template="plotly_dark",
                yaxis=dict(range=[0, 100]),
                margin=dict(l=20, r=20, t=20, b=20),
                height=450,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        # 6. Layout: Row 4 - News Headlines
        st.markdown("### 📰 Real-Time News Sentiment")
        articles = news_result.get("articles", [])
        if articles:
            for art in articles:
                st.markdown(
                    f"**[{art.get('title')}]({art.get('url')})**"
                )
                st.caption(
                    f"Published at {art.get('publishedAt')} | Publisher: {art.get('publisher', 'Financial News')}"
                )
                st.write("")
        else:
            st.info("No recent news articles found for this stock symbol.")
