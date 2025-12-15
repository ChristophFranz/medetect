const DatabaseView = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[300px] animate-fade-in">
      <div className="text-center p-8 bg-card rounded-lg border border-border">
        <h2 className="text-xl font-semibold text-foreground mb-2">Inspection Database</h2>
        <p className="text-muted-foreground">Past inspection records will appear here</p>
      </div>
    </div>
  );
};

export default DatabaseView;
