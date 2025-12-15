import { useState, useEffect } from "react";
import { ChevronRight, ChevronLeft, Eye, Download, Mail, Shield } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "./ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

interface InspectionCase {
  id: number;
  caseNo: string;
  date: string;
  time: string;
}

// Mock data - will be replaced with actual database data
const mockCases: InspectionCase[] = [
  { id: 1, caseNo: "Case - 123", date: "03/01/2024", time: "14:23:00" },
  { id: 2, caseNo: "Case - 145", date: "10/03/2024", time: "14:23:00" },
  { id: 3, caseNo: "Case - 167", date: "27/05/2024", time: "14:23:00" },
  { id: 4, caseNo: "Case - 188", date: "01/06/2024", time: "14:23:00" },
  { id: 5, caseNo: "Case - 299", date: "13/07/2024", time: "14:23:00" },
  { id: 6, caseNo: "Case - 381", date: "18/11/2024", time: "14:23:00" },
];

type FilterType = "recent" | "flagged" | "date" | "user" | null;

const DatabaseView = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState<FilterType>(null);
  const [cases] = useState<InspectionCase[]>(mockCases);
  const [isAdmin, setIsAdmin] = useState(false);
  const [showAdminTab, setShowAdminTab] = useState(false);
  const [searchParams] = useSearchParams();

  const userId = searchParams.get("user");

  useEffect(() => {
    const checkAdminRole = async () => {
      if (!userId) return;
      
      const { data } = await supabase
        .from("user_roles")
        .select("role")
        .eq("user_id", userId)
        .eq("role", "admin")
        .maybeSingle();
      
      setIsAdmin(!!data);
    };

    checkAdminRole();
  }, [userId]);

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
                  By User
                </Button>
              </div>

              {isAdmin && (
                <div className="pt-4 border-t border-border mt-4">
                  <p className="text-sm font-medium text-muted-foreground flex items-center gap-2 mb-2">
                    <Shield className="w-4 h-4" /> Admin
                  </p>
                  <Button
                    variant={showAdminTab ? "secondary" : "outline"}
                    size="sm"
                    className="w-full justify-center text-xs"
                    onClick={() => setShowAdminTab(!showAdminTab)}
                  >
                    Admin Panel
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
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="w-16 text-center">No.</TableHead>
                <TableHead>Case No.</TableHead>
                <TableHead className="w-32 text-center">Date</TableHead>
                <TableHead className="w-28 text-center">Time</TableHead>
                <TableHead className="w-28 text-center">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {cases.map((caseItem) => (
                <TableRow key={caseItem.id} className="hover:bg-muted/30">
                  <TableCell className="text-center font-medium">
                    {caseItem.id}
                  </TableCell>
                  <TableCell>{caseItem.caseNo}</TableCell>
                  <TableCell className="text-center">{caseItem.date}</TableCell>
                  <TableCell className="text-center">{caseItem.time}</TableCell>
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
        </div>
      </div>
    </div>
  );
};

export default DatabaseView;
