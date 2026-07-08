import cv2
import joblib
import numpy as np
import customtkinter as ctk

from PIL import Image, ImageTk

from src.vision.camera import Camera
from src.vision.hand_tracker import HandTracker

from src.core.game_state import GameState
from src.core.gesture_recognizer import GestureRecognizer

from src.sign_language.feature_engineering import (
    extract_features_from_landmarks
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def predict_with_confidence(model, features):
    pred = model.predict([features])[0]

    confidence = 1.0

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba([features])[0]
        confidence = float(np.max(proba))

    return pred, confidence


class LibrasHangmanApp:

    def __init__(self):

        print("Inicializando sistema...")

        self.camera = Camera()
        self.hand_tracker = HandTracker()

        bundle = joblib.load("model.joblib")

        self.model = bundle["model"]
        self.label_encoder = bundle["label_encoder"]

        self.gesture_recognizer = GestureRecognizer()
        self.game_state = GameState()

        self.current_gesture = "-"
        self.current_confidence = 0.0

        self.window = ctk.CTk()
        self.window.title("Jogo da Forca em LIBRAS")
        self.window.geometry("1400x850")

        self.build_ui()

        self.update_frame()

    def build_ui(self):

        title = ctk.CTkLabel(
            self.window,
            text="JOGO DA FORCA EM LIBRAS",
            font=("Arial", 30, "bold")
        )
        title.pack(pady=15)

        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        # ==========================
        # ESQUERDA - CAMERA
        # ==========================

        self.camera_frame = ctk.CTkFrame(self.main_frame)
        self.camera_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.camera_label = ctk.CTkLabel(
            self.camera_frame,
            text=""
        )
        self.camera_label.pack(
            fill="both",
            expand=True
        )

        # ==========================
        # DIREITA - JOGO
        # ==========================

        self.info_frame = ctk.CTkFrame(
            self.main_frame,
            width=450
        )
        self.info_frame.pack(
            side="right",
            fill="y",
            padx=10,
            pady=10
        )

        self.word_label = ctk.CTkLabel(
            self.info_frame,
            text=self.game_state.obter_palavra_mascarada(),
            font=("Consolas", 38, "bold")
        )
        self.word_label.pack(pady=20)

        self.hint_label = ctk.CTkLabel(
            self.info_frame,
            text=f"Dica: {self.game_state.dica}",
            font=("Arial", 20)
        )
        self.hint_label.pack(pady=10)

        self.letter_label = ctk.CTkLabel(
            self.info_frame,
            text="Letra: -",
            font=("Arial", 28, "bold")
        )
        self.letter_label.pack(pady=20)

        self.confidence_label = ctk.CTkLabel(
            self.info_frame,
            text="Confiança: 0%",
            font=("Arial", 18)
        )
        self.confidence_label.pack(pady=10)

        self.progress = ctk.CTkProgressBar(
            self.info_frame,
            width=300
        )
        self.progress.pack(pady=10)
        self.progress.set(0)

        self.used_label = ctk.CTkLabel(
            self.info_frame,
            text="Letras usadas:",
            font=("Arial", 18)
        )
        self.used_label.pack(pady=20)

        self.life_label = ctk.CTkLabel(
            self.info_frame,
            text="❤️" * self.game_state.max_erros,
            font=("Arial", 24)
        )
        self.life_label.pack(pady=10)

        self.status_label = ctk.CTkLabel(
            self.info_frame,
            text="",
            font=("Arial", 22, "bold")
        )
        self.status_label.pack(pady=15)

        self.new_game_button = ctk.CTkButton(
            self.info_frame,
            text="Novo Jogo",
            command=self.new_game
        )
        self.new_game_button.pack(pady=20)

    def new_game(self):

        self.game_state.reset()

        self.status_label.configure(text="")

        self.update_game_labels()

    def update_game_labels(self):

        self.word_label.configure(
            text=self.game_state.obter_palavra_mascarada()
        )

        self.hint_label.configure(
            text=f"Dica: {self.game_state.dica}"
        )

        usadas = ", ".join(
            sorted(self.game_state.letras_tentadas)
        )

        self.used_label.configure(
            text=f"Letras usadas: {usadas}"
        )

        vidas = (
            self.game_state.max_erros
            - self.game_state.erros_atuais
        )

        self.life_label.configure(
            text="❤️" * max(vidas, 0)
        )

    def update_frame(self):

        ret, frame = self.camera.read_frame()

        if ret:

            hands = self.hand_tracker.find_hands(frame)

            current_gesture = None
            confidence = 0.0

            confirmed_gesture = None
            progress_ratio = 0.0

            if hands:

                hand = hands[0]

                self.hand_tracker.draw_landmarks(
                    frame,
                    hand
                )

                try:

                    features = extract_features_from_landmarks(
                        hand
                    )

                    pred_enc, confidence = (
                        predict_with_confidence(
                            self.model,
                            features
                        )
                    )

                    current_gesture = (
                        self.label_encoder.inverse_transform(
                            [pred_enc]
                        )[0]
                    )

                    confirmed_gesture, progress_ratio = (
                        self.gesture_recognizer.update(
                            current_gesture
                        )
                    )

                    self.letter_label.configure(
                        text=f"Letra: {current_gesture}"
                    )

                    self.confidence_label.configure(
                        text=f"Confiança: {confidence:.2%}"
                    )

                    self.progress.set(
                        progress_ratio
                    )

                except Exception as e:

                    self.status_label.configure(
                        text=f"Erro: {e}"
                    )

            else:

                self.letter_label.configure(
                    text="Nenhuma mão"
                )

                self.confidence_label.configure(
                    text="Confiança: 0%"
                )

                self.progress.set(0)

            if confirmed_gesture:

                resultado = (
                    self.game_state.processar_tentativa(
                        confirmed_gesture
                    )
                )

                self.update_game_labels()

                if resultado is True:

                    self.status_label.configure(
                        text=f"✅ {confirmed_gesture} correta"
                    )

                elif resultado is False:

                    self.status_label.configure(
                        text=f"❌ {confirmed_gesture} incorreta"
                    )

            if self.game_state.verificar_vitoria():

                self.status_label.configure(
                    text="🎉 VOCÊ VENCEU!"
                )

            elif self.game_state.verificar_derrota():

                self.status_label.configure(
                    text=(
                        f"💀 GAME OVER\n"
                        f"Palavra: {self.game_state.palavra_secreta}"
                    )
                )

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            image = Image.fromarray(rgb)

            image.thumbnail(
                (850, 700)
            )

            photo = ImageTk.PhotoImage(image)

            self.camera_label.configure(
                image=photo
            )

            self.camera_label.image = photo

        self.window.after(
            15,
            self.update_frame
        )

    def run(self):

        try:
            self.window.mainloop()

        finally:
            self.camera.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":

    app = LibrasHangmanApp()
    app.run()