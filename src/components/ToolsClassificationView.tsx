import { useState } from "react";
import { ChevronDown, ChevronRight, ArrowLeft } from "lucide-react";
import { Button } from "./ui/button";
import { useNavigate, useSearchParams } from "react-router-dom";

interface ToolImage {
  id: number;
  url: string;
  name: string;
  capturedAt: string;
}

interface Tool {
  id: number;
  name: string;
  description: string;
  images: ToolImage[];
}

// Mock data - will be replaced with actual database data
const mockTools: Tool[] = [
  {
    id: 1,
    name: "Chop Phaco",
    description: "Phacoemulsification chopper instrument",
    images: [
      { id: 1, url: "/placeholder.svg", name: "Chop Phaco - Sample 1", capturedAt: "03/01/2024 14:23:00" },
      { id: 2, url: "/placeholder.svg", name: "Chop Phaco - Sample 2", capturedAt: "10/03/2024 09:15:00" },
      { id: 3, url: "/placeholder.svg", name: "Chop Phaco - Sample 3", capturedAt: "15/05/2024 11:30:00" },
    ],
  },
  {
    id: 2,
    name: "Forceps Macpherson",
    description: "Macpherson tying forceps for suture manipulation",
    images: [
      { id: 4, url: "/placeholder.svg", name: "Forceps Macpherson - Sample 1", capturedAt: "05/02/2024 10:45:00" },
      { id: 5, url: "/placeholder.svg", name: "Forceps Macpherson - Sample 2", capturedAt: "22/04/2024 16:20:00" },
    ],
  },
  {
    id: 3,
    name: "Forceps Utrata",
    description: "Utrata capsulorhexis forceps",
    images: [
      { id: 6, url: "/placeholder.svg", name: "Forceps Utrata - Sample 1", capturedAt: "12/01/2024 08:30:00" },
      { id: 7, url: "/placeholder.svg", name: "Forceps Utrata - Sample 2", capturedAt: "28/03/2024 13:55:00" },
      { id: 8, url: "/placeholder.svg", name: "Forceps Utrata - Sample 3", capturedAt: "19/06/2024 15:10:00" },
      { id: 9, url: "/placeholder.svg", name: "Forceps Utrata - Sample 4", capturedAt: "02/08/2024 09:40:00" },
    ],
  },
  {
    id: 4,
    name: "Hook Sinskey",
    description: "Sinskey hook for IOL manipulation",
    images: [
      { id: 10, url: "/placeholder.svg", name: "Hook Sinskey - Sample 1", capturedAt: "18/02/2024 11:15:00" },
    ],
  },
];

const ToolsClassificationView = () => {
  const [expandedTool, setExpandedTool] = useState<number | null>(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const handleToolClick = (toolId: number) => {
    setExpandedTool(expandedTool === toolId ? null : toolId);
  };

  const handleBack = () => {
    const user = searchParams.get("user");
    const name = searchParams.get("name");
    navigate(`/database?user=${user}&name=${name}`);
  };

  return (
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
        {mockTools.map((tool) => (
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
                      className="bg-card border border-border rounded-lg overflow-hidden hover:border-primary/50 transition-colors cursor-pointer"
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
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ToolsClassificationView;
