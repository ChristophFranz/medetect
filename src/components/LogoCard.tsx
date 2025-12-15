import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

interface LogoCardProps {
  showScanButton?: boolean;
}

const LogoCard = ({ showScanButton = true }: LogoCardProps) => {
  const navigate = useNavigate();

  const handleScanClick = () => {
    // Simulate NFC scan - in production, this would be triggered by actual NFC scan
    // For demo, we'll navigate to login with a sample user ID
    navigate("/login?nfc=12345");
  };

  return (
    <div className="flex flex-col items-center gap-6 p-8 bg-card rounded-lg border border-border shadow-sm animate-slide-up">
      <div className="flex flex-col items-center justify-center w-32 h-24 border-2 border-dashed border-muted-foreground/30 rounded-md">
        <span className="text-lg font-semibold text-foreground">MEDetect</span>
        <span className="text-sm text-muted-foreground">Logo</span>
      </div>
      
      {showScanButton && (
        <Button 
          variant="accent" 
          size="lg"
          onClick={handleScanClick}
          className="min-w-[120px]"
        >
          Scan<br />to Login
        </Button>
      )}
    </div>
  );
};

export default LogoCard;
