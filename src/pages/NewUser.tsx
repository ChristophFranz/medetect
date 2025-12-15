import { useSearchParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import AppLayout from "@/components/AppLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { UserPlus } from "lucide-react";

type UserTag = "medetect_team" | "nurses" | "administrator";

const NewUser = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [userName, setUserName] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);

  // Form state
  const [nfcTagId, setNfcTagId] = useState("");
  const [newUserName, setNewUserName] = useState("");
  const [role, setRole] = useState("");
  const [selectedTags, setSelectedTags] = useState<UserTag[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!nfcTagId.trim() || !newUserName.trim()) {
      toast.error("Please fill in NFC Tag ID and Name");
      return;
    }

    if (selectedTags.length === 0) {
      toast.error("Please select at least one tag");
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
        if (error.code === "23505") {
          toast.error("A user with this NFC Tag ID already exists");
        } else {
          toast.error("Failed to create user: " + error.message);
        }
        return;
      }

      toast.success("User created successfully");
      setNfcTagId("");
      setNewUserName("");
      setRole("");
      setSelectedTags([]);
    } catch (err) {
      toast.error("An unexpected error occurred");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading || !userId) {
    return null;
  }

  if (!hasAccess) {
    return (
      <AppLayout
        showNavigation={true}
        activeTab="database"
        onLogout={handleLogout}
        userName={userName}
        showFooter={true}
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
      showFooter={true}
    >
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
