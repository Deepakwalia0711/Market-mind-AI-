from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf

from agents.decision_agent import DecisionAgent
from agents.historical_agent import HistoricalAgent
from agents.news_agent import NewsAgent
from agents.technical_agent import TechnicalAgent
from agents.moneycontrol_agent import MoneycontrolAgent
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
decision = DecisionAgent()


@app.get("/")
@app.head("/")
def root():
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
    mc_result = moneycontrol.analyze(resolved_symbol)   # ← NOW WIRED UP
    final_decision = decision.analyze(
        history_result,
        technical_result,
        news_result,
        moneycontrol=mc_result,
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
        "agent_scores": final_decision["agent_scores"],  # ← DYNAMIC, NOT HARDCODED
    }


@app.get("/chart-data/{symbol}")
def get_chart_data(symbol: str):
    data, resolved_symbol = stock_service.get_stock_data(symbol)
    if data.empty:
        return {"error": "Stock not found"}

    # Include SMA overlays
    close = data["Close"]
    sma20 = close.rolling(20).mean().round(2).tolist()
    sma50 = close.rolling(50).mean().round(2).tolist() if len(data) >= 50 else []

    return {
        "dates": [str(x.date()) for x in data.index],
        "open": [round(float(v), 2) for v in data["Open"]],
        "high": [round(float(v), 2) for v in data["High"]],
        "low": [round(float(v), 2) for v in data["Low"]],
        "close": [round(float(v), 2) for v in close],
        "volume": [int(v) for v in data["Volume"]],
        "sma20": sma20,
        "sma50": sma50,
    }


@app.get("/price/{symbol}")
def get_price(symbol: str):
    data, resolved_symbol = stock_service.get_stock_data(symbol)
    if data.empty:
        return {"error": "Stock not found"}
    prices = _get_exchange_prices(resolved_symbol, data)
    return {"prices": prices, "resolved_symbol": resolved_symbol}
