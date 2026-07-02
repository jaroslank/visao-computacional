import { useEffect, useRef, useState } from "react";

interface CameraProps {
  title: string;
  videoRef?: React.RefObject<HTMLVideoElement | null>;
  gatilho?: boolean;
  resetGatilho: () => void;
}

function CameraWindow({ title, videoRef, gatilho, resetGatilho }: CameraProps) {
  const internalVideoRef = useRef<HTMLVideoElement>(null);
  const activeVideoRef = videoRef || internalVideoRef;
  const [previewImagem, setPreviewImagem] = useState<string | null>(null);

  useEffect(() => {
    let streamEmUso: MediaStream | null = null;

    async function ativarCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720 },
          audio: false,
        });

        streamEmUso = stream;

        if (activeVideoRef.current) {
          activeVideoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Erro ao acessar a câmera do usuário:", err);
      }
    }

    ativarCamera();

    return () => {
      if (streamEmUso) {
        streamEmUso.getTracks().forEach((track) => track.stop());
      }
    };
  }, [activeVideoRef]);

  useEffect(() => {
    if (gatilho) {
      const video = activeVideoRef.current;

      if (video && video.readyState === video.HAVE_ENOUGH_DATA) {
        const canvas = document.createElement("canvas");
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const context = canvas.getContext("2d");

        if (context) {
          context.translate(canvas.width, 0);
          context.scale(-1, 1);

          context.drawImage(video, 0, 0, canvas.width, canvas.height);

          const fotoBase64 = canvas.toDataURL("image/jpeg");
          setPreviewImagem(fotoBase64);

          alert("Print tirado com sucesso de dentro da câmera!");
          console.log("Sua imagem em Base64 está pronta:", fotoBase64);

          // O próximo passo aqui será enviar essa 'fotoBase64' para o Python ou devolver para o App.tsx
        }
      } else {
        console.warn("A câmera ainda não está pronta para tirar o print.");
      }

      if (resetGatilho) {
        resetGatilho();
      }
    }
  }, [gatilho, activeVideoRef, resetGatilho]);
  return (
    <div className="flex flex-col w-[50vw] h-[60vh] border border-gray-200 rounded-xl shadow-lg overflow-hidden bg-black">
      <div className="bg-blue-400 py-2 shrink-0">
        <p className="font-bold text-xl text-center text-white">{title}</p>
      </div>

      <div className="bg-black flex-1 flex justify-center items-center relative overflow-hidden">
        <video
          ref={activeVideoRef}
          autoPlay
          playsInline
          className="w-full h-full object-cover transform -scale-x-100"
        />

        <div className="absolute inset-0 border-4 border-dashed border-white/20 pointer-events-none my-15 mx-30  rounded-lg flex items-center justify-center">
          <p className="text-white/40 text-sm font-semibold select-none">
            Posicione sua mão aqui
          </p>
        </div>

        {previewImagem && (
          <div className="absolute bottom-4 right-4 w-32 md:h-40 md:w-40 bg-slate-900/90 p-1.5 rounded-lg shadow-2xl border border-white/20 flex flex-col gap-1 transition-all animate-fade-in backdrop-blur-sm">
            <div className="flex justify-between items-center px-1">
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                Último Print
              </span>

              <button
                onClick={() => setPreviewImagem(null)}
                className="text-gray-400 hover:text-white text-xs font-semibold px-1"
              >
                ×
              </button>
            </div>

            <img
              src={previewImagem}
              alt="Preview capturado"
              className="w-full h-24 md:h-52 object-cover rounded-md border border-white/10 shadow-inner"
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default CameraWindow;
