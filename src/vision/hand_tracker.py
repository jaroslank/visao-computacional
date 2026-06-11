import cv2
import mediapipe as mp
from .. import config

class HandTracker:
    """
    Encapsula a detecção de mãos e o desenho de landmarks usando MediaPipe.
    """
    def __init__(self,
                 max_hands=config.HANDS_MAX_NUM,
                 min_detection_confidence=config.HANDS_MIN_DETECTION_CONFIDENCE,
                 min_tracking_confidence=config.HANDS_MIN_TRACKING_CONFIDENCE):
        """
        Inicializa o detector de mãos do MediaPipe.
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=max_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_draw = mp.solutions.drawing_utils

    def find_hands(self, frame):
        """
        Encontra as mãos em um frame e retorna os landmarks.

        Args:
            frame (numpy.ndarray): O frame da câmera (em BGR).

        Returns:
            list: Uma lista de landmarks de mão detectados. Retorna None se nenhuma mão for encontrada.
        """
        # Converte a imagem para RGB, pois o MediaPipe espera esse formato
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False # Otimização: marca como não-gravável

        # Processa a imagem para encontrar as mãos
        results = self.hands.process(rgb_frame)

        rgb_frame.flags.writeable = True # Reabilita a escrita
        return results.multi_hand_landmarks

    def draw_landmarks(self, frame, hand_landmarks):
        """
        Desenha os landmarks e as conexões da mão no frame.

        Args:
            frame (numpy.ndarray): O frame onde desenhar.
            hand_landmarks: Os landmarks de uma única mão.
        """
        self.mp_draw.draw_landmarks(
            frame,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS
        )