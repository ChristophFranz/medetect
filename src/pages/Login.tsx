import { useSearchParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import LogoCard from "@/components/LogoCard";
import UserWelcomeCard from "@/components/UserWelcomeCard";
import { supabase } from "@/integrations/supabase/client";

interface User {
  id: string;
  name: string;
  role: string | null;
  department: string | null;
}

const Login = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchUser = async (nfcId: string) => {
      setLoading(true);
      const { data, error } = await supabase
        .from("users")
        .select("id, name, role, department")
        .eq("nfc_tag_id", nfcId)
        .maybeSingle();

      if (data && !error) {
        setUser(data);
        
        // Auto-redirect to selection after 2 seconds
        const redirectTimer = setTimeout(() => {
          navigate(`/selection?user=${data.id}&name=${encodeURIComponent(data.name)}`);
        }, 2000);

        return () => clearTimeout(redirectTimer);
      }
      setLoading(false);
    };

    const nfcId = searchParams.get("nfc");
    if (nfcId) {
      fetchUser(nfcId);
    }
  }, [searchParams, navigate]);

  return (
    <AppLayout>
      <div className="flex flex-col md:flex-row items-center justify-center gap-8 animate-fade-in">
        <LogoCard showNfcInput={!user && !loading} />
        {loading && <p className="text-muted-foreground">Looking up user...</p>}
        {user && <UserWelcomeCard userName={user.name} />}
      </div>
    </AppLayout>
  );
};

export default Login;
