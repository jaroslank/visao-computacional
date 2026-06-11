import cv2
from .. import config

class Camera:
    """
    Encapsula a lógica de captura de vídeo do OpenCV, garantindo que a
    câmera seja inicializada e liberada corretamente.
    """
    def __init__(self, device_index=config.CAMERA_INDEX, width=config.FRAME_WIDTH, height=config.FRAME_HEIGHT):
        """
        Inicializa a câmera com as definições normais usando backend DShow 
        para evitar lentidão no Windows.
        """
        # Força o uso do backend DirectShow no Windows, que costuma abrir na hora!
        self.cap = cv2.VideoCapture(device_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            # Fallback para o default se o dshow falhar
            self.cap = cv2.VideoCapture(device_index)
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read_frame(self):
        """
        Lê um único frame da câmera.

        Returns:
            Tuple[bool, numpy.ndarray]: Uma tupla contendo um booleano de sucesso
                                        e o frame capturado (se bem-sucedido).
                                        O frame é espelhado horizontalmente.
        """
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
        return ret, frame

    def release(self):
        """Libera o recurso da câmera."""
        self.cap.release()

    def __del__(self):
        """Garante que a câmera seja liberada quando o objeto for destruído."""
        self.release()