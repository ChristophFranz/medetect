import { useState, useEffect } from "react";
import { Download, Loader2, AlertTriangle, CheckCircle2, Package } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { supabase } from "@/integrations/supabase/client";
import ToolReviewDialog from "./ToolReviewDialog";

interface ToolResult {
  name: string;
  count: number;
  status: string;
  image?: string;
  image_path?: string;
  status_override?: {
    original_status: string;
    new_status: string;
    primary_user: { id: string; name: string };
    second_user: { id: string; name: string };
    overridden_at: string;
  };
}

interface LayerReport {
  overall: string;
  tools: ToolResult[];
  annotated_image?: string;
  annotated_image_path?: string;
}

const getStorageUrl = (path: string | undefined | null, bucket: string = 'case-images'): string | null => {
  if (!path) return null;
  const { data } = supabase.storage.from(bucket).getPublicUrl(path);
  return data.publicUrl;
};

interface CaseDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentUserId: string;
  currentUserName: string;
  caseData: {
    id: string;
    case_number: number;
    patient_name: string;
    user_name: string;
    folder_path: string;
    layer1_image_path: string | null;
    layer2_image_path: string | null;
    layer1_report?: any;
    layer2_report?: any;
    created_at: string;
  } | null;
  onCaseUpdated?: () => void;
}

const isDefective = (status: string) =>
  status.toLowerCase().includes("defective") && !status.toLowerCase().includes("non");

const isMissing = (tool: ToolResult) =>
  tool.count === 0 || tool.status.toLowerCase().includes("missing");

interface LayerReportViewProps {
  report: LayerReport | null;
  label: string;
  layer: "layer1" | "layer2";
  caseId: string;
  currentUserId: string;
  currentUserName: string;
  onStatusUpdated: () => void;
}

