import { useSearchParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import ToolsClassificationView from "@/components/ToolsClassificationView";
import { supabase } from "@/integrations/supabase/client";

type UserTag = "medetect_team" | "nurses" | "administrator";

const ToolsClassification = () => {
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

    // Fetch user tags
    const fetchTags = async () => {
      const { data } = await supabase
        .from("users")
        .select("tags")
        .eq("id", user)
        .maybeSingle();
      
      if (data?.tags) {
        const tags = data.tags as UserTag[];
        // Verify user has access to this page
        if (!tags.includes("administrator") && !tags.includes("medetect_team")) {
          navigate(`/database?user=${user}&name=${encodeURIComponent(name)}`);
          return;
        }
        setUserTags(tags);
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

  const backToDatabase = `/database?user=${userId}&name=${encodeURIComponent(userName)}`;

  return (
    <AppLayout
      showNavigation={true}
      activeTab="database"
      onLogout={handleLogout}
      userName={userName}
      userId={userId}
      userTags={userTags}
      showFooter={true}
      showBack={true}
      backTo={backToDatabase}
    >
      <ToolsClassificationView />
    </AppLayout>
  );
};

export default ToolsClassification;
