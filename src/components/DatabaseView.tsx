import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ChevronRight, ChevronLeft, Eye, Download, Mail, Loader2 } from "lucide-react";
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

interface InspectionCase {
  id: string;
  case_number: number;
  patient_name: string;
  user_id: string;
  user_name: string;
  folder_path: string;
  layer1_image_path: string | null;
  layer2_image_path: string | null;
  created_at: string;
}

type UserTag = "medetect_team" | "nurses" | "administrator";

interface DatabaseViewProps {
  userTags: UserTag[];
}

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
  
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const canAccessToolsClassification = userTags.includes("administrator") || userTags.includes("medetect_team");

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
      const downloadImage = async (imagePath: string | null, filename: string) => {
        if (!imagePath) return;
        
        const { data } = supabase.storage
          .from('case-images')
          .getPublicUrl(imagePath);
        
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
      };

      if (caseItem.layer1_image_path) {
        await downloadImage(caseItem.layer1_image_path, `case-${caseItem.case_number}-layer1.jpg`);
      }
      
      if (caseItem.layer2_image_path) {
        await downloadImage(caseItem.layer2_image_path, `case-${caseItem.case_number}-layer2.jpg`);
      }

      toast({
        title: "Download Complete",
        description: `Case ${caseItem.case_number} images downloaded successfully.`,
      });
    } catch (error) {
      console.error('Error downloading case:', error);
      toast({
        title: "Download Failed",
        description: "Failed to download case images.",
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
    <div className="flex h-full animate-fade-in">
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
      <div className="flex-1 ml-4">
        <div className="bg-card border border-border rounded-lg overflow-hidden">
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
                {cases.map((caseItem, index) => (
                  <TableRow key={caseItem.id} className="hover:bg-muted/30">
                    <TableCell className="text-center font-medium">
                      {index + 1}
                    </TableCell>
                    <TableCell>
                      Case {caseItem.case_number} ({caseItem.patient_name})
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
