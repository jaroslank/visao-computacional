"""Classificação em tempo real usando `dataset.csv` como base.

Este script usa o mesmo pré-processamento do treino, um modelo escolhido por
validação cruzada e suavização temporal para reduzir oscilações entre letras.

Uso:
    python classify_live_dataset.py
    python classify_live_dataset.py --model model.joblib

Pressione `q` para sair.
"""

from __future__ import annotations

import argparse
from collections import Counter, deque
from pathlib import Path

import cv2
import joblib
import numpy as np

from src.sign_language.feature_engineering import extract_features_from_landmarks, load_dataset
from src.vision.camera import Camera
from src.vision.hand_tracker import HandTracker


def train_bundle(dataset_path: str, save_model_path: str | None = None):
    from classify_offline import build_candidate_models
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
    from sklearn.preprocessing import LabelEncoder
    from collections import Counter

    X, y_str, _, resolved_path = load_dataset(dataset_path)

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_str)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    candidate_models = build_candidate_models()
    class_counts = Counter(y_train)
    min_class_count = max(2, min(class_counts.values()))
    n_splits = min(5, min_class_count)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

    best_name = None
    best_model = None
    best_score = -1.0

    for name, model in candidate_models.items():
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="balanced_accuracy")
        score = float(np.mean(scores))
        print(f"[{name}] balanced_accuracy CV: {score:.4f}")
        if score > best_score:
            best_name = name
            best_model = model
            best_score = score

    best_model.fit(X_train, y_train)
    holdout_acc = float(accuracy_score(y_test, best_model.predict(X_test)))

    bundle = {
        "model": best_model,
        "label_encoder": label_encoder,
        "feature_version": "v2_normalized_engineered",
        "model_name": best_name,
        "cv_score": best_score,
        "holdout_accuracy": holdout_acc,
        "dataset_path": resolved_path,
    }

    if save_model_path:
        Path(save_model_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(bundle, save_model_path)
        print(f"Modelo salvo em: {save_model_path}")

    return bundle


def predict_with_confidence(model, features: np.ndarray):
    pred = model.predict([features])[0]
    confidence = 1.0
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba([features])[0]
        confidence = float(np.max(proba))
    return pred, confidence


def summarize_buffer(buffer):
    if not buffer:
        return None, 0.0, 0
    labels = [label for label, _ in buffer]
    best_label, votes = Counter(labels).most_common(1)[0]
    confidences = [conf for label, conf in buffer if label == best_label]
    avg_conf = float(np.mean(confidences)) if confidences else 0.0
    return best_label, avg_conf, votes


def main(dataset_path: str = "dataset.csv", model_path: str | None = None, min_votes: int = 4, min_confidence: float = 0.65):
    if model_path and Path(model_path).exists():
        print(f"Carregando modelo de {model_path}")
        bundle = joblib.load(model_path)
    else:
        print(f"Treinando modelo a partir de {dataset_path}")
        bundle = train_bundle(dataset_path, save_model_path=model_path)

    model = bundle["model"]
    label_encoder = bundle["label_encoder"]
    model_name = bundle.get("model_name", "unknown")

    cam = Camera()
    tracker = HandTracker()
    recent_predictions = deque(maxlen=7)
    no_hand_frames = 0
    stable_label = None

    try:
        while True:
            ret, frame = cam.read_frame()
            if not ret:
                print("Falha ao ler frame da câmera")
                break

            hands = tracker.find_hands(frame)

            if hands:
                no_hand_frames = 0
                hand = hands[0]
                tracker.draw_landmarks(frame, hand)

                features = extract_features_from_landmarks(hand)
                pred_enc, confidence = predict_with_confidence(model, features)
                pred_label = label_encoder.inverse_transform([pred_enc])[0]

                recent_predictions.append((pred_label, confidence))
                voted_label, avg_confidence, votes = summarize_buffer(recent_predictions)

                if voted_label and votes >= min_votes and avg_confidence >= min_confidence:
                    stable_label = voted_label

                if stable_label:
                    display_text = f"{stable_label} ({avg_confidence:.2f})"
                else:
                    display_text = f"{pred_label} ({confidence:.2f})"

                cv2.putText(
                    frame,
                    f"Modelo: {model_name}",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 0),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    f"Letra: {display_text}",
                    (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.6,
                    (0, 255, 0),
                    3,
                    cv2.LINE_AA,
                )
            else:
                no_hand_frames += 1
                if no_hand_frames > 8:
                    recent_predictions.clear()
                    stable_label = None
                cv2.putText(
                    frame,
                    f"Modelo: {model_name}",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 0),
                    2,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    frame,
                    "Nenhuma mao detectada",
                    (30, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.2,
                    (0, 0, 255),
                    3,
                    cv2.LINE_AA,
                )

            cv2.imshow("Classificador Live (dataset)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q"), 27):  # q, Q, ou ESC
                break

    finally:
        cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classificador live usando dataset.csv")
    parser.add_argument("--dataset", "-d", default="dataset.csv", help="Caminho para dataset.csv")
    parser.add_argument("--model", "-m", default=None, help="Caminho para salvar/carregar modelo (joblib)")
    parser.add_argument("--min-votes", type=int, default=4, help="Quantidade mínima de votos na janela temporal")
    parser.add_argument("--min-confidence", type=float, default=0.65, help="Confiança mínima média para estabilizar")
    args = parser.parse_args()

    main(dataset_path=args.dataset, model_path=args.model, min_votes=args.min_votes, min_confidence=args.min_confidence)
