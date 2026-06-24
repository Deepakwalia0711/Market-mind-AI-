class HistoricalAgent:
    def analyze(self, data):
        if data.empty:
            return {"trend": "Neutral"}

        first_close = data["Close"].iloc[0]
        last_close = data["Close"].iloc[-1]

        if last_close > first_close * 1.05:
            trend = "Bullish"
        elif last_close < first_close * 0.95:
            trend = "Bearish"
        else:
            trend = "Neutral"

        return {"trend": trend}
