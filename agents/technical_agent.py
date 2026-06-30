class TechnicalAgent:
    def analyze(self, data):
        if data.empty or len(data) < 14:
            return {
                "RSI": 50.0,
                "signal": "Neutral",
                "sma20": None,
                "sma50": None,
                "macd": None,
                "macd_signal": None,
                "macd_trend": "Neutral",
                "sma_signal": "Neutral",
                "score": 50,
            }

        close = data["Close"]

        # --- RSI ---
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = round(float(rsi.iloc[-1]), 2)

        # --- SMA 20 / 50 ---
        sma20 = close.rolling(20).mean()
        sma50 = close.rolling(50).mean() if len(data) >= 50 else None

        sma20_val = round(float(sma20.iloc[-1]), 2) if not sma20.isna().iloc[-1] else None
        sma50_val = round(float(sma50.iloc[-1]), 2) if sma50 is not None and not sma50.isna().iloc[-1] else None

        # SMA crossover signal
        sma_signal = "Neutral"
        if sma20_val and sma50_val:
            if sma20_val > sma50_val:
                sma_signal = "Bullish"  # Golden cross zone
            else:
                sma_signal = "Bearish"  # Death cross zone

        # --- MACD ---
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()

        macd_val = round(float(macd_line.iloc[-1]), 4)
        macd_sig_val = round(float(signal_line.iloc[-1]), 4)

        macd_trend = "Bullish" if macd_val > macd_sig_val else "Bearish"

        # --- Composite Score (0–100) ---
        score = 50  # Start neutral

        # RSI contribution
        if rsi_val < 30:
            score += 20  # Oversold = strong buy
        elif rsi_val < 45:
            score += 10  # Healthy
        elif rsi_val > 70:
            score -= 20  # Overbought = sell pressure
        elif rsi_val > 60:
            score -= 5

        # SMA contribution
        if sma_signal == "Bullish":
            score += 15
        elif sma_signal == "Bearish":
            score -= 15

        # MACD contribution
        if macd_trend == "Bullish":
            score += 15
        else:
            score -= 10

        score = max(0, min(100, score))

        # Overall signal
        if score >= 60:
            overall_signal = "Bullish"
        elif score <= 40:
            overall_signal = "Bearish"
        else:
            overall_signal = "Neutral"

        return {
            "RSI": rsi_val,
            "signal": overall_signal,
            "sma20": sma20_val,
            "sma50": sma50_val,
            "macd": macd_val,
            "macd_signal": macd_sig_val,
            "macd_trend": macd_trend,
            "sma_signal": sma_signal,
            "score": score,
            # Pass the series for chart overlays (None instead of NaN for clean Plotly gaps)
            "_sma20_series": [None if v != v else round(v, 2) for v in sma20],
            "_sma50_series": [None if v != v else round(v, 2) for v in sma50] if sma50 is not None else [],
        }