const LayerReportView = ({ report, label, layer, caseId, currentUserId, currentUserName, onStatusUpdated }: LayerReportViewProps) => {
  const [selectedTool, setSelectedTool] = useState<ToolResult | null>(null);
  const [reviewOpen, setReviewOpen] = useState(false);

  if (!report || !report.tools || report.tools.length === 0) {
    return (
      <div className="border border-border rounded-md p-3 text-center text-xs text-muted-foreground bg-muted/20">
        No report available for {label}
      </div>
    );
  }

  const defectiveCount = report.tools.filter(t => isDefective(t.status) || isMissing(t)).length;
  const overallOk = report.overall?.toLowerCase().includes("all present") && !report.tools.some(t => isMissing(t));

  const handleToolClick = (tool: ToolResult) => {
    setSelectedTool(tool);
    setReviewOpen(true);
  };

  const handleStatusUpdated = (_toolName: string, _newStatus: string, _secondUserId: string, _secondUserName: string) => {
    onStatusUpdated();
  };

  return (
    <div className="space-y-2">
      {/* Overall status */}
      <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium ${
        overallOk
          ? "bg-green-500/10 text-green-700 dark:text-green-400"
          : "bg-destructive/10 text-destructive"
      }`}>
        {overallOk ? <CheckCircle2 className="w-3.5 h-3.5 shrink-0" /> : <AlertTriangle className="w-3.5 h-3.5 shrink-0" />}
        {report.overall}
        <Badge variant={defectiveCount > 0 ? "destructive" : "secondary"} className="ml-auto text-[10px]">
          {defectiveCount > 0 ? `${defectiveCount} issue(s)` : "All OK"}
        </Badge>
      </div>

      {/* Tools table */}
      <div className="rounded-md border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead className="text-[11px] font-semibold h-7">Tool</TableHead>
              <TableHead className="text-[11px] font-semibold h-7 text-center w-10">Qty</TableHead>
              <TableHead className="text-[11px] font-semibold h-7 text-right">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {report.tools.map((tool, i) => {
              const defective = isDefective(tool.status);
              const missing = isMissing(tool);
              return (
                <TableRow
                  key={i}
                  className={`cursor-pointer transition-colors ${defective || missing ? "bg-destructive/5 hover:bg-destructive/10" : "hover:bg-muted/50"}`}
                  onClick={() => handleToolClick(tool)}
                >
                  <TableCell className="py-1.5 text-xs">
                    <div className="flex items-center gap-2">
                      {(tool.image || tool.image_path) ? (
                        <img src={tool.image || getStorageUrl(tool.image_path) || ''} alt={tool.name} className="w-8 h-8 rounded border border-border object-cover shrink-0" />
                      ) : (
                        <Package className="w-3 h-3 text-muted-foreground shrink-0" />
                      )}
                      <span>{tool.name}</span>
                      {tool.status_override && (
                        <Badge variant="outline" className="text-[9px] px-1 py-0">Overridden</Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="py-1.5 text-xs text-center text-muted-foreground">{tool.count}</TableCell>
                  <TableCell className="py-1.5 text-xs text-right">
                    <span className={`inline-flex items-center gap-1 font-medium ${
                      defective || missing ? "text-destructive" : "text-green-600 dark:text-green-400"
                    }`}>
                      {missing ? (
                        <><AlertTriangle className="w-3 h-3" /> Missing</>
                      ) : defective ? (
                        <><AlertTriangle className="w-3 h-3" /> Defective</>
                      ) : (
                        <><CheckCircle2 className="w-3 h-3" /> OK</>
                      )}
                    </span>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      <ToolReviewDialog
        tool={selectedTool}
        open={reviewOpen}
        onOpenChange={setReviewOpen}
        caseId={caseId}
        layer={layer}
        primaryUserId={currentUserId}
        primaryUserName={currentUserName}
        onStatusUpdated={handleStatusUpdated}
      />
    </div>
  );
};

const CaseDetailDialog = ({ open, onOpenChange, caseData, currentUserId, currentUserName, onCaseUpdated }: CaseDetailDialogProps) => {
  const [layer1Url, setLayer1Url] = useState<string | null>(null);
  const [layer2Url, setLayer2Url] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [liveReports, setLiveReports] = useState<{ layer1: LayerReport | null; layer2: LayerReport | null }>({ layer1: null, layer2: null });

  useEffect(() => {
    if (open && caseData) {
      loadImages();
      setLiveReports({
        layer1: caseData.layer1_report as LayerReport | null,
        layer2: caseData.layer2_report as LayerReport | null,
      });
    }
  }, [open, caseData]);

  const loadImages = async () => {
    if (!caseData) return;
    setLoading(true);
    try {
      if (caseData.layer1_image_path) {
        const { data } = supabase.storage.from('case-images').getPublicUrl(caseData.layer1_image_path);
        setLayer1Url(data.publicUrl);
      }
      if (caseData.layer2_image_path) {
        const { data } = supabase.storage.from('case-images').getPublicUrl(caseData.layer2_image_path);
        setLayer2Url(data.publicUrl);
      }
    } catch (error) {
      console.error('Error loading images:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadImage = async (imagePath: string | null, filename: string) => {
    if (!imagePath) return;
    try {
      const { data } = supabase.storage.from('case-images').getPublicUrl(imagePath);
      const response = await fetch(data.publicUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading image:', error);
    }
  };

  const refreshReports = async () => {
    if (!caseData) return;
    try {
      const { data } = await supabase.functions.invoke('get-inspection-cases', {
        body: { search_query: '', filter_type: null, filter_value: null }
      });
      const updated = data?.cases?.find((c: any) => c.id === caseData.id);
      if (updated) {
        setLiveReports({
          layer1: updated.layer1_report as LayerReport | null,
          layer2: updated.layer2_report as LayerReport | null,
        });
      }
      onCaseUpdated?.();
    } catch (err) {
      console.error('Error refreshing reports:', err);
    }
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-GB', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  if (!caseData) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Case {caseData.case_number} - {caseData.patient_name}</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Case Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Patient:</span>
              <span className="ml-2 font-medium">{caseData.patient_name}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Inspector:</span>
              <span className="ml-2 font-medium">{caseData.user_name}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Date/Time:</span>
              <span className="ml-2 font-medium">{formatDateTime(caseData.created_at)}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Case ID:</span>
              <span className="ml-2 font-medium">#{caseData.case_number}</span>
            </div>
          </div>

          <p className="text-xs text-muted-foreground italic">Click on any tool row to review or change its status.</p>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="space-y-8">
              {/* Layer 1 */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Layer 1 - Pre-Operation</h4>
                  {caseData.layer1_image_path && (
                    <Button variant="ghost" size="sm" onClick={() => handleDownloadImage(caseData.layer1_image_path, `case-${caseData.case_number}-layer1.jpg`)}>
                      <Download className="w-4 h-4 mr-1" /> Download
                    </Button>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Raw Image</p>
                    {layer1Url ? (
                      <div className="border border-border rounded-lg overflow-hidden bg-muted/20">
                        <img src={layer1Url} alt="Layer 1 Raw" className="w-full h-auto object-contain max-h-64" />
                      </div>
                    ) : (
                      <div className="border border-border rounded-lg p-8 text-center text-muted-foreground bg-muted/20 text-xs">No image</div>
                    )}
                  </div>
                  <div className="space-y-1">
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Annotated Analysis</p>
                    {liveReports.layer1?.annotated_image ? (
                      <div className="border border-border rounded-lg overflow-hidden bg-muted/20">
                        <img src={liveReports.layer1.annotated_image} alt="Layer 1 Annotated" className="w-full h-auto object-contain max-h-64" />
                      </div>
                    ) : (
                      <div className="border border-border rounded-lg p-8 text-center text-muted-foreground bg-muted/20 text-xs">No annotated image</div>
                    )}
                  </div>
                </div>
                <LayerReportView
                  report={liveReports.layer1}
                  label="Layer 1"
                  layer="layer1"
                  caseId={caseData.id}
                  currentUserId={currentUserId}
                  currentUserName={currentUserName}
                  onStatusUpdated={refreshReports}
                />
              </div>

              {/* Layer 2 */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Layer 2 - Post-Operation</h4>
                  {caseData.layer2_image_path && (
                    <Button variant="ghost" size="sm" onClick={() => handleDownloadImage(caseData.layer2_image_path, `case-${caseData.case_number}-layer2.jpg`)}>
                      <Download className="w-4 h-4 mr-1" /> Download
                    </Button>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Raw Image</p>
                    {layer2Url ? (
                      <div className="border border-border rounded-lg overflow-hidden bg-muted/20">
                        <img src={layer2Url} alt="Layer 2 Raw" className="w-full h-auto object-contain max-h-64" />
                      </div>
                    ) : (
                      <div className="border border-border rounded-lg p-8 text-center text-muted-foreground bg-muted/20 text-xs">No image</div>
                    )}
                  </div>
                  <div className="space-y-1">
                    <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Annotated Analysis</p>
                    {liveReports.layer2?.annotated_image ? (
                      <div className="border border-border rounded-lg overflow-hidden bg-muted/20">
                        <img src={liveReports.layer2.annotated_image} alt="Layer 2 Annotated" className="w-full h-auto object-contain max-h-64" />
                      </div>
                    ) : (
                      <div className="border border-border rounded-lg p-8 text-center text-muted-foreground bg-muted/20 text-xs">No annotated image</div>
                    )}
                  </div>
                </div>
                <LayerReportView
                  report={liveReports.layer2}
                  label="Layer 2"
                  layer="layer2"
                  caseId={caseData.id}
                  currentUserId={currentUserId}
                  currentUserName={currentUserName}
                  onStatusUpdated={refreshReports}
                />
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CaseDetailDialog;
