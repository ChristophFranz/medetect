import { Button } from "@/components/ui/button";
import { LogOut, Minimize2, Maximize2, X } from "lucide-react";

interface AppHeaderProps {
  showNavigation?: boolean;
  activeTab?: "inspection" | "database";
  onTabChange?: (tab: "inspection" | "database") => void;
  onLogout?: () => void;
  showWindowControls?: boolean;
}

const AppHeader = ({ 
  showNavigation = false, 
  activeTab = "inspection",
  onTabChange,
  onLogout,
  showWindowControls = false
}: AppHeaderProps) => {
  return (
    <header className="w-full bg-header rounded-t-lg flex items-center justify-between px-2 py-1">
      <div className="flex items-center gap-1">
        {showNavigation && (
          <>
            <Button
              variant={activeTab === "inspection" ? "default" : "ghost"}
              size="sm"
              onClick={() => onTabChange?.("inspection")}
              className={`text-xs h-6 px-2 ${activeTab === "inspection" ? "bg-accent text-accent-foreground" : "bg-header-foreground/20 text-header-foreground hover:bg-header-foreground/30"}`}
            >
              Inspection System
            </Button>
            <Button
              variant={activeTab === "database" ? "default" : "ghost"}
              size="sm"
              onClick={() => onTabChange?.("database")}
              className={`text-xs h-6 px-2 ${activeTab === "database" ? "bg-accent text-accent-foreground" : "bg-transparent text-header-foreground hover:bg-header-foreground/20"}`}
            >
              Database
            </Button>
          </>
        )}
      </div>
      
      <div className="flex items-center gap-1">
        {showWindowControls && (
          <>
            <button className="w-4 h-4 flex items-center justify-center text-header-foreground/70 hover:text-header-foreground">
              <Minimize2 size={10} />
            </button>
            <button className="w-4 h-4 flex items-center justify-center text-header-foreground/70 hover:text-header-foreground">
              <Maximize2 size={10} />
            </button>
            <button className="w-4 h-4 flex items-center justify-center text-header-foreground/70 hover:text-header-foreground">
              <X size={10} />
            </button>
          </>
        )}
        {onLogout && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onLogout}
            className="text-xs h-6 px-2 text-header-foreground hover:bg-header-foreground/20 ml-2"
          >
            <LogOut size={12} />
            Logout
          </Button>
        )}
      </div>
    </header>
  );
};

export default AppHeader;
