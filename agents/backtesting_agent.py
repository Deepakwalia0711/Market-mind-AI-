import pandas as pd
import numpy as np


class BacktestingAgent:
    """
    Advanced Backtesting with:
    - SMA Crossover Strategy (20/50)
    - RSI-based strategy
    - Sharpe Ratio
    - Sortino Ratio
    - Calmar Ratio
    - Win Rate, Profit Factor
    - Market comparison (Buy & Hold vs Strategy)
    """

    def analyze(self, data: pd.DataFrame) -> dict:
        if data is None or data.empty or len(data) < 60:
            return {}

        try:
            df = data.copy()
            df['Daily_Return'] = df['Close'].pct_change()

            # --- Strategy 1: SMA Crossover (20/50) ---
            df['SMA20'] = df['Close'].rolling(20).mean()
            df['SMA50'] = df['Close'].rolling(50).mean()
            df['SMA_Signal'] = np.where(df['SMA20'] > df['SMA50'], 1, 0)
            df['SMA_Strategy_Return'] = df['SMA_Signal'].shift(1) * df['Daily_Return']

            # --- Strategy 2: RSI Strategy ---
            delta = df['Close'].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            df['RSI'] = 100 - (100 / (1 + rs))
            # Buy when RSI < 40, Sell when RSI > 65
            df['RSI_Signal'] = np.where(df['RSI'] < 40, 1, np.where(df['RSI'] > 65, 0, np.nan))
            df['RSI_Signal'] = df['RSI_Signal'].ffill().fillna(0)
            df['RSI_Strategy_Return'] = df['RSI_Signal'].shift(1) * df['Daily_Return']

            # Choose best strategy
            sma_total = (1 + df['SMA_Strategy_Return'].dropna()).prod() - 1
            rsi_total = (1 + df['RSI_Strategy_Return'].dropna()).prod() - 1

            if rsi_total > sma_total:
                strat_col = 'RSI_Strategy_Return'
                strategy_name = "RSI Strategy (Buy<40 / Sell>65)"
            else:
                strat_col = 'SMA_Strategy_Return'
                strategy_name = "SMA Crossover (20/50)"

            strat_returns = df[strat_col].dropna()
            market_returns = df['Daily_Return'].dropna()

            # --- Total Returns ---
            total_return = float((1 + strat_returns).prod() - 1)
            market_return = float((1 + market_returns).prod() - 1)

            # --- Annualized Return ---
            days = (df.index[-1] - df.index[0]).days
            years = days / 365.25 if days > 0 else 1
            ann_return = float(((1 + total_return) ** (1 / years)) - 1)

            # --- Sharpe Ratio (Risk-free = 6.5% annual) ---
            rf_daily = 0.065 / 252
            excess = strat_returns - rf_daily
            sharpe = float((excess.mean() / strat_returns.std()) * np.sqrt(252)) if strat_returns.std() > 0 else 0.0

            # --- Sortino Ratio (only downside std) ---
            downside = strat_returns[strat_returns < 0]
            downside_std = downside.std() if len(downside) > 0 else strat_returns.std()
            sortino = float((excess.mean() / downside_std) * np.sqrt(252)) if downside_std > 0 else 0.0

            # --- Max Drawdown ---
            cum = (1 + strat_returns).cumprod()
            rolling_max = cum.cummax()
            drawdown = (cum - rolling_max) / rolling_max
            max_dd = float(drawdown.min())

            # --- Calmar Ratio ---
            calmar = float(ann_return / abs(max_dd)) if max_dd != 0 else 0.0

            # --- Win Rate ---
            winning = (strat_returns > 0).sum()
            total_trades = (strat_returns != 0).sum()
            win_rate = float(winning / total_trades) if total_trades > 0 else 0.0

            # --- Profit Factor ---
            gross_profit = strat_returns[strat_returns > 0].sum()
            gross_loss = abs(strat_returns[strat_returns < 0].sum())
            profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else 0.0

            # --- Signal ---
            if total_return > 0.3 and sharpe > 1.0:
                signal = "Highly Profitable"
            elif total_return > 0:
                signal = "Profitable"
            else:
                signal = "Unprofitable"

            alpha = total_return - market_return  # Excess return vs buy & hold

            score = min(100, max(0, 50 + int(total_return * 30) + int(sharpe * 10)))

            return {
                "strategy": strategy_name,
                "years_tested": round(years, 1),
                "total_return": f"{total_return * 100:+.1f}%",
                "market_return": f"{market_return * 100:+.1f}%",
                "alpha": f"{alpha * 100:+.1f}%",
                "annualized_return": f"{ann_return * 100:+.1f}%",
                "sharpe_ratio": round(sharpe, 2),
                "sortino_ratio": round(sortino, 2),
                "calmar_ratio": round(calmar, 2),
                "max_drawdown": f"{abs(max_dd) * 100:.1f}%",
                "win_rate": f"{win_rate * 100:.1f}%",
                "profit_factor": round(profit_factor, 2),
                "signal": signal,
                "score": score
            }

        except Exception as e:
            print(f"BacktestingAgent error: {e}")
            return {}
