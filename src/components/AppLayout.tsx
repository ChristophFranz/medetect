import { ReactNode } from "react";
import AppHeader from "./AppHeader";

interface AppLayoutProps {
  children: ReactNode;
}

const AppLayout = ({ children }: AppLayoutProps) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-2xl bg-card/50 rounded-lg shadow-lg overflow-hidden border border-border">
        <AppHeader />
        <div className="p-8 md:p-12">
          {children}
        </div>
      </div>
    </div>
  );
};

export default AppLayout;
