import { useSearchParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import InspectionView from "@/components/InspectionView";

const Inspection = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [userName, setUserName] = useState<string>("");
  const [userId, setUserId] = useState<string>("");

  useEffect(() => {
    const user = searchParams.get("user");
    const name = searchParams.get("name");
    
    if (!user || !name) {
      navigate("/");
      return;
    }
    
    setUserId(user);
    setUserName(decodeURIComponent(name));
  }, [searchParams, navigate]);

  const handleLogout = () => {
    navigate("/login");
  };

  if (!userId) {
    return null;
  }

  return (
    <AppLayout
      showNavigation={true}
      activeTab="inspection"
      onLogout={handleLogout}
      userName={userName}
      showFooter={true}
    >
      <InspectionView />
    </AppLayout>
  );
};

export default Inspection;
