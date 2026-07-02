"""Ferramentas de features para landmarks de mão.

Este módulo centraliza o pré-processamento usado tanto no treino com `dataset.csv`
quanto na inferência em tempo real. A ideia é reduzir sensibilidade a posição,
distância e escala da mão na imagem.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np
import pandas as pd


LANDMARK_COUNT = 21
RAW_COORDS_PER_SAMPLE = LANDMARK_COUNT * 3


def resolve_dataset_path(dataset_path: str | None = None) -> str:
    """Resolve o caminho do dataset procurando em locais comuns do projeto."""
    candidates = []
    if dataset_path:
        candidates.append(Path(dataset_path))
    candidates.extend(
        [
            Path("dataset.csv"),
            Path("data") / "dataset.csv",
            Path("scripts") / "data" / "dataset.csv",
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise FileNotFoundError(
        "Não foi possível localizar o dataset. Verifique dataset.csv, data/dataset.csv ou scripts/data/dataset.csv."
    )


def _reshape_raw_coords(raw_values: Iterable[float]) -> np.ndarray:
    values = np.asarray(list(raw_values), dtype=np.float32)
    if values.size != RAW_COORDS_PER_SAMPLE:
        raise ValueError(
            f"Esperado vetor com {RAW_COORDS_PER_SAMPLE} valores, recebido {values.size}."
        )
    return values.reshape(LANDMARK_COUNT, 3)


def landmarks_to_array(landmarks) -> np.ndarray:
    """Converte landmarks do MediaPipe para um array (21, 3)."""
    points = getattr(landmarks, "landmark", landmarks)
    coords = [[p.x, p.y, p.z] for p in points[:LANDMARK_COUNT]]
    if len(coords) != LANDMARK_COUNT:
        raise ValueError(f"Esperados {LANDMARK_COUNT} landmarks, recebidos {len(coords)}.")
    return np.asarray(coords, dtype=np.float32)


def _safe_norm(vec: np.ndarray) -> float:
    value = float(np.linalg.norm(vec))
    return value if value > 1e-6 else 1.0


def normalize_landmarks(coords: np.ndarray) -> np.ndarray:
    """Centraliza no punho e normaliza pela escala da palma."""
    coords = np.asarray(coords, dtype=np.float32).reshape(LANDMARK_COUNT, 3)
    centered = coords - coords[0]

    palm_points = centered[[5, 9, 13, 17]]
    scale_candidates = [np.linalg.norm(p) for p in palm_points]
    scale = float(np.mean([s for s in scale_candidates if s > 1e-6])) if any(
        s > 1e-6 for s in scale_candidates
    ) else _safe_norm(centered[9])
    return centered / scale


def _angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    ba = a - b
    bc = c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom < 1e-6:
        return 0.0
    cos_value = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_value)))


def extract_features_from_array(coords: np.ndarray) -> np.ndarray:
    """Gera features robustas a partir de um array (21, 3)."""
    normalized = normalize_landmarks(coords)

    flattened = normalized.flatten().tolist()

    # Distâncias do punho às pontas dos dedos
    tip_ids = [4, 8, 12, 16, 20]
    tip_distances = [float(np.linalg.norm(normalized[idx])) for idx in tip_ids]

    # Distâncias entre as pontas dos dedos — úteis para diferenciar letras parecidas
    tip_pairs = [
        float(np.linalg.norm(normalized[i] - normalized[j]))
        for i, j in combinations(tip_ids, 2)
    ]

    # Ângulos de flexão aproximados dos dedos
    angles = [
        _angle(normalized[0], normalized[2], normalized[4]),
        _angle(normalized[0], normalized[5], normalized[8]),
        _angle(normalized[0], normalized[9], normalized[12]),
        _angle(normalized[0], normalized[13], normalized[16]),
        _angle(normalized[0], normalized[17], normalized[20]),
    ]

    # Proporções da palma e abertura entre dedos
    palm_spans = [
        float(np.linalg.norm(normalized[5] - normalized[17])),
        float(np.linalg.norm(normalized[5] - normalized[9])),
        float(np.linalg.norm(normalized[9] - normalized[13])),
        float(np.linalg.norm(normalized[13] - normalized[17])),
        float(np.linalg.norm(normalized[4] - normalized[8])),
        float(np.linalg.norm(normalized[8] - normalized[12])),
        float(np.linalg.norm(normalized[12] - normalized[16])),
        float(np.linalg.norm(normalized[16] - normalized[20])),
    ]

    return np.asarray(flattened + tip_distances + tip_pairs + angles + palm_spans, dtype=np.float32)


def extract_features_from_landmarks(landmarks) -> np.ndarray:
    """Extrai features diretamente de landmarks do MediaPipe."""
    return extract_features_from_array(landmarks_to_array(landmarks))


def load_dataset(dataset_path: str | None = None) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame, str]:
    """Carrega o dataset, converte os landmarks e retorna X, y, df e caminho resolvido."""
    resolved_path = resolve_dataset_path(dataset_path)
    df = pd.read_csv(resolved_path)

    if "label" not in df.columns:
        raise ValueError("CSV esperado com coluna `label`.")

    feature_columns = [col for col in df.columns if col != "label"]
    raw = df[feature_columns].to_numpy(dtype=np.float32)
    if raw.shape[1] != RAW_COORDS_PER_SAMPLE:
        raise ValueError(
            f"CSV esperado com {RAW_COORDS_PER_SAMPLE} colunas de features, encontrado {raw.shape[1]}."
        )

    X = np.vstack([extract_features_from_array(_reshape_raw_coords(row)) for row in raw])
    y = df["label"].astype(str).to_numpy()
    return X, y, df, resolved_path
