import cv2
import time

# Importa todas as nossas classes dos módulos
from src.vision.camera import Camera
from src.vision.hand_tracker import HandTracker
from src.sign_language.classifier import LibrasClassifier
from src.core.gesture_recognizer import GestureRecognizer
from src.core.game_state import GameState
from src.ui.renderer import UIRenderer

def main():
    print("Iniciando componentes...")
    try:
        print("- Câmera")
        camera = Camera()
        print("- Tracker MediaPipe")
        hand_tracker = HandTracker()
        print("- Jogo base")
        classifier = LibrasClassifier()
        gesture_recognizer = GestureRecognizer()
        game_state = GameState()
        print("- UI Render")
        renderer = UIRenderer()
    except Exception as e:
        print(f"ERRO CRÍTICO NA INICIALIZAÇÃO: {e}")
        return

    print("Componentes Inicializados!")
    print(f"A dica é: {game_state.dica}")

    # Loop principal do jogo
    while True:
        # 2. Captura de Imagem
        ret, frame = camera.read_frame()
        if not ret:
            print("Erro ao capturar o frame da câmera. Encerrando.")
            break

        # 3. Detecção e Classificação de Gestos
        hand_landmarks = hand_tracker.find_hands(frame)
        current_gesture = None
        confirmed_gesture = None
        progress_ratio = 0.0

        if hand_landmarks:
            # Pega a primeira mão detectada
            mao = hand_landmarks[0]
            
            # Desenha os landmarks na tela
            hand_tracker.draw_landmarks(frame, mao)
            
            # Classifica o gesto
            current_gesture = classifier.classify(mao)
            
            # Atualiza o reconhecedor de gestos para aplicar o Dwell Time
            confirmed_gesture, progress_ratio = gesture_recognizer.update(current_gesture)

        # 4. Lógica do Jogo
        if confirmed_gesture:
            print(f"Letra confirmada: {confirmed_gesture}")
            game_state.processar_tentativa(confirmed_gesture)
            
            # Se o jogo acabou (vitória ou derrota), espera um pouco e reseta
            if game_state.verificar_vitoria() or game_state.verificar_derrota():
                renderer.draw_game_elements(frame, game_state, current_gesture, progress_ratio)
                cv2.imshow("Jogo da Forca em LIBRAS", frame)
                cv2.waitKey(3000) # Pausa por 3 segundos
                game_state.reset()


        # 5. Renderização da UI
        renderer.draw_game_elements(frame, game_state, current_gesture, progress_ratio)

        # 6. Exibição do Frame
        cv2.imshow("Jogo da Forca em LIBRAS", frame)

        # 7. Condição de Saída
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Libera os recursos
    camera.release()
    cv2.destroyAllWindows()
    print("Jogo encerrado.")

if __name__ == '__main__':
    main()