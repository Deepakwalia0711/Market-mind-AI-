import numpy as np
from learning.model_trainer import train_and_save_model, load_model, FEATURE_ORDER

_MODEL = None

def _get_model():
    """Load saved model from disk, otherwise train fresh on synthetic data."""
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    # Try loading saved model first (from real training pipeline)
    _MODEL = load_model()
    if _MODEL is None:
        # First run: no saved model yet, train on synthetic data
        print("[DecisionAgent] No saved model found — training on synthetic baseline...")
        _, _, _MODEL = train_and_save_model()
    return _MODEL


class DecisionAgent:
    LABEL_MAP = {0: "SELL", 1: "HOLD", 2: "BUY"}

    def reload_model(self):
        """Force reload model from disk (called after retraining)."""
        global _MODEL
        _MODEL = None
        _get_model()

    def analyze(self, history, technical, news, moneycontrol=None,
                fundamentals=None, sentiment=None, insider=None, sector=None, risk=None):

        agent_scores = {}
        reasons = []

        # Collect scores from all agents
        agent_scores["Historical"]   = round(history.get("score", 50))
        agent_scores["Technical"]    = round(technical.get("score", 50))
        agent_scores["News"]         = {"Positive": 72, "Neutral": 50, "Negative": 28}.get(news.get("sentiment", "Neutral"), 50)
        agent_scores["Moneycontrol"] = round(moneycontrol["analysis"].get("score", 50)) if moneycontrol and moneycontrol.get("analysis") else 50
        agent_scores["Fundamental"]  = fundamentals.get("score", 50) if fundamentals else 50
        agent_scores["Sentiment"]    = sentiment.get("score", 50) if sentiment else 50
        agent_scores["Insider"]      = insider.get("score", 50) if insider else 50
        agent_scores["Sector"]       = sector.get("score", 50) if sector else 50
        agent_scores["Risk"]         = risk.get("score", 60) if risk else 60
        risk_penalty = risk.get("risk_penalty", 0) if risk else 0

        # Feature vector for Random Forest (order must match FEATURE_ORDER)
        feature_vector = np.array([[agent_scores.get(f, 50) for f in FEATURE_ORDER]])

        # Random Forest prediction
        model = _get_model()
        rf_label  = int(model.predict(feature_vector)[0])
        rf_proba  = model.predict_proba(feature_vector)[0]
        decision  = self.LABEL_MAP[rf_label]
        rf_conf   = round(float(max(rf_proba)) * 100, 2)

        # Weighted numeric score (for confidence display)
        weights = {"Historical": 0.05, "Technical": 0.20, "News": 0.10,
                   "Moneycontrol": 0.10, "Fundamental": 0.20, "Sentiment": 0.10,
                   "Insider": 0.05, "Sector": 0.10}
        weighted_sum = sum(agent_scores.get(k, 50) * w for k, w in weights.items())
        total_w = sum(weights.values())
        weighted_score = max(0, min(100, (weighted_sum / total_w) + risk_penalty))

        # Reasons
        trend = history.get("trend", "Neutral")
        change_pct = history.get("change_pct", 0.0)
        if "Bullish" in trend:
            reasons.append(f"Historical trend is {trend} ({change_pct:+.1f}% over 2 years)")
        elif "Bearish" in trend:
            reasons.append(f"Historical trend is {trend} ({change_pct:+.1f}% over 2 years) — caution advised")

        rsi = technical.get("RSI", 50)
        if rsi < 30:
            reasons.append(f"RSI oversold at {rsi:.1f} — reversal opportunity")
        elif rsi > 70:
            reasons.append(f"RSI overbought at {rsi:.1f} — sell pressure likely")
        else:
            reasons.append(f"RSI at {rsi:.1f} — healthy range")

        sma = technical.get("sma_signal", "Neutral")
        macd = technical.get("macd_trend", "Neutral")
        if sma == "Bullish":   reasons.append("SMA20 above SMA50 — bullish crossover confirmed")
        elif sma == "Bearish": reasons.append("SMA20 below SMA50 — bearish crossover signal")
        if macd == "Bullish":  reasons.append("MACD above signal line — upward momentum")
        else:                  reasons.append("MACD below signal line — downward momentum")

        news_sentiment = news.get("sentiment", "Neutral")
        if news_sentiment != "Neutral":
            reasons.append(f"News sentiment: {news_sentiment} ({news.get('news_count', 0)} articles via FinBERT)")

        if moneycontrol and moneycontrol.get("analysis"):
            mc = moneycontrol["analysis"]
            reasons.append(f"Moneycontrol SWOT: {mc.get('strengths_total',0)} strengths vs {mc.get('weaknesses_total',0)} weaknesses")

        if fundamentals: reasons.append(f"Fundamentals: PE {fundamentals.get('pe_ratio')}, Health {fundamentals.get('health_score')}/100")
        if sentiment:    reasons.append(f"Sentiment: {sentiment.get('market_sentiment')} ({sentiment.get('analysis_method', 'FinBERT')})")
        if insider:      reasons.append(f"Insider: {insider.get('net_activity')} — {insider.get('insider_ownership_pct', 0):.1f}% owned")
        if sector:       reasons.append(f"Sector ({sector.get('sector')}): {sector.get('trend')} ({sector.get('sector_performance')})")
        if risk:
            reasons.append(f"Risk: Beta={risk.get('beta')}, Sharpe={risk.get('sharpe_ratio')}, VaR={risk.get('value_at_risk')}")
            if risk_penalty < 0:
                reasons.append(f"Risk penalty {risk_penalty} applied (high volatility/beta)")

        reasons.append(f"Random Forest decision confidence: {rf_conf}%")

        return {
            "decision": decision,
            "confidence": round(weighted_score, 2),
            "rf_confidence": rf_conf,
            "reasons": reasons,
            "agent_scores": agent_scores,
            "weighted_score": round(weighted_score, 2),
            "model_used": "Random Forest (Real-Time Learning Pipeline)"
        }
