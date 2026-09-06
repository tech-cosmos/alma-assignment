import { Brand } from "@/components/brand";
import { LeadForm } from "@/components/lead-form";

const steps = [
  ["Tell us who you are", "Your name, an email we can reach, and your current resume or CV."],
  ["We review your background", "An Alma attorney reads your resume against the visa paths that fit."],
  ["We reach out", "You get a confirmation now and a personal follow-up from the attorney."],
] as const;

export default function HomePage() {
  return (
    <main className="grid min-h-dvh lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <section className="ink-panel relative flex flex-col justify-between px-6 py-8 text-ink-foreground sm:px-10 lg:px-14 lg:py-12">
        <Brand className="rise text-ink-foreground" />
        <div className="my-14 max-w-md space-y-8 lg:my-0">
          <div className="space-y-4">
            <p className="eyebrow rise rise-1 text-brass">Case assessment</p>
            <h1 className="rise rise-2 font-display text-5xl leading-[1.02] sm:text-6xl">
              Start your immigration case with a <em className="text-brass">real</em> attorney.
            </h1>
            <p className="rise rise-3 max-w-sm text-base leading-relaxed text-ink-foreground/75">
              Share a few details and your resume. We use them to match you with the right visa strategy before we ever
              get on a call.
            </p>
          </div>
          <ol className="rise rise-4 space-y-4 border-l border-ink-foreground/20 pl-5">
            {steps.map(([title, body], i) => (
              <li key={title} className="relative">
                <span className="absolute -left-[1.6rem] top-1 font-display text-xs text-brass">0{i + 1}</span>
                <p className="font-medium">{title}</p>
                <p className="text-sm text-ink-foreground/65">{body}</p>
              </li>
            ))}
          </ol>
        </div>
        <p className="rise rise-5 text-xs text-ink-foreground/50">
          Attorney–client privilege does not attach until an engagement letter is signed.
        </p>
      </section>

      <section className="relative flex items-center justify-center px-6 py-12 sm:px-10 lg:px-16">
        <div aria-hidden className="ruled pointer-events-none absolute inset-0" />
        <div className="rise rise-2 relative w-full max-w-xl rounded-xl border border-border bg-card p-6 shadow-[0_1px_0_0_color-mix(in_oklch,var(--ink)_8%,transparent),0_24px_60px_-30px_color-mix(in_oklch,var(--ink)_35%,transparent)] sm:p-9">
          <div className="mb-8 space-y-1">
            <p className="eyebrow text-muted-foreground">Intake form</p>
            <h2 className="font-display text-2xl">Your details</h2>
          </div>
          <LeadForm />
        </div>
      </section>
    </main>
  );
}
