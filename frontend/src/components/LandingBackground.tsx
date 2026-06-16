type LandingBackgroundProps = {
  variant?: "default" | "hero";
};

export default function LandingBackground({ variant = "default" }: LandingBackgroundProps) {
  return (
    <>
      <div className="absolute top-0 left-0 w-full h-full grid-pattern pointer-events-none z-0 opacity-40" />
      <div className="absolute top-0 left-0 w-full h-full noise-texture pointer-events-none z-0" />
      <div
        className={[
          "absolute top-0 left-0 w-full natural-glow pointer-events-none z-0",
          variant === "hero" ? "h-[1000px]" : "h-[800px]",
        ].join(" ")}
      />
      <div
        className={[
          "absolute top-0 left-1/2 -translate-x-1/2 w-full hero-gradient opacity-15 pointer-events-none z-0",
          variant === "hero" ? "h-[1000px]" : "h-[800px]",
        ].join(" ")}
      />
      {variant === "hero" ? (
        <>
          <div className="absolute top-[1500px] left-0 w-full h-[1000px] natural-glow opacity-50 pointer-events-none z-0 rotate-180" />
          <div className="absolute top-[2000px] right-0 w-[800px] h-[800px] hero-gradient opacity-10 pointer-events-none z-0 blur-[120px]" />
          <div className="absolute bottom-0 left-0 w-full h-[1000px] natural-glow opacity-30 pointer-events-none z-0" />
        </>
      ) : null}
    </>
  );
}
