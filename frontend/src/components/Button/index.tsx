interface ButtonProps {
  title?: string;
  action?: () => void;
  color?: ButtonColors;
}

type ButtonColors = "yellow" | "teal";

const colorVariants = {
  teal: "bg-teal-500 hover:bg-teal-600 focus:ring-teal-400",
  yellow: "bg-amber-500 hover:bg-amber-600 focus:ring-amber-400 text-slate-900",
};

function Button({ title, action, color = "teal" }: ButtonProps) {
  const currentVariant = colorVariants[color];
  return (
    <button
      onClick={action}
      className={`
        h-[50px] px-6 py-2 
        font-semibold rounded-xl 
        active:scale-95 transition-all duration-200 shadow-md
        focus:outline-none focus:ring-2 focus:ring-offset-2
        ${currentVariant}
      `}
    >
      {title}
    </button>
  );
}

export default Button;
