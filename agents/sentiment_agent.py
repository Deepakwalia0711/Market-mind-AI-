from agents.news_agent import _get_finbert


class SentimentAgent:
    """
    Uses FinBERT (Deep Learning NLP) to analyze market sentiment.
    Falls back to a score based on stock symbol hash if FinBERT is unavailable.
    """

    def analyze(self, symbol: str, news_articles: list = None) -> dict:
        """
        Analyze sentiment using FinBERT on news headlines.
        
        Args:
            symbol: Stock ticker symbol
            news_articles: List of article dicts with 'title' key (from NewsAgent)
        """
        if not news_articles:
            # No news available - return neutral
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

        finbert = _get_finbert()
        if finbert:
            try:
                results = finbert(titles, truncation=True, max_length=512)

                label_scores = {"positive": 0, "neutral": 0, "negative": 0}
                confidence_sum = {"positive": 0.0, "neutral": 0.0, "negative": 0.0}

                for r in results:
                    lbl = r["label"].lower()
                    label_scores[lbl] += 1
                    confidence_sum[lbl] += r["score"]

                total = len(results)
                pos_ratio = label_scores["positive"] / total
                neg_ratio = label_scores["negative"] / total

                # Score from 0-100 (50 = neutral)
                score = int(50 + (pos_ratio * 50) - (neg_ratio * 50))
                score = max(0, min(100, score))

                # Market Sentiment
                if score > 65:
                    market_sentiment = "Bullish"
                elif score < 35:
                    market_sentiment = "Bearish"
                else:
                    market_sentiment = "Neutral"

                # Social Sentiment (based on confidence)
                avg_pos_conf = (confidence_sum["positive"] / label_scores["positive"]) if label_scores["positive"] > 0 else 0
                if avg_pos_conf > 0.85 and pos_ratio > 0.5:
                    social_sentiment = "Highly Positive"
                elif pos_ratio > 0.4:
                    social_sentiment = "Positive"
                elif neg_ratio > 0.4:
                    social_sentiment = "Negative"
                else:
                    social_sentiment = "Neutral"

                return {
                    "market_sentiment": market_sentiment,
                    "social_sentiment": social_sentiment,
                    "sentiment_score": score,
                    "signal": "Positive" if score > 50 else "Negative",
                    "score": score,
                    "positive_count": label_scores["positive"],
                    "neutral_count": label_scores["neutral"],
                    "negative_count": label_scores["negative"],
                    "analysis_method": "FinBERT (Deep Learning NLP)"
                }

            except Exception as e:
                print(f"SentimentAgent FinBERT error: {e}")

        # Fallback: neutral
        return {
            "market_sentiment": "Neutral",
            "social_sentiment": "Neutral",
            "sentiment_score": 50,
            "signal": "Neutral",
            "score": 50,
            "analysis_method": "Fallback (FinBERT unavailable)"
        }
