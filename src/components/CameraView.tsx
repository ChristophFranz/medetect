import { useEffect, useRef, useState } from "react";
import { Button } from "./ui/button";
import { Camera, Globe, RefreshCw, ExternalLink } from "lucide-react";

type CameraSource = "webcam" | "ip";
type IpDisplayMode = "mjpeg" | "iframe";

interface CameraViewProps {
  onImageCapture?: (imageData: string) => void;
  isCapturing?: boolean;
  onCameraReady?: (ready: boolean) => void;
}

const FIXED_IP_BASE = "http://192.168.1.10";

const MJPEG_CANDIDATES = [
  `${FIXED_IP_BASE}/mjpeg`,
  `${FIXED_IP_BASE}/video`,
  `${FIXED_IP_BASE}/video/mjpg`,
  `${FIXED_IP_BASE}/mjpg/video.mjpg`,
  `${FIXED_IP_BASE}/cgi-bin/mjpg/video.cgi`,
  `${FIXED_IP_BASE}/axis-cgi/mjpg/video.cgi`,
];

const CameraView = ({ onImageCapture, isCapturing = false, onCameraReady }: CameraViewProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [hasCamera, setHasCamera] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [cameraSource, setCameraSource] = useState<CameraSource>("webcam");

  // IP camera states
  const [ipConnected, setIpConnected] = useState(false);
  const [ipMode, setIpMode] = useState<IpDisplayMode>("mjpeg");
  const [ipUrl, setIpUrl] = useState<string>(MJPEG_CANDIDATES[0]);
  const [ipTryIndex, setIpTryIndex] = useState(0);
  const [reloadKey, setReloadKey] = useState(0);

  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const isReady = cameraSource === "webcam" ? hasCamera : ipConnected;
    onCameraReady?.(isReady);
  }, [hasCamera, ipConnected, cameraSource, onCameraReady]);

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
        tracks.forEach((track) => track.stop());
      }
    };
  }, [cameraSource]);

  // When switching to IP mode, start with MJPEG attempt #0
  useEffect(() => {
    if (cameraSource !== "ip") return;

    setError(null);
    setIpConnected(false);
    setIpMode("mjpeg");
    setIpTryIndex(0);
    setIpUrl(MJPEG_CANDIDATES[0]);
    setReloadKey((k) => k + 1);
  }, [cameraSource]);

  const handleIpReload = () => {
    setError(null);
    setIpConnected(false);
    setIpMode("mjpeg");
    setIpTryIndex(0);
    setIpUrl(MJPEG_CANDIDATES[0]);
    setReloadKey((k) => k + 1);
  };

  const handleMjpegError = () => {
    // Try next candidate; if none left, fall back to iframe gateway
    const next = ipTryIndex + 1;
    if (next < MJPEG_CANDIDATES.length) {
      setIpTryIndex(next);
      setIpUrl(MJPEG_CANDIDATES[next]);
      setReloadKey((k) => k + 1);
      return;
    }

    setIpMode("iframe");
    setIpUrl(FIXED_IP_BASE);
    setReloadKey((k) => k + 1);
  };

  const handleIpLoad = () => {
    setIpConnected(true);
    setError(null);
  };

  const handleIframeError = () => {
    setIpConnected(false);
    setError("Could not load the camera gateway. Check that you are on the same network as 192.168.1.10.");
  };

  const switchSource = (source: CameraSource) => {
    // Stop webcam if switching away
    if (cameraSource === "webcam" && videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach((track) => track.stop());
    }
    setCameraSource(source);
    setError(null);
    setHasCamera(false);
    setIpConnected(false);
  };

  // Capture handling (webcam only, unchanged)
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
    } else if (cameraSource === "ip") {
      // Still blocked for capture unless same-origin/proxy
      console.warn("IP camera capture not supported without a same-origin proxy/snapshot endpoint.");
    }
  }, [isCapturing, hasCamera, cameraSource, onImageCapture]);

  const ipSrcWithBuster =
    ipMode === "mjpeg"
      ? `${ipUrl}${ipUrl.includes("?") ? "&" : "?"}t=${reloadKey}`
      : `${FIXED_IP_BASE}${FIXED_IP_BASE.includes("?") ? "&" : "?"}t=${reloadKey}`;

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

      {/* IP controls (no input, fixed IP) */}
      {cameraSource === "ip" && (
        <div className="flex gap-2 items-center">
          <Button size="sm" variant="outline" onClick={handleIpReload}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Reload
          </Button>

          <a
            href={FIXED_IP_BASE}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center text-sm underline"
          >
            Open Gateway <ExternalLink className="w-4 h-4 ml-1" />
          </a>

          <div className="ml-auto text-xs text-muted-foreground">
            {ipMode === "mjpeg" ? `Trying stream: ${ipTryIndex + 1}/${MJPEG_CANDIDATES.length}` : "Gateway mode"}
          </div>
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
            <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
          ) : ipMode === "mjpeg" ? (
            <img
              src={ipSrcWithBuster}
              className="w-full h-full object-cover"
              onLoad={handleIpLoad}
              onError={handleMjpegError}
              alt="IP Camera Stream"
            />
          ) : (
            <iframe
              ref={iframeRef}
              src={ipSrcWithBuster}
              title="IP Camera Gateway"
              onLoad={handleIpLoad}
              // iframe onError is unreliable, but keep it
              onError={handleIframeError}
              className="w-full h-full border-0"
            />
          )}

          <canvas ref={canvasRef} className="hidden" />

          {/* Loading overlay */}
          {((cameraSource === "webcam" && !hasCamera) || (cameraSource === "ip" && !ipConnected)) && !error && (
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
