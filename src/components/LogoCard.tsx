import { Input } from "@/components/ui/input";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useState, useRef, useEffect } from "react";
import medetectLogo from "@/assets/medetect-logo.png";

interface LogoCardProps {
  showNfcInput?: boolean;
}

const LogoCard = ({ showNfcInput = false }: LogoCardProps) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [nfcValue, setNfcValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // Clear input when nfc param is removed (after failed lookup)
  useEffect(() => {
    const nfcParam = searchParams.get("nfc");
    if (!nfcParam && nfcValue) {
      setNfcValue("");
    }
  }, [searchParams]);

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
    <div className="flex flex-col items-center gap-8 p-12 bg-card rounded-lg border border-border shadow-sm animate-slide-up flex-1 justify-center min-w-[280px]">
      <div className="flex flex-col items-center justify-center w-48 h-36 border-2 border-dashed border-muted-foreground/30 rounded-md">
        <span className="text-2xl font-semibold text-foreground">MEDetect</span>
        <span className="text-base text-muted-foreground">Logo</span>
      </div>
      
      {showNfcInput && (
        <div className="flex flex-col items-center gap-3">
          <p className="text-base text-muted-foreground">Scan NFC tag to login</p>
          <Input
            ref={inputRef}
            type="text"
            value={nfcValue}
            onChange={(e) => setNfcValue(e.target.value)}
            placeholder="Awaiting NFC scan..."
            className="min-w-[260px] text-center text-base h-11"
            autoFocus
          />
        </div>
      )}
    </div>
  );
};

export default LogoCard;
