interface GameProps {
  title: string;
  gameContent?: any;
}

function GameWindow({ title, gameContent }: GameProps) {
  console.log(gameContent);
  return (
    <div className="mx-auto flex-col gap-5">
      <div className="bg-blue-400 rounded-t-xl ">
        <p className="font-bold text-xl text-center py-1">{title}</p>
      </div>
      <div className="bg-white">
        <img
          src="https://images.unsplash.com/photo-1515879218367-8466d910aaa4"
          className="w-50vh h-50vh object-cover"
        />
      </div>
    </div>
  );
}

export default GameWindow;
