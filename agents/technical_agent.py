class TechnicalAgent:
    def analyze(self, data):
        if data.empty or len(data) < 14:
            return {"RSI": 50.0}

        delta = data["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return {"RSI": round(float(rsi.iloc[-1]), 2)}
