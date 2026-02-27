import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { AlertTriangle, CheckCircle2, ShieldCheck, Loader2, UserCheck } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "@/hooks/use-toast";
import type { ToolResult } from "./AnalysisResults";

interface ToolReviewDialogProps {
  tool: ToolResult | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  caseId: string | null;
  layer: "layer1" | "layer2";
  primaryUserId: string;
  primaryUserName: string;
  onStatusUpdated: (toolName: string, newStatus: string, secondUserId: string, secondUserName: string) => void;
}

const isDefective = (status: string) =>
  status.toLowerCase().includes("defective") && !status.toLowerCase().includes("non");

type ReviewStep = "review" | "nfc_confirm" | "saving";

const ToolReviewDialog = ({
  tool,
  open,
  onOpenChange,
  caseId,
  layer,
  primaryUserId,
  primaryUserName,
  onStatusUpdated,
}: ToolReviewDialogProps) => {
  const [step, setStep] = useState<ReviewStep>("review");
  const [nfcInput, setNfcInput] = useState("");
  const [nfcLoading, setNfcLoading] = useState(false);
  const [nfcError, setNfcError] = useState<string | null>(null);
  const [wantsChange, setWantsChange] = useState(false);

  if (!tool) return null;

  const defective = isDefective(tool.status);
  const newStatus = defective ? "Non-defective" : "Defective";

  const handleClose = () => {
    setStep("review");
    setNfcInput("");
    setNfcError(null);
    setWantsChange(false);
    setNfcLoading(false);
    onOpenChange(false);
  };

  const handleChangeRequest = () => {
    setWantsChange(true);
    setStep("nfc_confirm");
  };

  const handleNfcSubmit = async () => {
    if (!nfcInput.trim()) return;

    setNfcLoading(true);
    setNfcError(null);

    try {
      // Lookup 2nd user via NFC
      const { data, error } = await supabase.functions.invoke("nfc-lookup", {
        body: { nfc_tag_id: nfcInput.trim() },
      });

      if (error || !data?.found) {
        setNfcError("User not found. Please try another NFC card.");
        setNfcLoading(false);
        return;
      }

      const secondUser = data.user;

      // Prevent same user from confirming
      if (secondUser.id === primaryUserId) {
        setNfcError("A different user must confirm the change.");
        setNfcLoading(false);
        return;
      }

      setStep("saving");

      // Save override via edge function
      const { error: saveError } = await supabase.functions.invoke("save-status-override", {
        body: {
          case_id: caseId,
          layer,
          tool_name: tool.name,
          new_status: newStatus,
          primary_user_id: primaryUserId,
          primary_user_name: primaryUserName,
          second_user_id: secondUser.id,
          second_user_name: secondUser.name,
        },
      });

      if (saveError) {
        throw new Error("Failed to save override");
      }

      onStatusUpdated(tool.name, newStatus, secondUser.id, secondUser.name);

      toast({
        title: "Status updated",
        description: `${tool.name} changed to ${newStatus}. Confirmed by ${secondUser.name}.`,
      });

      handleClose();
    } catch (err) {
      console.error("NFC confirm error:", err);
      setNfcError("Failed to save status change. Please try again.");
      setStep("nfc_confirm");
    } finally {
      setNfcLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {defective ? (
              <AlertTriangle className="w-5 h-5 text-destructive" />
            ) : (
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            )}
            {tool.name}
          </DialogTitle>
          <DialogDescription>
            Status: {defective ? "Defective" : "Non-defective"} · Qty: {tool.count}
          </DialogDescription>
        </DialogHeader>

        {/* Tool image */}
        {tool.image && (
          <div className="rounded-md overflow-hidden border border-border">
            <img
              src={tool.image}
              alt={`${tool.name} detail`}
              className="w-full h-auto object-contain"
            />
          </div>
        )}

        {/* Current status badge */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">Current Decision:</span>
          <Badge variant={defective ? "destructive" : "secondary"} className="text-sm">
            {defective ? "Defective" : "Non-defective"}
          </Badge>
        </div>

        {/* Step: Review - show change button */}
        {step === "review" && !wantsChange && (
          <DialogFooter className="flex-row gap-2 sm:justify-between">
            <Button variant="outline" onClick={handleClose}>
              Confirm as-is
            </Button>
            <Button
              variant={defective ? "default" : "destructive"}
              onClick={handleChangeRequest}
            >
              Change to {newStatus}
            </Button>
          </DialogFooter>
        )}

        {/* Step: NFC Confirmation */}
        {step === "nfc_confirm" && (
          <div className="space-y-3 pt-2 border-t border-border">
            <div className="flex items-center gap-2 text-sm font-medium text-foreground">
              <ShieldCheck className="w-4 h-4 text-primary" />
              Second user confirmation required
            </div>
            <p className="text-xs text-muted-foreground">
              Changing <strong>{tool.name}</strong> from{" "}
              <strong>{defective ? "Defective" : "Non-defective"}</strong> to{" "}
              <strong>{newStatus}</strong>. A second user must scan their NFC card to confirm.
            </p>
            <div className="flex gap-2">
              <Input
                placeholder="Scan NFC card…"
                value={nfcInput}
                onChange={(e) => setNfcInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleNfcSubmit()}
                autoFocus
                disabled={nfcLoading}
              />
              <Button onClick={handleNfcSubmit} disabled={!nfcInput.trim() || nfcLoading}>
                {nfcLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserCheck className="w-4 h-4" />}
              </Button>
            </div>
            {nfcError && (
              <p className="text-xs text-destructive">{nfcError}</p>
            )}
          </div>
        )}

        {/* Step: Saving */}
        {step === "saving" && (
          <div className="flex items-center gap-3 py-4">
            <Loader2 className="w-5 h-5 text-primary animate-spin" />
            <p className="text-sm text-muted-foreground">Saving status change…</p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default ToolReviewDialog;
