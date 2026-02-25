import { useEffect, useRef, useState } from "react";
import { Button } from "./ui/button";
import { ImagePlus, Globe, RefreshCw, ExternalLink } from "lucide-react";

type CameraSource = "upload" | "ip";

interface CameraViewProps {
  onImageCapture?: (imageData: string) => void;
  isCapturing?: boolean;
  onCameraReady?: (ready: boolean) => void;
}

const FIXED_IP_URL = "http://192.168.0.10/?page-id=0";

const CameraView = ({ onImageCapture, isCapturing = false, onCameraReady }: CameraViewProps) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [error, setError] = useState<string | null>(null);
  const [cameraSource, setCameraSource] = useState<CameraSource>("upload");
  const [ipConnected, setIpConnected] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [uploadedImage, setUploadedImage] = useState<string | null>(null);

  useEffect(() => {
    const isReady = cameraSource === "upload" ? !!uploadedImage : ipConnected;
    onCameraReady?.(isReady);
  }, [uploadedImage, ipConnected, cameraSource, onCameraReady]);

  // IP camera setup
  useEffect(() => {
    if (cameraSource !== "ip") return;
    setError(null);
    setIpConnected(false);
    setReloadKey((k) => k + 1);
  }, [cameraSource]);

  const handleIpReload = () => {
    setError(null);
    setIpConnected(false);
    setReloadKey((k) => k + 1);
  };

  const handleIframeLoad = () => {
    setIpConnected(true);
    setError(null);
  };

  const handleIframeError = () => {
    setIpConnected(false);
    setError("Could not load the camera gateway. Check that you are on the same network as 192.168.0.10.");
  };

  const switchSource = (source: CameraSource) => {
    setCameraSource(source);
    setError(null);
    setUploadedImage(null);
    setIpConnected(false);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      setUploadedImage(result);
      setError(null);
    };
    reader.onerror = () => {
      setError("Failed to read the selected image.");
    };
    reader.readAsDataURL(file);
    // Reset input so the same file can be re-selected
    e.target.value = "";
  };

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  // Capture handling
  useEffect(() => {
    if (!isCapturing) return;

    if (cameraSource === "upload" && uploadedImage) {
      onImageCapture?.(uploadedImage);
    } else if (cameraSource === "ip") {
      console.warn("IP camera capture not supported without a same-origin proxy/snapshot endpoint.");
    }
  }, [isCapturing, uploadedImage, cameraSource, onImageCapture]);

  const ipSrcWithBuster = `${FIXED_IP_URL}${FIXED_IP_URL.includes("?") ? "&" : "?"}t=${reloadKey}`;

  return (
    <div className="space-y-3 flex flex-col h-full">
      {/* Camera source toggle */}
      <div className="flex gap-2">
        <Button
          variant={cameraSource === "upload" ? "default" : "outline"}
          size="sm"
          onClick={() => switchSource("upload")}
          className="flex-1"
        >
          <ImagePlus className="w-4 h-4 mr-2" />
          Upload Image
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

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* IP controls */}
      {cameraSource === "ip" && (
        <div className="flex gap-2 items-center">
          <Button size="sm" variant="outline" onClick={handleIpReload}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Reload
          </Button>
          <a
            href={FIXED_IP_URL}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center text-sm underline"
          >
            Open Gateway <ExternalLink className="w-4 h-4 ml-1" />
          </a>
        </div>
      )}

      {/* Camera/Upload view */}
      {error ? (
        <div className="w-full flex-1 min-h-[200px] bg-muted rounded-lg flex items-center justify-center border border-border">
          <p className="text-muted-foreground text-sm text-center px-4">{error}</p>
        </div>
      ) : (
        <div className="relative w-full flex-1 min-h-[200px] bg-foreground/90 rounded-lg overflow-hidden border border-border">
          {cameraSource === "upload" ? (
            uploadedImage ? (
              <div className="relative w-full h-full">
                <img src={uploadedImage} alt="Uploaded" className="w-full h-full object-cover" />
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={openFilePicker}
                  className="absolute bottom-3 right-3 shadow-lg"
                >
                  <ImagePlus className="w-4 h-4 mr-2" />
                  Change
                </Button>
              </div>
            ) : (
              <div
                onClick={openFilePicker}
                className="w-full h-full flex flex-col items-center justify-center cursor-pointer hover:bg-muted/20 transition-colors"
              >
                <ImagePlus className="w-12 h-12 text-muted-foreground/60 mb-3" />
                <p className="text-muted-foreground text-sm font-medium">Click to choose an image</p>
                <p className="text-muted-foreground/60 text-xs mt-1">JPG, PNG, or other image formats</p>
              </div>
            )
          ) : (
            <iframe
              ref={iframeRef}
              key={reloadKey}
              src={ipSrcWithBuster}
              title="IP Camera Gateway"
              onLoad={handleIframeLoad}
              onError={handleIframeError}
              className="w-full h-full border-0"
              allow="autoplay"
            />
          )}

          {/* Loading overlay for IP */}
          {cameraSource === "ip" && !ipConnected && !error && (
            <div className="absolute inset-0 flex items-center justify-center bg-muted">
              <p className="text-muted-foreground">Connecting to IP camera...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CameraView;
