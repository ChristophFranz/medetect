import { useState, useEffect } from "react";
import { Search, User, Calendar, Wrench, X } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "./ui/popover";
import { Calendar as CalendarComponent } from "./ui/calendar";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { supabase } from "@/integrations/supabase/client";

interface InspectionUser {
  id: string;
  name: string;
  tags: string[];
}

interface DatabaseFiltersProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  selectedUserId: string | null;
  onUserChange: (userId: string | null) => void;
  selectedDate: Date | undefined;
  onDateChange: (date: Date | undefined) => void;
  showModifiedOnly: boolean;
  onModifiedChange: (value: boolean) => void;
  canAccessToolsClassification: boolean;
  onToolsClassificationClick: () => void;
}

const DatabaseFilters = ({
  searchQuery,
  onSearchChange,
  selectedUserId,
  onUserChange,
  selectedDate,
  onDateChange,
  canAccessToolsClassification,
  onToolsClassificationClick,
  showModifiedOnly,
  onModifiedChange,
}: DatabaseFiltersProps) => {
  const [users, setUsers] = useState<InspectionUser[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const { data, error } = await supabase.functions.invoke('get-inspection-users', {
        body: {}
      });

      if (error) {
        console.error('Error fetching users:', error);
        return;
      }

      if (data?.users) {
        setUsers(data.users);
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoadingUsers(false);
    }
  };

  const clearFilters = () => {
    onSearchChange("");
    onUserChange(null);
    onDateChange(undefined);
  };

  const hasActiveFilters = searchQuery || selectedUserId || selectedDate;

  return (
    <div className="space-y-4">
      {/* Search Input */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-muted-foreground flex items-center gap-2">
          <Search className="w-3 h-3" /> Search
        </p>
        <Input
          placeholder="Search cases..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-8 text-xs"
        />
      </div>

      {/* User Filter */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-muted-foreground flex items-center gap-2">
          <User className="w-3 h-3" /> Filter by User
        </p>
        <Select
          value={selectedUserId || "all"}
          onValueChange={(value) => onUserChange(value === "all" ? null : value)}
        >
          <SelectTrigger className="h-8 text-xs">
            <SelectValue placeholder="All Users" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Users</SelectItem>
            {users.map((user) => (
              <SelectItem key={user.id} value={user.id}>
                {user.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Date Filter */}
      <div className="space-y-2">
        <p className="text-xs font-medium text-muted-foreground flex items-center gap-2">
          <Calendar className="w-3 h-3" /> Filter by Date
        </p>
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className={cn(
                "w-full justify-start text-left text-xs h-8",
                !selectedDate && "text-muted-foreground"
              )}
            >
              {selectedDate ? format(selectedDate, "dd/MM/yyyy") : "Select date"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <CalendarComponent
              mode="single"
              selected={selectedDate}
              onSelect={onDateChange}
              initialFocus
              className={cn("p-3 pointer-events-auto")}
            />
          </PopoverContent>
        </Popover>
      </div>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          className="w-full text-xs h-8"
          onClick={clearFilters}
        >
          <X className="w-3 h-3 mr-1" />
          Clear Filters
        </Button>
      )}

      {/* Tools Classification */}
      {canAccessToolsClassification && (
        <div className="pt-4 border-t border-border mt-4">
          <p className="text-xs font-medium text-muted-foreground flex items-center gap-2 mb-2">
            <Wrench className="w-3 h-3" /> Tools
          </p>
          <Button
            variant="outline"
            size="sm"
            className="w-full justify-center text-xs h-8"
            onClick={onToolsClassificationClick}
          >
            Tools Classification
          </Button>
        </div>
      )}
    </div>
  );
};

export default DatabaseFilters;
