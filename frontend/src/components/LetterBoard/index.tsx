import Button from "../Button";

interface LetterBoardProps {
  title?: string;
  gameContent?: any;
}

type WordType = {
  word: string;
  alreadyUsed: boolean;
};

function LetterBoard({ title, gameContent }: LetterBoardProps) {
  console.log(gameContent);

  const alphabet: WordType[] = Array.from({ length: 26 }, (_, i) => ({
    word: String.fromCharCode(65 + i),
    alreadyUsed: false,
  }));

  return (
    <div className="mx-auto w-full justify-center items-center flex gap-5">
      {/* botao para confirmar o envio da camera */}
      <Button title="ENVIAR SINAL" color="yellow" />
      {/* letras */}
      <div className="text-center">
        <p>{title}</p>

        <div className="flex flex-wrap gap-2 justify-center p-4 min-w-[20vw] max-w-[50vw]">
          {alphabet.map((item: WordType, index) => (
            <button
              key={index}
              disabled={item.alreadyUsed}
              className={`
                    flex items-center justify-center 
                    w-12 h-12 
                    text-lg font-bold uppercase rounded-xl 
                    border-2 transition-all duration-200
                    ${
                      item.alreadyUsed
                        ? "bg-slate-800 border-slate-700 text-slate-500 cursor-not-allowed opacity-50"
                        : "bg-slate-700 border-slate-600 text-white hover:bg-teal-500 hover:border-teal-400 hover:scale-105 active:scale-95 shadow-md"
                    }
                `}
            >
              {item.word}
            </button>
          ))}
        </div>
      </div>
      {/* botao para recomecar o jogo */}
      <Button title="NOVO JOGO" />
    </div>
  );
}

export default LetterBoard;
