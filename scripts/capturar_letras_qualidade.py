"""Coletor de dados de alta qualidade para letras em LIBRAS.

Objetivo
--------
Capturar landmarks da mão com uma experiência mais confiável que o coletor simples,
reduzindo frames ruins e facilitando a criação de um dataset mais útil para treino.

Recursos
--------
- Captura pela webcam com `Camera` e `HandTracker` do projeto.
- Captura por etiqueta/letra em modo manual, inspirado no coletor legado.
- Barra de progresso por letra e total.
- Checagens de qualidade:
  - uma única mão detectada
  - landmarks dentro do frame
  - mão estável por alguns frames
- Controles simples no teclado:
    - ESPAÇO/G: iniciar/pausar captura
  - N: próximo rótulo
  - P: rótulo anterior
  - Q: sair
- Salvamento incremental em CSV com cabeçalho automático.

Uso
---
python scripts/capturar_letras_qualidade.py --labels A B C D E --samples-per-label 400
python scripts/capturar_letras_qualidade.py --labels M N P Q R S T U --output scripts/data/dataset.csv

Se `--labels` não for passado, o script pergunta interativamente.
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import deque
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.vision.camera import Camera
from src.vision.hand_tracker import HandTracker


LANDMARK_COUNT = 21
FEATURE_COUNT = LANDMARK_COUNT * 3


def build_header() -> list[str]:
    cols: list[str] = []
    for i in range(LANDMARK_COUNT):
        cols.extend([f"x{i}", f"y{i}", f"z{i}"])
    cols.append("label")
    return cols


def landmarks_to_row(hand_landmarks) -> list[float]:
    row: list[float] = []
    for lm in hand_landmarks.landmark[:LANDMARK_COUNT]:
        row.extend([float(lm.x), float(lm.y), float(lm.z)])
    if len(row) != FEATURE_COUNT:
        raise ValueError(f"Esperados {FEATURE_COUNT} valores, obtidos {len(row)}.")
    return row


def normalize_label_list(labels: Iterable[str]) -> list[str]:
    normalized = []
    for label in labels:
        value = str(label).strip().upper()
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def ensure_parent_dir(csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)


def append_rows_to_csv(rows: list[list[float]], label: str, csv_path: Path) -> int:
    if not rows:
        return 0

    df = pd.DataFrame(rows, columns=build_header()[:-1])
    df["label"] = label
    header = not csv_path.exists()
    df.to_csv(csv_path, mode="a", header=header, index=False)
    return len(rows)


def load_existing_counts(csv_path: Path) -> dict[str, int]:
    if not csv_path.exists():
        return {}
    try:
        df = pd.read_csv(csv_path, usecols=["label"])
        return df["label"].astype(str).value_counts().to_dict()
    except Exception:
        return {}


def sample_is_inside_frame(hand_landmarks, margin: float = 0.02) -> bool:
    for lm in hand_landmarks.landmark[:LANDMARK_COUNT]:
        if lm.x < margin or lm.x > 1.0 - margin or lm.y < margin or lm.y > 1.0 - margin:
            return False
    return True


def hand_motion_score(history: deque[np.ndarray]) -> float:
    if len(history) < 2:
        return float("inf")
    deltas = []
    for prev, curr in zip(list(history)[:-1], list(history)[1:]):
        deltas.append(float(np.mean(np.abs(curr - prev))))
    return float(np.mean(deltas)) if deltas else float("inf")


def put_text(frame, text, y, color=(255, 255, 255), scale=0.7, thickness=2):
    cv2.putText(frame, text, (20, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def prompt_labels() -> list[str]:
    raw = input("Digite as letras separadas por espaço (ex: A B C D): ").strip().split()
    labels = normalize_label_list(raw)
    if not labels:
        raise ValueError("Nenhuma letra válida informada.")
    return labels


def draw_progress(frame, labels: list[str], counts: dict[str, int], active_index: int, target_per_label: int):
    y = 30
    put_text(frame, f"Label atual: {labels[active_index]} ({active_index + 1}/{len(labels)})", y, (0, 255, 255), 0.8, 2)
    y += 30
    put_text(frame, f"Capturando: {'SIM' if target_per_label > 0 else 'NAO'} | alvo por letra: {target_per_label}", y, (0, 255, 0), 0.7, 2)
    y += 30
    total = sum(counts.get(lbl, 0) for lbl in labels)
    put_text(frame, f"Total gravado: {total}", y, (255, 255, 0), 0.7, 2)
    y += 30
    for lbl in labels:
        put_text(frame, f"{lbl}: {counts.get(lbl, 0)}/{target_per_label}", y, (200, 200, 200), 0.6, 1)
        y += 22


def save_buffer_if_needed(buffered_rows: list[list[float]], current_label: str, csv_path: Path, session_counts: dict[str, int]) -> int:
    """Grava o buffer atual no CSV e retorna quantas linhas foram salvas."""
    saved = append_rows_to_csv(buffered_rows, current_label, csv_path)
    if saved:
        session_counts[current_label] = session_counts.get(current_label, 0) + saved
    return saved


def main():
    parser = argparse.ArgumentParser(description="Coletor robusto de letras para dataset.csv")
    parser.add_argument("--labels", nargs="*", default=None, help="Lista de letras a coletar, ex: A B C")
    parser.add_argument("--output", default="scripts/data/dataset.csv", help="Arquivo CSV de saída")
    parser.add_argument("--samples-per-label", type=int, default=400, help="Quantidade alvo por letra")
    parser.add_argument("--warmup-frames", type=int, default=15, help="Frames de aquecimento antes de começar a gravar")
    parser.add_argument("--stability-window", type=int, default=8, help="Janela de estabilidade em frames")
    parser.add_argument("--max-motion", type=float, default=0.015, help="Movimento médio máximo para considerar estável")
    parser.add_argument("--edge-margin", type=float, default=0.02, help="Margem mínima para não gravar mãos na borda")
    parser.add_argument("--append", action="store_true", help="Apenas acrescenta ao CSV existente")
    args = parser.parse_args()

    labels = normalize_label_list(args.labels or prompt_labels())
    if not labels:
        print("Nenhuma letra válida foi informada.")
        return

    csv_path = Path(args.output)
    ensure_parent_dir(csv_path)

    existing_counts = load_existing_counts(csv_path)
    if existing_counts and not args.append:
        print(f"CSV existente detectado em {csv_path}")
        print("As contagens atuais serão usadas como base. Use --append para adicionar sem aviso.")

    # Contagem da sessão atual, separada do histórico já existente no CSV.
    session_counts = {lbl: 0 for lbl in labels}
    active_index = 0
    paused = True
    recording = False
    session_rows: list[list[float]] = []

    cam = Camera()
    tracker = HandTracker()
    history: deque[np.ndarray] = deque(maxlen=max(2, args.stability_window))
    warmup_left = args.warmup_frames
    last_save_time = 0.0
    current_run = 1
    total_runs_per_label = 999999  # sem auto-encerramento; modo manual como o legado

    print("Controle:")
    print("  ESPAÇO/G = iniciar/pausar")
    print("  N      = próxima letra")
    print("  P      = letra anterior")
    print("  Q      = sair")
    print(f"Saída: {csv_path}")
    print(f"Metas por letra: {args.samples_per_label}")
    print("Modo: manual, sem auto-avanço. Cada letra deve ser iniciada pelo usuário.")

    try:
        while True:
            ret, frame = cam.read_frame()
            if not ret:
                print("Falha ao ler frame da câmera.")
                break

            frame = cv2.resize(frame, (960, 720))
            hands = tracker.find_hands(frame)
            current_label = labels[active_index]
            target_count = args.samples_per_label
            current_count = session_counts.get(current_label, 0)

            # overlays base
            draw_progress(frame, labels, session_counts, active_index, target_count)
            put_text(frame, "ESPACO/G: pausar/iniciar | N/P: trocar letra | Q: sair", 30 + 30 + 30 + 30 + 22 * len(labels) + 35, (180, 180, 180), 0.55, 1)

            if paused:
                put_text(frame, "PAUSADO", 620, (0, 0, 255), 1.0, 3)
            else:
                put_text(frame, "GRAVANDO", 620, (0, 255, 0), 1.0, 3)
            put_text(frame, f"Rodada atual: {current_run}", 650, (255, 255, 255), 0.7, 2)

            # hand processing
            if hands:
                if len(hands) > 1:
                    put_text(frame, "Apenas uma mao por vez", 470, (0, 0, 255), 0.8, 2)
                    history.clear()
                hand = hands[0]
                tracker.draw_landmarks(frame, hand)
                inside = sample_is_inside_frame(hand, margin=args.edge_margin)
                row = np.asarray(landmarks_to_row(hand), dtype=np.float32)
                history.append(row.reshape(LANDMARK_COUNT, 3))
                motion = hand_motion_score(history)

                stability_ok = len(history) >= args.stability_window and motion <= args.max_motion
                ready_to_record = (recording and inside and stability_ok and warmup_left <= 0 and current_count < target_count)

                put_text(frame, f"Mao dentro do frame: {'SIM' if inside else 'NAO'}", 30 + 30 + 30 + 30 + 22 * len(labels) + 70, (0, 255, 255) if inside else (0, 0, 255), 0.6, 2)
                put_text(frame, f"Estabilidade: {motion:.4f} (limite {args.max_motion:.4f})", 30 + 30 + 30 + 30 + 22 * len(labels) + 95, (0, 255, 255) if stability_ok else (0, 0, 255), 0.6, 2)

                if warmup_left > 0:
                    put_text(frame, f"Aquecendo... {warmup_left} frames", 530, (255, 255, 0), 0.9, 2)
                    warmup_left -= 1
                elif ready_to_record:
                    session_rows.append(row.tolist())
                    session_counts[current_label] = session_counts.get(current_label, 0) + 1
                    last_save_time = time.time()
                    put_text(frame, f"CAPTURADO {session_counts[current_label]}/{target_count}", 560, (0, 255, 0), 1.0, 3)
                else:
                    reasons = []
                    if paused:
                        reasons.append("pausado")
                    if not inside:
                        reasons.append("na borda")
                    if not stability_ok:
                        reasons.append("instavel")
                    if current_count >= target_count:
                        reasons.append("alvo concluido")
                    if warmup_left > 0:
                        reasons.append("aquecendo")
                    put_text(frame, f"Nao gravando: {', '.join(reasons) if reasons else 'aguardando'}", 560, (0, 0, 255), 0.7, 2)
            else:
                history.clear()
                warmup_left = args.warmup_frames
                put_text(frame, "Nenhuma mao detectada", 500, (0, 0, 255), 0.9, 3)

            # grava incremental ao atingir o alvo atual; não avança sozinho para a próxima letra
            if session_counts[current_label] >= target_count:
                saved = save_buffer_if_needed(session_rows, current_label, csv_path, session_counts)
                session_rows = []
                warmup_left = args.warmup_frames
                history.clear()
                recording = False
                paused = True
                print(f"Label {current_label} concluída: {saved} amostras novas salvas em {csv_path}.")
                print("Escolha a próxima letra com N/P e pressione ESPAÇO para gravar novamente.")

            # keyboard
            cv2.imshow("Coletor de Letras - Alta Qualidade", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == 32:  # space
                paused = not paused
                recording = not paused
                warmup_left = args.warmup_frames if recording else warmup_left
                if recording:
                    print(f"Gravação iniciada para {current_label}.")
                else:
                    print(f"Gravação pausada em {current_label}.")
            elif key in (ord("g"), ord("G")):
                paused = not paused
                recording = not paused
                warmup_left = args.warmup_frames if recording else warmup_left
                if recording:
                    print(f"Gravação iniciada para {current_label}.")
                else:
                    print(f"Gravação pausada em {current_label}.")
            elif key in (ord("n"), ord("N")):
                if active_index < len(labels) - 1:
                    active_index += 1
                    history.clear()
                    warmup_left = args.warmup_frames
                    session_rows = []
                    paused = True
                    recording = False
                    print(f"Mudando para {labels[active_index]}.")
            elif key in (ord("p"), ord("P")):
                if active_index > 0:
                    active_index -= 1
                    history.clear()
                    warmup_left = args.warmup_frames
                    session_rows = []
                    paused = True
                    recording = False
                    print(f"Voltando para {labels[active_index]}.")

        if session_rows:
            saved = save_buffer_if_needed(session_rows, labels[active_index], csv_path, session_counts)
            print(f"Salvando amostras restantes: {saved}.")

    finally:
        cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
