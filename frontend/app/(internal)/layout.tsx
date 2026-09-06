import { Brand } from "@/components/brand";
import { LogoutButton } from "@/components/logout-button";

export default function InternalLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-20 border-b border-border bg-paper/85 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <Brand href="/leads" />
            <span className="eyebrow rounded-sm bg-ink px-1.5 py-0.5 text-[0.6rem] text-ink-foreground">Internal</span>
          </div>
          <LogoutButton />
        </div>
      </header>
      <div className="mx-auto w-full max-w-7xl flex-1 px-6 py-8">{children}</div>
    </div>
  );
}
