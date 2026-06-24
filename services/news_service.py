from newsapi import NewsApiClient

from utils.config import NEWS_API_KEY


class NewsService:
    def __init__(self):
        self.client = NewsApiClient(api_key=NEWS_API_KEY)

    def get_news(self, company):
        news = self.client.get_everything(
            q=company,
            language="en",
            sort_by="publishedAt",
            page_size=5,
        )
        return news["articles"]
