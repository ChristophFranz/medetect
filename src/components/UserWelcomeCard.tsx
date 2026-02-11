interface UserWelcomeCardProps {
  userName: string;
}

const UserWelcomeCard = ({ userName }: UserWelcomeCardProps) => {
  return (
    <div className="flex flex-col items-center justify-center gap-3 p-12 bg-card rounded-lg border border-border shadow-sm animate-slide-up flex-1 min-w-[280px]" style={{ animationDelay: "0.1s" }}>
      <span className="text-lg text-muted-foreground">Welcome</span>
      <span className="text-lg text-muted-foreground">User</span>
      <span className="text-2xl font-semibold text-foreground underline mt-3">{userName}</span>
    </div>
  );
};

export default UserWelcomeCard;
