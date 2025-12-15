import { useSearchParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import InspectionView from "@/components/InspectionView";
import DatabaseView from "@/components/DatabaseView";

// Mock user database
const mockUsers: Record<string, { name: string; id: string }> = {
  "12345": { name: "Matthias", id: "12345" },
  "67890": { name: "Sarah", id: "67890" },
  "11111": { name: "John", id: "11111" },
};

const Inspection = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<"inspection" | "database">("inspection");
  const [user, setUser] = useState<{ name: string; id: string } | null>(null);

  useEffect(() => {
    const userId = searchParams.get("user");
    if (userId && mockUsers[userId]) {
      setUser(mockUsers[userId]);
    } else {
      // Redirect to landing if no valid user
      navigate("/");
    }
  }, [searchParams, navigate]);

  const handleLogout = () => {
    navigate("/");
  };

  const handleTabChange = (tab: "inspection" | "database") => {
    setActiveTab(tab);
  };

  if (!user) {
    return null;
  }

  return (
    <AppLayout
      showNavigation={true}
      activeTab={activeTab}
      onTabChange={handleTabChange}
      onLogout={handleLogout}
      userName={`User_${user.id}`}
      showFooter={true}
    >
      {activeTab === "inspection" ? (
        <InspectionView />
      ) : (
        <DatabaseView />
      )}
    </AppLayout>
  );
};

export default Inspection;
