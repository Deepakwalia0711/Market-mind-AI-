import sqlite3, json, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "predictions.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        predicted_at TEXT NOT NULL,
        prediction TEXT NOT NULL,
        price_at_predict REAL,
        agent_scores TEXT,
        labeled INTEGER DEFAULT 0,
        actual_label TEXT,
        actual_return REAL,
        labeled_at TEXT
    )""")
    conn.commit(); conn.close()

def save_prediction(symbol, prediction, price, agent_scores):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO predictions (symbol,predicted_at,prediction,price_at_predict,agent_scores,labeled) VALUES (?,?,?,?,?,0)",
        (symbol, datetime.now().isoformat(), prediction, price, json.dumps(agent_scores)))
    conn.commit(); conn.close()
    print(f"[PredictionStore] Saved: {symbol} → {prediction} @ ₹{price:.2f}")

def get_unlabeled_predictions():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id,symbol,predicted_at,prediction,price_at_predict,agent_scores FROM predictions WHERE labeled=0").fetchall()
    conn.close(); return rows

def update_label(prediction_id, actual_label, actual_return):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE predictions SET labeled=1,actual_label=?,actual_return=?,labeled_at=? WHERE id=?",
        (actual_label, actual_return, datetime.now().isoformat(), prediction_id))
    conn.commit(); conn.close()
    print(f"[PredictionStore] Labeled #{prediction_id}: {actual_label} ({actual_return:+.2f}%)")

def get_all_labeled_data():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT agent_scores,actual_label FROM predictions WHERE labeled=1 AND actual_label IS NOT NULL").fetchall()
    conn.close()
    return [(json.loads(s), l) for s, l in rows if s]

def get_stats():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    total    = conn.execute("SELECT COUNT(*) FROM predictions").fetchone()[0]
    labeled  = conn.execute("SELECT COUNT(*) FROM predictions WHERE labeled=1").fetchone()[0]
    unlabeled= conn.execute("SELECT COUNT(*) FROM predictions WHERE labeled=0").fetchone()[0]
    conn.close()
    return {"total": total, "labeled": labeled, "unlabeled": unlabeled}
