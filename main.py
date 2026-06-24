from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agents.decision_agent import DecisionAgent
from agents.historical_agent import HistoricalAgent
from agents.news_agent import NewsAgent
from agents.technical_agent import TechnicalAgent
from services.stock_service import StockService

app = FastAPI()

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
decision = DecisionAgent()


@app.get("/")
@app.head("/")
def root():
    return {"status": "healthy", "message": "MarketMind AI API is running"}




def _chart_payload(data):
    if data.empty:
        return []

    return [
        {
            "date": index.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
        }
        for index, row in data.iterrows()
    ]


@app.get("/analyze/{symbol}")
def analyze(symbol: str):
    data, resolved_symbol = stock_service.get_stock_data(symbol)
    if data.empty:
        return {"error": "Stock not found"}
    history_result = historical.analyze(data)
    technical_result = technical.analyze(data)
    news_result = news.analyze(symbol)
    final_decision = decision.analyze(
        history_result,
        technical_result,
        news_result,
    )

    candle_result = {"sentiment": "Positive", "pattern": "Bullish Engulfing"}
    final_result = final_decision
    ai_summary = "Bullish trend with positive sentiment..."

    prices = {}
    if resolved_symbol.endswith((".NS", ".BO")):
        import yfinance as yf
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
        prices["Default"] = round(float(data["Close"].iloc[-1]), 2)

    return {
        "stock": symbol,
        "resolved_symbol": resolved_symbol,
        "prices": prices,
        "history": history_result,
        "technical": technical_result,
        "news": news_result,
        "candle": candle_result,
        "decision": final_result,
        "agent_scores": {
            "Historical": 75,
            "Technical": 85,
            "News": 70,
            "Candlestick": 80,
            "Risk": 65
        },
        "ai_summary": ai_summary
    }


@app.get("/chart-data/{symbol}")
def get_chart_data(symbol: str):
    data, resolved_symbol = stock_service.get_stock_data(symbol)
    if data.empty:
        return {"error": "Stock not found"}
    return {
        "dates": [str(x.date()) for x in data.index],
        "open": data["Open"].tolist(),
        "high": data["High"].tolist(),
        "low": data["Low"].tolist(),
        "close": data["Close"].tolist()
    }


@app.get("/price/{symbol}")
def get_price(symbol: str):
    data, resolved_symbol = stock_service.get_stock_data(symbol)
    if data.empty:
        return {"error": "Stock not found"}
    
    prices = {}
    if resolved_symbol.endswith((".NS", ".BO")):
        import yfinance as yf
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
        prices["Default"] = round(float(data["Close"].iloc[-1]), 2)

    return {
        "prices": prices,
        "resolved_symbol": resolved_symbol
    }



