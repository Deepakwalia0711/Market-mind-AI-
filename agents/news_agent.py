from services.news_service import NewsService


class NewsAgent:
    def __init__(self):
        self.news_service = NewsService()

    def analyze(self, company):
        articles = self.news_service.get_news(company)

        if not articles:
            return {
                "sentiment": "Neutral",
                "news_count": 0,
                "articles": [],
            }

        positive_words = [
            "gain",
            "growth",
            "profit",
            "rise",
            "surge",
            "beat",
            "strong",
        ]
        negative_words = [
            "loss",
            "fall",
            "drop",
            "decline",
            "weak",
            "crash",
        ]

        score = 0
        for article in articles:
            title = article["title"].lower()
            for word in positive_words:
                if word in title:
                    score += 1
            for word in negative_words:
                if word in title:
                    score -= 1

        sentiment = "Neutral"
        if score > 0:
            sentiment = "Positive"
        elif score < 0:
            sentiment = "Negative"

        return {
            "sentiment": sentiment,
            "news_count": len(articles),
            "articles": [
                {
                    "title": article.get("title"),
                    "url": article.get("url"),
                    "publishedAt": article.get("publishedAt"),
                }
                for article in articles
            ],
        }
