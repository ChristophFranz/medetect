import { useEffect, useRef, useState } from "react";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Camera, Globe, RefreshCw } from "lucide-react";

type CameraSource = "webcam" | "ip";

interface CameraViewProps {
  onImageCapture?: (imageData: string) => void;
  isCapturing?: boolean;
  onCameraReady?: (ready: boolean) => void;
}

const CameraView = ({ onImageCapture, isCapturing = false, onCameraReady }: CameraViewProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [hasCamera, setHasCamera] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Camera source state
  const [cameraSource, setCameraSource] = useState<CameraSource>("webcam");
  const [ipCameraUrl, setIpCameraUrl] = useState("http://192.168.0.10");
  const [ipCameraConnected, setIpCameraConnected] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const isReady = cameraSource === "webcam" ? hasCamera : ipCameraConnected;
    onCameraReady?.(isReady);
  }, [hasCamera, ipCameraConnected, cameraSource, onCameraReady]);

  // Webcam setup
  useEffect(() => {
    if (cameraSource !== "webcam") return;
    
    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
        });
        
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setHasCamera(true);
          setError(null);
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
  }, [cameraSource]);

  // IP camera connection handler
  const handleIpCameraConnect = () => {
    setIpCameraConnected(false);
    setError(null);
    // Force iframe reload by briefly clearing and resetting
    if (iframeRef.current) {
      iframeRef.current.src = "";
      setTimeout(() => {
        if (iframeRef.current) {
          iframeRef.current.src = ipCameraUrl;
        }
      }, 100);
    }
  };

  const handleIframeLoad = () => {
    setIpCameraConnected(true);
    setError(null);
  };

  const handleIframeError = () => {
    setIpCameraConnected(false);
    setError("Failed to connect to IP camera. Check URL and network connection.");
  };

  // Capture handling
  useEffect(() => {
    if (!isCapturing) return;

    if (cameraSource === "webcam" && videoRef.current && canvasRef.current && hasCamera) {
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
    } else if (cameraSource === "ip" && ipCameraConnected) {
      // Cannot capture frames from cross-origin iframe
      // Notify user that capture is not supported for IP camera iframe mode
      console.warn("Frame capture is not supported for IP camera iframe mode");
      setError("Frame capture is not available for IP camera mode. Use webcam for capturing.");
    }
  }, [isCapturing, hasCamera, ipCameraConnected, cameraSource, onImageCapture]);

  const switchSource = (source: CameraSource) => {
    // Stop webcam if switching away
    if (cameraSource === "webcam" && videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach(track => track.stop());
    }
    setCameraSource(source);
    setError(null);
    setHasCamera(false);
    setIpCameraConnected(false);
  };

  return (
    <div className="space-y-3">
      {/* Camera source toggle */}
      <div className="flex gap-2">
        <Button
          variant={cameraSource === "webcam" ? "default" : "outline"}
          size="sm"
          onClick={() => switchSource("webcam")}
          className="flex-1"
        >
          <Camera className="w-4 h-4 mr-2" />
          Webcam
        </Button>
        <Button
          variant={cameraSource === "ip" ? "default" : "outline"}
          size="sm"
          onClick={() => switchSource("ip")}
          className="flex-1"
        >
          <Globe className="w-4 h-4 mr-2" />
          IP Camera
        </Button>
      </div>

      {/* IP camera URL input */}
      {cameraSource === "ip" && (
        <div className="flex gap-2">
          <Input
            value={ipCameraUrl}
            onChange={(e) => setIpCameraUrl(e.target.value)}
            placeholder="http://192.168.0.10/video"
            className="flex-1 text-sm"
          />
          <Button size="sm" variant="outline" onClick={handleIpCameraConnect}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      )}

      {/* Camera view */}
      {error ? (
        <div className="w-full h-64 bg-muted rounded-lg flex items-center justify-center border border-border">
          <p className="text-muted-foreground text-sm text-center px-4">{error}</p>
        </div>
      ) : (
        <div className="relative w-full aspect-video bg-foreground/90 rounded-lg overflow-hidden border border-border">
          {cameraSource === "webcam" ? (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
          ) : (
            <iframe
              ref={iframeRef}
              src={ipCameraUrl}
              title="IP Camera Stream"
              onLoad={handleIframeLoad}
              onError={handleIframeError}
              className="w-full h-full border-0"
              allow="camera; microphone"
            />
          )}
          <canvas ref={canvasRef} className="hidden" />
          
          {/* Loading state */}
          {((cameraSource === "webcam" && !hasCamera) || (cameraSource === "ip" && !ipCameraConnected)) && !error && (
            <div className="absolute inset-0 flex items-center justify-center bg-muted">
              <p className="text-muted-foreground">
                {cameraSource === "webcam" ? "Loading camera..." : "Connecting to IP camera..."}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CameraView;
