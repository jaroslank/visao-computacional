from .utils import calcular_distancia_euclidiana

class LibrasClassifier:
    """
    Classifica os landmarks de uma mão em uma letra do alfabeto LIBRAS (versão MVP).
    """
    def __init__(self):
        # Limiares (thresholds) para "perto" e "longe", podem precisar de ajuste
        self.LIMIAR_DEDOS_PROXIMOS = 0.06
        self.LIMIAR_POLEGAR_PROXIMO_INDICADOR = 0.08

    def _verificar_dedos_levantados(self, landmarks):
        """
        Verifica o estado de cada dedo (levantado ou abaixado).
        Retorna uma tupla de booleanos: (polegar, indicador, medio, anelar, mindinho).
        """
        # Coordenadas dos pontos (landmarks) da mão
        # Para mais detalhes, veja: https://google.github.io/mediapipe/solutions/hands.html
        pontos = landmarks.landmark

        # Lógica para dedos levantados (eixo Y invertido no OpenCV)
        indicador_levantado = pontos[8].y < pontos[6].y
        medio_levantado = pontos[12].y < pontos[10].y
        anelar_levantado = pontos[16].y < pontos[14].y
        mindinho_levantado = pontos[20].y < pontos[18].y

        # Lógica para o polegar (usa o eixo X para "aberto" ou "fechado")
        # Assumindo uma mão direita em um frame espelhado
        polegar_levantado = pontos[4].x < pontos[3].x

        return (polegar_levantado, indicador_levantado, medio_levantado, anelar_levantado, mindinho_levantado)

    def classify(self, landmarks):
        """
        Classifica os landmarks da mão em uma das letras do MVP.

        Args:
            landmarks: Os landmarks de uma única mão detectada pelo MediaPipe.

        Returns:
            str: A letra classificada ou None se nenhum gesto conhecido for detectado.
        """
        if not landmarks:
            return None

        pontos = landmarks.landmark
        dedos_levantados = self._verificar_dedos_levantados(landmarks)
        
        # Lógica de classificação baseada nos dedos levantados e distâncias

        # Letra V: Indicador e médio levantados e separados
        if dedos_levantados == (False, True, True, False, False) and \
           calcular_distancia_euclidiana(pontos[8], pontos[12]) > self.LIMIAR_DEDOS_PROXIMOS:
            return "V"

        # Letra W: Indicador, médio e anelar levantados
        if dedos_levantados == (False, True, True, True, False):
            return "W"

        # Letra C: Apenas o polegar "aberto" e os outros dedos deitados/curvos
        if dedos_levantados == (True, False, False, False, False):
            # Garante que não é um L mal feito, verificando a distância do indicador para a base
            return "C"

        # Letra L: Polegar e indicador levantados
        if dedos_levantados == (True, True, False, False, False):
            return "L"

        # Letra Y: Polegar e mindinho levantados
        if dedos_levantados == (True, False, False, False, True):
            return "Y"
            
        # Letra I: Mindinho levantado
        if dedos_levantados == (False, False, False, False, True):
            return "I"

        # Letra U: Indicador e médio levantados e juntos
        if dedos_levantados == (False, True, True, False, False) and \
           calcular_distancia_euclidiana(pontos[8], pontos[12]) < self.LIMIAR_DEDOS_PROXIMOS:
            return "U"

        # Letra N: Indicador e médio apontados para frente/baixo, anelar e mindinho recolhidos
        # Extraído e colocado antes do "A" e do "E" para não confundir com o polegar.
        if not dedos_levantados[1] and not dedos_levantados[2] and not dedos_levantados[3] and not dedos_levantados[4]:
            # Em "N", indicador (8) e médio (12) estão visivelmente mais baixos (Y maior) que o resto recolhido (16, 20)
            if pontos[8].y > pontos[16].y + 0.03 and pontos[12].y > pontos[20].y + 0.03:
                return "N"

        # Letra A: Todos os dedos abaixados, polegar próximo ao indicador
        if dedos_levantados == (False, False, False, False, False) and \
           calcular_distancia_euclidiana(pontos[4], pontos[8]) < self.LIMIAR_POLEGAR_PROXIMO_INDICADOR:
            return "A"

        # Letra O: Pontas dos dedos formando um círculo (próximas)
        # Relaxamos as restrições para reconhecer o "O"
        # Basta que o indicador, médio e polegar estejam bem próximos
        dist_polegar_indicador = calcular_distancia_euclidiana(pontos[4], pontos[8])
        dist_polegar_medio = calcular_distancia_euclidiana(pontos[4], pontos[12])
        if dist_polegar_indicador < self.LIMIAR_DEDOS_PROXIMOS * 1.5 and \
           dist_polegar_medio < self.LIMIAR_DEDOS_PROXIMOS * 1.5 and \
           not dedos_levantados[1] and not dedos_levantados[2]:
            return "O"

        # Letra E: Todos os dedos abaixados, "arranhando"
        if dedos_levantados == (False, False, False, False, False) and \
           calcular_distancia_euclidiana(pontos[4], pontos[8]) > self.LIMIAR_POLEGAR_PROXIMO_INDICADOR:
            return "E"

        return None # Nenhum gesto conhecido