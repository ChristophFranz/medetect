import { useState, useCallback } from "react";
import CameraView from "./CameraView";
import AnalysisStatus from "./AnalysisStatus";
import { Button } from "./ui/button";
import { Camera, Layers, CheckCircle2 } from "lucide-react";
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

  const handleImageCapture = (imageData: string) => {
    setIsCapturing(false);
    
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

  const showCamera = captureStep === "layer1" || captureStep === "layer2";

  return (
    <div className="flex flex-col md:flex-row gap-6 animate-fade-in">
      <div className="flex-1 space-y-4">
        {/* Camera or captured image display */}
        {showCamera ? (
          <CameraView 
            onImageCapture={handleImageCapture}
            isCapturing={isCapturing}
            onCameraReady={handleCameraReady}
          />
        ) : (
          <div className="relative w-full aspect-video bg-muted rounded-lg overflow-hidden border border-border flex items-center justify-center">
            {layer2Image && (
              <img 
                src={layer2Image} 
                alt="Layer 2 capture" 
                className="w-full h-full object-cover"
              />
            )}
          </div>
        )}

        {/* Prompt box - only shows when camera is ready */}
        {isCameraReady && showCamera && (
          <Card className="p-4 bg-primary/10 border-primary/30">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-primary/20">
                <Layers className="w-5 h-5 text-primary" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-foreground">{getPromptMessage()}</p>
                <p className="text-sm text-muted-foreground">
                  {captureStep === "layer1" && "Position the camera above the tool box and capture when ready"}
                  {captureStep === "layer2" && "Remove the top layer and capture the second layer"}
                </p>
              </div>
              {captureStep === "layer2" && layer1Image && (
                <div className="flex-shrink-0">
                  <div className="relative w-16 h-16 rounded-md overflow-hidden border-2 border-primary/50">
                    <img 
                      src={layer1Image} 
                      alt="Layer 1 captured" 
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute bottom-0 right-0 bg-primary rounded-tl-md p-0.5">
                      <CheckCircle2 className="w-3 h-3 text-primary-foreground" />
                    </div>
                  </div>
                  <p className="text-xs text-center text-muted-foreground mt-1">Layer 1</p>
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
              <p className="font-medium text-foreground">{getPromptMessage()}</p>
            </div>
          </Card>
        )}

        {/* Capture/Reset buttons */}
        <div className="flex gap-2">
          {showCamera && isCameraReady && (
            <Button onClick={handleCapture} className="flex-1" disabled={isCapturing}>
              <Camera className="w-4 h-4 mr-2" />
              {captureStep === "layer1" ? "Capture Top Layer" : "Capture 2nd Layer"}
            </Button>
          )}
          {captureStep === "complete" && (
            <Button onClick={handleReset} variant="outline" className="flex-1">
              New Inspection
            </Button>
          )}
        </div>
      </div>
      
      {/* Right side - Analysis status with captured images */}
      <div className="w-full md:w-64 space-y-4">
        <AnalysisStatus 
          status={captureStep === "layer1" || captureStep === "layer2" ? "live" : captureStep} 
          capturedImage={layer2Image || layer1Image} 
        />
        
        {/* Captured layers preview */}
        {(layer1Image || layer2Image) && (
          <Card className="p-3 space-y-2">
            <p className="text-sm font-medium text-muted-foreground">Captured Layers</p>
            <div className="grid grid-cols-2 gap-2">
              {layer1Image && (
                <div className="space-y-1">
                  <div className="aspect-square rounded-md overflow-hidden border border-border">
                    <img src={layer1Image} alt="Layer 1" className="w-full h-full object-cover" />
                  </div>
                  <p className="text-xs text-center text-muted-foreground">Top Layer</p>
                </div>
              )}
              {layer2Image && (
                <div className="space-y-1">
                  <div className="aspect-square rounded-md overflow-hidden border border-border">
                    <img src={layer2Image} alt="Layer 2" className="w-full h-full object-cover" />
                  </div>
                  <p className="text-xs text-center text-muted-foreground">2nd Layer</p>
                </div>
              )}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default InspectionView;
