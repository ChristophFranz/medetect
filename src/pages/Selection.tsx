import { useSearchParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import { Button } from "@/components/ui/button";
import { Camera, Database } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";

type UserTag = "medetect_team" | "nurses" | "administrator";

const Selection = () => {
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

    // Server-side verification to get user tags securely
    const verifyUser = async () => {
      const { data, error } = await supabase.functions.invoke('verify-access', {
        body: { 
          user_id: user, 
          required_tags: ['nurses', 'administrator', 'medetect_team'] 
        }
      });

      if (error || !data?.authorized) {
        // Redirect to login if user doesn't exist or has no valid tags
        navigate("/login");
        return;
      }

      if (data?.user?.tags) {
        setUserTags(data.user.tags as UserTag[]);
      }
      setLoading(false);
    };

    verifyUser();
  }, [searchParams, navigate]);

  const handleSelection = (mode: "inspection" | "database") => {
    navigate(`/${mode}?user=${userId}&name=${encodeURIComponent(userName)}`);
  };

  const handleLogout = () => {
    navigate("/login");
  };

  // Check access permissions based on tags
  const canAccessInspection = userTags.includes("nurses") || userTags.includes("medetect_team");
  const canAccessDatabase = userTags.includes("nurses") || userTags.includes("administrator") || userTags.includes("medetect_team");

  if (loading || !userId) {
    return null;
  }

  return (
    <AppLayout
      userId={userId}
      userName={userName}
      userTags={userTags}
      onLogout={handleLogout}
    >
      <div className="flex flex-col items-center justify-center gap-8 animate-fade-in flex-1">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-foreground mb-2">
            Welcome, {userName}
          </h1>
          <p className="text-muted-foreground">Please select an option to continue</p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-6">
          {canAccessInspection && (
            <Button
              variant="outline"
              size="lg"
              onClick={() => handleSelection("inspection")}
              className="flex flex-col items-center gap-4 h-auto py-8 px-12 bg-card hover:bg-accent/10 border-2 hover:border-accent transition-all"
            >
              <Camera size={48} className="text-accent" />
              <span className="text-lg font-medium">Inspection System</span>
            </Button>
          )}
          
          {canAccessDatabase && (
            <Button
              variant="outline"
              size="lg"
              onClick={() => handleSelection("database")}
              className="flex flex-col items-center gap-4 h-auto py-8 px-12 bg-card hover:bg-accent/10 border-2 hover:border-accent transition-all"
            >
              <Database size={48} className="text-accent" />
              <span className="text-lg font-medium">Database Access</span>
            </Button>
          )}
        </div>
      </div>
    </AppLayout>
  );
};

export default Selection;