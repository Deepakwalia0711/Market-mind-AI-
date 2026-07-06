from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import yfinance as yf
import os

from agents.decision_agent import DecisionAgent
from agents.historical_agent import HistoricalAgent
from agents.news_agent import NewsAgent
from agents.technical_agent import TechnicalAgent
from agents.moneycontrol_agent import MoneycontrolAgent
from agents.fundamental_agent import FundamentalAgent
from agents.sentiment_agent import SentimentAgent
from agents.insider_agent import InsiderAgent
from agents.sector_agent import SectorAgent
from agents.risk_agent import RiskAgent
from agents.backtesting_agent import BacktestingAgent
from agents.prediction_agent import PredictionAgent
from agents.pattern_agent import PatternAgent
from services.stock_service import StockService

app = FastAPI(title="MarketMind AI", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

stock_service = StockService()
historical = HistoricalAgent()
technical = TechnicalAgent()
news = NewsAgent()
moneycontrol = MoneycontrolAgent()
fundamental = FundamentalAgent()
sentiment = SentimentAgent()
insider = InsiderAgent()
sector = SectorAgent()
risk = RiskAgent()
backtesting = BacktestingAgent()
prediction = PredictionAgent()
pattern = PatternAgent()
decision = DecisionAgent()


@app.get("/health")
@app.head("/health")
def health_check():
    return {"status": "healthy", "message": "MarketMind AI API v2 is running"}


def _get_exchange_prices(resolved_symbol: str, data) -> dict:
    """Fetch NSE + BSE prices or fall back to default close."""
    prices = {}
    if resolved_symbol.endswith((".NS", ".BO")):
        base_symbol = resolved_symbol[:-3]
        for suffix, key in [(".NS", "NSE"), (".BO", "BSE")]:
            try:
                ticker_data = yf.Ticker(f"{base_symbol}{suffix}").history(period="1d")
                if not ticker_data.empty:
                    prices[key] = round(float(ticker_data["Close"].iloc[-1]), 2)
            except Exception:
                pass
    if not prices:
        prices["Default"] = round(float(data["Close"].iloc[-1]), 2)
    return prices


@app.get("/analyze/{symbol}")
def analyze(symbol: str):
    data, resolved_symbol = stock_service.get_stock_data(symbol)
    if data.empty:
        return {"error": "Stock not found"}

    # Run all agents
    history_result = historical.analyze(data)
    technical_result = technical.analyze(data)
    news_result = news.analyze(resolved_symbol)
    mc_result = moneycontrol.analyze(resolved_symbol)
    fund_result = fundamental.analyze(resolved_symbol)
    sentiment_result = sentiment.analyze(resolved_symbol)
    insider_result = insider.analyze(resolved_symbol)
    sector_result = sector.analyze(resolved_symbol)
    risk_result = risk.analyze(resolved_symbol)
    backtest_result = backtesting.analyze(data)
    pred_result = prediction.analyze(data)
    pattern_result = pattern.analyze(data)

    final_decision = decision.analyze(
        history_result,
        technical_result,
        news_result,
        moneycontrol=mc_result,
        fundamentals=fund_result,
        sentiment=sentiment_result,
        insider=insider_result,
        sector=sector_result,
        risk=risk_result
    )

    prices = _get_exchange_prices(resolved_symbol, data)

    # Strip internal series from technical result (not JSON-serializable cleanly)
    technical_clean = {k: v for k, v in technical_result.items() if not k.startswith("_")}

    return {
        "stock": symbol,
        "resolved_symbol": resolved_symbol,
        "prices": prices,
        "history": history_result,
        "technical": technical_clean,
        "news": news_result,
        "moneycontrol": mc_result,
        "decision": final_decision["decision"],
        "confidence": final_decision["confidence"],
        "reasons": final_decision["reasons"],
        "agent_scores": final_decision["agent_scores"],
        "prediction": pred_result,
        "pattern": pattern_result,
        "backtesting": backtest_result,
        "risk": risk_result,
    }


@app.get("/chart-data/{symbol}")
def get_chart_data(symbol: str):
    data, resolved_symbol = stock_service.get_stock_data(symbol)
    if data.empty:
        return {"error": "Stock not found"}

    import math
    def clean_val(v):
        try:
            val = float(v)
            return None if math.isnan(val) or math.isinf(val) else round(val, 2)
        except (ValueError, TypeError):
            return None

    # Include SMA overlays
    close = data["Close"]
    
    return {
        "dates": [str(x.date()) for x in data.index],
        "open": [clean_val(v) for v in data["Open"]],
        "high": [clean_val(v) for v in data["High"]],
        "low": [clean_val(v) for v in data["Low"]],
        "close": [clean_val(v) for v in close],
        "volume": [int(v) if not math.isnan(float(v)) else 0 for v in data["Volume"]],
        "sma20": [clean_val(v) for v in close.rolling(20).mean()],
        "sma50": [clean_val(v) for v in close.rolling(50).mean()] if len(data) >= 50 else [],
    }


@app.get("/price/{symbol}")
def get_price(symbol: str):
    data, resolved_symbol = stock_service.get_stock_data(symbol)
    if data.empty:
        return {"error": "Stock not found"}
    prices = _get_exchange_prices(resolved_symbol, data)
    return {"prices": prices, "resolved_symbol": resolved_symbol}

# Mount frontend
from pathlib import Path
frontend_path = str(Path(__file__).resolve().parent / "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"WARNING: Frontend path not found at {frontend_path}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    # Render requires binding to 0.0.0.0
    uvicorn.run("main:app", host="0.0.0.0", port=port)
