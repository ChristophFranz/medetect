import { Button } from "@/components/ui/button";
import { LogOut, UserPlus } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface AppHeaderProps {
  showNavigation?: boolean;
  activeTab?: "inspection" | "database";
  onLogout?: () => void;
  userId?: string;
  userName?: string;
  userTags?: string[];
}

const AppHeader = ({ 
  showNavigation = false, 
  activeTab = "inspection",
  onLogout,
  userId,
  userName,
  userTags = []
}: AppHeaderProps) => {
  const navigate = useNavigate();
  
  const getPageTitle = () => {
    if (activeTab === "inspection") return "Inspection System";
    if (activeTab === "database") return "Database Access";
    return "";
  };

  const canCreateUsers = userTags.includes("administrator") || userTags.includes("medetect_team");

  const handleNewUser = () => {
    if (userId && userName) {
      navigate(`/new-user?user=${userId}&name=${encodeURIComponent(userName)}`);
    }
  };

  return (
    <header className="w-full bg-header rounded-t-lg flex items-center justify-between px-4 py-2">
      <div className="flex items-center gap-2">
        {showNavigation && (
          <span className="text-sm font-medium text-header-foreground">
            {getPageTitle()}
          </span>
        )}
      </div>
      
      <div className="flex items-center gap-2">
        {canCreateUsers && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleNewUser}
            className="text-xs h-7 px-3 text-header-foreground hover:bg-header-foreground/20"
          >
            <UserPlus size={14} className="mr-1" />
            New User Creation
          </Button>
        )}
        {onLogout && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onLogout}
            className="text-xs h-7 px-3 text-header-foreground hover:bg-header-foreground/20"
          >
            <LogOut size={14} className="mr-1" />
            Logout
          </Button>
        )}
      </div>
    </header>
  );
};

export default AppHeader;
