import type { Metadata } from "next";
import Link from "next/link";
import { Brand } from "@/components/brand";
import { LoginForm } from "@/components/login-form";

export const metadata: Metadata = { title: "Sign in" };

type Props = { searchParams: Promise<{ next?: string | string[] }> };

export default async function LoginPage({ searchParams }: Props) {
  const params = await searchParams;
  const next = Array.isArray(params.next) ? params.next[0] : params.next;

  return (
    <main className="relative flex min-h-dvh items-center justify-center px-6 py-12">
      <div aria-hidden className="ruled pointer-events-none absolute inset-0" />
      <div className="rise relative w-full max-w-sm space-y-8">
        <Brand />
        <div className="rounded-xl border border-border bg-card p-6 shadow-[0_24px_60px_-30px_color-mix(in_oklch,var(--ink)_35%,transparent)] sm:p-8">
          <div className="mb-6 space-y-1">
            <p className="eyebrow text-muted-foreground">Internal</p>
            <h1 className="font-display text-2xl">Attorney sign in</h1>
          </div>
          <LoginForm next={next} />
        </div>
        <p className="text-center text-xs text-muted-foreground">
          Prospects don&apos;t need an account. Looking for the intake form? <Link href="/" className="underline underline-offset-4">Go back</Link>.
        </p>
      </div>
    </main>
  );
}
