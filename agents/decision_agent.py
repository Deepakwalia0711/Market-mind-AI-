class DecisionAgent:
    def analyze(self, history, technical, news, moneycontrol=None):
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
            reasons.append("Positive news sentiment")

        max_score = 3
        if moneycontrol and moneycontrol.get("analysis"):
            max_score += 1
            mc_analysis = moneycontrol["analysis"]
            if mc_analysis["sentiment"] == "Positive":
                score += 1
                reasons.append("Moneycontrol SWOT analysis is positive")
            elif mc_analysis["sentiment"] == "Negative":
                score -= 1
                reasons.append("Moneycontrol SWOT analysis shows high risk")

        decision = "Hold"
        if max_score == 4:
            if score >= 3:
                decision = "Buy"
            elif score <= 1:
                decision = "Avoid"
        else:
            if score >= 2:
                decision = "Buy"
            elif score <= 0:
                decision = "Avoid"

        confidence = round((max(0, score) / max_score) * 100, 2)

        return {
            "decision": decision,
            "confidence": confidence,
            "reasons": reasons,
        }

