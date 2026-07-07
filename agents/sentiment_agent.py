from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = None

def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


class SentimentAgent:
    """
    Uses VADER (lightweight NLP lexicon) to analyze market sentiment.
    Works on both local and Render Free Tier without any RAM issues.
    """

    def analyze(self, symbol: str, news_articles: list = None) -> dict:
        if not news_articles:
            return {
                "market_sentiment": "Neutral",
                "social_sentiment": "Neutral",
                "sentiment_score": 50,
                "signal": "Neutral",
                "score": 50,
                "analysis_method": "No news data available"
            }

        titles = [a.get("title", "") for a in news_articles if a.get("title")]
        if not titles:
            return {
                "market_sentiment": "Neutral",
                "social_sentiment": "Neutral",
                "sentiment_score": 50,
                "signal": "Neutral",
                "score": 50,
                "analysis_method": "No article titles found"
            }

        analyzer = _get_analyzer()
        total_compound = 0.0

        for title in titles:
            scores = analyzer.polarity_scores(title)
            total_compound += scores["compound"]

        avg_compound = total_compound / len(titles)

        # Map compound (-1 to +1) → score (0 to 100)
        score = int(50 + (avg_compound * 50))
        score = max(0, min(100, score))

        if avg_compound >= 0.05:
            signal = "Positive"
        elif avg_compound <= -0.05:
            signal = "Negative"
        else:
            signal = "Neutral"

        return {
            "market_sentiment": signal,
            "social_sentiment": signal,
            "sentiment_score": score,
            "signal": signal,
            "score": score,
            "analysis_method": "VADER (NLP Lexicon)"
        }
