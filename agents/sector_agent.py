import yfinance as yf


# Map NSE/BSE suffix to sector-index mapping
NIFTY_SECTOR_MAP = {
    "IT": ["INFY.NS", "TCS.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
    "Energy": ["RELIANCE.NS", "ONGC.NS", "POWERGRID.NS", "NTPC.NS", "BPCL.NS"],
    "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS"],
    "Auto": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS"],
    "FMCG": ["HINDUNILVR.NS", "ITC.NS", "NESTLEIND.NS", "BRITANNIA.NS", "DABUR.NS"],
    "Metal": ["TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "COALINDIA.NS", "VEDL.NS"],
    "Infra": ["LTIM.NS", "LT.NS", "ADANIPORTS.NS", "ULTRACEMCO.NS", "GRASIM.NS"],
}


def _get_sector_for_symbol(symbol: str) -> tuple:
    """Try to detect sector from yfinance info."""
    try:
        info = yf.Ticker(symbol).info
        sector = info.get("sector", None)
        industry = info.get("industry", None)
        return sector, industry
    except Exception:
        return None, None


def _get_nifty50_performance() -> float:
    """Get recent NIFTY 50 index performance (1 month)."""
    try:
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period="1mo")
        if not hist.empty:
            start = float(hist['Close'].iloc[0])
            end = float(hist['Close'].iloc[-1])
            return round(((end - start) / start) * 100, 2)
    except Exception:
        pass
    return 0.0


def _get_sector_performance(sector_symbols: list) -> float:
    """Average performance of sector peers over 1 month."""
    performances = []
    for sym in sector_symbols[:3]:  # limit to 3 to keep fast
        try:
            hist = yf.Ticker(sym).history(period="1mo")
            if not hist.empty and len(hist) > 1:
                perf = ((float(hist['Close'].iloc[-1]) - float(hist['Close'].iloc[0])) /
                        float(hist['Close'].iloc[0])) * 100
                performances.append(perf)
        except Exception:
            pass
    return round(sum(performances) / len(performances), 2) if performances else 0.0


class SectorAgent:
    """
    Uses real Yahoo Finance data to determine sector and sector performance.
    """

    def analyze(self, symbol: str) -> dict:
        try:
            # Get sector from yfinance
            yf_sector, industry = _get_sector_for_symbol(symbol)

            # Map yfinance sector to our local map
            sector_name = yf_sector or "Unknown"
            sector_peers = None

            for our_sector, peers in NIFTY_SECTOR_MAP.items():
                if our_sector.lower() in (sector_name or "").lower():
                    sector_name = our_sector
                    sector_peers = peers
                    break

            # Get performance
            if sector_peers:
                sector_perf = _get_sector_performance(sector_peers)
            else:
                # Fallback: use NIFTY 50 broad market
                sector_perf = _get_nifty50_performance()
                sector_name = yf_sector or "Broad Market"

            score = int(50 + (sector_perf * 2))
            score = max(0, min(100, score))

            return {
                "sector": sector_name,
                "industry": industry or "N/A",
                "sector_performance": f"{sector_perf:+.1f}%",
                "trend": "Upward" if sector_perf > 0 else "Downward",
                "signal": "Positive" if sector_perf > 0 else "Negative",
                "score": score,
                "data_source": "Yahoo Finance (Real)"
            }

        except Exception as e:
            print(f"SectorAgent error for {symbol}: {e}")
            return {
                "sector": "Unknown",
                "industry": "N/A",
                "sector_performance": "+0.0%",
                "trend": "Neutral",
                "signal": "Neutral",
                "score": 50,
                "data_source": "Fallback (API Error)"
            }
