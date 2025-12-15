import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AppLayout from "@/components/AppLayout";
import LogoCard from "@/components/LogoCard";

const Index = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate("/login");
    }, 1500);

    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <AppLayout>
      <div className="flex flex-col items-center justify-center animate-fade-in">
        <LogoCard showNfcInput={false} />
      </div>
    </AppLayout>
  );
};

export default Index;
