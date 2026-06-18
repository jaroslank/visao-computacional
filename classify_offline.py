"""Classificador offline simples que usa apenas `dataset.csv`.

Ele carrega `dataset.csv` (colunas x0,y0,z0...x20,y20,z20,label), treina um KNN,
exibe relatório de classificação e acurácia.

Uso:
    python scripts/classify_offline.py

Opções:
    --save-model PATH    Salva o modelo treinado em PATH (joblib)
"""
import argparse
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os


def main(dataset_path='dataset.csv', save_model_path=None):
    if not os.path.exists(dataset_path):
        print(f"Arquivo não encontrado: {dataset_path}")
        return

    df = pd.read_csv(dataset_path)
    if 'label' not in df.columns:
        print('CSV esperado com coluna `label`.')
        return

    X = df.drop(columns=['label']).values
    y = df['label'].values

    # Codifica labels
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    # Normaliza
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Split simples
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    clf = KNeighborsClassifier(n_neighbors=3)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)

    print('Acurácia (test):', acc)
    print('\nRelatório de classificação:')
    print(classification_report(y_test, preds, target_names=le.classes_))

    if save_model_path:
        joblib.dump({'model': clf, 'label_encoder': le, 'scaler': scaler}, save_model_path)
        print(f'Modelo salvo em: {save_model_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Classificador offline usando dataset.csv')
    parser.add_argument('--dataset', '-d', default='dataset.csv', help='Caminho para dataset.csv')
    parser.add_argument('--save-model', '-s', default=None, help='Salvar modelo treinado (joblib)')
    args = parser.parse_args()

    main(dataset_path=args.dataset, save_model_path=args.save_model)
