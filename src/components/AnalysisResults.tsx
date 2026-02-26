import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Loader2, AlertTriangle, CheckCircle2, Package, ClipboardList } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

export interface ToolResult {
  name: string;
  count: number;
  status: string;
}

export interface AnalysisReport {
  overall: string;
  tools: ToolResult[];
}

interface AnalysisResultsProps {
  report: AnalysisReport | null;
  isAnalyzing: boolean;
  error: string | null;
  layer: "layer1" | "layer2";
}

const isDefective = (status: string) =>
  status.toLowerCase().includes("defective") && !status.toLowerCase().includes("non");

const AnalysisResults = ({ report, isAnalyzing, error, layer }: AnalysisResultsProps) => {
  const layerLabel = layer === "layer1" ? "Top Layer" : "2nd Layer";

  if (isAnalyzing) {
    return (
      <Card className="p-4 bg-primary/5 border-primary/20">
        <div className="flex items-center gap-3">
          <Loader2 className="w-5 h-5 text-primary animate-spin shrink-0" />
          <div>
            <p className="font-medium text-sm text-foreground">Analyzing {layerLabel}…</p>
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

  if (!report || !report.tools || report.tools.length === 0) return null;

  const defectiveCount = report.tools.filter(t => isDefective(t.status)).length;
  const overallOk = report.overall?.toLowerCase().includes("all present");

  return (
    <Card className="p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-4 h-4 text-primary" />
          <p className="font-semibold text-sm text-foreground">{layerLabel} Report</p>
        </div>
        <Badge variant={defectiveCount > 0 ? "destructive" : "secondary"} className="text-xs">
          {defectiveCount > 0 ? `${defectiveCount} defective` : "All OK"}
        </Badge>
      </div>

      {/* Overall status */}
      <div className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium ${
        overallOk
          ? "bg-green-500/10 text-green-700 dark:text-green-400"
          : "bg-destructive/10 text-destructive"
      }`}>
        {overallOk ? (
          <CheckCircle2 className="w-4 h-4 shrink-0" />
        ) : (
          <AlertTriangle className="w-4 h-4 shrink-0" />
        )}
        {report.overall}
      </div>

      {/* Tools table */}
      <div className="rounded-md border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead className="text-xs font-semibold h-8">Tool</TableHead>
              <TableHead className="text-xs font-semibold h-8 text-center w-12">Qty</TableHead>
              <TableHead className="text-xs font-semibold h-8 text-right">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.tools.map((tool, i) => {
              const defective = isDefective(tool.status);
              return (
                <TableRow key={i} className={defective ? "bg-destructive/5" : ""}>
                  <TableCell className="py-2 text-sm">
                    <div className="flex items-center gap-2">
                      <Package className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                      <span className="text-foreground">{tool.name}</span>
                    </div>
                  </TableCell>
                  <TableCell className="py-2 text-sm text-center text-muted-foreground">
                    {tool.count}
                  </TableCell>
                  <TableCell className="py-2 text-sm text-right">
                    {defective ? (
                      <span className="inline-flex items-center gap-1 text-destructive font-medium">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Defective
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400 font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        OK
                      </span>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
};

export default AnalysisResults;
