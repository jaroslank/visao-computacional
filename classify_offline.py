"""Treino offline usando apenas `dataset.csv`, com features robustas.

O script faz:
- carregamento do `dataset.csv`
- extração de features normalizadas dos landmarks
- comparação de modelos por validação cruzada
- avaliação em holdout e salvamento opcional do melhor modelo

Uso:
    python classify_offline.py
    python classify_offline.py --dataset scripts/data/dataset.csv --save-model model.joblib
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import SVC

from src.sign_language.feature_engineering import load_dataset


def build_candidate_models(random_state: int = 42):
    return {
        "knn": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("model", KNeighborsClassifier(n_neighbors=5, weights="distance")),
            ]
        ),
        "svm": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "model",
                    SVC(
                        C=10.0,
                        gamma="scale",
                        kernel="rbf",
                        probability=True,
                        class_weight="balanced",
                        random_state=random_state,
                    ),
                ),
            ]
        ),
        "rf": RandomForestClassifier(
            n_estimators=400,
            random_state=random_state,
            class_weight="balanced_subsample",
            n_jobs=-1,
        ),
    }


def pick_best_model(X_train, y_train, random_state: int = 42):
    candidate_models = build_candidate_models(random_state=random_state)
    class_counts = Counter(y_train)
    min_class_count = max(2, min(class_counts.values()))
    n_splits = min(5, min_class_count)
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    best_name = None
    best_model = None
    best_score = -1.0

    for name, model in candidate_models.items():
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="balanced_accuracy")
        mean_score = float(np.mean(scores))
        std_score = float(np.std(scores))
        print(f"[{name}] balanced_accuracy CV: {mean_score:.4f} ± {std_score:.4f}")

        if mean_score > best_score:
            best_name = name
            best_model = model
            best_score = mean_score

    best_model.fit(X_train, y_train)
    return best_name, best_model, best_score


def main(dataset_path: str = "dataset.csv", save_model_path: str | None = None):
    X, y_str, df, resolved_path = load_dataset(dataset_path)
    print(f"Dataset carregado de: {resolved_path}")
    print(f"Amostras: {len(df)} | Features por amostra: {X.shape[1]}")

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y_str)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    best_name, best_model, cv_score = pick_best_model(X_train, y_train)
    print(f"\nMelhor modelo: {best_name} | CV balanced_accuracy: {cv_score:.4f}")

    y_pred = best_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)

    print(f"\nAcurácia (holdout): {acc:.4f}")
    print(f"Balanced accuracy (holdout): {bal_acc:.4f}")
    print("\nRelatório de classificação:")
    print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))

    if save_model_path:
        Path(save_model_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": best_model,
                "label_encoder": label_encoder,
                "feature_version": "v2_normalized_engineered",
                "model_name": best_name,
                "cv_score": cv_score,
                "dataset_path": resolved_path,
            },
            save_model_path,
        )
        print(f"\nModelo salvo em: {save_model_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classificador offline usando dataset.csv")
    parser.add_argument("--dataset", "-d", default="dataset.csv", help="Caminho para dataset.csv")
    parser.add_argument("--save-model", "-s", default=None, help="Salvar modelo treinado (joblib)")
    args = parser.parse_args()

    main(dataset_path=args.dataset, save_model_path=args.save_model)
