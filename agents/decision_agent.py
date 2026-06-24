class DecisionAgent:
    def analyze(self, history, technical, news):
        score = 0
        reasons = []

        if history["trend"] == "Bullish":
            score += 1
            reasons.append("Historical trend positive")

        if technical["RSI"] < 70:
            score += 1
            reasons.append("RSI healthy")

        if news["sentiment"] == "Positive":
            score += 1
            reasons.append("Positive news")

        decision = "Hold"
        if score >= 3:
            decision = "Buy"
        elif score <= 1:
            decision = "Avoid"

        confidence = round((score / 3) * 100, 2)

        return {
            "decision": decision,
            "confidence": confidence,
            "reasons": reasons,
        }
