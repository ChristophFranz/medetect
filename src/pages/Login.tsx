import { useSearchParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import AppLayout from "@/components/AppLayout";
import LogoCard from "@/components/LogoCard";
import UserWelcomeCard from "@/components/UserWelcomeCard";

// Mock user database - in production, this would come from a backend
const mockUsers: Record<string, { name: string; id: string }> = {
  "12345": { name: "Matthias", id: "12345" },
  "67890": { name: "Sarah", id: "67890" },
  "11111": { name: "John", id: "11111" },
};

const Login = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [user, setUser] = useState<{ name: string; id: string } | null>(null);

  useEffect(() => {
    const nfcId = searchParams.get("nfc");
    if (nfcId && mockUsers[nfcId]) {
      const foundUser = mockUsers[nfcId];
      setUser(foundUser);
      
      // Auto-redirect to inspection after 2 seconds
      const redirectTimer = setTimeout(() => {
        navigate(`/inspection?user=${foundUser.id}`);
      }, 2000);

      return () => clearTimeout(redirectTimer);
    }
  }, [searchParams, navigate]);

  return (
    <AppLayout>
      <div className="flex flex-col md:flex-row items-center justify-center gap-8 animate-fade-in">
        <LogoCard showScanButton={true} />
        {user && <UserWelcomeCard userName={user.name} />}
      </div>
    </AppLayout>
  );
};

export default Login;
