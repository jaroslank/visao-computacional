import { useEffect, useRef } from "react";

interface CameraProps {
  title: string;
  videoRef?: React.RefObject<HTMLVideoElement | null>;
}

function CameraWindow({ title, videoRef }: CameraProps) {
  const internalVideoRef = useRef<HTMLVideoElement>(null);
  const activeVideoRef = videoRef || internalVideoRef;

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

  return (
    <div className="flex flex-col w-[50vw] h-[60vh] border border-gray-200 rounded-xl shadow-lg overflow-hidden">
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

        <div className="absolute inset-0 border-4 border-dashed border-white/20 pointer-events-none m-15 rounded-lg flex items-center justify-center">
          <p className="text-white/40 text-sm font-semibold select-none">
            Posicione sua mão aqui
          </p>
        </div>
      </div>
    </div>
  );
}

export default CameraWindow;
