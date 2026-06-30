class HistoricalAgent:
    def analyze(self, data):
        if data.empty:
            return {"trend": "Neutral", "score": 50, "change_pct": 0.0, "volatility": 0.0}

        close = data["Close"]
        first_close = float(close.iloc[0])
        last_close = float(close.iloc[-1])

        change_pct = round(((last_close - first_close) / first_close) * 100, 2)

        # Trend classification
        if change_pct > 10:
            trend = "Strongly Bullish"
        elif change_pct > 5:
            trend = "Bullish"
        elif change_pct > 0:
            trend = "Mildly Bullish"
        elif change_pct > -5:
            trend = "Mildly Bearish"
        elif change_pct > -10:
            trend = "Bearish"
        else:
            trend = "Strongly Bearish"

        # Volatility (std dev of daily returns)
        daily_returns = close.pct_change().dropna()
        volatility = round(float(daily_returns.std() * 100), 2)  # % daily std dev

        # Score 0–100 based on price change
        # Map [-20%, +20%] → [0, 100]
        score = round(max(0, min(100, 50 + (change_pct * 2.5))), 2)

        return {
            "trend": trend,
            "change_pct": change_pct,
            "volatility": volatility,
            "score": score,
        }
