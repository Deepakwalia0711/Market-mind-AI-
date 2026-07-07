from services.news_service import NewsService
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = None

def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


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
                "analysis_method": "No News Found",
                "score": 0
            }

        analyzer = _get_analyzer()
        total_compound = 0
        article_list = []

        for article in articles:
            title = article.get("title", "")
            if not title:
                continue
                
            scores = analyzer.polarity_scores(title)
            compound = scores['compound']
            total_compound += compound
            
            if compound >= 0.05:
                art_sent = "Positive"
            elif compound <= -0.05:
                art_sent = "Negative"
            else:
                art_sent = "Neutral"

            article_list.append({
                "title": title,
                "url": article.get("url"),
                "publishedAt": article.get("publishedAt"),
                "sentiment": art_sent,
                "compound_score": compound
            })

        avg_compound = total_compound / max(len(article_list), 1)

        if avg_compound >= 0.05:
            overall_sentiment = "Positive"
        elif avg_compound <= -0.05:
            overall_sentiment = "Negative"
        else:
            overall_sentiment = "Neutral"

        return {
            "sentiment": overall_sentiment,
            "news_count": len(article_list),
            "articles": article_list,
            "analysis_method": "VADER (NLP Lexicon)",
            "score": avg_compound
        }
