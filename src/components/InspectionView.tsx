import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import CameraView from "./CameraView";
import AnalysisStatus from "./AnalysisStatus";
import AnalysisResults, { AnalysisReport } from "./AnalysisResults";
import { Button } from "./ui/button";
import { ImagePlus, Layers, CheckCircle2, RotateCcw, X, Mic, MicOff, Loader2 } from "lucide-react";
import { Card } from "./ui/card";
import { useVoiceCommand } from "@/hooks/use-voice-command";
import { useAudioCues } from "@/hooks/use-audio-cues";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "@/hooks/use-toast";

const PYTHON_API_URL = "http://localhost:5000/analyze";

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
  const [layer1Report, setLayer1Report] = useState<AnalysisReport | null>(null);
  const [layer2Report, setLayer2Report] = useState<AnalysisReport | null>(null);
  const [analyzingLayer, setAnalyzingLayer] = useState<"layer1" | "layer2" | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const startListeningRef = useRef<(() => void) | null>(null);
  const stopListeningRef = useRef<(() => void) | null>(null);
  const [micActive, setMicActive] = useState(false);
  const { signalPosition, signalCaptured, signalInspectionComplete, cancelPending } = useAudioCues({
    onReadyToCapture: () => {
      // Turn mic ON after "Ready to capture image" TTS finishes
      setMicActive(true);
      startListeningRef.current?.();
    },
    onCapturedDone: () => {
      // Turn mic OFF after "Image captured" TTS finishes
      setMicActive(false);
      stopListeningRef.current?.();
    },
  });
  const hasPlayedReadyRef = useRef(false);

  const handleCameraReady = useCallback((ready: boolean) => {
    setIsCameraReady(ready);
  }, []);

  const analyzeImage = async (imageData: string, layer: "layer1" | "layer2") => {
    setAnalyzingLayer(layer);
    setAnalysisError(null);
    try {
      const response = await fetch(PYTHON_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: imageData, layer }),
      });
      if (!response.ok) throw new Error(`Server returned ${response.status}`);
      const data = await response.json();
      const tools: ToolResult[] = data.tools || [];
      if (layer === "layer1") setLayer1Results(tools);
      else setLayer2Results(tools);
    } catch (err) {
      console.error("Analysis error:", err);
      const msg = err instanceof Error ? err.message : "Unknown error";
      setAnalysisError(msg);
      toast({
        title: "Analysis failed",
        description: `Could not reach Python API. ${msg}`,
        variant: "destructive",
      });
    } finally {
      setAnalyzingLayer(null);
    }
  };

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
      setLayer1Results(null);
      setRecaptureMode(null);
      signalCaptured();
      analyzeImage(imageData, "layer1");
      hasPlayedReadyRef.current = false;
      setTimeout(() => signalPosition("layer2"), 1500);
      hasPlayedReadyRef.current = true;
      return;
    }
    
    if (recaptureMode === "layer2") {
      setLayer2Image(imageData);
      setLayer2Results(null);
      setRecaptureMode(null);
      signalInspectionComplete();
      analyzeImage(imageData, "layer2");
      saveCase(layer1Image!, imageData);
      return;
    }
    
    if (captureStep === "layer1") {
      setLayer1Image(imageData);
      setLayer1Results(null);
      setCaptureStep("layer2");
      signalCaptured();
      analyzeImage(imageData, "layer1");
      hasPlayedReadyRef.current = true;
      setTimeout(() => signalPosition("layer2"), 1500);
    } else if (captureStep === "layer2") {
      setLayer2Image(imageData);
      setLayer2Results(null);
      signalInspectionComplete();
      analyzeImage(imageData, "layer2");
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
    setLayer1Results(null);
    setLayer2Results(null);
    setAnalysisError(null);
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
    "recap top": handleRecaptureTop,
    "recap second": handleRecaptureSecond,
    "new inspection": handleReset,
    "cancel": cancelRecapture,
  }), [handleCapture, handleRecaptureTop, handleRecaptureSecond, handleReset, cancelRecapture]);

  // Voice command support - controlled by audio cue lifecycle
  const voiceEnabled = micActive;
  
  const { isListening, isSupported, transcript, isCommandMatch, startListening, stopListening } = useVoiceCommand({
    commands: voiceCommands,
    enabled: voiceEnabled,
  });

  // Keep refs in sync so audio cues can control recognition
  useEffect(() => {
    startListeningRef.current = startListening;
    stopListeningRef.current = stopListening;
  }, [startListening, stopListening]);


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
    <div className="flex flex-col md:flex-row gap-6 animate-fade-in flex-1 min-h-0">
      <div className="flex-1 flex flex-col space-y-4 min-h-0">
        {/* Camera or captured image display */}
        {showCamera ? (
          <div className="relative flex-1 min-h-0">
            <CameraView 
              onImageCapture={handleImageCapture}
              isCapturing={isCapturing}
              onCameraReady={handleCameraReady}
            />
            {/* Layer 1 thumbnail overlay when capturing layer 2 (not when recapturing layer 1) */}
            {captureStep === "layer2" && layer1Image && recaptureMode !== "layer1" && (
              <div className="absolute top-3 left-3 w-20 h-14 rounded-md overflow-hidden border-2 border-primary shadow-lg z-10">
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
                <div className={`flex items-center gap-2.5 px-4 py-2.5 rounded-full text-sm font-semibold shrink-0 shadow-lg backdrop-blur-sm transition-colors ${
                  isListening 
                    ? "bg-green-500/90 text-white ring-2 ring-green-400/50" 
                    : "bg-black/70 text-white/70"
                }`}>
                  {isListening ? (
                    <>
                      <Mic className="w-5 h-5 animate-pulse" />
                      Mic Active
                    </>
                  ) : (
                    <>
                      <MicOff className="w-5 h-5" />
                      Mic Off
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="relative w-full flex-1 bg-muted rounded-lg overflow-hidden border border-border">
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
              <ImagePlus className="w-4 h-4 mr-2" />
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
      
      {/* Right side - Analysis status, results, and voice commands */}
      <div className="w-full md:w-64 shrink-0 space-y-3 flex flex-col overflow-y-auto">
        <AnalysisStatus 
          status={captureStep === "layer1" || captureStep === "layer2" ? "live" : captureStep} 
          capturedImage={layer2Image || layer1Image} 
        />

        {/* Analysis results */}
        <AnalysisResults
          results={layer1Results}
          isAnalyzing={analyzingLayer === "layer1"}
          error={analyzingLayer === "layer1" ? analysisError : null}
          layer="layer1"
        />
        <AnalysisResults
          results={layer2Results}
          isAnalyzing={analyzingLayer === "layer2"}
          error={analyzingLayer === "layer2" ? analysisError : null}
          layer="layer2"
        />
        {/* Voice command status - always visible */}
        <Card className={`p-4 transition-colors ${
          isListening 
            ? "bg-green-500/10 border-green-500/40 ring-1 ring-green-400/30" 
            : !isSupported
              ? "bg-destructive/5 border-destructive/30"
              : "bg-muted/50 border-border"
        }`}>
          <div className="flex items-center gap-3">
            <div className={`p-2.5 rounded-full ${
              isListening ? "bg-green-500/20" : !isSupported ? "bg-destructive/10" : "bg-muted"
            }`}>
              {isListening ? (
                <Mic className="w-6 h-6 text-green-500 animate-pulse" />
              ) : (
                <MicOff className="w-6 h-6 text-muted-foreground" />
              )}
            </div>
            <div className="flex-1">
              <p className={`font-semibold text-sm ${
                isListening ? "text-green-600 dark:text-green-400" : "text-muted-foreground"
              }`}>
                {isListening ? "🎙️ Microphone Active" : !isSupported ? "🎙️ Microphone Unavailable" : "🎙️ Microphone Inactive"}
              </p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {isListening 
                  ? "Listening for commands…" 
                  : !isSupported 
                    ? "Use Chrome for voice commands"
                    : voiceEnabled 
                      ? "Waiting for microphone…" 
                      : "Activate camera to enable voice"
                }
              </p>
            </div>
          </div>
          {isListening && (
            <div className="mt-3 pt-3 border-t border-border/50 space-y-1.5">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Say:</p>
              {["Capture", "Recap top", "Recap second", "New inspection"].map((cmd) => (
                <div key={cmd} className="flex items-center gap-2 text-sm text-foreground/80">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 shrink-0" />
                  <span>"{cmd}"</span>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Saving spinner */}
        {captureStep === "saving" && (
          <Card className="p-4 bg-primary/10 border-primary/30">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 text-primary animate-spin" />
              <p className="font-medium text-foreground text-sm">Saving case…</p>
            </div>
          </Card>
        )}
        
      </div>
    </div>
  );
};

export default InspectionView;
