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
  tags: string[] | null;
}

const Login = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    const fetchUser = async (nfcId: string) => {
      setLoading(true);
      setNotFound(false);
      
      // Use Edge Function for secure NFC lookup
      const { data, error } = await supabase.functions.invoke('nfc-lookup', {
        body: { nfc_tag_id: nfcId }
      });

      if (data?.found && data?.user && !error) {
        setUser(data.user as User);
        
        // Auto-redirect to selection after 2 seconds
        const redirectTimer = setTimeout(() => {
          navigate(`/selection?user=${data.user.id}&name=${encodeURIComponent(data.user.name)}`);
        }, 2000);

        return () => clearTimeout(redirectTimer);
      } else {
        // User not found - show error and clear the nfc param
        setNotFound(true);
        setSearchParams({});
      }
      setLoading(false);
    };

    const nfcId = searchParams.get("nfc");
    if (nfcId) {
      fetchUser(nfcId);
    } else {
      // Reset state when nfc param is cleared
      setNotFound(false);
      setUser(null);
    }
  }, [searchParams, navigate, setSearchParams]);

  return (
    <AppLayout>
      <div className="flex flex-col md:flex-row items-center justify-center gap-8 animate-fade-in flex-1">
        <LogoCard showNfcInput={!user && !loading} />
        {loading && <p className="text-muted-foreground">Looking up user...</p>}
        {notFound && (
          <p className="text-destructive font-medium">User does not exist. Try another NFC card.</p>
        )}
        {user && <UserWelcomeCard userName={user.name} />}
      </div>
    </AppLayout>
  );
};

export default Login;
