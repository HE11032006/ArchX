import { Footer } from "@/shared/components/footer";
import { Navbar } from "@/shared/components/navbar";

interface AppShellProps {
  children: React.ReactNode;
  showBack?: boolean;
}

export function AppShell({ children, showBack = false }: AppShellProps) {
  return (
    <div className="mesh-gradient relative flex min-h-screen flex-col overflow-hidden">
      <div className="geometric-pattern pointer-events-none absolute inset-0" />
      <div className="scanline" />

      <div
        className="floating absolute top-20 left-10 h-32 w-32 border-2 blur-sm"
        style={{ borderColor: "rgba(0,245,255,0.15)", borderRadius: "50%" }}
      />
      <div
        className="floating-delay absolute right-10 bottom-20 h-48 w-48 border-2 blur-sm"
        style={{
          borderColor: "rgba(255,0,255,0.12)",
          clipPath: "polygon(50% 0%, 0% 100%, 100% 100%)",
        }}
      />
      <div
        className="pointer-events-none absolute top-1/2 left-1/4 h-64 w-px opacity-30"
        style={{
          background: "linear-gradient(to bottom, transparent, var(--neon-cyan), transparent)",
        }}
      />
      <div
        className="pointer-events-none absolute top-1/3 right-1/4 h-64 w-px opacity-30"
        style={{
          background: "linear-gradient(to bottom, transparent, var(--neon-magenta), transparent)",
        }}
      />

      <Navbar showBack={showBack} />
      <main className="relative z-10 flex-1">{children}</main>
      <Footer />
    </div>
  );
}
