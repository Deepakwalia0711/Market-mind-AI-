import hashlib
import random

class RiskAgent:
    def analyze(self, symbol: str) -> dict:
        seed = int(hashlib.md5(symbol.encode()).hexdigest(), 16)
        rng = random.Random(seed + 4)
        
        beta = round(rng.uniform(0.5, 2.5), 2)
        volatility = "High" if beta > 1.5 else "Moderate" if beta > 0.8 else "Low"
        var = f"{round(rng.uniform(1.0, 10.0), 1)}%"
        
        penalty = -10 if beta > 1.8 else -5 if beta > 1.2 else 0
        score = 100 - int(beta * 20)
        
        return {
            "volatility": volatility,
            "beta": beta,
            "value_at_risk": var,
            "signal": f"{volatility} Risk",
            "score": max(0, min(100, score)),
            "risk_penalty": penalty
        }
