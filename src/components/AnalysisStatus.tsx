import { Loader2, Video } from "lucide-react";

interface AnalysisStatusProps {
  status: "live" | "captured" | "analysing" | "complete";
  capturedImage?: string | null;
}

const AnalysisStatus = ({ status, capturedImage }: AnalysisStatusProps) => {
  return (
    <div className="flex flex-col items-center justify-center p-6 bg-card rounded-lg border border-border min-h-[200px]">
      {status === "live" && (
        <div className="text-center animate-fade-in">
          <Video className="w-8 h-8 text-primary mx-auto mb-2" />
          <p className="text-xl font-medium text-foreground">Live Feed</p>
          <p className="text-sm text-muted-foreground mt-2">Camera ready</p>
        </div>
      )}
      
      {status === "captured" && (
        <div className="text-center animate-fade-in">
          <p className="text-xl font-medium text-foreground">Image Captured</p>
        </div>
      )}
      
      {status === "analysing" && (
        <div className="text-center animate-fade-in">
          <p className="text-xl font-medium text-foreground mb-4">Analysing</p>
          <Loader2 className="w-8 h-8 animate-spin text-foreground mx-auto" />
          <p className="text-sm text-muted-foreground mt-2">~3 seconds</p>
        </div>
      )}
      
      {status === "complete" && (
        <div className="text-center animate-fade-in">
          <p className="text-xl font-medium text-accent">Analysis Complete</p>
        </div>
      )}
    </div>
  );
};

export default AnalysisStatus;
