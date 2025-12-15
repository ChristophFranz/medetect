import { useState, useCallback } from "react";
import CameraView from "./CameraView";
import AnalysisStatus from "./AnalysisStatus";
import { Button } from "./ui/button";
import { Camera, Layers, CheckCircle2, RotateCcw, X } from "lucide-react";
import { Card } from "./ui/card";

type CaptureStep = "layer1" | "layer2" | "analysing" | "complete";

const InspectionView = () => {
  const [captureStep, setCaptureStep] = useState<CaptureStep>("layer1");
  const [layer1Image, setLayer1Image] = useState<string | null>(null);
  const [layer2Image, setLayer2Image] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isCameraReady, setIsCameraReady] = useState(false);

  const handleCameraReady = useCallback((ready: boolean) => {
    setIsCameraReady(ready);
  }, []);

  const [recaptureMode, setRecaptureMode] = useState<"layer1" | "layer2" | null>(null);

  const handleImageCapture = (imageData: string) => {
    setIsCapturing(false);
    
    if (recaptureMode === "layer1") {
      setLayer1Image(imageData);
      setRecaptureMode(null);
      return;
    }
    
    if (recaptureMode === "layer2") {
      setLayer2Image(imageData);
      setRecaptureMode(null);
      return;
    }
    
    if (captureStep === "layer1") {
      setLayer1Image(imageData);
      setCaptureStep("layer2");
    } else if (captureStep === "layer2") {
      setLayer2Image(imageData);
      setCaptureStep("analysing");
      
      // Start analysis after both images captured
      setTimeout(() => {
        setCaptureStep("complete");
      }, 3000);
    }
  };

  const handleRecapture = (layer: "layer1" | "layer2") => {
    setRecaptureMode(layer);
  };

  const cancelRecapture = () => {
    setRecaptureMode(null);
  };

  const handleCapture = () => {
    setIsCapturing(true);
  };

  const handleReset = () => {
    setLayer1Image(null);
    setLayer2Image(null);
    setCaptureStep("layer1");
  };

  const getPromptMessage = () => {
    switch (captureStep) {
      case "layer1":
        return "Please capture the TOP LAYER of the surgical tool box";
      case "layer2":
        return "Please capture the 2ND LAYER of the surgical tool box";
      case "analysing":
        return "Analysing captured images...";
      case "complete":
        return "Analysis complete!";
    }
  };

  const getCurrentImage = () => {
    if (captureStep === "layer2" || captureStep === "analysing" || captureStep === "complete") {
      return layer2Image || layer1Image;
    }
    return null;
  };

  const showCamera = captureStep === "layer1" || captureStep === "layer2" || recaptureMode !== null;

  return (
    <div className="flex flex-col md:flex-row gap-6 animate-fade-in">
      <div className="flex-1 space-y-4">
        {/* Camera or captured image display */}
        {showCamera ? (
          <div className="relative">
            <CameraView 
              onImageCapture={handleImageCapture}
              isCapturing={isCapturing}
              onCameraReady={handleCameraReady}
            />
            {/* Layer 1 thumbnail overlay when capturing layer 2 (not when recapturing layer 1) */}
            {captureStep === "layer2" && layer1Image && recaptureMode !== "layer1" && (
              <div className="absolute top-3 left-3 w-24 h-18 rounded-md overflow-hidden border-2 border-primary shadow-lg">
                <img 
                  src={layer1Image} 
                  alt="Layer 1 captured" 
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs py-0.5 text-center">
                  Top Layer ✓
                </div>
                <button 
                  onClick={() => handleRecapture("layer1")}
                  className="absolute top-1 right-1 p-1 bg-black/60 rounded-full hover:bg-black/80 transition-colors"
                >
                  <RotateCcw className="w-3 h-3 text-white" />
                </button>
              </div>
            )}
            {/* Recapture mode indicator */}
            {recaptureMode && (
              <div className="absolute top-3 right-3 flex items-center gap-2">
                <div className="bg-orange-500/90 text-white px-3 py-1.5 rounded-md text-sm font-medium flex items-center gap-2">
                  <RotateCcw className="w-4 h-4" />
                  Recapturing {recaptureMode === "layer1" ? "Top Layer" : "2nd Layer"}
                </div>
                <button 
                  onClick={cancelRecapture}
                  className="p-1.5 bg-black/60 rounded-full hover:bg-black/80 transition-colors"
                >
                  <X className="w-4 h-4 text-white" />
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="relative w-full aspect-video bg-muted rounded-lg overflow-hidden border border-border">
            <div className="grid grid-cols-2 h-full">
              {layer1Image && (
                <div className="relative border-r border-border group">
                  <img 
                    src={layer1Image} 
                    alt="Layer 1 capture" 
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs py-1 text-center">
                    Top Layer
                  </div>
                  {captureStep !== "complete" && (
                    <button 
                      onClick={() => handleRecapture("layer1")}
                      className="absolute top-2 right-2 p-1.5 bg-black/60 rounded-full hover:bg-black/80 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <RotateCcw className="w-4 h-4 text-white" />
                    </button>
                  )}
                </div>
              )}
              {layer2Image && (
                <div className="relative group">
                  <img 
                    src={layer2Image} 
                    alt="Layer 2 capture" 
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs py-1 text-center">
                    2nd Layer
                  </div>
                  {captureStep !== "complete" && (
                    <button 
                      onClick={() => handleRecapture("layer2")}
                      className="absolute top-2 right-2 p-1.5 bg-black/60 rounded-full hover:bg-black/80 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <RotateCcw className="w-4 h-4 text-white" />
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Capture/Reset buttons */}
        <div className="flex gap-2">
          {showCamera && isCameraReady && (
            <Button onClick={handleCapture} className="flex-1" disabled={isCapturing}>
              <Camera className="w-4 h-4 mr-2" />
              {recaptureMode 
                ? `Recapture ${recaptureMode === "layer1" ? "Top Layer" : "2nd Layer"}`
                : captureStep === "layer1" 
                  ? "Capture Top Layer" 
                  : "Capture 2nd Layer"
              }
            </Button>
          )}
          {captureStep === "complete" && (
            <Button onClick={handleReset} variant="outline" className="flex-1">
              New Inspection
            </Button>
          )}
        </div>
      </div>
      
      {/* Right side - Analysis status, prompt box, and captured images */}
      <div className="w-full md:w-64 space-y-4">
        <AnalysisStatus 
          status={captureStep === "layer1" || captureStep === "layer2" ? "live" : captureStep} 
          capturedImage={layer2Image || layer1Image} 
        />

        {/* Prompt box - only shows when camera is ready */}
        {isCameraReady && showCamera && !recaptureMode && (
          <Card className="p-4 bg-primary/10 border-primary/30">
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-full bg-primary/20">
                  <Layers className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-foreground text-sm">{getPromptMessage()}</p>
                  <p className="text-xs text-muted-foreground">
                    {captureStep === "layer1" && "Position camera and capture"}
                    {captureStep === "layer2" && "Remove top layer and capture"}
                  </p>
                </div>
              </div>
              {captureStep === "layer2" && layer1Image && (
                <div className="flex items-center gap-2 pt-2 border-t border-primary/20">
                  <div className="relative w-12 h-12 rounded-md overflow-hidden border-2 border-primary/50">
                    <img 
                      src={layer1Image} 
                      alt="Layer 1 captured" 
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute bottom-0 right-0 bg-primary rounded-tl-md p-0.5">
                      <CheckCircle2 className="w-2.5 h-2.5 text-primary-foreground" />
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">Layer 1 captured</p>
                </div>
              )}
            </div>
          </Card>
        )}

        {/* Analysis status prompt */}
        {(captureStep === "analysing" || captureStep === "complete") && (
          <Card className={`p-4 ${captureStep === "complete" ? "bg-green-500/10 border-green-500/30" : "bg-primary/10 border-primary/30"}`}>
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-full ${captureStep === "complete" ? "bg-green-500/20" : "bg-primary/20"}`}>
                {captureStep === "complete" ? (
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                ) : (
                  <Layers className="w-5 h-5 text-primary animate-pulse" />
                )}
              </div>
              <p className="font-medium text-foreground text-sm">{getPromptMessage()}</p>
            </div>
          </Card>
        )}
        
      </div>
    </div>
  );
};

export default InspectionView;
