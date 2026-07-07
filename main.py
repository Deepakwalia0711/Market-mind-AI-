from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import yfinance as yf
import os
import math
import threading
import time
from pathlib import Path

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
from learning.prediction_store import save_prediction, get_stats
from learning.outcome_checker import check_and_label_outcomes
from learning.model_trainer import train_and_save_model

app = FastAPI(title="MarketMind AI", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

stock_service  = StockService()
historical     = HistoricalAgent()
technical      = TechnicalAgent()
news           = NewsAgent()
moneycontrol   = MoneycontrolAgent()
fundamental    = FundamentalAgent()
sentiment      = SentimentAgent()
insider        = InsiderAgent()
sector         = SectorAgent()
risk           = RiskAgent()
backtesting    = BacktestingAgent()
prediction     = PredictionAgent()
pattern        = PatternAgent()
decision       = DecisionAgent()


# ─── Background Learning Scheduler ──────────────────────────────────────────
def _nightly_learning_job():
    """
    Background thread: raat ko har 24 ghante mein:
    1. Purani predictions ka actual outcome check karo
    2. Enough labeled data hone par model retrain karo
    """
    RETRAIN_THRESHOLD = 10  # kitne real samples ke baad retrain karein
    INTERVAL_SECONDS = 24 * 60 * 60  # 24 hours

    # Pehla run: 2 minute baad (server start hone ke baad)
    time.sleep(120)

    while True:
        print("\n[Scheduler] Running nightly learning job...")
        try:
            check_and_label_outcomes()
            stats = get_stats()
            print(f"[Scheduler] Total labeled data: {stats['labeled']} samples")

            if stats["labeled"] >= RETRAIN_THRESHOLD:
                print(f"[Scheduler] {stats['labeled']} samples — retraining model...")
                accuracy, total, _ = train_and_save_model()
                decision.reload_model()
                print(f"[Scheduler] Model retrained! Accuracy: {accuracy}%, Samples: {total}")
            else:
                remaining = RETRAIN_THRESHOLD - stats["labeled"]
                print(f"[Scheduler] Need {remaining} more labeled samples before retraining.")
        except Exception as e:
            print(f"[Scheduler] Error in learning job: {e}")

        time.sleep(INTERVAL_SECONDS)

# Start background thread
_thread = threading.Thread(target=_nightly_learning_job, daemon=True)
_thread.start()
print("[Scheduler] Nightly learning scheduler started (first run in 2 min)")


# ─── Helpers ────────────────────────────────────────────────────────────────
def _get_exchange_prices(resolved_symbol: str, data) -> dict:
    prices = {}
    if resolved_symbol.endswith((".NS", ".BO")):
        base = resolved_symbol[:-3]
        for suffix, key in [(".NS", "NSE"), (".BO", "BSE")]:
            try:
                hist = yf.Ticker(f"{base}{suffix}").history(period="1d")
                if not hist.empty:
                    prices[key] = round(float(hist["Close"].iloc[-1]), 2)
            except Exception:
                pass
    if not prices:
        prices["Default"] = round(float(data["Close"].iloc[-1]), 2)
    return prices


def _clean_val(v):
    try:
        val = float(v)
        return None if math.isnan(val) or math.isinf(val) else round(val, 2)
    except (ValueError, TypeError):
        return None


# ─── Routes ─────────────────────────────────────────────────────────────────
@app.get("/health")
@app.head("/health")
def health_check():
    stats = get_stats()
    return {
        "status": "healthy",
        "message": "MarketMind AI API v3 (Real-Time Learning Pipeline)",
        "learning_pipeline": stats
    }


@app.get("/analyze/{symbol}")
def analyze(symbol: str):
    data, resolved_symbol = stock_service.get_stock_data(symbol)
    if data.empty:
        return {"error": "Stock not found"}

    # Run all agents
    history_result   = historical.analyze(data)
    technical_result = technical.analyze(data)
    news_result      = news.analyze(resolved_symbol)
    mc_result        = moneycontrol.analyze(resolved_symbol)
    fund_result      = fundamental.analyze(resolved_symbol)
    sentiment_result = sentiment.analyze(resolved_symbol, news_articles=news_result.get("articles", []))
    insider_result   = insider.analyze(resolved_symbol)
    sector_result    = sector.analyze(resolved_symbol)
    risk_result      = risk.analyze(resolved_symbol)
    backtest_result  = backtesting.analyze(data)
    pred_result      = prediction.analyze(data)
    pattern_result   = pattern.analyze(data)

    final_decision = decision.analyze(
        history_result, technical_result, news_result,
        moneycontrol=mc_result, fundamentals=fund_result,
        sentiment=sentiment_result, insider=insider_result,
        sector=sector_result, risk=risk_result
    )

    prices = _get_exchange_prices(resolved_symbol, data)
    current_price = list(prices.values())[0] if prices else 0.0

    # Save prediction to learning pipeline DB
    try:
        save_prediction(
            symbol=resolved_symbol,
            prediction=final_decision["decision"],
            price=current_price,
            agent_scores=final_decision["agent_scores"]
        )
    except Exception as e:
        print(f"[Pipeline] Failed to save prediction: {e}")

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
    close = data["Close"]
    return {
        "dates":  [str(x.date()) for x in data.index],
        "open":   [_clean_val(v) for v in data["Open"]],
        "high":   [_clean_val(v) for v in data["High"]],
        "low":    [_clean_val(v) for v in data["Low"]],
        "close":  [_clean_val(v) for v in close],
        "volume": [int(v) if not math.isnan(float(v)) else 0 for v in data["Volume"]],
        "sma20":  [_clean_val(v) for v in close.rolling(20).mean()],
        "sma50":  [_clean_val(v) for v in close.rolling(50).mean()] if len(data) >= 50 else [],
    }


@app.get("/price/{symbol}")
def get_price(symbol: str):
    data, resolved_symbol = stock_service.get_stock_data(symbol)
    if data.empty:
        return {"error": "Stock not found"}
    prices = _get_exchange_prices(resolved_symbol, data)
    return {"prices": prices, "resolved_symbol": resolved_symbol}


@app.get("/learning/stats")
def learning_stats():
    """Learning pipeline ka status dekho."""
    return get_stats()


# Mount frontend
frontend_path = str(Path(__file__).resolve().parent / "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
