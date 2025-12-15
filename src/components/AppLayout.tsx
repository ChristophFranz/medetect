import { ReactNode } from "react";
import AppHeader from "./AppHeader";
import AppFooter from "./AppFooter";

interface AppLayoutProps {
  children: ReactNode;
  showNavigation?: boolean;
  activeTab?: "inspection" | "database";
  onLogout?: () => void;
  userName?: string;
  userId?: string;
  userTags?: string[];
  showFooter?: boolean;
}

const AppLayout = ({ 
  children, 
  showNavigation = false,
  activeTab = "inspection",
  onLogout,
  userName,
  userId,
  userTags = [],
  showFooter = false
}: AppLayoutProps) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-4xl bg-card/50 rounded-lg shadow-lg overflow-hidden border border-border flex flex-col">
        <AppHeader 
          showNavigation={showNavigation}
          activeTab={activeTab}
          onLogout={onLogout}
          userId={userId}
          userName={userName}
          userTags={userTags}
        />
        <div className="p-6 md:p-8 flex-1">
          {children}
        </div>
        {showFooter && <AppFooter userName={userName} />}
      </div>
    </div>
  );
};

export default AppLayout;
