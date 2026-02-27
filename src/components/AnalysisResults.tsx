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
import { AspectRatio } from "./ui/aspect-ratio";
import ToolReviewDialog from "./ToolReviewDialog";
import { useState } from "react";

export interface ToolResult {
  name: string;
  count: number;
  status: string;
  image?: string;
  status_override?: {
    original_status: string;
    new_status: string;
    primary_user: { id: string; name: string };
    second_user: { id: string; name: string };
    overridden_at: string;
  };
}

export interface AnalysisReport {
  overall: string;
  tools: ToolResult[];
  annotated_image?: string;
}

interface AnalysisResultsProps {
  report: AnalysisReport | null;
  isAnalyzing: boolean;
  error: string | null;
  layer: "layer1" | "layer2";
  caseId?: string | null;
  userId?: string;
  userName?: string;
  onReportUpdated?: (layer: "layer1" | "layer2", updatedReport: AnalysisReport) => void;
}

const isDefective = (status: string) =>
  status.toLowerCase().includes("defective") && !status.toLowerCase().includes("non");

const AnalysisResults = ({
  report,
  isAnalyzing,
  error,
  layer,
  caseId,
  userId,
  userName,
  onReportUpdated,
}: AnalysisResultsProps) => {
  const layerLabel = layer === "layer1" ? "Top Layer" : "2nd Layer";
  const [selectedTool, setSelectedTool] = useState<ToolResult | null>(null);

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

  const handleStatusUpdated = (toolName: string, newStatus: string, secondUserId: string, secondUserName: string) => {
    if (!report || !onReportUpdated) return;

    const updatedTools = report.tools.map(t => {
      if (t.name.toLowerCase() === toolName.toLowerCase()) {
        return {
          ...t,
          status: newStatus,
          status_override: {
            original_status: t.status,
            new_status: newStatus,
            primary_user: { id: userId || "", name: userName || "" },
            second_user: { id: secondUserId, name: secondUserName },
            overridden_at: new Date().toISOString(),
          },
        };
      }
      return t;
    });

    const hasDefective = updatedTools.some(t => isDefective(t.status));
    const updatedReport: AnalysisReport = {
      ...report,
      tools: updatedTools,
      overall: hasDefective
        ? "Issue detected – some tools are defective"
        : "All present and non-defective",
    };

    onReportUpdated(layer, updatedReport);
  };

  return (
    <>
      <Card className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-primary" />
            <p className="font-semibold text-sm text-foreground">{layerLabel} Report</p>
          </div>
          <Badge variant={defectiveCount > 0 ? "destructive" : "secondary"} className="text-xs">
            {defectiveCount > 0 ? `${defectiveCount} defective` : "All OK"}
          </Badge>
        </div>

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

        {report.annotated_image && (
          <div className="rounded-md border border-border overflow-hidden">
            <AspectRatio ratio={16 / 9}>
              <img
                src={report.annotated_image}
                alt={`${layerLabel} annotated`}
                className="w-full h-full object-cover"
              />
            </AspectRatio>
          </div>
        )}

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
                        {tool.status_override && (
                          <Badge variant="outline" className="text-[10px] px-1 py-0">
                            Overridden
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="py-2 text-sm text-center text-muted-foreground">
                      {tool.count}
                    </TableCell>
                    <TableCell className="py-2 text-sm text-right">
                      <button
                        onClick={() => setSelectedTool(tool)}
                        className={`inline-flex items-center gap-1 font-medium underline-offset-2 hover:underline cursor-pointer transition-colors ${
                          defective
                            ? "text-destructive hover:text-destructive/80"
                            : "text-green-600 dark:text-green-400 hover:text-green-500"
                        }`}
                      >
                        {defective ? (
                          <>
                            <AlertTriangle className="w-3.5 h-3.5" />
                            Defective
                          </>
                        ) : (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            OK
                          </>
                        )}
                      </button>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </Card>

      <ToolReviewDialog
        tool={selectedTool}
        open={!!selectedTool}
        onOpenChange={(open) => !open && setSelectedTool(null)}
        caseId={caseId || null}
        layer={layer}
        primaryUserId={userId || ""}
        primaryUserName={userName || ""}
        onStatusUpdated={handleStatusUpdated}
      />
    </>
  );
};

export default AnalysisResults;
