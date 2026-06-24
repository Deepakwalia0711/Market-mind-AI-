from newsapi import NewsApiClient

from utils.config import NEWS_API_KEY


class NewsService:
    def __init__(self):
        self.client = NewsApiClient(api_key=NEWS_API_KEY)

    def get_news(self, company):
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
