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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const user = searchParams.get("user");
    const name = searchParams.get("name");
    
    if (!user || !name) {
      navigate("/");
      return;
    }
    
    setUserId(user);
    setUserName(decodeURIComponent(name));

    // Server-side access verification
    const verifyAccess = async () => {
      const { data, error } = await supabase.functions.invoke('verify-access', {
        body: { 
          user_id: user, 
          required_tags: ['administrator', 'medetect_team'] 
        }
      });

      if (error || !data?.authorized) {
        // Redirect to database if not authorized for tools classification
        navigate(`/database?user=${user}&name=${encodeURIComponent(name)}`);
        return;
      }

      if (data?.user?.tags) {
        setUserTags(data.user.tags as UserTag[]);
      }
      setLoading(false);
    };

    verifyAccess();
  }, [searchParams, navigate]);

  const handleLogout = () => {
    navigate("/login");
  };

  if (loading || !userId) {
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
