import { useState, useEffect } from "react";
import { X, Download, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { supabase } from "@/integrations/supabase/client";

interface CaseDetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  caseData: {
    id: string;
    case_number: number;
    patient_name: string;
    user_name: string;
    folder_path: string;
    layer1_image_path: string | null;
    layer2_image_path: string | null;
    created_at: string;
  } | null;
}

const CaseDetailDialog = ({ open, onOpenChange, caseData }: CaseDetailDialogProps) => {
  const [layer1Url, setLayer1Url] = useState<string | null>(null);
  const [layer2Url, setLayer2Url] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open && caseData) {
      loadImages();
    }
  }, [open, caseData]);

  const loadImages = async () => {
    if (!caseData) return;
    setLoading(true);

    try {
      if (caseData.layer1_image_path) {
        const { data: layer1Data } = supabase.storage
          .from('case-images')
          .getPublicUrl(caseData.layer1_image_path);
        setLayer1Url(layer1Data.publicUrl);
      }

      if (caseData.layer2_image_path) {
        const { data: layer2Data } = supabase.storage
          .from('case-images')
          .getPublicUrl(caseData.layer2_image_path);
        setLayer2Url(layer2Data.publicUrl);
      }
    } catch (error) {
      console.error('Error loading images:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadImage = async (imagePath: string | null, filename: string) => {
    if (!imagePath) return;

    try {
      const { data } = supabase.storage
        .from('case-images')
        .getPublicUrl(imagePath);
      
      const response = await fetch(data.publicUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading image:', error);
    }
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!caseData) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Case {caseData.case_number} - {caseData.patient_name}</span>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Case Info */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Patient:</span>
              <span className="ml-2 font-medium">{caseData.patient_name}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Inspector:</span>
              <span className="ml-2 font-medium">{caseData.user_name}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Date/Time:</span>
              <span className="ml-2 font-medium">{formatDateTime(caseData.created_at)}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Case ID:</span>
              <span className="ml-2 font-medium">#{caseData.case_number}</span>
            </div>
          </div>

          {/* Images */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Layer 1 */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Layer 1 - Pre-Operation</h4>
                  {caseData.layer1_image_path && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDownloadImage(caseData.layer1_image_path, `case-${caseData.case_number}-layer1.jpg`)}
                    >
                      <Download className="w-4 h-4 mr-1" />
                      Download
                    </Button>
                  )}
                </div>
                {layer1Url ? (
                  <div className="border border-border rounded-lg overflow-hidden bg-muted/20">
                    <img
                      src={layer1Url}
                      alt="Layer 1 - Pre-Operation"
                      className="w-full h-auto object-contain max-h-80"
                    />
                  </div>
                ) : (
                  <div className="border border-border rounded-lg p-8 text-center text-muted-foreground bg-muted/20">
                    No image available
                  </div>
                )}
              </div>

              {/* Layer 2 */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Layer 2 - Post-Operation</h4>
                  {caseData.layer2_image_path && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDownloadImage(caseData.layer2_image_path, `case-${caseData.case_number}-layer2.jpg`)}
                    >
                      <Download className="w-4 h-4 mr-1" />
                      Download
                    </Button>
                  )}
                </div>
                {layer2Url ? (
                  <div className="border border-border rounded-lg overflow-hidden bg-muted/20">
                    <img
                      src={layer2Url}
                      alt="Layer 2 - Post-Operation"
                      className="w-full h-auto object-contain max-h-80"
                    />
                  </div>
                ) : (
                  <div className="border border-border rounded-lg p-8 text-center text-muted-foreground bg-muted/20">
                    No image available
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CaseDetailDialog;
