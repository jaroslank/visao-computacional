// import { useState } from "react";

import CameraWindow from "./components/CameraWindow";
import GameWindow from "./components/GameWindow";
import Header from "./components/Header";
import LetterBoard from "./components/LetterBoard/index";

function Home() {
  // const [count, setCount] = useState(0);

  return (
    <div className="min-h-screen w-full bg-jogo bg-cover bg-center bg-no-repeat bg-fixed flex flex-col">
      <div className="mx-[5vw] bg-blue-200 border-blue-200 rounded-2xl my-5">
        <Header />

        <div className="mx-5 flex justify-between gap-5 py-8">
          <CameraWindow title={"CAMERA"} />
          <GameWindow title={"Game"} />
        </div>

        <div className="mx-5">
          <LetterBoard title={"LETRAS SOBRANDO"} />
        </div>
      </div>
    </div>
  );
}

export default Home;
