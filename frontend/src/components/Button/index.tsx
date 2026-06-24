interface ButtonProps {
  title?: string;
  action?: () => void;
}

function Button({ title, action }: ButtonProps) {
  return (
    <button
      onClick={action}
      className="h-[50px] px-4 py-2 bg-teal-500 hover:bg-teal-600 active:scale-95 text-white font-semibold rounded-xl transition-all duration-200 shadow-md"
    >
      {title}
    </button>
  );
}

export default Button;
