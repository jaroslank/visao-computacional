import cv2
import numpy as np
from pathlib import Path

class UIRenderer:
    """
    Responsável por desenhar todos os elementos visuais do jogo na tela,
    incluindo a forca, texto, e barras de progresso.
    """
    def __init__(self):
        # Cores (BGR)
        self.COLOR_WHITE = (255, 255, 255)
        self.COLOR_GREEN = (0, 255, 0)
        self.COLOR_RED = (0, 0, 255)
        self.COLOR_BLUE = (255, 0, 0)

        # Fontes
        self.FONT = cv2.FONT_HERSHEY_SIMPLEX
        
        # Carregar assets da forca
        self.hangman_assets = self._load_hangman_assets()

    def _load_hangman_assets(self):
        """Carrega as imagens da forca da pasta de assets."""
        assets_path = Path(__file__).parent.parent.parent / "assets" / "hangman"
        # Supondo que os arquivos se chamem 0.png, 1.png, ..., 6.png
        # Crie esses arquivos na pasta assets/hangman
        return [cv2.imread(str(assets_path / f"{i}.png"), cv2.IMREAD_UNCHANGED) for i in range(7)]

    def _overlay_transparent(self, background, overlay, x, y):
        """Sobrepõe uma imagem PNG transparente no frame."""
        bg_h, bg_w, _ = background.shape
        h, w, _ = overlay.shape

        # Garante que a sobreposição não saia dos limites do frame
        if x >= bg_w or y >= bg_h:
            return background
        
        # Lida com a transparência (canal alfa)
        alpha = overlay[:, :, 3] / 255.0
        alpha_inv = 1.0 - alpha

        # Define a região de interesse (ROI)
        roi = background[y:y+h, x:x+w]

        for c in range(0, 3):
            roi[:, :, c] = (alpha * overlay[:, :, c] + alpha_inv * roi[:, :, c])
        
        background[y:y+h, x:x+w] = roi
        return background

    def draw_progress_bar(self, frame, ratio, x=50, y=650, width=200, height=30):
        """Desenha a barra de progresso para o Dwell Time."""
        # Desenha o contorno
        cv2.rectangle(frame, (x, y), (x + width, y + height), self.COLOR_WHITE, 2)
        # Desenha o preenchimento
        fill_width = int(width * ratio)
        cv2.rectangle(frame, (x, y), (x + fill_width, y + height), self.COLOR_GREEN, -1)

    def draw_game_elements(self, frame, game_state, current_gesture, progress_ratio):
        """
        Desenha todos os elementos do jogo no frame.
        """
        # 1. Desenha a forca baseada nos erros
        if game_state.erros_atuais > 0 and game_state.erros_atuais < len(self.hangman_assets):
            hangman_img = self.hangman_assets[game_state.erros_atuais]
            if hangman_img is not None:
                frame = self._overlay_transparent(frame, hangman_img, 900, 100)

        # 2. Desenha a palavra mascarada
        cv2.putText(frame, game_state.obter_palavra_mascarada(), (50, 500), self.FONT, 2, self.COLOR_WHITE, 3)

        # 3. Desenha a dica
        cv2.putText(frame, f"Dica: {game_state.dica}", (50, 580), self.FONT, 1, self.COLOR_WHITE, 2)

        # 4. Desenha a letra detectada atualmente
        if current_gesture:
            cv2.putText(frame, f"Gesto: {current_gesture}", (50, 100), self.FONT, 2, self.COLOR_BLUE, 3)

        # 5. Desenha a barra de progresso
        self.draw_progress_bar(frame, progress_ratio)

        # 6. Lógica de Fim de Jogo
        if game_state.verificar_vitoria():
            cv2.putText(frame, "VOCE VENCEU!", (300, 350), self.FONT, 3, self.COLOR_GREEN, 5)
        elif game_state.verificar_derrota():
            cv2.putText(frame, "GAME OVER", (350, 350), self.FONT, 3, self.COLOR_RED, 5)
            # Mostra a última parte da forca
            final_hangman = self.hangman_assets[-1]
            if final_hangman is not None:
                frame = self._overlay_transparent(frame, final_hangman, 900, 100)
