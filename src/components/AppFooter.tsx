import { useEffect, useState } from "react";

interface AppFooterProps {
  userName?: string;
}

const AppFooter = ({ userName }: AppFooterProps) => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  return (
    <footer className="w-full bg-header px-4 py-2 flex items-center justify-between rounded-b-lg">
      <span className="text-xs text-header-foreground">
        Welcome: {userName || "Guest"}
      </span>
      <span className="text-xs text-header-foreground">
        {formatTime(currentTime)} - {formatDate(currentTime)}
      </span>
    </footer>
  );
};

export default AppFooter;
