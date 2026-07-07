import numpy as np, os, joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from collections import Counter
from learning.prediction_store import get_all_labeled_data

MODEL_PATH   = os.path.join(os.path.dirname(__file__), "rf_model.pkl")
FEATURE_ORDER= ["Historical","Technical","News","Moneycontrol","Fundamental","Sentiment","Insider","Sector","Risk"]
LABEL_MAP    = {"SELL": 0, "HOLD": 1, "BUY": 2}

# Synthetic baseline (26 expert scenarios - always included)
SYNTHETIC_X = np.array([
    [80,85,72,75,82,78,70,75,70],[75,80,72,70,85,75,65,80,65],[70,78,65,72,80,72,72,72,68],
    [85,90,72,80,88,82,75,78,72],[72,75,80,70,75,78,68,70,70],[65,72,65,65,70,68,60,65,60],
    [68,70,65,68,72,65,62,68,62],[60,72,70,62,68,70,58,60,65],[55,55,50,55,60,52,55,55,55],
    [52,58,50,52,55,50,50,52,50],[58,52,55,55,58,55,52,55,52],[60,60,50,60,60,55,55,58,55],
    [48,55,55,50,55,52,48,52,50],[50,50,50,50,50,50,50,50,50],[55,62,48,55,60,50,52,55,55],
    [35,30,28,35,38,32,40,35,38],[30,28,22,30,32,28,35,30,32],[40,35,28,38,35,32,38,35,35],
    [28,25,22,25,28,25,30,28,28],[38,32,28,32,35,30,35,32,30],[20,18,15,20,22,18,25,20,20],
    [25,22,18,22,25,20,28,22,22],[70,80,28,72,78,45,68,72,70],[75,72,72,28,75,70,65,68,68],
    [35,28,75,32,35,72,38,35,35],[38,35,72,38,38,70,35,32,32],
])
SYNTHETIC_Y = np.array([2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,0,0,0,0,0,0,0,2,2,0,0])

def train_and_save_model():
    real_data = get_all_labeled_data()
    real_X, real_Y = [], []
    for scores_dict, label in real_data:
        if label in LABEL_MAP:
            real_X.append([float(scores_dict.get(f, 50)) for f in FEATURE_ORDER])
            real_Y.append(LABEL_MAP[label])

    X = np.vstack([SYNTHETIC_X, np.array(real_X)]) if real_X else SYNTHETIC_X
    y = np.concatenate([SYNTHETIC_Y, np.array(real_Y)]) if real_Y else SYNTHETIC_Y

    class_dist  = Counter(y)
    max_class   = max(class_dist.values())
    class_weight= {k: max_class/v for k,v in class_dist.items() if v>0}

    print(f"\n[ModelTrainer] Training: {len(X)} samples (real={len(real_X)}, synthetic={len(SYNTHETIC_X)})")
    print(f"[ModelTrainer] Classes: SELL={class_dist[0]}, HOLD={class_dist[1]}, BUY={class_dist[2]}")

    model = RandomForestClassifier(n_estimators=200, max_depth=8, min_samples_leaf=2, random_state=42, class_weight=class_weight)
    model.fit(X, y)

    accuracy = None
    if len(X) >= 10:
        cv = cross_val_score(model, X, y, cv=min(5, len(X)//3))
        accuracy = round(float(cv.mean())*100, 1)
        print(f"[ModelTrainer] CV Accuracy: {accuracy}%")

    joblib.dump(model, MODEL_PATH)
    print(f"[ModelTrainer] Model saved → {MODEL_PATH}\n")
    return accuracy, len(X), model

def load_model():
    if os.path.exists(MODEL_PATH):
        try:
            m = joblib.load(MODEL_PATH)
            print(f"[ModelTrainer] Loaded saved model from disk")
            return m
        except Exception as e:
            print(f"[ModelTrainer] Load failed: {e}")
    return None
