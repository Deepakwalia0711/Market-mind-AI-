class DecisionAgent:
    def analyze(self, history, technical, news, moneycontrol=None, fundamentals=None, sentiment=None, insider=None, sector=None, risk=None):
        """
        Aggregates all agent signals into a final Buy / Hold / Avoid decision.
        Each input dict must include a `score` (0–100).
        Returns the decision, confidence %, agent_scores dict, and reasons list.
        """
        reasons = []
        agent_scores = {}

        # --- Historical Agent ---
        hist_score = history.get("score", 50)
        agent_scores["Historical"] = round(hist_score)
        trend = history.get("trend", "Neutral")
        change_pct = history.get("change_pct", 0.0)
        if "Bullish" in trend:
            reasons.append(f"Historical trend is {trend} ({change_pct:+.1f}% over 2 years)")
        elif "Bearish" in trend:
            reasons.append(f"Historical trend is {trend} ({change_pct:+.1f}% over 2 years) — caution advised")

        # --- Technical Agent ---
        tech_score = technical.get("score", 50)
        agent_scores["Technical"] = round(tech_score)
        rsi = technical.get("RSI", 50)
        sma_signal = technical.get("sma_signal", "Neutral")
        macd_trend = technical.get("macd_trend", "Neutral")

        if rsi < 30:
            reasons.append(f"RSI is oversold at {rsi:.1f} — potential reversal buying opportunity")
        elif rsi > 70:
            reasons.append(f"RSI is overbought at {rsi:.1f} — sell pressure likely")
        else:
            reasons.append(f"RSI at {rsi:.1f} — in healthy range")

        if sma_signal == "Bullish":
            reasons.append("SMA20 above SMA50 — bullish crossover confirmed")
        elif sma_signal == "Bearish":
            reasons.append("SMA20 below SMA50 — bearish crossover signal")

        if macd_trend == "Bullish":
            reasons.append("MACD above signal line — upward momentum")
        else:
            reasons.append("MACD below signal line — downward momentum")

        # --- News Agent ---
        news_score_map = {"Positive": 72, "Neutral": 50, "Negative": 28}
        news_sentiment = news.get("sentiment", "Neutral")
        news_score = news_score_map.get(news_sentiment, 50)
        agent_scores["News"] = news_score
        news_count = news.get("news_count", 0)
        if news_sentiment != "Neutral":
            reasons.append(f"News sentiment is {news_sentiment} based on {news_count} recent articles")

        # --- Moneycontrol Agent ---
        mc_score = 50  # Default neutral
        if moneycontrol and moneycontrol.get("analysis"):
            mc_analysis = moneycontrol["analysis"]
            raw_score = mc_analysis.get("score", 50)
            mc_score = round(raw_score)
            mc_sentiment = mc_analysis.get("sentiment", "Neutral")
            sw = mc_analysis.get("strengths_total", 0)
            wk = mc_analysis.get("weaknesses_total", 0)
            op = mc_analysis.get("opportunities_total", 0)
            th = mc_analysis.get("threats_total", 0)
            reasons.append(
                f"Moneycontrol SWOT: {sw} strengths, {op} opportunities vs {wk} weaknesses, {th} threats — {mc_sentiment} outlook"
            )

        agent_scores["Moneycontrol"] = mc_score

        # --- New Agents ---
        if fundamentals:
            agent_scores["Fundamental"] = fundamentals.get("score", 50)
            reasons.append(f"Fundamentals: PE {fundamentals.get('pe_ratio')}, Health {fundamentals.get('health_score')}/100")
        if sentiment:
            agent_scores["Sentiment"] = sentiment.get("score", 50)
            reasons.append(f"Sentiment: {sentiment.get('market_sentiment')} (Social: {sentiment.get('social_sentiment')})")
        if insider:
            agent_scores["Insider"] = insider.get("score", 50)
            reasons.append(f"Insider: {insider.get('net_activity')} trend ({insider.get('recent_transactions')} recent transactions)")
        if sector:
            agent_scores["Sector"] = sector.get("score", 50)
            reasons.append(f"Sector ({sector.get('sector')}): {sector.get('trend')} ({sector.get('sector_performance')})")
        
        if risk:
            agent_scores["Risk"] = risk.get("score", 60)
            reasons.append(f"Risk Profile: {risk.get('signal')} (Beta: {risk.get('beta')})")
        else:
            agent_scores["Risk"] = 60

        # --- Weighted Final Score ---
        # Updated weights matching new multi-agent architecture
        weights = {
            "Historical": 0.05,
            "Technical": 0.20,
            "News": 0.10,
            "Moneycontrol": 0.10,
            "Fundamental": 0.20,
            "Sentiment": 0.10,
            "Insider": 0.05,
            "Sector": 0.10,
        }
        
        total_weight = 0
        weighted_sum = 0
        for k, w in weights.items():
            if k in agent_scores:
                weighted_sum += agent_scores[k] * w
                total_weight += w
        
        if total_weight > 0:
            weighted_score = weighted_sum / total_weight
        else:
            weighted_score = 50
            
        # Apply risk penalty if any
        if risk and "risk_penalty" in risk:
            weighted_score += risk["risk_penalty"]
            agent_scores["Risk Penalty"] = risk["risk_penalty"]
            reasons.append(f"Risk Penalty Applied: {risk['risk_penalty']}")

        weighted_score = max(0, min(100, weighted_score))

        # --- Decision (User's requested thresholds) ---
        if weighted_score > 70:
            decision = "BUY"
        elif weighted_score > 45:
            decision = "HOLD"
        else:
            decision = "SELL"

        confidence = round(weighted_score, 2)

        return {
            "decision": decision,
            "confidence": confidence,
            "reasons": reasons,
            "agent_scores": agent_scores,
            "weighted_score": round(weighted_score, 2),
        }

