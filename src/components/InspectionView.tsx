import { useState, useEffect, useCallback } from "react";
import CameraView from "./CameraView";
import AnalysisStatus from "./AnalysisStatus";

type InspectionStatus = "capturing" | "captured" | "analysing" | "complete";

const InspectionView = () => {
  const [status, setStatus] = useState<InspectionStatus>("capturing");
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);

  const handleImageCapture = useCallback((imageData: string) => {
    setCapturedImage(imageData);
    setStatus("captured");
  }, []);

  useEffect(() => {
    // Auto-capture after 2 seconds
    const captureTimer = setTimeout(() => {
      setIsCapturing(true);
    }, 2000);

    return () => clearTimeout(captureTimer);
  }, []);

  useEffect(() => {
    if (status === "captured") {
      // Start analysing after capture
      const analyseTimer = setTimeout(() => {
        setStatus("analysing");
      }, 1000);

      return () => clearTimeout(analyseTimer);
    }
  }, [status]);

  useEffect(() => {
    if (status === "analysing") {
      // Complete analysis after 3 seconds
      const completeTimer = setTimeout(() => {
        setStatus("complete");
      }, 3000);

      return () => clearTimeout(completeTimer);
    }
  }, [status]);

  return (
    <div className="flex flex-col md:flex-row gap-6 animate-fade-in">
      <div className="flex-1">
        {capturedImage ? (
          <img 
            src={capturedImage} 
            alt="Captured inspection" 
            className="w-full aspect-video object-cover rounded-lg border border-border"
          />
        ) : (
          <CameraView 
            onImageCapture={handleImageCapture}
            isCapturing={isCapturing}
          />
        )}
      </div>
      <div className="w-full md:w-64">
        <AnalysisStatus status={status} capturedImage={capturedImage} />
      </div>
    </div>
  );
};

export default InspectionView;
