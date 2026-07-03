import hashlib
import random

class SentimentAgent:
    def analyze(self, symbol: str) -> dict:
        seed = int(hashlib.md5(symbol.encode()).hexdigest(), 16)
        rng = random.Random(seed + 1)
        
        score = rng.randint(30, 95)
        mkt_sentiment = "Bullish" if score > 70 else "Bearish" if score < 40 else "Neutral"
        soc_sentiment = "Highly Positive" if score > 80 else "Positive" if score > 60 else "Neutral" if score > 40 else "Negative"
        
        return {
            "market_sentiment": mkt_sentiment,
            "social_sentiment": soc_sentiment,
            "sentiment_score": score,
            "signal": "Positive" if score > 60 else "Negative",
            "score": score
        }
