import { Component } from "react";

class Header extends Component {
  render() {
    return (
      <header className="sticky top-0 z-50 w-full border-slate-800 bg-slate-900/80 backdrop-blur-md py-4 px-6 flex justify-between items-center rounded-t-2xl">
        <h1 className="text-2xl md:text-3xl font-black tracking-wider bg-gradient-to-r from-teal-400 to-emerald-400 bg-clip-text text-transparent drop-shadow-sm select-none">
          JOGO DA FORCA EM LIBRAS
        </h1>

        <div className="flex items-center gap-4 text-sm font-medium text-slate-400">
          <span className="bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700/50">
            🤖 Visão Computacional
          </span>
        </div>
      </header>
    );
  }
}

export default Header;
