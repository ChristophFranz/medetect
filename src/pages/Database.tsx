import { useSearchParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import DatabaseView from "@/components/DatabaseView";
import { supabase } from "@/integrations/supabase/client";

type UserTag = "medetect_team" | "nurses" | "administrator";

const Database = () => {
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
        setUserTags(data.tags as UserTag[]);
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
      activeTab="database"
      onLogout={handleLogout}
      userName={userName}
      userId={userId}
      userTags={userTags}
      showFooter={true}
    >
      <DatabaseView userTags={userTags} />
    </AppLayout>
  );
};

export default Database;