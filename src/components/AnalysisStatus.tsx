import { Loader2, Video, Save } from "lucide-react";

interface AnalysisStatusProps {
  status: "live" | "captured" | "saving" | "complete";
  capturedImage?: string | null;
}

const AnalysisStatus = ({ status, capturedImage }: AnalysisStatusProps) => {
  return (
    <div className="flex flex-col items-center justify-center p-6 bg-card rounded-lg border border-border flex-1 min-h-[160px]">
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
      
      {status === "saving" && (
        <div className="text-center animate-fade-in">
          <Save className="w-8 h-8 text-primary mx-auto mb-2" />
          <p className="text-xl font-medium text-foreground mb-4">Saving Case</p>
          <Loader2 className="w-8 h-8 animate-spin text-foreground mx-auto" />
          <p className="text-sm text-muted-foreground mt-2">Uploading images...</p>
        </div>
      )}
      
      {status === "complete" && (
        <div className="text-center animate-fade-in">
          <p className="text-xl font-medium text-accent">Case Saved!</p>
        </div>
      )}
    </div>
  );
};

export default AnalysisStatus;
