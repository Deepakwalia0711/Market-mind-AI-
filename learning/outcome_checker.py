import yfinance as yf
from datetime import datetime
from learning.prediction_store import get_unlabeled_predictions, update_label, get_stats

OUTCOME_DELAY_DAYS = 5
BUY_THRESHOLD  =  3.0
SELL_THRESHOLD = -3.0

def check_and_label_outcomes():
    unlabeled = get_unlabeled_predictions()
    now = datetime.now()
    labeled_count = 0
    print(f"[OutcomeChecker] Checking {len(unlabeled)} unlabeled predictions...")
    for row in unlabeled:
        pred_id, symbol, predicted_at_str, prediction, price_at_predict, _ = row
        try:
            predicted_at = datetime.fromisoformat(predicted_at_str)
        except Exception:
            continue
        if (now - predicted_at).days < OUTCOME_DELAY_DAYS:
            continue
        try:
            hist = yf.Ticker(symbol).history(period="2d")
            if hist.empty or not price_at_predict:
                continue
            current_price = float(hist['Close'].iloc[-1])
            actual_return = ((current_price - price_at_predict) / price_at_predict) * 100
            actual_label = "BUY" if actual_return >= BUY_THRESHOLD else "SELL" if actual_return <= SELL_THRESHOLD else "HOLD"
            update_label(pred_id, actual_label, actual_return)
            labeled_count += 1
            correct = "✅" if prediction == actual_label else "❌"
            print(f"[OutcomeChecker] #{pred_id} {symbol}: predicted={prediction}, actual={actual_label} ({actual_return:+.2f}%) {correct}")
        except Exception as e:
            print(f"[OutcomeChecker] Error {symbol}: {e}")
    stats = get_stats()
    print(f"[OutcomeChecker] Done. Labeled today: {labeled_count} | Total: {stats['labeled']}/{stats['total']}")
    return labeled_count
