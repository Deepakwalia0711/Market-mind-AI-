import yfinance as yf
import numpy as np
import pandas as pd


class RiskAgent:
    """
    Real Risk Analysis using:
    - Beta (vs NIFTY 50 benchmark)
    - Historical Volatility (Annualized Std Dev)
    - Value at Risk (VaR 95%)
    - Maximum Drawdown
    """

    def analyze(self, symbol: str) -> dict:
        try:
            # Fetch stock and NIFTY 50 (benchmark) data - 1 year
            stock_data = yf.Ticker(symbol).history(period="1y")
            nifty_data = yf.Ticker("^NSEI").history(period="1y")

            if stock_data.empty or len(stock_data) < 30:
                return self._fallback()

            # Daily returns
            stock_returns = stock_data['Close'].pct_change().dropna()

            # --- Annualized Volatility ---
            daily_vol = stock_returns.std()
            annual_vol = daily_vol * np.sqrt(252)  # 252 trading days per year

            # --- Beta vs NIFTY 50 ---
            beta = 1.0
            if not nifty_data.empty:
                nifty_returns = nifty_data['Close'].pct_change().dropna()
                # Align both series by date
                combined = pd.DataFrame({
                    'stock': stock_returns,
                    'nifty': nifty_returns
                }).dropna()
                if len(combined) > 20:
                    cov = combined['stock'].cov(combined['nifty'])
                    var_nifty = combined['nifty'].var()
                    beta = round(cov / var_nifty, 2) if var_nifty != 0 else 1.0

            # --- Value at Risk (VaR 95%) ---
            # 95% VaR: worst loss on 95% of days
            var_95 = float(np.percentile(stock_returns, 5))

            # --- Maximum Drawdown ---
            cum_returns = (1 + stock_returns).cumprod()
            rolling_max = cum_returns.cummax()
            drawdown = (cum_returns - rolling_max) / rolling_max
            max_drawdown = float(drawdown.min())

            # --- Sharpe Ratio (Risk-adjusted return) ---
            risk_free_rate = 0.065 / 252  # ~6.5% India risk-free rate daily
            excess_returns = stock_returns - risk_free_rate
            sharpe = float((excess_returns.mean() / stock_returns.std()) * np.sqrt(252)) if stock_returns.std() > 0 else 0.0

            # --- Risk Classification ---
            if annual_vol > 0.4 or beta > 1.8:
                volatility_label = "High"
                risk_penalty = -10
            elif annual_vol > 0.25 or beta > 1.2:
                volatility_label = "Moderate"
                risk_penalty = -5
            else:
                volatility_label = "Low"
                risk_penalty = 0

            # Score: higher Sharpe = better, lower beta = safer
            score = 60
            score += min(20, sharpe * 10)  # good Sharpe adds points
            score -= min(30, beta * 10)    # high beta deducts points
            score = max(0, min(100, int(score)))

            return {
                "volatility": volatility_label,
                "annual_volatility": f"{annual_vol * 100:.1f}%",
                "beta": round(beta, 2),
                "value_at_risk": f"{abs(var_95) * 100:.2f}%",
                "max_drawdown": f"{abs(max_drawdown) * 100:.1f}%",
                "sharpe_ratio": round(sharpe, 2),
                "signal": f"{volatility_label} Risk",
                "score": score,
                "risk_penalty": risk_penalty,
                "data_source": "Yahoo Finance (Real - Beta vs NIFTY50)"
            }

        except Exception as e:
            print(f"RiskAgent error for {symbol}: {e}")
            return self._fallback()

    def _fallback(self):
        return {
            "volatility": "Moderate",
            "annual_volatility": "N/A",
            "beta": 1.0,
            "value_at_risk": "N/A",
            "max_drawdown": "N/A",
            "sharpe_ratio": 0.0,
            "signal": "Moderate Risk",
            "score": 50,
            "risk_penalty": 0,
            "data_source": "Fallback"
        }
