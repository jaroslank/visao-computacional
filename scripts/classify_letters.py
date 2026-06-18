"""Script simples para capturar a webcam, detectar mãos e classificar letras.

Uso:
    python scripts/classify_letters.py

Pressione `q` para sair.
"""
import cv2
import time

from src.vision.camera import Camera
from src.vision.hand_tracker import HandTracker
from src.sign_language.classifier import LibrasClassifier


def main():
    cam = Camera()
    tracker = HandTracker()
    classifier = LibrasClassifier()

    last_prediction = None
    last_time = 0

    try:
        while True:
            ret, frame = cam.read_frame()
            if not ret:
                print("Falha ao ler frame da câmera")
                break

            hands = tracker.find_hands(frame)

            if hands:
                # Usa apenas a primeira mão detectada
                hand = hands[0]
                tracker.draw_landmarks(frame, hand)

                letra = classifier.classify(hand)
                if letra:
                    # Debounce simples: mostra nova letra a cada 0.5s
                    now = time.time()
                    if letra != last_prediction or now - last_time > 0.5:
                        last_prediction = letra
                        last_time = now

                    cv2.putText(frame, f'Letra: {letra}', (30, 60), cv2.FONT_HERSHEY_SIMPLEX,
                                2, (0, 255, 0), 3, cv2.LINE_AA)
            else:
                last_prediction = None

            cv2.imshow('Classificador de Letras - Pressione q para sair', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
    finally:
        cam.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
