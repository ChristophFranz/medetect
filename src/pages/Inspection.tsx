import { useSearchParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import InspectionView from "@/components/InspectionView";
import { supabase } from "@/integrations/supabase/client";

type UserTag = "medetect_team" | "nurses" | "administrator";

const Inspection = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [userName, setUserName] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [userTags, setUserTags] = useState<UserTag[]>([]);

  useEffect(() => {
    const user = searchParams.get("user");
    const name = searchParams.get("name");
    
    if (!user || !name) {
      navigate("/");
      return;
    }
    
    setUserId(user);
    setUserName(decodeURIComponent(name));

    // Fetch user tags and verify access
    const fetchTags = async () => {
      const { data } = await supabase
        .from("users")
        .select("tags")
        .eq("id", user)
        .maybeSingle();
      
      if (data?.tags) {
        const tags = data.tags as UserTag[];
        setUserTags(tags);
        
        // Check if user has inspection access
        const hasAccess = tags.includes("nurses") || tags.includes("medetect_team");
        if (!hasAccess) {
          navigate(`/selection?user=${user}&name=${encodeURIComponent(name)}`);
        }
      }
    };

    fetchTags();
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
      userId={userId}
      userTags={userTags}
      showFooter={true}
    >
      <InspectionView />
    </AppLayout>
  );
};

export default Inspection;
