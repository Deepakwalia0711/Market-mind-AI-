import hashlib
import random

class FundamentalAgent:
    def analyze(self, symbol: str) -> dict:
        seed = int(hashlib.md5(symbol.encode()).hexdigest(), 16)
        rng = random.Random(seed)
        
        pe_ratio = round(rng.uniform(10.0, 50.0), 1)
        eps = round(rng.uniform(2.0, 150.0), 1)
        revenue_growth = round(rng.uniform(-5.0, 30.0), 1)
        debt_to_equity = round(rng.uniform(0.1, 2.5), 2)
        roe = round(rng.uniform(5.0, 35.0), 1)
        roce = round(rng.uniform(5.0, 30.0), 1)
        health_score = rng.randint(40, 95)
        
        signal = "Strong Buy" if health_score > 80 else "Buy" if health_score > 60 else "Hold" if health_score > 40 else "Sell"
        score = health_score
        
        return {
            "pe_ratio": pe_ratio,
            "eps": eps,
            "revenue_growth": revenue_growth,
            "debt_to_equity": debt_to_equity,
            "roe": roe,
            "roce": roce,
            "health_score": health_score,
            "signal": signal,
            "score": score
        }
