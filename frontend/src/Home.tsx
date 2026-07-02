// import { useState } from "react";

import { useRef, useState } from "react";
import CameraWindow from "./components/CameraWindow";
import GameWindow from "./components/GameWindow";
import Header from "./components/Header";
import LetterBoard from "./components/LetterBoard/index";

function Home() {
  const [disparo, setDisparo] = useState(false);
  const dispararSinal = () => {
    setDisparo(true);
  };

  return (
    <div className="min-h-screen w-full bg-jogo bg-cover bg-center bg-no-repeat bg-fixed flex flex-col">
      <div className="mx-[5vw] bg-blue-200 border-blue-200  my-5 mt-10">
        <Header />

        <div className="mx-5 flex justify-between gap-5 py-8">
          <CameraWindow
            title={"CAMERA"}
            gatilho={disparo}
            resetGatilho={() => setDisparo(false)}
          />
          <GameWindow title={"Game"} />
          //aqui vai ficar a lógica da palavra, ele vai receber a letra do back
          e validar pra ver se errou ou não //se acertar vai adicionar e enviar
          a letra usada pro letterboard //se
        </div>

        <div className="mx-5">
          <LetterBoard title={"LETRAS SOBRANDO"} disparo={dispararSinal} />
          //aqui ele tem todas as letras, e quando uma letra for usada o jogo
          tem que bloquear a letra dentro do letter board
        </div>
      </div>
    </div>
  );
}

export default Home;
