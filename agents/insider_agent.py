import hashlib
import random

class InsiderAgent:
    def analyze(self, symbol: str) -> dict:
        seed = int(hashlib.md5(symbol.encode()).hexdigest(), 16)
        rng = random.Random(seed + 2)
        
        score = rng.randint(40, 85)
        recent = rng.randint(0, 15)
        is_buying = rng.choice([True, False, True]) # slightly biased to buying
        
        return {
            "insider_buying": is_buying,
            "recent_transactions": recent,
            "net_activity": "Buying" if is_buying else "Selling",
            "signal": "Positive" if is_buying else "Negative",
            "score": score if is_buying else 100 - score
        }
