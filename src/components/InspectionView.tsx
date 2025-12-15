import { useState } from "react";
import CameraView from "./CameraView";
import AnalysisStatus from "./AnalysisStatus";
import { Button } from "./ui/button";
import { Camera } from "lucide-react";

type InspectionStatus = "live" | "captured" | "analysing" | "complete";

const InspectionView = () => {
  const [status, setStatus] = useState<InspectionStatus>("live");
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);

  const handleImageCapture = (imageData: string) => {
    setCapturedImage(imageData);
    setStatus("captured");
    setIsCapturing(false);
    
    // Start analysis after capture
    setTimeout(() => {
      setStatus("analysing");
      setTimeout(() => {
        setStatus("complete");
      }, 3000);
    }, 1000);
  };

  const handleCapture = () => {
    setIsCapturing(true);
  };

  const handleReset = () => {
    setCapturedImage(null);
    setStatus("live");
  };

  return (
    <div className="flex flex-col md:flex-row gap-6 animate-fade-in">
      <div className="flex-1 space-y-4">
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
        <div className="flex gap-2">
          {status === "live" && (
            <Button onClick={handleCapture} className="flex-1">
              <Camera className="w-4 h-4 mr-2" />
              Capture Image
            </Button>
          )}
          {status === "complete" && (
            <Button onClick={handleReset} variant="outline" className="flex-1">
              New Inspection
            </Button>
          )}
        </div>
      </div>
      <div className="w-full md:w-64">
        <AnalysisStatus status={status} capturedImage={capturedImage} />
      </div>
    </div>
  );
};

export default InspectionView;
