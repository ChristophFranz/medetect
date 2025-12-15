import { useSearchParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import AppLayout from "@/components/AppLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { UserPlus, CheckCircle, XCircle, X, ArrowLeft } from "lucide-react";

type UserTag = "medetect_team" | "nurses" | "administrator";

interface ResultPopup {
  show: boolean;
  success: boolean;
  nfcTagId: string;
  name: string;
  tags: UserTag[];
  errorMessage?: string;
}

const tagLabels: Record<UserTag, string> = {
  nurses: "Nurses",
  administrator: "Administrator",
  medetect_team: "Medetect Team",
};

const NewUser = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [userName, setUserName] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [userTags, setUserTags] = useState<UserTag[]>([]);
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);

  // Form state
  const [nfcTagId, setNfcTagId] = useState("");
  const [newUserName, setNewUserName] = useState("");
  const [role, setRole] = useState("");
  const [selectedTags, setSelectedTags] = useState<UserTag[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Result popup state
  const [resultPopup, setResultPopup] = useState<ResultPopup>({
    show: false,
    success: false,
    nfcTagId: "",
    name: "",
    tags: [],
  });

  useEffect(() => {
    const user = searchParams.get("user");
    const name = searchParams.get("name");
    
    if (!user || !name) {
      navigate("/");
      return;
    }
    
    setUserId(user);
    setUserName(decodeURIComponent(name));
  }, [searchParams, navigate]);

  useEffect(() => {
    const checkAccess = async () => {
      if (!userId) return;
      
      const { data } = await supabase
        .from("users")
        .select("tags")
        .eq("id", userId)
        .maybeSingle();
      
      if (data?.tags) {
        const tags = data.tags as UserTag[];
        setUserTags(tags);
        const canAccess = tags.includes("administrator") || tags.includes("medetect_team");
        setHasAccess(canAccess);
      }
      setLoading(false);
    };

    checkAccess();
  }, [userId]);

  const handleLogout = () => {
    navigate("/login");
  };

  const handleTagToggle = (tag: UserTag) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const closePopup = () => {
    setResultPopup(prev => ({ ...prev, show: false }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!nfcTagId.trim() || !newUserName.trim()) {
      setResultPopup({
        show: true,
        success: false,
        nfcTagId: nfcTagId.trim(),
        name: newUserName.trim(),
        tags: selectedTags,
        errorMessage: "Please fill in NFC Tag ID and Name",
      });
      return;
    }

    if (selectedTags.length === 0) {
      setResultPopup({
        show: true,
        success: false,
        nfcTagId: nfcTagId.trim(),
        name: newUserName.trim(),
        tags: [],
        errorMessage: "Please select at least one tag",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const { error } = await supabase
        .from("users")
        .insert({
          nfc_tag_id: nfcTagId.trim(),
          name: newUserName.trim(),
          role: role.trim() || null,
          tags: selectedTags,
        });

      if (error) {
        let errorMessage = "Failed to create user";
        if (error.code === "23505") {
          errorMessage = "A user with this NFC Tag ID already exists";
        } else {
          errorMessage = error.message;
        }
        
        setResultPopup({
          show: true,
          success: false,
          nfcTagId: nfcTagId.trim(),
          name: newUserName.trim(),
          tags: selectedTags,
          errorMessage,
        });
        return;
      }

      setResultPopup({
        show: true,
        success: true,
        nfcTagId: nfcTagId.trim(),
        name: newUserName.trim(),
        tags: selectedTags,
      });

      // Clear form on success
      setNfcTagId("");
      setNewUserName("");
      setRole("");
      setSelectedTags([]);
    } catch (err) {
      setResultPopup({
        show: true,
        success: false,
        nfcTagId: nfcTagId.trim(),
        name: newUserName.trim(),
        tags: selectedTags,
        errorMessage: "An unexpected error occurred",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading || !userId) {
    return null;
  }

  const backToDatabase = `/database?user=${userId}&name=${encodeURIComponent(userName)}`;

  if (!hasAccess) {
    return (
      <AppLayout
        showNavigation={true}
        activeTab="database"
        onLogout={handleLogout}
        userName={userName}
        userId={userId}
        userTags={userTags}
        showFooter={true}
        showBack={true}
        backTo={backToDatabase}
      >
        <div className="flex items-center justify-center h-full">
          <p className="text-muted-foreground">Access denied. Administrator privileges required.</p>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout
      showNavigation={true}
      activeTab="database"
      onLogout={handleLogout}
      userName={userName}
      userId={userId}
      userTags={userTags}
      showFooter={true}
      showBack={true}
      backTo={backToDatabase}
    >
      {/* Result Popup Overlay */}
      {resultPopup.show && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div 
            className="absolute inset-0 bg-background/60 backdrop-blur-sm"
            onClick={closePopup}
          />
          <div 
            className={`relative z-10 w-full max-w-sm rounded-lg border-2 p-6 shadow-xl backdrop-blur-md transition-all ${
              resultPopup.success 
                ? "bg-green-500/20 border-green-500/50" 
                : "bg-red-500/20 border-red-500/50"
            }`}
          >
            <button
              onClick={closePopup}
              className="absolute top-3 right-3 text-foreground/70 hover:text-foreground transition-colors"
            >
              <X size={20} />
            </button>
            
            <div className="flex flex-col items-center gap-4">
              {resultPopup.success ? (
                <CheckCircle className="w-16 h-16 text-green-500" />
              ) : (
                <XCircle className="w-16 h-16 text-red-500" />
              )}
              
              <h2 className={`text-xl font-semibold ${
                resultPopup.success ? "text-green-400" : "text-red-400"
              }`}>
                {resultPopup.success ? "User Created Successfully" : "User Creation Failed"}
              </h2>

              {resultPopup.errorMessage && (
                <p className="text-red-300 text-sm text-center">
                  {resultPopup.errorMessage}
                </p>
              )}

              <div className="w-full space-y-2 mt-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">NFC Tag ID:</span>
                  <span className="font-medium text-foreground">
                    {resultPopup.nfcTagId || "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Name:</span>
                  <span className="font-medium text-foreground">
                    {resultPopup.name || "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tags:</span>
                  <span className="font-medium text-foreground">
                    {resultPopup.tags.length > 0 
                      ? resultPopup.tags.map(t => tagLabels[t]).join(", ")
                      : "—"
                    }
                  </span>
                </div>
              </div>

              <div className="flex gap-2 mt-4 w-full">
                <Button 
                  onClick={() => navigate(backToDatabase)} 
                  variant="outline"
                  className="flex-1"
                >
                  <ArrowLeft size={14} className="mr-1" />
                  Back
                </Button>
                <Button 
                  onClick={closePopup} 
                  className="flex-1"
                  variant={resultPopup.success ? "default" : "outline"}
                >
                  {resultPopup.success ? "Create Another" : "Try Again"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col items-center justify-center gap-8 animate-fade-in max-w-md mx-auto">
        <div className="text-center">
          <UserPlus className="w-12 h-12 mx-auto mb-4 text-accent" />
          <h1 className="text-2xl font-semibold text-foreground mb-2">
            New User Creation
          </h1>
          <p className="text-muted-foreground">Create a new user account</p>
        </div>

        <form onSubmit={handleSubmit} className="w-full space-y-6 bg-card border border-border rounded-lg p-6">
          <div className="space-y-2">
            <Label htmlFor="nfcTagId">NFC Tag ID *</Label>
            <Input
              id="nfcTagId"
              value={nfcTagId}
              onChange={(e) => setNfcTagId(e.target.value)}
              placeholder="Scan NFC Tag ID"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={newUserName}
              onChange={(e) => setNewUserName(e.target.value)}
              placeholder="Enter user name"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="role">Role (Optional)</Label>
            <Input
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="Enter role (e.g., Senior Nurse)"
            />
          </div>

          <div className="space-y-3">
            <Label>Tags *</Label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="nurses"
                  checked={selectedTags.includes("nurses")}
                  onCheckedChange={() => handleTagToggle("nurses")}
                />
                <Label htmlFor="nurses" className="font-normal cursor-pointer">
                  Nurses - Inspection & Database access
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="administrator"
                  checked={selectedTags.includes("administrator")}
                  onCheckedChange={() => handleTagToggle("administrator")}
                />
                <Label htmlFor="administrator" className="font-normal cursor-pointer">
                  Administrator - Database & Hidden Database access
                </Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="medetect_team"
                  checked={selectedTags.includes("medetect_team")}
                  onCheckedChange={() => handleTagToggle("medetect_team")}
                />
                <Label htmlFor="medetect_team" className="font-normal cursor-pointer">
                  Medetect Team - Full access to all functions
                </Label>
              </div>
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Create User"}
          </Button>
        </form>
      </div>
    </AppLayout>
  );
};

export default NewUser;
