import json
import time
import urllib.request
import urllib.parse
import pandas as pd
import yfinance as yf


def _safe_history(symbol, period="6mo", max_retries=3):
    """Fetch yfinance history with retry + exponential backoff for rate limits."""
    for attempt in range(max_retries):
        try:
            data = yf.Ticker(symbol).history(period=period)
            return data
        except Exception as e:
            err_name = type(e).__name__
            if "RateLimit" in err_name or "429" in str(e):
                wait = 2 ** attempt  # 1s, 2s, 4s
                print(f"[yfinance] Rate limited on '{symbol}', retrying in {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                # Non-rate-limit error — return empty
                print(f"[yfinance] Error fetching '{symbol}': {e}")
                return pd.DataFrame()
    print(f"[yfinance] Exhausted retries for '{symbol}'")
    return pd.DataFrame()


class StockService:
    def get_stock_data(self, symbol):
        # 1. Try resolving symbol using Yahoo Finance Search API
        resolved_symbol = self._resolve_symbol(symbol)
        if resolved_symbol:
            data = _safe_history(resolved_symbol)
            if not data.empty:
                return data, resolved_symbol

        # 2. Fallback to original symbol if resolving failed or returned empty
        data = _safe_history(symbol)
        if not data.empty:
            return data, symbol

        # 3. Try fallback methods (strip spaces, NSE, BSE)
        cleaned = symbol.replace(" ", "").upper()
        if cleaned != symbol.upper():
            data = _safe_history(cleaned)
            if not data.empty:
                return data, cleaned

        data = _safe_history(f"{cleaned}.NS")
        if not data.empty:
            return data, f"{cleaned}.NS"

        data = _safe_history(f"{cleaned}.BO")
        if not data.empty:
            return data, f"{cleaned}.BO"

        return pd.DataFrame(), symbol

    def _resolve_symbol(self, query):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(query)}&quotesCount=10"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                quotes = data.get("quotes", [])
                if quotes:
                    # 1. Prioritize NSE (.NS) listing
                    for q in quotes:
                        sym = q.get("symbol", "")
                        if sym.upper().endswith(".NS"):
                            return sym
                    # 2. Prioritize BSE (.BO) listing
                    for q in quotes:
                        sym = q.get("symbol", "")
                        if sym.upper().endswith(".BO"):
                            return sym
                    # 3. Fallback to the top suggestion
                    return quotes[0].get("symbol")
        except Exception as e:
            print(f"Error resolving symbol '{query}': {e}")
        return None
