import time
from .. import config

class GestureRecognizer:
    """
    Gerencia a confirmação de gestos com base no tempo de permanência (Dwell Time).
    Isso evita que gestos transitórios ou tremidos sejam registrados como uma tentativa.
    """
    def __init__(self, dwell_time_seconds=config.DWELL_TIME_SECONDS):
        """
        Inicializa o reconhecedor de gestos.

        Args:
            dwell_time_seconds (float): O tempo em segundos que um gesto deve ser
                                        mantido para ser confirmado.
        """
        self.dwell_time = dwell_time_seconds
        self.current_gesture = None
        self.gesture_start_time = 0
        self.last_confirmed_gesture = None

    def update(self, detected_gesture):
        """
        Atualiza o estado do reconhecedor com o gesto detectado no frame atual.

        Args:
            detected_gesture (str | None): A letra classificada pelo LibrasClassifier
                                           ou None se nenhum gesto foi detectado.

        Returns:
            Tuple[str | None, float]: Uma tupla contendo:
                                      - A letra confirmada (str) ou None.
                                      - O progresso da confirmação (float de 0.0 a 1.0).
        """
        current_time = time.time()
        progress_ratio = 0.0
        confirmed_gesture = None

        # Se o gesto mudou ou desapareceu
        if detected_gesture != self.current_gesture:
            self.current_gesture = detected_gesture
            self.gesture_start_time = current_time
            # Se o gesto mudou, o último confirmado não é mais válido para bloqueio
            if self.current_gesture is None:
                self.last_confirmed_gesture = None

        # Se estamos mantendo um gesto válido
        if self.current_gesture is not None:
            elapsed_time = current_time - self.gesture_start_time
            progress_ratio = min(elapsed_time / self.dwell_time, 1.0)

            # Se o tempo de espera foi atingido e este gesto ainda não foi o último confirmado
            if progress_ratio >= 1.0 and self.current_gesture != self.last_confirmed_gesture:
                confirmed_gesture = self.current_gesture
                self.last_confirmed_gesture = self.current_gesture # Bloqueia re-confirmação

        return confirmed_gesture, progress_ratio
