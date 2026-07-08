import cv2
import joblib
import numpy as np

from src.vision.camera import Camera
from src.vision.hand_tracker import HandTracker

from src.core.gesture_recognizer import GestureRecognizer
from src.core.game_state import GameState
from src.ui.renderer import UIRenderer

from src.sign_language.feature_engineering import (
    extract_features_from_landmarks
)


def predict_with_confidence(model, features):
    pred = model.predict([features])[0]

    confidence = 1.0

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba([features])[0]
        confidence = float(np.max(proba))

    return pred, confidence


def main():
    print("========================================")
    print("JOGO DA FORCA LIBRAS")
    print("Classificação baseada no dataset.csv")
    print("========================================")

    try:
        print("[1/6] Inicializando câmera...")
        camera = Camera()

        print("[2/6] Inicializando MediaPipe...")
        hand_tracker = HandTracker()

        print("[3/6] Carregando modelo treinado...")
        bundle = joblib.load("model.joblib")

        model = bundle["model"]
        label_encoder = bundle["label_encoder"]

        print("[4/6] Inicializando reconhecimento...")
        gesture_recognizer = GestureRecognizer()

        print("[5/6] Inicializando estado do jogo...")
        game_state = GameState()

        print("[6/6] Inicializando interface...")
        renderer = UIRenderer()

        print("\nSistema iniciado com sucesso!")
        print(f"Dica atual: {game_state.dica}")

    except Exception as e:
        print(f"\nERRO CRÍTICO:")
        print(e)
        return

    while True:

        ret, frame = camera.read_frame()

        if not ret:
            print("Erro ao capturar frame.")
            break

        hand_landmarks = hand_tracker.find_hands(frame)

        current_gesture = None
        confidence = 0.0

        confirmed_gesture = None
        progress_ratio = 0.0

        if hand_landmarks:

            mao = hand_landmarks[0]

            hand_tracker.draw_landmarks(frame, mao)

            try:
                features = extract_features_from_landmarks(mao)

                pred_enc, confidence = predict_with_confidence(
                    model,
                    features
                )

                current_gesture = label_encoder.inverse_transform(
                    [pred_enc]
                )[0]

                confirmed_gesture, progress_ratio = (
                    gesture_recognizer.update(current_gesture)
                )

            except Exception as e:
                print(f"Erro na classificação: {e}")

            cv2.putText(
                frame,
                f"Letra: {current_gesture}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Confianca: {confidence:.2%}",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 0),
                2
            )

        else:

            cv2.putText(
                frame,
                "Nenhuma mao detectada",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

        if confirmed_gesture:

            print(
                f"Letra confirmada: {confirmed_gesture} "
                f"(conf: {confidence:.2%})"
            )

            game_state.processar_tentativa(
                confirmed_gesture
            )

            if (
                game_state.verificar_vitoria()
                or
                game_state.verificar_derrota()
            ):

                renderer.draw_game_elements(
                    frame,
                    game_state,
                    current_gesture,
                    progress_ratio
                )

                cv2.imshow(
                    "Jogo da Forca em LIBRAS",
                    frame
                )

                cv2.waitKey(3000)

                game_state.reset()

        renderer.draw_game_elements(
            frame,
            game_state,
            current_gesture,
            progress_ratio
        )

        cv2.imshow(
            "Jogo da Forca em LIBRAS",
            frame
        )

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    print("Jogo encerrado.")


if __name__ == "__main__":
    main()