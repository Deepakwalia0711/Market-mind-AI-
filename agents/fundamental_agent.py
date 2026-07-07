import yfinance as yf

class FundamentalAgent:
    """
    Fetches real fundamental data from Yahoo Finance.
    """
    def analyze(self, symbol: str) -> dict:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                return self._fallback()

            # Extract metrics
            pe_ratio = info.get('trailingPE', 0)
            eps = info.get('trailingEps', 0)
            revenue_growth = info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0
            debt_to_equity = info.get('debtToEquity', 0) / 100 if info.get('debtToEquity') else 0
            roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
            
            # Simple health score logic based on common metrics
            health_score = 50 # Base score
            
            # PE Ratio (lower is generally better, but not negative)
            if 0 < pe_ratio < 20: health_score += 10
            elif 20 <= pe_ratio < 40: health_score += 5
            elif pe_ratio > 40: health_score -= 5
            
            # ROE (higher is better)
            if roe > 15: health_score += 15
            elif roe > 10: health_score += 10
            elif roe < 5: health_score -= 10
            
            # Revenue Growth (higher is better)
            if revenue_growth > 15: health_score += 15
            elif revenue_growth > 5: health_score += 5
            elif revenue_growth < 0: health_score -= 10
            
            # Debt to Equity (lower is better)
            if 0 <= debt_to_equity < 1: health_score += 10
            elif debt_to_equity > 2: health_score -= 10

            health_score = max(0, min(100, health_score))

            signal = "Strong Buy" if health_score > 80 else "Buy" if health_score > 60 else "Hold" if health_score > 40 else "Sell"

            return {
                "pe_ratio": round(pe_ratio, 2) if pe_ratio else "N/A",
                "eps": round(eps, 2) if eps else "N/A",
                "revenue_growth": round(revenue_growth, 2) if revenue_growth else "N/A",
                "debt_to_equity": round(debt_to_equity, 2) if debt_to_equity else "N/A",
                "roe": round(roe, 2) if roe else "N/A",
                "roce": "N/A", # Yahoo finance doesn't directly provide ROCE easily in 'info'
                "health_score": health_score,
                "signal": signal,
                "score": health_score,
                "data_source": "Yahoo Finance (Real)"
            }

        except Exception as e:
            print(f"FundamentalAgent error for {symbol}: {e}")
            return self._fallback()

    def _fallback(self):
        return {
            "pe_ratio": "N/A",
            "eps": "N/A",
            "revenue_growth": "N/A",
            "debt_to_equity": "N/A",
            "roe": "N/A",
            "roce": "N/A",
            "health_score": 50,
            "signal": "Neutral",
            "score": 50,
            "data_source": "Fallback (API Error)"
        }
