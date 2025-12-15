import AppLayout from "@/components/AppLayout";
import LogoCard from "@/components/LogoCard";

const Index = () => {
  return (
    <AppLayout>
      <div className="flex flex-col items-center justify-center animate-fade-in">
        <LogoCard showScanButton={true} />
      </div>
    </AppLayout>
  );
};

export default Index;
