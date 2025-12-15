import { Input } from "@/components/ui/input";
import { useNavigate } from "react-router-dom";
import { useState, useRef, useEffect } from "react";

interface LogoCardProps {
  showNfcInput?: boolean;
}

const LogoCard = ({ showNfcInput = false }: LogoCardProps) => {
  const navigate = useNavigate();
  const [nfcValue, setNfcValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (showNfcInput && inputRef.current) {
      inputRef.current.focus();
    }
  }, [showNfcInput]);

  useEffect(() => {
    if (nfcValue.length >= 5) {
      const timer = setTimeout(() => {
        navigate(`/login?nfc=${encodeURIComponent(nfcValue)}`);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [nfcValue, navigate]);

  return (
    <div className="flex flex-col items-center gap-6 p-8 bg-card rounded-lg border border-border shadow-sm animate-slide-up">
      <div className="flex flex-col items-center justify-center w-32 h-24 border-2 border-dashed border-muted-foreground/30 rounded-md">
        <span className="text-lg font-semibold text-foreground">MEDetect</span>
        <span className="text-sm text-muted-foreground">Logo</span>
      </div>
      
      {showNfcInput && (
        <div className="flex flex-col items-center gap-2">
          <p className="text-sm text-muted-foreground">Scan NFC tag to login</p>
          <Input
            ref={inputRef}
            type="text"
            value={nfcValue}
            onChange={(e) => setNfcValue(e.target.value)}
            placeholder="Awaiting NFC scan..."
            className="min-w-[200px] text-center"
            autoFocus
          />
        </div>
      )}
    </div>
  );
};

export default LogoCard;
