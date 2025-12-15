interface UserWelcomeCardProps {
  userName: string;
}

const UserWelcomeCard = ({ userName }: UserWelcomeCardProps) => {
  return (
    <div className="flex flex-col items-center justify-center gap-2 p-8 bg-card rounded-lg border border-border shadow-sm animate-slide-up" style={{ animationDelay: "0.1s" }}>
      <span className="text-base text-muted-foreground">Welcome</span>
      <span className="text-base text-muted-foreground">User</span>
      <span className="text-lg font-semibold text-foreground underline mt-2">{userName}</span>
    </div>
  );
};

export default UserWelcomeCard;
