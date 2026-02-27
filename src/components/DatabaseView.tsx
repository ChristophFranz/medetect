import { useState, useEffect, useCallback, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ChevronRight, ChevronLeft, Eye, Download, Mail, Loader2 } from "lucide-react";
import JSZip from "jszip";
import { Button } from "./ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";
import DatabaseFilters from "./DatabaseFilters";
import CaseDetailDialog from "./CaseDetailDialog";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from "./ui/pagination";
import { ScrollArea } from "./ui/scroll-area";

interface InspectionCase {
  id: string;
  case_number: number;
  patient_name: string;
  user_id: string;
  user_name: string;
  folder_path: string;
  layer1_image_path: string | null;
  layer2_image_path: string | null;
  layer1_report?: any;
  layer2_report?: any;
  confirmed_by_users?: string[] | null;
  created_at: string;
}

type UserTag = "medetect_team" | "nurses" | "administrator";

interface DatabaseViewProps {
  userTags: UserTag[];
}

const ITEMS_PER_PAGE = 10;

const DatabaseView = ({ userTags }: DatabaseViewProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [cases, setCases] = useState<InspectionCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);
  const [selectedCase, setSelectedCase] = useState<InspectionCase | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [downloadingCaseId, setDownloadingCaseId] = useState<string | null>(null);
  const [showModifiedOnly, setShowModifiedOnly] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const canAccessToolsClassification = userTags.includes("administrator") || userTags.includes("medetect_team");

  const filteredCases = useMemo(() => {
    if (!showModifiedOnly) return cases;
    return cases.filter(c => c.confirmed_by_users && c.confirmed_by_users.length > 0);
  }, [cases, showModifiedOnly]);

  const totalPages = Math.max(1, Math.ceil(filteredCases.length / ITEMS_PER_PAGE));
  const paginatedCases = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredCases.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredCases, currentPage]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedUserId, selectedDate, showModifiedOnly]);

  const fetchCases = useCallback(async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('get-inspection-cases', {
        body: { 
          filter_type: selectedUserId ? 'user' : selectedDate ? 'date' : null,
          filter_value: selectedUserId || (selectedDate ? selectedDate.toISOString() : null),
          search_query: searchQuery
        }
      });

      if (error) {
        console.error('Error fetching cases:', error);
        return;
      }

      if (data?.cases) {
        setCases(data.cases);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedUserId, selectedDate]);

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      fetchCases();
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [fetchCases]);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const handleToolsClassificationClick = () => {
    const user = searchParams.get("user");
    const name = searchParams.get("name");
    navigate(`/tools-classification?user=${user}&name=${name}`);
  };

  const handleViewCase = (caseItem: InspectionCase) => {
    setSelectedCase(caseItem);
    setDetailDialogOpen(true);
  };

  const handleDownloadCase = async (caseItem: InspectionCase) => {
    setDownloadingCaseId(caseItem.id);
    
    try {
      const zip = new JSZip();
      const caseFolder = zip.folder(`case-${String(caseItem.case_number).padStart(2, "0")}-${caseItem.patient_name}`)!;

      // Download images and add to zip
      const downloadAndAdd = async (imagePath: string | null, filename: string) => {
        if (!imagePath) return;
        const { data } = supabase.storage.from('case-images').getPublicUrl(imagePath);
        const response = await fetch(data.publicUrl);
        const blob = await response.blob();
        caseFolder.file(filename, blob);
      };

      await Promise.all([
        downloadAndAdd(caseItem.layer1_image_path, `layer1.jpg`),
        downloadAndAdd(caseItem.layer2_image_path, `layer2.jpg`),
      ]);

      // Fetch reports from database
      const { data: caseData } = await supabase.functions.invoke('get-inspection-cases', {
        body: { search_query: '', filter_type: null, filter_value: null }
      });
      const fullCase = caseData?.cases?.find((c: any) => c.id === caseItem.id);

      // Fetch full case with reports directly
      const { data: reportData } = await supabase
        .from('inspection_cases')
        .select('layer1_report, layer2_report')
        .eq('id', caseItem.id)
        .single();

      const addReport = (report: any, layerName: string) => {
        if (!report || !report.tools || report.tools.length === 0) return;
        const reportsFolder = caseFolder.folder(`${layerName}_report`)!;
        
        // Overall summary
        let summary = `${layerName.toUpperCase()} REPORT\n`;
        summary += `========================\n\n`;
        summary += `Overall: ${report.overall || 'N/A'}\n\n`;
        summary += `Tools detected: ${report.tools.length}\n\n`;
        
        report.tools.forEach((tool: any, i: number) => {
          summary += `--- Tool ${i + 1} ---\n`;
          summary += `Name: ${tool.name || 'Unknown'}\n`;
          summary += `Status: ${tool.status || 'N/A'}\n`;
          if (tool.confidence) summary += `Confidence: ${tool.confidence}\n`;
          if (tool.notes) summary += `Notes: ${tool.notes}\n`;
          summary += `\n`;
        });

        reportsFolder.file(`report.txt`, summary);
      };

      if (reportData) {
        addReport(reportData.layer1_report, 'layer1');
        addReport(reportData.layer2_report, 'layer2');
      }

      // Generate and download zip
      const blob = await zip.generateAsync({ type: "blob" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `case-${String(caseItem.case_number).padStart(2, "0")}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Download Complete",
        description: `Case ${caseItem.case_number} downloaded as ZIP.`,
      });
    } catch (error) {
      console.error('Error downloading case:', error);
      toast({
        title: "Download Failed",
        description: "Failed to download case.",
        variant: "destructive",
      });
    } finally {
      setDownloadingCaseId(null);
    }
  };

  const handleEmailCase = (caseItem: InspectionCase) => {
    toast({
      title: "Email Feature",
      description: "Email functionality requires Resend integration. Please contact support to enable this feature.",
    });
  };

  return (
    <div className="flex h-full flex-1 animate-fade-in">
      {/* Collapsible Sidebar */}
      <div
        className={`relative flex transition-all duration-300 ease-in-out ${
          sidebarOpen ? "w-56" : "w-8"
        }`}
      >
        {/* Sidebar Content */}
        <div
          className={`bg-card border border-border rounded-lg overflow-hidden transition-all duration-300 ${
            sidebarOpen ? "w-56 p-4" : "w-0 p-0 border-0"
          }`}
        >
          {sidebarOpen && (
            <DatabaseFilters
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              selectedUserId={selectedUserId}
              onUserChange={setSelectedUserId}
              selectedDate={selectedDate}
              onDateChange={setSelectedDate}
              showModifiedOnly={showModifiedOnly}
              onModifiedChange={setShowModifiedOnly}
              canAccessToolsClassification={canAccessToolsClassification}
              onToolsClassificationClick={handleToolsClassificationClick}
            />
          )}
        </div>

        {/* Toggle Button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 z-10 w-6 h-12 bg-card border border-border rounded-r-md flex items-center justify-center hover:bg-accent/20 transition-colors"
        >
          {sidebarOpen ? (
            <ChevronLeft className="w-4 h-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="w-4 h-4 text-muted-foreground" />
          )}
        </button>
      </div>

      {/* Main Table Area */}
      <div className="flex-1 ml-4 flex flex-col">
        <div className="bg-card border border-border rounded-lg overflow-hidden flex flex-col flex-1">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : cases.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <p className="text-sm">No inspection cases found</p>
              <p className="text-xs mt-1">Cases will appear here after completing inspections</p>
            </div>
          ) : (
            <>
              <ScrollArea className="flex-1">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/50">
                      <TableHead className="w-16 text-center">No.</TableHead>
                      <TableHead>Case No. (Patient)</TableHead>
                      <TableHead className="w-32 text-center">Date</TableHead>
                      <TableHead className="w-28 text-center">Time</TableHead>
                      <TableHead className="w-28 text-center">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginatedCases.map((caseItem, index) => (
                      <TableRow key={caseItem.id} className="hover:bg-muted/30">
                        <TableCell className="text-center font-medium">
                          {(currentPage - 1) * ITEMS_PER_PAGE + index + 1}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            {caseItem.confirmed_by_users && caseItem.confirmed_by_users.length > 0 && (
                              <span className="relative flex h-2.5 w-2.5 shrink-0" title="Modified">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500" />
                              </span>
                            )}
                            <span>Case {caseItem.case_number} ({caseItem.patient_name})</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-center">{formatDate(caseItem.created_at)}</TableCell>
                        <TableCell className="text-center">{formatTime(caseItem.created_at)}</TableCell>
                        <TableCell>
                          <div className="flex items-center justify-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              title="View Case"
                              onClick={() => handleViewCase(caseItem)}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              title="Download Case"
                              onClick={() => handleDownloadCase(caseItem)}
                              disabled={downloadingCaseId === caseItem.id}
                            >
                              {downloadingCaseId === caseItem.id ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <Download className="w-4 h-4" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7"
                              title="Email Case"
                              onClick={() => handleEmailCase(caseItem)}
                            >
                              <Mail className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
              {totalPages > 1 && (
                <div className="border-t border-border px-4 py-2 flex items-center justify-between text-xs text-muted-foreground">
                  <span>Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1}–{Math.min(currentPage * ITEMS_PER_PAGE, filteredCases.length)} of {filteredCases.length}</span>
                  <Pagination className="mx-0 w-auto">
                    <PaginationContent>
                      <PaginationItem>
                        <PaginationPrevious
                          onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                          className={currentPage === 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                        />
                      </PaginationItem>
                      {Array.from({ length: totalPages }, (_, i) => i + 1)
                        .filter(page => page === 1 || page === totalPages || Math.abs(page - currentPage) <= 1)
                        .map((page, idx, arr) => (
                          <span key={page} className="flex items-center">
                            {idx > 0 && arr[idx - 1] !== page - 1 && (
                              <PaginationItem><PaginationEllipsis /></PaginationItem>
                            )}
                            <PaginationItem>
                              <PaginationLink
                                isActive={page === currentPage}
                                onClick={() => setCurrentPage(page)}
                                className="cursor-pointer"
                              >
                                {page}
                              </PaginationLink>
                            </PaginationItem>
                          </span>
                        ))}
                      <PaginationItem>
                        <PaginationNext
                          onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                          className={currentPage === totalPages ? "pointer-events-none opacity-50" : "cursor-pointer"}
                        />
                      </PaginationItem>
                    </PaginationContent>
                  </Pagination>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Case Detail Dialog */}
      <CaseDetailDialog
        open={detailDialogOpen}
        onOpenChange={setDetailDialogOpen}
        caseData={selectedCase}
      />
    </div>
  );
};

export default DatabaseView;
