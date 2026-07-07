from newsapi import NewsApiClient
import yfinance as yf

from utils.config import NEWS_API_KEY


class NewsService:
    def __init__(self):
        if NEWS_API_KEY:
            self.client = NewsApiClient(api_key=NEWS_API_KEY)
        else:
            self.client = None

    def get_news(self, company):
        if not self.client:
            print(f"NewsAPI key is missing. Skipping news fetch for {company}.")
            return []
        try:
            # Try to get the actual company name for better search accuracy
            try:
                ticker = yf.Ticker(company)
                short_name = ticker.info.get('shortName')
                if short_name:
                    # Use the first two words (e.g., "RELIANCE INDUSTRIES LTD" -> "RELIANCE INDUSTRIES")
                    words = short_name.split()
                    if len(words) > 1:
                        name_phrase = " ".join(words[:2]).replace(",", "")
                        clean_query = f'"{name_phrase}"'
                    else:
                        clean_query = words[0]
                else:
                    # Fallback if no shortName
                    clean_query = company
                    if company.endswith((".NS", ".BO")):
                        clean_query = company[:-3]
                    clean_query = f"{clean_query} stock"
            except Exception as e:
                print(f"Error resolving company name for news: {e}")
                clean_query = company
                if company.endswith((".NS", ".BO")):
                    clean_query = company[:-3]
                clean_query = f"{clean_query} stock"

            news = self.client.get_everything(
                q=clean_query,
                language="en",
                sort_by="relevancy",
                page_size=5,
            )
            return news.get("articles", [])
        except Exception as e:
            print(f"Error fetching news for {company}: {e}")
            return []
