import yfinance as yf


class InsiderAgent:
    """
    Fetches real insider trading data from Yahoo Finance.
    Uses major holders data + institutional holdings as proxy for smart money activity.
    """

    def analyze(self, symbol: str) -> dict:
        try:
            ticker = yf.Ticker(symbol)

            # Get major holders (institutional + insider %)
            holders = ticker.major_holders
            insider_pct = 0.0
            institution_pct = 0.0

            if holders is not None and not holders.empty:
                try:
                    # Row 0: % of shares held by insiders
                    # Row 1: % of shares held by institutions
                    insider_pct = float(str(holders.iloc[0, 0]).replace('%', ''))
                    institution_pct = float(str(holders.iloc[1, 0]).replace('%', ''))
                except Exception:
                    pass

            # Get recent insider transactions
            insider_tx = ticker.insider_transactions
            recent_transactions = 0
            net_buying = 0  # positive = buying, negative = selling

            if insider_tx is not None and not insider_tx.empty:
                recent_transactions = len(insider_tx)

                # Check transaction types
                if 'Transaction' in insider_tx.columns:
                    buys = insider_tx['Transaction'].str.contains('Buy|Purchase', case=False, na=False).sum()
                    sells = insider_tx['Transaction'].str.contains('Sale|Sell', case=False, na=False).sum()
                    net_buying = int(buys) - int(sells)
                elif 'Shares' in insider_tx.columns:
                    # Positive shares = buy, negative = sell
                    net_buying = int(insider_tx['Shares'].sum() > 0)

            # Score: based on insider % + net buying activity
            score = 50
            score += min(20, insider_pct * 0.5)       # Higher insider ownership = good
            score += min(20, institution_pct * 0.1)   # Higher inst. holding = good
            score += net_buying * 5                     # Each net buy adds 5 points
            score = max(0, min(100, int(score)))

            is_buying = net_buying >= 0

            return {
                "insider_buying": is_buying,
                "insider_ownership_pct": round(insider_pct, 2),
                "institution_ownership_pct": round(institution_pct, 2),
                "recent_transactions": recent_transactions,
                "net_activity": "Buying" if is_buying else "Selling",
                "signal": "Positive" if is_buying else "Negative",
                "score": score,
                "data_source": "Yahoo Finance (Real)"
            }

        except Exception as e:
            print(f"InsiderAgent error for {symbol}: {e}")
            return {
                "insider_buying": True,
                "insider_ownership_pct": 0.0,
                "institution_ownership_pct": 0.0,
                "recent_transactions": 0,
                "net_activity": "Unknown",
                "signal": "Neutral",
                "score": 50,
                "data_source": "Fallback (API Error)"
            }
