from newsapi import NewsApiClient

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
            # Strip exchange suffixes like .NS / .BO from search query for NewsAPI
            clean_query = company
            if company.endswith((".NS", ".BO")):
                clean_query = company[:-3]

            news = self.client.get_everything(
                q=clean_query,
                language="en",
                sort_by="publishedAt",
                page_size=5,
            )
            return news.get("articles", [])
        except Exception as e:
            print(f"Error fetching news for {company}: {e}")
            return []
