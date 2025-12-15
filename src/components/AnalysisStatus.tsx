import { Loader2 } from "lucide-react";

interface AnalysisStatusProps {
  status: "capturing" | "captured" | "analysing" | "complete";
  capturedImage?: string | null;
}

const AnalysisStatus = ({ status, capturedImage }: AnalysisStatusProps) => {
  return (
    <div className="flex flex-col items-center justify-center p-6 bg-card rounded-lg border border-border min-h-[200px]">
      {status === "capturing" && (
        <div className="text-center animate-fade-in">
          <p className="text-xl font-medium text-foreground">Capturing</p>
          <p className="text-xl font-medium text-foreground">Image</p>
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
