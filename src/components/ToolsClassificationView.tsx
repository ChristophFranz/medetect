import { useState, useEffect } from "react";
import { ChevronDown, ChevronRight, ArrowLeft, Trash2 } from "lucide-react";
import { Button } from "./ui/button";
import { useNavigate, useSearchParams } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { toast } from "@/hooks/use-toast";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./ui/alert-dialog";

interface ToolImage {
  id: string;
  url: string;
  name: string;
  fileName: string;
  capturedAt: string;
}

interface Tool {
  id: number;
  name: string;
  folderName: string;
  description: string;
  images: ToolImage[];
}

interface DeleteTarget {
  folderName: string;
  fileName: string;
  imageName: string;
}

const toolDefinitions = [
  {
    id: 1,
    name: "Chop Phaco",
    folderName: "chop-phaco",
    description: "Phacoemulsification chopper instrument",
  },
  {
    id: 2,
    name: "Forceps Macpherson",
    folderName: "forceps-macpherson",
    description: "Macpherson tying forceps for suture manipulation",
  },
  {
    id: 3,
    name: "Forceps Utrata",
    folderName: "forceps-utrata",
    description: "Utrata capsulorhexis forceps",
  },
  {
    id: 4,
    name: "Hook Sinskey",
    folderName: "hook-sinskey",
    description: "Sinskey hook for IOL manipulation",
  },
];

const ToolsClassificationView = () => {
  const [expandedTool, setExpandedTool] = useState<number | null>(null);
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const fetchToolImages = async () => {
      const toolsWithImages: Tool[] = [];

      for (const toolDef of toolDefinitions) {
        const { data: files, error } = await supabase.storage
          .from("tool-images")
          .list(toolDef.folderName);

        if (error) {
          console.error(`Error fetching images for ${toolDef.name}:`, error);
          toolsWithImages.push({ ...toolDef, images: [] });
          continue;
        }

        const images: ToolImage[] = (files || [])
          .filter((file) => file.name !== ".emptyFolderPlaceholder")
          .map((file) => {
            const { data: urlData } = supabase.storage
              .from("tool-images")
              .getPublicUrl(`${toolDef.folderName}/${file.name}`);

            return {
              id: file.id,
              url: urlData.publicUrl,
              name: file.name.replace(/\.[^/.]+$/, ""),
              fileName: file.name,
              capturedAt: new Date(file.created_at).toLocaleString(),
            };
          });

        toolsWithImages.push({ ...toolDef, images });
      }

      setTools(toolsWithImages);
      setLoading(false);
    };

    fetchToolImages();
  }, []);

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    
    setIsDeleting(true);
    const filePath = `${deleteTarget.folderName}/${deleteTarget.fileName}`;
    
    const { error } = await supabase.storage
      .from("tool-images")
      .remove([filePath]);

    if (error) {
      toast({
        title: "Error",
        description: "Failed to delete image. Please try again.",
        variant: "destructive",
      });
      setIsDeleting(false);
      setDeleteTarget(null);
      return;
    }

    // Update local state to remove the deleted image
    setTools((prevTools) =>
      prevTools.map((tool) =>
        tool.folderName === deleteTarget.folderName
          ? { ...tool, images: tool.images.filter((img) => img.fileName !== deleteTarget.fileName) }
          : tool
      )
    );

    toast({
      title: "Image deleted",
      description: "The image has been removed successfully.",
    });
    
    setIsDeleting(false);
    setDeleteTarget(null);
  };

  const handleToolClick = (toolId: number) => {
    setExpandedTool(expandedTool === toolId ? null : toolId);
  };

  const handleBack = () => {
    const user = searchParams.get("user");
    const name = searchParams.get("name");
    navigate(`/database?user=${user}&name=${name}`);
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-muted-foreground">Loading tools...</p>
      </div>
    );
  }

  return (
    <>
      <AlertDialog open={!!deleteTarget} onOpenChange={(open) => !open && setDeleteTarget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Image</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteTarget?.imageName}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    <div className="h-full animate-fade-in">
      {/* Header with Back Button */}
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={handleBack}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Database
        </Button>
        <h2 className="text-xl font-semibold text-foreground">Tools Classification Database</h2>
      </div>

      {/* Tools List */}
      <div className="space-y-3">
        {tools.map((tool) => (
          <div
            key={tool.id}
            className="bg-card border border-border rounded-lg overflow-hidden"
          >
            {/* Tool Header */}
            <button
              onClick={() => handleToolClick(tool.id)}
              className="w-full flex items-center justify-between p-4 hover:bg-muted/30 transition-colors"
            >
              <div className="flex items-center gap-3">
                {expandedTool === tool.id ? (
                  <ChevronDown className="w-5 h-5 text-muted-foreground" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-muted-foreground" />
                )}
                <div className="text-left">
                  <h3 className="font-medium text-foreground">{tool.name}</h3>
                  <p className="text-sm text-muted-foreground">{tool.description}</p>
                </div>
              </div>
              <span className="text-sm text-muted-foreground bg-muted px-2 py-1 rounded">
                {tool.images.length} image{tool.images.length !== 1 ? "s" : ""}
              </span>
            </button>

            {/* Expanded Images */}
            {expandedTool === tool.id && (
              <div className="border-t border-border p-4 bg-muted/20">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {tool.images.map((image) => (
                    <div
                      key={image.id}
                      className="bg-card border border-border rounded-lg overflow-hidden hover:border-primary/50 transition-colors group relative"
                    >
                      <div className="aspect-square bg-muted">
                        <img
                          src={image.url}
                          alt={image.name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="p-2">
                        <p className="text-xs font-medium text-foreground truncate">
                          {image.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {image.capturedAt}
                        </p>
                      </div>
                      <Button
                        variant="destructive"
                        size="icon"
                        className="absolute top-2 right-2 h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteTarget({
                            folderName: tool.folderName,
                            fileName: image.fileName,
                            imageName: image.name,
                          });
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
    </>
  );
};

export default ToolsClassificationView;
