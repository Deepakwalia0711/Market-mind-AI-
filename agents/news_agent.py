from services.news_service import NewsService

# Lazy load FinBERT to avoid slow startup
_finbert_pipeline = None

def _get_finbert():
    global _finbert_pipeline
    if _finbert_pipeline is None:
        try:
            from transformers import pipeline
            print("Loading FinBERT model... (first load takes ~30s)")
            _finbert_pipeline = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert",
                device=-1  # CPU
            )
            print("FinBERT loaded successfully!")
        except Exception as e:
            print(f"FinBERT load failed: {e}")
            _finbert_pipeline = None
    return _finbert_pipeline


def _keyword_fallback(articles):
    """Simple keyword fallback if FinBERT unavailable."""
    positive_words = ["gain", "growth", "profit", "rise", "surge", "beat", "strong", "record", "rally"]
    negative_words = ["loss", "fall", "drop", "decline", "weak", "crash", "fear", "risk", "sell-off"]
    score = 0
    for article in articles:
        title = article.get("title", "").lower()
        for w in positive_words:
            if w in title:
                score += 1
        for w in negative_words:
            if w in title:
                score -= 1
    if score > 0:
        return "Positive"
    elif score < 0:
        return "Negative"
    return "Neutral"


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
                "analysis_method": "No News Found"
            }

        # Extract titles for analysis
        titles = [a.get("title", "") for a in articles if a.get("title")]

        # Try FinBERT first
        finbert = _get_finbert()
        analysis_method = "Keyword Matching"

        if finbert and titles:
            try:
                results = finbert(titles, truncation=True, max_length=512)
                # Map FinBERT labels to scores
                label_map = {"positive": 1, "neutral": 0, "negative": -1}
                total = sum(label_map.get(r["label"].lower(), 0) for r in results)

                if total > 0:
                    overall_sentiment = "Positive"
                elif total < 0:
                    overall_sentiment = "Negative"
                else:
                    overall_sentiment = "Neutral"

                analysis_method = "FinBERT (Deep Learning NLP)"

                # Per-article sentiment from FinBERT
                article_list = []
                for i, article in enumerate(articles):
                    if i < len(results):
                        art_sent = results[i]["label"].capitalize()
                        art_conf = round(results[i]["score"] * 100, 1)
                    else:
                        art_sent = "Neutral"
                        art_conf = 50.0
                    article_list.append({
                        "title": article.get("title"),
                        "url": article.get("url"),
                        "publishedAt": article.get("publishedAt"),
                        "sentiment": art_sent,
                        "confidence": f"{art_conf}%"
                    })

                return {
                    "sentiment": overall_sentiment,
                    "news_count": len(articles),
                    "articles": article_list,
                    "analysis_method": analysis_method
                }

            except Exception as e:
                print(f"FinBERT inference error: {e}")

        # Fallback to keyword matching
        overall_sentiment = _keyword_fallback(articles)
        return {
            "sentiment": overall_sentiment,
            "news_count": len(articles),
            "articles": [
                {
                    "title": a.get("title"),
                    "url": a.get("url"),
                    "publishedAt": a.get("publishedAt"),
                }
                for a in articles
            ],
            "analysis_method": analysis_method
        }
