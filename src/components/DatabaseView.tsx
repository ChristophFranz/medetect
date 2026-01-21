import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ChevronRight, ChevronLeft, Eye, Download, Mail, Wrench, Loader2 } from "lucide-react";
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

interface InspectionCase {
  id: string;
  case_number: number;
  patient_name: string;
  user_id: string;
  user_name: string;
  folder_path: string;
  created_at: string;
}

type FilterType = "recent" | "flagged" | "date" | "user" | null;
type UserTag = "medetect_team" | "nurses" | "administrator";

interface DatabaseViewProps {
  userTags: UserTag[];
}

const DatabaseView = ({ userTags }: DatabaseViewProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<FilterType>(null);
  const [cases, setCases] = useState<InspectionCase[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const userId = searchParams.get("user");

  // Check if user can access tools classification database
  const canAccessToolsClassification = userTags.includes("administrator") || userTags.includes("medetect_team");

  useEffect(() => {
    fetchCases();
  }, [activeFilter, userId]);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('get-inspection-cases', {
        body: { 
          user_id: userId,
          filter_type: activeFilter,
          filter_value: activeFilter === 'user' ? userId : undefined
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
  };

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

  const handleFilterClick = (filter: FilterType) => {
    setActiveFilter(activeFilter === filter ? null : filter);
  };

  return (
    <div className="flex h-full animate-fade-in">
      {/* Collapsible Sidebar */}
      <div
        className={`relative flex transition-all duration-300 ease-in-out ${
          sidebarOpen ? "w-48" : "w-8"
        }`}
      >
        {/* Sidebar Content */}
        <div
          className={`bg-card border border-border rounded-lg overflow-hidden transition-all duration-300 ${
            sidebarOpen ? "w-48 p-4" : "w-0 p-0 border-0"
          }`}
        >
          {sidebarOpen && (
            <div className="space-y-4">
              <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <span>▽</span> Quick Filter
              </p>
              <div className="space-y-2">
                <Button
                  variant={activeFilter === "recent" ? "secondary" : "outline"}
                  size="sm"
                  className="w-full justify-center text-xs"
                  onClick={() => handleFilterClick("recent")}
                >
                  Recent Scans
                </Button>
                <Button
                  variant={activeFilter === "flagged" ? "secondary" : "outline"}
                  size="sm"
                  className="w-full justify-center text-xs"
                  onClick={() => handleFilterClick("flagged")}
                >
                  Flagged Cases
                </Button>
                <Button
                  variant={activeFilter === "date" ? "secondary" : "outline"}
                  size="sm"
                  className="w-full justify-center text-xs"
                  onClick={() => handleFilterClick("date")}
                >
                  By Date
                </Button>
                <Button
                  variant={activeFilter === "user" ? "secondary" : "outline"}
                  size="sm"
                  className="w-full justify-center text-xs"
                  onClick={() => handleFilterClick("user")}
                >
                  My Cases
                </Button>
              </div>

              {canAccessToolsClassification && (
                <div className="pt-4 border-t border-border mt-4">
                  <p className="text-sm font-medium text-muted-foreground flex items-center gap-2 mb-2">
                    <Wrench className="w-4 h-4" /> Tools
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full justify-center text-xs"
                    onClick={handleToolsClassificationClick}
                  >
                    Tools Classification
                  </Button>
                </div>
              )}
            </div>
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
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          title="Download Case"
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7"
                          title="Secure Email Case"
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
    </div>
  );
};

export default DatabaseView;
