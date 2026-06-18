#!/usr/bin/env python3
"""
Script de coleta de dados para o projeto Jogo da Forca em LIBRAS.

Uso:
  python scripts/coletar_dados.py

O script captura os 21 landmarks da mão via MediaPipe (x,y,z) e grava
as 63 features por frame em `data/dataset.csv` com a última coluna `label`.

Funcionalidade:
- Pergunta ao utilizador qual a letra a gravar.
- Realiza 5 rodagens de 10 segundos cada (o utilizador inicia/pausa com 'G').
- Mostra feedback na janela do OpenCV com instruções e estado atual.

Notas para o utilizador:
- Durante cada rodagem, varie distância, inclinação do pulso e posição
  da mão no ecrã para aumentar a robustez do modelo.
"""
import os
import sys
import time
from collections import deque

import cv2
import numpy as np
import pandas as pd

# Garante que o pacote local `src` seja importável quando o script for
# executado a partir da raíz do repositório.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.vision.camera import Camera
from src.vision.hand_tracker import HandTracker


def ensure_data_dir(path="data"):
    os.makedirs(path, exist_ok=True)


def create_header():
    cols = []
    for i in range(21):
        cols += [f"x{i}", f"y{i}", f"z{i}"]
    cols.append("label")
    return cols


def landmarks_to_row(hand_landmarks):
    """Converte os 21 landmarks (MediaPipe) numa lista de 63 floats.

    hand_landmarks: objeto com a propriedade .landmark (iterável com 21 itens)
    """
    row = []
    for lm in hand_landmarks.landmark:
        row.extend([lm.x, lm.y, lm.z])
    return row


def append_rows_to_csv(rows, label, csv_path):
    if not rows:
        return
    df = pd.DataFrame(rows, columns=create_header()[:-1])
    df["label"] = label
    header = not os.path.exists(csv_path)
    df.to_csv(csv_path, mode="a", header=header, index=False)


def main():
    ensure_data_dir("data")
    csv_path = os.path.join("data", "dataset.csv")

    label = input("Letra a gravar (ex: A, B, C): ").strip().upper()
    if not label:
        print("Letra inválida. Saindo.")
        return

    total_runs = 5
    run_duration = 10.0  # segundos por rodagem

    cam = Camera()
    tracker = HandTracker()

    recording = False
    current_run = 1
    start_time = None
    buffered_rows = []

    # Mensagens rápidas mostradas na tela
    font = cv2.FONT_HERSHEY_SIMPLEX

    print("Iniciando captura. Pressione 'G' para iniciar/pausar, 'Q' para sair.")

    try:
        while True:
            ret, frame = cam.read_frame()
            if not ret:
                print("Falha ao ler frame da câmera. Saindo.")
                break

            hands = tracker.find_hands(frame)

            # Desenhar informações na tela
            status_text = f"Label: {label} | Run: {current_run}/{total_runs} | "
            status_text += "REC" if recording else "PAUSED"
            cv2.putText(frame, status_text, (10, 30), font, 0.8, (0, 255, 0), 2)

            # Instruções
            cv2.putText(frame, "Press G para iniciar/pausar. Q para sair.", (10, 60), font, 0.6, (200, 200, 200), 1)
            cv2.putText(frame, "Durante grava\u00e7\u00e3o varie distancia/inclinacao/posicao.", (10, 90), font, 0.5, (200, 200, 200), 1)
            cv2.putText(frame, f"Run time: {run_duration}s cada | ~30FPS (~300 frames)", (10, 120), font, 0.5, (200, 200, 200), 1)

            # Se houver mão detectada, desenhar landmarks na tela
            if hands:
                # Pegamos a primeira mão detectada
                first = hands[0]
                tracker.draw_landmarks(frame, first)

                if recording:
                    # Quando gravando, extrair a linha de 63 features
                    row = landmarks_to_row(first)
                    buffered_rows.append(row)

            # Mostrar tempo restante na gravação atual
            if recording and start_time is not None:
                elapsed = time.time() - start_time
                remaining = max(0.0, run_duration - elapsed)
                cv2.putText(frame, f"Recording... {remaining:.1f}s left", (10, 150), font, 0.7, (0, 0, 255), 2)
                if elapsed >= run_duration:
                    # Finaliza a rodada atual
                    print(f"Rodagem {current_run} completa. Gravadas ~{len(buffered_rows)} frames nesta rodada (serao gravadas no CSV).")
                    append_rows_to_csv(buffered_rows, label, csv_path)
                    buffered_rows = []
                    recording = False
                    start_time = None
                    current_run += 1
                    if current_run > total_runs:
                        print("Todas as rodagens conclu\u00eddas.")
                        break

            cv2.imshow("Coletar Dados - LIBRAS", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("Encerrando por teclado (Q).")
                break
            elif key == ord("g") or key == ord("G"):
                # Toggle gravação
                if not recording:
                    # Inicia ou retoma gravação; se já estivermos no tempo final da rodada,
                    # reinicia o temporizador desta rodada.
                    recording = True
                    start_time = time.time() if start_time is None else start_time
                    print(f"Grava\u00e7\u00e3o iniciada para rodagem {current_run}.")
                else:
                    recording = False
                    # Mantemos start_time para permitir retomar o tempo restante
                    print(f"Grava\u00e7\u00e3o pausada na rodagem {current_run}.")

        # Quando sair do loop, se houver frames em buffer, gravar no CSV
        if buffered_rows:
            print(f"Gravando {len(buffered_rows)} frames restantes para a label {label} no arquivo {csv_path}.")
            append_rows_to_csv(buffered_rows, label, csv_path)

    finally:
        cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
