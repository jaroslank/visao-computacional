import json
import random
from pathlib import Path

class GameState:
    """
    Gerencia o estado completo do jogo da forca, incluindo a palavra secreta,
    tentativas, erros e condições de vitória/derrota.
    """
    def __init__(self, max_erros=6):
        """
        Inicializa o estado do jogo.

        Args:
            max_erros (int): Número máximo de tentativas incorretas permitidas.
        """
        self.max_erros = max_erros
        self.palavras_por_categoria = self._carregar_palavras()
        self.palavra_secreta, self.dica = self._escolher_nova_palavra()
        self.letras_tentadas = set()
        self.erros_atuais = 0

    def _carregar_palavras(self):
        """Carrega as palavras do arquivo JSON."""
        caminho_json = Path(__file__).parent.parent.parent / "data" / "words.json"
        with open(caminho_json, 'r', encoding='utf-8') as f:
            return json.load(f)["categorias"]

    def _escolher_nova_palavra(self):
        """Escolhe aleatoriamente uma nova palavra e sua dica do banco."""
        categoria = random.choice(list(self.palavras_por_categoria.keys()))
        item_palavra = random.choice(self.palavras_por_categoria[categoria])
        return item_palavra["palavra"].upper(), item_palavra["dica"]

    def processar_tentativa(self, letra):
        """
        Processa uma nova tentativa de letra.

        Args:
            letra (str): A letra que o jogador tentou.

        Returns:
            bool: True se a letra estava na palavra, False caso contrário.
                  Retorna None se a letra já foi tentada.
        """
        letra = letra.upper()
        if letra in self.letras_tentadas:
            return None # Tentativa repetida

        self.letras_tentadas.add(letra)

        if letra in self.palavra_secreta:
            return True
        else:
            self.erros_atuais += 1
            return False

    def obter_palavra_mascarada(self):
        """
        Retorna a palavra secreta com underscores para letras não adivinhadas.
        Ex: 'P _ _ A V R A'
        """
        display = [letra if letra in self.letras_tentadas else '_' for letra in self.palavra_secreta]
        return " ".join(display)

    def verificar_vitoria(self):
        """Verifica se o jogador venceu."""
        return all(letra in self.letras_tentadas for letra in self.palavra_secreta)

    def verificar_derrota(self):
        """Verifica se o jogador perdeu (atingiu o limite de erros)."""
        return self.erros_atuais >= self.max_erros

    def reset(self):
        """Reseta o jogo para uma nova partida com uma nova palavra."""
        self.palavra_secreta, self.dica = self._escolher_nova_palavra()
        self.letras_tentadas = set()
        self.erros_atuais = 0
        print(f"Novo jogo iniciado! A dica é: {self.dica}")

# Exemplo de como usar a classe (para teste)
if __name__ == '__main__':
    jogo = GameState()
    print(f"Bem-vindo ao Jogo da Forca!")
    print(f"A dica é: {jogo.dica}")

    while not jogo.verificar_vitoria() and not jogo.verificar_derrota():
        print(f"\nPalavra: {jogo.obter_palavra_mascarada()}")
        print(f"Erros: {jogo.erros_atuais}/{jogo.max_erros}")
        print(f"Tentativas: {', '.join(sorted(list(jogo.letras_tentadas)))}")
        
        tentativa = input("Digite uma letra: ")
        if not tentativa: continue

        resultado = jogo.processar_tentativa(tentativa[0])
        if resultado is None:
            print("Você já tentou essa letra!")
        elif resultado:
            print("Boa! A letra está na palavra.")
        else:
            print("Que pena! A letra não está na palavra.")

    if jogo.verificar_vitoria():
        print(f"\nParabéns! Você venceu! A palavra era: {jogo.palavra_secreta}")
    else:
        print(f"\nGame Over! Você perdeu. A palavra era: {jogo.palavra_secreta}")

    # Testando o reset
    jogar_novamente = input("Jogar novamente? (s/n): ")
    if jogar_novamente.lower() == 's':
        jogo.reset()
        # Aqui o loop do jogo começaria novamente
