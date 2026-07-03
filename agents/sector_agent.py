import hashlib
import random

class SectorAgent:
    def analyze(self, symbol: str) -> dict:
        seed = int(hashlib.md5(symbol.encode()).hexdigest(), 16)
        rng = random.Random(seed + 3)
        
        sectors = ["Technology", "Finance", "Energy", "Healthcare", "Consumer", "Industrials"]
        sector = rng.choice(sectors)
        perf = rng.uniform(-10.0, 15.0)
        
        score = int(50 + (perf * 2))
        score = max(0, min(100, score))
        
        return {
            "sector": sector,
            "sector_performance": f"{perf:+.1f}%",
            "trend": "Upward" if perf > 0 else "Downward",
            "signal": "Positive" if perf > 0 else "Negative",
            "score": score
        }
