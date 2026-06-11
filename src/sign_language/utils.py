import math

def calcular_distancia_euclidiana(ponto1, ponto2):
    """
    Calcula a distância euclidiana 2D entre dois landmarks.
    """
    return math.sqrt((ponto1.x - ponto2.x)**2 + (ponto1.y - ponto2.y)**2)
