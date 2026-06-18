"""Classificação em tempo real usando `dataset.csv` como base.

O script treina (ou carrega) um classificador + scaler a partir de `dataset.csv`
(e codificador de labels) e usa a câmera + MediaPipe para extrair landmarks
em tempo real, prevê a letra e sobrepõe no frame.

Uso:
    python scripts/classify_live_dataset.py
    python scripts/classify_live_dataset.py --model model.joblib

Pressione `q` para sair.
"""
import argparse
import os
import time

import cv2
import numpy as np
import pandas as pd

from src.vision.camera import Camera
from src.vision.hand_tracker import HandTracker

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import KNeighborsClassifier
import joblib


def extract_features_from_landmarks(landmarks):
    """Extrai vetor [x0,y0,z0,...,x20,y20,z20] de `landmarks` do MediaPipe."""
    pts = landmarks.landmark
    feat = []
    for i in range(21):
        p = pts[i]
        feat.extend([p.x, p.y, p.z])
    return np.array(feat, dtype=np.float32)


def train_from_csv(path):
    df = pd.read_csv(path)
    if 'label' not in df.columns:
        raise ValueError('CSV precisa ter coluna `label`.')

    X = df.drop(columns=['label']).values
    y = df['label'].values

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    clf = KNeighborsClassifier(n_neighbors=3)
    clf.fit(X_scaled, y_enc)

    return {'model': clf, 'scaler': scaler, 'label_encoder': le}


def main(dataset_path='dataset.csv', model_path=None, min_consensus=3):
    # Load or train model
    if model_path and os.path.exists(model_path):
        print('Carregando modelo de', model_path)
        data = joblib.load(model_path)
        clf = data['model']
        scaler = data['scaler']
        le = data['label_encoder']
    else:
        print('Treinando modelo a partir de', dataset_path)
        data = train_from_csv(dataset_path)
        clf = data['model']
        scaler = data['scaler']
        le = data['label_encoder']
        if model_path:
            joblib.dump({'model': clf, 'scaler': scaler, 'label_encoder': le}, model_path)
            print('Modelo salvo em', model_path)

    cam = Camera()
    tracker = HandTracker()

    consensus_count = 0
    last_pred = None
    stable_pred = None
    last_time = 0

    try:
        while True:
            ret, frame = cam.read_frame()
            if not ret:
                print('Falha ao ler frame da câmera')
                break

            hands = tracker.find_hands(frame)
            display_text = 'Nenhuma mão'

            if hands:
                hand = hands[0]
                tracker.draw_landmarks(frame, hand)
                feat = extract_features_from_landmarks(hand)
                feat_scaled = scaler.transform([feat])
                pred_enc = clf.predict(feat_scaled)[0]
                pred_label = le.inverse_transform([pred_enc])[0]

                # Consensus smoothing
                if pred_label == last_pred:
                    consensus_count += 1
                else:
                    consensus_count = 1
                    last_pred = pred_label

                if consensus_count >= min_consensus:
                    stable_pred = pred_label
                    last_time = time.time()

                if stable_pred:
                    display_text = f'Letra: {stable_pred}'
                else:
                    display_text = f'... detectando: {pred_label}'
            else:
                # reset small counters when no hand
                last_pred = None
                consensus_count = 0

            # Mostrar texto no frame
            cv2.putText(frame, display_text, (30, 60), cv2.FONT_HERSHEY_SIMPLEX,
                        2, (0, 255, 0), 3, cv2.LINE_AA)

            cv2.imshow('Classificador Live (dataset)', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    finally:
        cam.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Classificador live usando dataset.csv')
    parser.add_argument('--dataset', '-d', default='dataset.csv', help='Caminho para dataset.csv')
    parser.add_argument('--model', '-m', default=None, help='Caminho para salvar/carregar modelo (joblib)')
    parser.add_argument('--consensus', '-c', type=int, default=3, help='Quantidade de frames consecutivos para confirmar a predição')
    args = parser.parse_args()

    main(dataset_path=args.dataset, model_path=args.model, min_consensus=args.consensus)
