import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import CameraView from "./CameraView";
import AnalysisStatus from "./AnalysisStatus";
import { Button } from "./ui/button";
import { Camera, Layers, CheckCircle2, RotateCcw, X, Mic, MicOff, Loader2 } from "lucide-react";
import { Card } from "./ui/card";
import { useVoiceCommand } from "@/hooks/use-voice-command";
import { useAudioCues } from "@/hooks/use-audio-cues";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "@/hooks/use-toast";

type CaptureStep = "layer1" | "layer2" | "saving" | "complete";

interface SavedCase {
  case_number: number;
  patient_name: string;
  folder_path: string;
}

const InspectionView = () => {
  const [searchParams] = useSearchParams();
  const userId = searchParams.get("user") || "";
  const userName = decodeURIComponent(searchParams.get("name") || "");
  
  const [captureStep, setCaptureStep] = useState<CaptureStep>("layer1");
  const [layer1Image, setLayer1Image] = useState<string | null>(null);
  const [layer2Image, setLayer2Image] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [savedCase, setSavedCase] = useState<SavedCase | null>(null);
  const { signalPosition, signalCaptured, signalInspectionComplete, cancelPending } = useAudioCues();
  const hasPlayedReadyRef = useRef(false);

  const handleCameraReady = useCallback((ready: boolean) => {
    setIsCameraReady(ready);
  }, []);

  const [recaptureMode, setRecaptureMode] = useState<"layer1" | "layer2" | null>(null);

  // Play "ready" sound when camera becomes active and ready
  const showCamera = captureStep === "layer1" || captureStep === "layer2" || recaptureMode !== null;

  useEffect(() => {
    if (isCameraReady && showCamera) {
      if (!hasPlayedReadyRef.current) {
        const context = recaptureMode ? "recapture" : captureStep === "layer2" ? "layer2" : "layer1";
        signalPosition(context);
        hasPlayedReadyRef.current = true;
      }
    } else {
      hasPlayedReadyRef.current = false;
    }
  }, [isCameraReady, showCamera, signalPosition, captureStep, recaptureMode]);

  // Cleanup pending timers on unmount
  useEffect(() => cancelPending, [cancelPending]);

  const handleImageCapture = (imageData: string) => {
    setIsCapturing(false);
    
    if (recaptureMode === "layer1") {
      setLayer1Image(imageData);
      setRecaptureMode(null);
      signalCaptured();
      // After recapturing layer1, move to layer2 audio
      hasPlayedReadyRef.current = false;
      setTimeout(() => signalPosition("layer2"), 1500);
      hasPlayedReadyRef.current = true;
      return;
    }
    
    if (recaptureMode === "layer2") {
      setLayer2Image(imageData);
      setRecaptureMode(null);
      signalInspectionComplete();
      saveCase(layer1Image!, imageData);
      return;
    }
    
    if (captureStep === "layer1") {
      setLayer1Image(imageData);
      setCaptureStep("layer2");
      signalCaptured();
      // Move to layer2 audio after a short pause
      hasPlayedReadyRef.current = true;
      setTimeout(() => signalPosition("layer2"), 1500);
    } else if (captureStep === "layer2") {
      setLayer2Image(imageData);
      signalInspectionComplete();
      saveCase(layer1Image!, imageData);
    }
  };

  const saveCase = async (layer1: string, layer2: string) => {
    setCaptureStep("saving");
    
    try {
      const { data, error } = await supabase.functions.invoke('save-inspection-case', {
        body: {
          user_id: userId,
          user_name: userName,
          layer1_image: layer1,
          layer2_image: layer2,
        }
      });

      if (error || !data?.success) {
        throw new Error(error?.message || data?.error || "Failed to save case");
      }

      setSavedCase(data.case);
      setCaptureStep("complete");
      
      toast({
        title: `Case ${String(data.case.case_number).padStart(2, "0")} saved`,
        description: `Patient: ${data.case.patient_name}`,
      });
    } catch (err) {
      console.error("Save case error:", err);
      toast({
        title: "Failed to save case",
        description: err instanceof Error ? err.message : "Please try again",
        variant: "destructive",
      });
      // Reset to layer2 so user can try again
      setCaptureStep("layer2");
    }
  };

  const handleRecapture = useCallback((layer: "layer1" | "layer2") => {
    setRecaptureMode(layer);
  }, []);

  const cancelRecapture = useCallback(() => {
    setRecaptureMode(null);
  }, []);

  const handleCapture = useCallback(() => {
    if (isCameraReady && showCamera) {
      setIsCapturing(true);
    }
  }, [isCameraReady, showCamera]);

  const handleReset = useCallback(() => {
    setLayer1Image(null);
    setLayer2Image(null);
    setCaptureStep("layer1");
  }, []);

  const handleRecaptureTop = useCallback(() => {
    if (layer1Image) handleRecapture("layer1");
  }, [layer1Image, handleRecapture]);

  const handleRecaptureSecond = useCallback(() => {
    if (layer2Image) handleRecapture("layer2");
  }, [layer2Image, handleRecapture]);

  // Memoize commands to prevent recreation on every render
  const voiceCommands = useMemo(() => ({
    "capture": handleCapture,
    "recapture top": handleRecaptureTop,
    "recapture second": handleRecaptureSecond,
    "new inspection": handleReset,
    "cancel": cancelRecapture,
  }), [handleCapture, handleRecaptureTop, handleRecaptureSecond, handleReset, cancelRecapture]);

  // Voice command support - enabled whenever camera is ready or in complete state
  const voiceEnabled = (isCameraReady && showCamera) || captureStep === "complete";
  
  const { isListening, isSupported, transcript, isCommandMatch } = useVoiceCommand({
    commands: voiceCommands,
    enabled: voiceEnabled,
  });


  const getPromptMessage = () => {
    switch (captureStep) {
      case "layer1":
        return "Please capture the TOP LAYER of the surgical tool box";
      case "layer2":
        return "Please capture the 2ND LAYER of the surgical tool box";
      case "saving":
        return "Saving case to database...";
      case "complete":
        return savedCase 
          ? `Case ${String(savedCase.case_number).padStart(2, "0")} saved!`
          : "Case saved!";
    }
  };

  const getCurrentImage = () => {
    if (captureStep === "layer2" || captureStep === "saving" || captureStep === "complete") {
      return layer2Image || layer1Image;
    }
    return null;
  };

  

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
            {/* Voice command indicator and transcript */}
            {isSupported && !recaptureMode && (
              <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between gap-2">
                {/* Transcript display */}
                {transcript && (
                  <div className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium animate-fade-in ${
                    isCommandMatch 
                      ? "bg-green-500/90 text-white" 
                      : "bg-black/70 text-white"
                  }`}>
                    <div className="flex items-center gap-2">
                      <span className="text-white/60 text-xs">Heard:</span>
                      <span className="capitalize">"{transcript}"</span>
                      {isCommandMatch && (
                        <CheckCircle2 className="w-4 h-4 ml-auto" />
                      )}
                    </div>
                  </div>
                )}
                
                {/* Voice status indicator */}
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium shrink-0 ${
                  isListening 
                    ? "bg-green-500/90 text-white" 
                    : "bg-black/60 text-white/70"
                }`}>
                  {isListening ? (
                    <>
                      <Mic className="w-3.5 h-3.5 animate-pulse" />
                      Voice active
                    </>
                  ) : (
                    <>
                      <MicOff className="w-3.5 h-3.5" />
                      Voice off
                    </>
                  )}
                </div>
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

        {/* Saving/Complete status prompt */}
        {(captureStep === "saving" || captureStep === "complete") && (
          <Card className={`p-4 ${captureStep === "complete" ? "bg-green-500/10 border-green-500/30" : "bg-primary/10 border-primary/30"}`}>
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-full ${captureStep === "complete" ? "bg-green-500/20" : "bg-primary/20"}`}>
                {captureStep === "complete" ? (
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                ) : (
                  <Loader2 className="w-5 h-5 text-primary animate-spin" />
                )}
              </div>
              <div className="flex-1">
                <p className="font-medium text-foreground text-sm">{getPromptMessage()}</p>
                {captureStep === "complete" && savedCase && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Patient: {savedCase.patient_name}
                  </p>
                )}
              </div>
            </div>
          </Card>
        )}
        
      </div>
    </div>
  );
};

export default InspectionView;
