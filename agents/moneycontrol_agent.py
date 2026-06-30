import re
from services.moneycontrol_service import MoneycontrolService

class MoneycontrolAgent:
    def __init__(self):
        self.service = MoneycontrolService()

    def analyze(self, symbol):
        data = self.service.get_analysis(symbol)
        if not data:
            return None

        # Analyze SWOT lists to calculate a sentiment/sentiment score
        swot = data.get("swot", {})
        
        strength_count = 0
        weakness_count = 0
        opportunity_count = 0
        threat_count = 0

        for key, items in swot.items():
            k_lower = key.lower()
            count = len(items)
            if "strength" in k_lower:
                # E.g. "Strengths (13)" -> extract 13 if possible, else use count of parsed items
                m = re.search(r'\d+', key)
                strength_count = int(m.group(0)) if m else count
            elif "weakness" in k_lower:
                m = re.search(r'\d+', key)
                weakness_count = int(m.group(0)) if m else count
            elif "opportunit" in k_lower:
                m = re.search(r'\d+', key)
                opportunity_count = int(m.group(0)) if m else count
            elif "threat" in k_lower:
                m = re.search(r'\d+', key)
                threat_count = int(m.group(0)) if m else count

        # Simple scoring mechanism
        total_pos = strength_count + opportunity_count
        total_neg = weakness_count + threat_count
        
        score = 50 # Neutral default
        if (total_pos + total_neg) > 0:
            score = round((total_pos / (total_pos + total_neg)) * 100, 2)

        sentiment = "Neutral"
        if score > 60:
            sentiment = "Positive"
        elif score < 40:
            sentiment = "Negative"

        return {
            "company_name": data.get("company_name"),
            "stock_name": data.get("stock_name"),
            "sector": data.get("sector"),
            "mc_url": data.get("mc_url"),
            "metrics": data.get("metrics"),
            "swot": swot,
            "analysis": {
                "score": score,
                "sentiment": sentiment,
                "strengths_total": strength_count,
                "weaknesses_total": weakness_count,
                "opportunities_total": opportunity_count,
                "threats_total": threat_count
            }
        }
