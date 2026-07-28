import { ThemeToggle } from "@/components/theme-toggle";
import { LanguageToggle } from "@/components/language-toggle";

export function AppHeader() {
  return (
    <header className="border-b border-foreground/10">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-4 lg:px-12">
        <a href="/" className="flex items-center gap-2">
          <span className="font-display text-xl">CLI MARKET</span>
          <span className="font-mono text-xs text-muted-foreground">PIT</span>
        </a>
        <div className="flex items-center gap-3">
          <LanguageToggle />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
