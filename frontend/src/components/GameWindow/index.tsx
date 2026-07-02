interface GameProps {
  title: string;
  gameContent?: any;
}

function GameWindow({ title, gameContent }: GameProps) {
  console.log(gameContent);

  return (
    <div className="flex flex-col w-[50vw] h-[60vh] border border-gray-200 rounded-xl shadow-lg overflow-hidden">
      <div className="bg-blue-400 py-2 shrink-0">
        <p className="font-bold text-xl text-center text-white">{title}</p>
      </div>

      <div className="bg-white flex-1 flex flex-col justify-between p-6 overflow-y-auto">
        <div className="flex flex-col items-center justify-center flex-1 gap-6">
          <div className="h-48 w-48 bg-gray-100 rounded-lg flex items-center justify-center border border-gray-200">
            <span className="text-gray-400 text-sm">[ Desenho da Forca ]</span>
          </div>

          <div className="flex gap-3 text-2xl font-bold tracking-widest my-4">
            _ _ _ _ _
          </div>

          <div className="text-center text-gray-600">
            <p className="text-sm font-semibold mb-2">Letras já tentadas:</p>
            <div className="flex gap-1 justify-center max-w-md flex-wrap text-sm">
              <span className="bg-gray-200 px-2 py-1 rounded">A</span>
              <span className="bg-gray-200 px-2 py-1 rounded">E</span>
              <span className="bg-gray-200 px-2 py-1 rounded">O</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default GameWindow;
