import pandas as pd
import numpy as np

class BacktestingAgent:
    def analyze(self, data: pd.DataFrame) -> dict:
        if data is None or data.empty or len(data) < 50:
            return {}

        # Simple SMA Crossover Strategy Backtest (SMA20 & SMA50)
        df = data.copy()
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        
        # 1 means Buy, 0 means Sell/Hold
        df['Signal'] = np.where(df['SMA20'] > df['SMA50'], 1, 0)
        df['Position'] = df['Signal'].diff()
        
        # Calculate daily returns
        df['Daily_Return'] = df['Close'].pct_change()
        
        # Strategy Returns (shift position to avoid look-ahead bias)
        df['Strategy_Return'] = df['Signal'].shift(1) * df['Daily_Return']
        
        # Cumulative returns
        df['Cum_Market_Return'] = (1 + df['Daily_Return']).cumprod() - 1
        df['Cum_Strategy_Return'] = (1 + df['Strategy_Return']).cumprod() - 1
        
        if len(df['Cum_Strategy_Return'].dropna()) == 0:
            return {}
            
        total_return = df['Cum_Strategy_Return'].iloc[-1]
        
        # Annualized return
        days = (df.index[-1] - df.index[0]).days
        years = days / 365.25 if days > 0 else 1
        annualized_return = ((1 + total_return) ** (1 / years)) - 1
        
        # Win Rate
        winning_days = len(df[df['Strategy_Return'] > 0])
        total_trading_days = len(df[df['Strategy_Return'] != 0])
        win_rate = (winning_days / total_trading_days) if total_trading_days > 0 else 0
        
        # Max Drawdown
        cum_ret = (1 + df['Strategy_Return']).cumprod()
        running_max = cum_ret.cummax()
        drawdown = (cum_ret - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Dynamic signal
        signal = "Highly Profitable" if total_return > 0.5 else "Profitable" if total_return > 0 else "Unprofitable"
        
        return {
            "strategy": "SMA Crossover (20/50)",
            "years_tested": round(years, 1),
            "total_return": f"{total_return * 100:+.1f}%",
            "annualized_return": f"{annualized_return * 100:+.1f}%",
            "max_drawdown": f"{max_drawdown * 100:.1f}%",
            "win_rate": f"{win_rate * 100:.1f}%",
            "signal": signal,
            "score": min(100, max(0, 50 + int(total_return * 50)))
        }
