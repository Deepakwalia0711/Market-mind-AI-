import json
import urllib.request
import urllib.parse
import re

class MoneycontrolService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def resolve_symbol(self, symbol):
        """
        Queries Moneycontrol search suggestion API to match symbol to a MC profile page
        """
        # Strip common exchange suffixes for cleaner search in MC
        clean_query = symbol
        if symbol.endswith((".NS", ".BO")):
            clean_query = symbol[:-3]
            
        url = f"https://www.moneycontrol.com/mccode/common/autosuggestion_solr.php?classic=true&query={urllib.parse.quote(clean_query)}&type=1&format=json"
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                text = response.read().decode('utf-8', errors='ignore').strip()
                if not text:
                    return None
                suggestions = json.loads(text)
                
                # Prioritize first match that has a link_src
                for s in suggestions:
                    if s.get('link_src'):
                        # If query matches closely
                        return s
        except Exception as e:
            print(f"Error resolving Moneycontrol symbol '{symbol}': {e}")
        return None

    def fetch_ratios(self, link_url):
        """
        Fetches main stock page and parses key valuation ratios/metrics
        """
        metrics = {}
        try:
            req = urllib.request.Request(link_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                tds = re.findall(r'<td[^>]*>(.*?)</td>', html, re.DOTALL)
                clean_tds = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', td)).strip() for td in tds]
                
                def get_val(label):
                    for idx, text in enumerate(clean_tds):
                        if text == label or text.startswith(label):
                            if idx + 1 < len(clean_tds):
                                return clean_tds[idx + 1]
                    return None
                
                metrics['market_cap_cr'] = get_val("Mkt Cap (Rs. Cr.)")
                metrics['pe'] = get_val("TTM PE")
                metrics['sector_pe'] = get_val("Sector PE")
                metrics['pb'] = get_val("P/B")
                metrics['dividend_yield'] = get_val("Dividend Yield")
                metrics['book_value'] = get_val("Book Value Per Share")
                metrics['beta'] = get_val("Beta")
                metrics['eps'] = get_val("TTM EPS")
                metrics['fifty_two_w_high'] = get_val("52 Week High")
                metrics['fifty_two_w_low'] = get_val("52 Week Low")
        except Exception as e:
            print(f"Error fetching Moneycontrol key ratios from {link_url}: {e}")
        return metrics

    def fetch_swot(self, mc_name, mc_code):
        """
        Fetches SWOT analysis sub-page and parses strengths, weaknesses, opportunities, and threats
        """
        swot_data = {}
        swot_url = f"https://www.moneycontrol.com/swot-analysis/{mc_name}/{mc_code}/strength"
        try:
            req = urllib.request.Request(swot_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                
                # Locate swot count and lists
                pattern = r'<div class="swot_count">\s*<strong>([^<]+)</strong>\s*</div>\s*<ul class="swotfeatlist">(.*?)</ul>'
                matches = re.findall(pattern, html, re.DOTALL)
                
                for title, list_html in matches:
                    title_clean = title.strip()
                    lis = re.findall(r'<li>(.*?)</li>', list_html, re.DOTALL)
                    lis_clean = [re.sub(r'<[^>]+>', '', li).strip() for li in lis]
                    swot_data[title_clean] = lis_clean
        except Exception as e:
            print(f"Error fetching SWOT data for {mc_name}/{mc_code}: {e}")
        return swot_data

    def get_analysis(self, symbol):
        """
        Orchestrates symbol resolution, metric parsing, and SWOT extraction
        """
        suggestion = self.resolve_symbol(symbol)
        if not suggestion:
            return None
            
        link_src = suggestion.get('link_src')
        if not link_src:
            return None
            
        parts = link_src.strip("/").split("/")
        if len(parts) < 2:
            return None
            
        mc_name = parts[-2]
        mc_code = parts[-1]
        
        metrics = self.fetch_ratios(link_src)
        swot = self.fetch_swot(mc_name, mc_code)
        
        return {
            "company_name": suggestion.get('name'),
            "stock_name": suggestion.get('stock_name'),
            "sector": suggestion.get('sc_sector'),
            "mc_url": link_src,
            "metrics": metrics,
            "swot": swot
        }
