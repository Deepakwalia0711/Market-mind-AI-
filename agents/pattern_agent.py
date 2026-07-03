import pandas as pd

class PatternAgent:
    def analyze(self, data: pd.DataFrame) -> dict:
        if data is None or data.empty or len(data) < 5:
            return {}
            
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        
        o, h, l, c = latest['Open'], latest['High'], latest['Low'], latest['Close']
        po, ph, pl, pc = prev['Open'], prev['High'], prev['Low'], prev['Close']
        
        body_size = abs(c - o)
        full_size = h - l
        
        if full_size == 0:
            return {"pattern": "None", "confidence": "", "signal": "Neutral"}
        
        pattern = "None"
        confidence = 0
        
        # Doji
        if body_size <= 0.05 * full_size:
            pattern = "Doji"
            confidence = 85
        # Bullish Engulfing
        elif c > o and pc < po and c > po and o < pc:
            pattern = "Bullish Engulfing"
            confidence = 90
        # Bearish Engulfing
        elif c < o and pc > po and c < po and o > pc:
            pattern = "Bearish Engulfing"
            confidence = 90
        # Hammer
        elif c > o and (o - l) > 2 * body_size and (h - c) < 0.1 * full_size:
            pattern = "Bullish Hammer"
            confidence = 82
        # Shooting Star
        elif c < o and (h - o) > 2 * body_size and (c - l) < 0.1 * full_size:
            pattern = "Bearish Shooting Star"
            confidence = 82
            
        if pattern == "None":
            return {}
            
        return {
            "pattern": pattern,
            "confidence": f"{confidence}%",
            "signal": "Bullish" if "Bullish" in pattern else "Bearish" if "Bearish" in pattern else "Neutral"
        }
