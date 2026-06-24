import json
import urllib.request
import urllib.parse
import yfinance as yf


class StockService:
    def get_stock_data(self, symbol):
        # 1. Try resolving symbol using Yahoo Finance Search API
        resolved_symbol = self._resolve_symbol(symbol)
        if resolved_symbol:
            data = yf.Ticker(resolved_symbol).history(period="6mo")
            if not data.empty:
                return data, resolved_symbol

        # 2. Fallback to original symbol if resolving failed or returned empty
        data = yf.Ticker(symbol).history(period="6mo")
        if not data.empty:
            return data, symbol

        # 3. Try fallback methods (strip spaces, NSE, BSE)
        cleaned = symbol.replace(" ", "").upper()
        if cleaned != symbol.upper():
            data = yf.Ticker(cleaned).history(period="6mo")
            if not data.empty:
                return data, cleaned

        data = yf.Ticker(f"{cleaned}.NS").history(period="6mo")
        if not data.empty:
            return data, f"{cleaned}.NS"

        data = yf.Ticker(f"{cleaned}.BO").history(period="6mo")
        if not data.empty:
            return data, f"{cleaned}.BO"

        return data, symbol

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
