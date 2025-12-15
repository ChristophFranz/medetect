import { useEffect, useRef, useState } from "react";

interface CameraViewProps {
  onImageCapture?: (imageData: string) => void;
  isCapturing?: boolean;
}

const CameraView = ({ onImageCapture, isCapturing = false }: CameraViewProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hasCamera, setHasCamera] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
        });
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setHasCamera(true);
        }
      } catch (err) {
        console.error("Camera access denied:", err);
        setError("Camera access denied or not available");
        setHasCamera(false);
      }
    };

    startCamera();

    return () => {
      if (videoRef.current?.srcObject) {
        const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, []);

  useEffect(() => {
    if (isCapturing && videoRef.current && canvasRef.current && hasCamera) {
      const canvas = canvasRef.current;
      const video = videoRef.current;
      const ctx = canvas.getContext("2d");
      
      if (ctx) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);
        const imageData = canvas.toDataURL("image/jpeg");
        onImageCapture?.(imageData);
      }
    }
  }, [isCapturing, hasCamera, onImageCapture]);

  if (error) {
    return (
      <div className="w-full h-64 bg-muted rounded-lg flex items-center justify-center border border-border">
        <p className="text-muted-foreground text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="relative w-full aspect-video bg-foreground/90 rounded-lg overflow-hidden border border-border">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover"
      />
      <canvas ref={canvasRef} className="hidden" />
      {!hasCamera && (
        <div className="absolute inset-0 flex items-center justify-center bg-muted">
          <p className="text-muted-foreground">Loading camera...</p>
        </div>
      )}
    </div>
  );
};

export default CameraView;
