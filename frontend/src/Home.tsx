// import { useState } from "react";

import GameWindow from "./components/GameWindow";
import Header from "./components/Header";
import LetterBoard from "./components/LetterBoard/index";

function Home() {
  // const [count, setCount] = useState(0);

  return (
    <>
      <div className="mx-[5vw] bg-blue-200 border-blue-200 rounded-2xl">
        <Header />

        <div className="mx-5 flex justify-between gap-5 py-8">
          <GameWindow title={"CAMERA"} />
          <GameWindow title={"Game"} />
        </div>

        <div className="mx-5">
          <LetterBoard title={"LETRAS SOBRANDO"} />
        </div>
      </div>
    </>
  );
}

export default Home;
