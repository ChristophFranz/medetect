import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Loader2, AlertTriangle, CheckCircle2, Package } from "lucide-react";

export interface ToolResult {
  name: string;
  count: number;
  status: string;
}

interface AnalysisResultsProps {
  results: ToolResult[] | null;
  isAnalyzing: boolean;
  error: string | null;
  layer: "layer1" | "layer2";
}

const AnalysisResults = ({ results, isAnalyzing, error, layer }: AnalysisResultsProps) => {
  if (isAnalyzing) {
    return (
      <Card className="p-4 bg-primary/5 border-primary/20">
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-primary animate-spin shrink-0" />
          <div>
            <p className="font-medium text-sm text-foreground">Analyzing {layer === "layer1" ? "Top Layer" : "2nd Layer"}…</p>
            <p className="text-xs text-muted-foreground mt-0.5">Sending to detection model</p>
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-4 bg-destructive/5 border-destructive/20">
        <div className="flex items-center gap-2 mb-1">
          <AlertTriangle className="w-4 h-4 text-destructive shrink-0" />
          <p className="font-medium text-sm text-destructive">Analysis Failed</p>
        </div>
        <p className="text-xs text-muted-foreground">{error}</p>
      </Card>
    );
  }

  if (!results || results.length === 0) return null;

  const defectiveCount = results.filter(t => t.classification === "defective").length;

  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="font-semibold text-sm text-foreground">
          {layer === "layer1" ? "Top Layer" : "2nd Layer"} Results
        </p>
        <Badge variant={defectiveCount > 0 ? "destructive" : "secondary"} className="text-xs">
          {defectiveCount > 0 ? `${defectiveCount} defective` : "All OK"}
        </Badge>
      </div>
      <div className="space-y-2">
        {results.map((tool, i) => (
          <div key={i} className="flex items-center justify-between gap-2 text-sm py-1.5 px-2 rounded-md bg-muted/50">
            <div className="flex items-center gap-2 min-w-0">
              <Package className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
              <span className="text-foreground truncate">{tool.name}</span>
              <span className="text-muted-foreground text-xs">×{tool.count}</span>
            </div>
            {tool.classification === "defective" ? (
              <div className="flex items-center gap-1 text-destructive shrink-0">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span className="text-xs font-medium">Defective</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-green-600 dark:text-green-400 shrink-0">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span className="text-xs font-medium">OK</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};

export default AnalysisResults;
