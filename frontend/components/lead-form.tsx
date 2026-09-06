"use client";

import { useId, useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { FileText, Loader2, Paperclip, X } from "lucide-react";

import { createLead, type Lead } from "@/lib/api";
import { RESUME_ACCEPT, formatBytes, leadFormSchema, type LeadFormValues } from "@/lib/validation/lead";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FieldError } from "@/components/field-error";
import { cn } from "@/lib/utils";

type Props = {
  onSubmitted?: (lead: Lead) => void;
};

export function LeadForm({ onSubmitted }: Props) {
  const id = useId();
  const [submitted, setSubmitted] = useState<Lead | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const form = useForm<LeadFormValues>({
    resolver: zodResolver(leadFormSchema),
    mode: "onTouched",
    defaultValues: { first_name: "", last_name: "", email: "" },
  });
  const { register, handleSubmit, control, setError, formState, reset } = form;
  const { errors, isSubmitting } = formState;

  const onSubmit = handleSubmit(async (values) => {
    setFormError(null);
    const result = await createLead(values);
    if (result.ok) {
      setSubmitted(result.data);
      onSubmitted?.(result.data);
      return;
    }
    const { error } = result;
    let placed = false;
    for (const [field, message] of Object.entries(error.fields)) {
      if (field in values) {
        setError(field as keyof LeadFormValues, { type: "server", message });
        placed = true;
      }
    }
    // A 400/413 from the resume validator arrives as a string detail; pin it to the file field.
    if (!placed && (error.status === 400 || error.status === 413)) {
      setError("resume", { type: "server", message: error.message });
      placed = true;
    }
    if (!placed) setFormError(error.message);
  });

  if (submitted) {
    return (
      <SuccessState
        lead={submitted}
        onReset={() => {
          reset();
          setSubmitted(null);
        }}
      />
    );
  }

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-6" aria-describedby={formError ? `${id}-form-error` : undefined}>
      {formError && (
        <Alert variant="destructive" id={`${id}-form-error`} className="rise">
          <AlertTitle>We couldn&apos;t submit your details</AlertTitle>
          <AlertDescription>{formError}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-5 sm:grid-cols-2">
        <Field id={`${id}-first`} label="First name" error={errors.first_name?.message}>
          <Input
            id={`${id}-first`}
            autoComplete="given-name"
            placeholder="Priya"
            aria-invalid={!!errors.first_name}
            aria-describedby={errors.first_name ? `${id}-first-error` : undefined}
            {...register("first_name")}
          />
        </Field>
        <Field id={`${id}-last`} label="Last name" error={errors.last_name?.message}>
          <Input
            id={`${id}-last`}
            autoComplete="family-name"
            placeholder="Natarajan"
            aria-invalid={!!errors.last_name}
            aria-describedby={errors.last_name ? `${id}-last-error` : undefined}
            {...register("last_name")}
          />
        </Field>
      </div>

      <Field id={`${id}-email`} label="Email" error={errors.email?.message} hint="We send a confirmation here.">
        <Input
          id={`${id}-email`}
          type="email"
          inputMode="email"
          autoComplete="email"
          placeholder="you@example.com"
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? `${id}-email-error` : undefined}
          {...register("email")}
        />
      </Field>

      <Controller
        control={control}
        name="resume"
        render={({ field, fieldState }) => (
          <Field id={`${id}-resume`} label="Resume or CV" error={fieldState.error?.message} hint="PDF, DOC, or DOCX up to 5 MB.">
            <FilePicker
              id={`${id}-resume`}
              file={field.value}
              invalid={!!fieldState.error}
              describedBy={fieldState.error ? `${id}-resume-error` : undefined}
              onChange={(f) => {
                field.onChange(f);
                field.onBlur();
              }}
            />
          </Field>
        )}
      />

      <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="max-w-xs text-xs leading-relaxed text-muted-foreground">
          By submitting you agree that an Alma attorney may contact you about your case.
        </p>
        <Button type="submit" size="lg" disabled={isSubmitting} className="min-w-40">
          {isSubmitting ? (
            <>
              <Loader2 className="animate-spin" data-icon="inline-start" /> Sending
            </>
          ) : (
            "Submit for review"
          )}
        </Button>
      </div>
    </form>
  );
}

function Field({
  id,
  label,
  hint,
  error,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-3">
        <Label htmlFor={id} className="eyebrow text-foreground/80">
          {label}
        </Label>
        {hint && !error && <span className="text-[0.7rem] text-muted-foreground">{hint}</span>}
      </div>
      {children}
      <FieldError id={`${id}-error`} message={error} />
    </div>
  );
}

function FilePicker({
  id,
  file,
  invalid,
  describedBy,
  onChange,
}: {
  id: string;
  file: File | undefined;
  invalid: boolean;
  describedBy?: string;
  onChange: (file: File | undefined) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const pick = (list: FileList | null) => {
    onChange(list && list.length > 0 ? list[0] : undefined);
  };

  return (
    <div
      className={cn(
        "group relative flex min-h-24 items-center gap-3 rounded-lg border border-dashed border-input bg-card/60 px-4 py-3 transition-colors",
        "focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/40",
        dragging && "border-brass bg-brass/10",
        invalid && "border-destructive ring-3 ring-destructive/20",
      )}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        pick(e.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        id={id}
        type="file"
        accept={RESUME_ACCEPT}
        aria-invalid={invalid}
        aria-describedby={describedBy}
        className="absolute inset-0 cursor-pointer opacity-0"
        onChange={(e) => pick(e.target.files)}
      />
      {file ? (
        <>
          <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-ink text-ink-foreground">
            <FileText className="size-5" />
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-medium">{file.name}</span>
            <span className="block text-xs text-muted-foreground">{formatBytes(file.size)}</span>
          </span>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="relative z-10"
            aria-label="Remove file"
            onClick={() => {
              if (inputRef.current) inputRef.current.value = "";
              onChange(undefined);
            }}
          >
            <X />
          </Button>
        </>
      ) : (
        <>
          <span className="flex size-10 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground transition-colors group-hover:bg-brass/20 group-hover:text-brass-foreground">
            <Paperclip className="size-5" />
          </span>
          <span className="text-sm">
            <span className="font-medium">Choose a file</span>
            <span className="text-muted-foreground"> or drag it here</span>
          </span>
        </>
      )}
    </div>
  );
}

function SuccessState({ lead, onReset }: { lead: Lead; onReset: () => void }) {
  return (
    <div className="relative space-y-6" role="status" aria-live="polite">
      <span
        aria-hidden
        className="stamp absolute -top-4 right-0 rounded-sm border-2 border-success px-3 py-1 font-display text-sm font-semibold uppercase tracking-[0.2em] text-success"
      >
        Received
      </span>
      <div className="space-y-3 pt-6">
        <h2 className="font-display text-3xl leading-tight">
          Thank you, <em className="text-ink">{lead.first_name}</em>.
        </h2>
        <p className="max-w-md text-base leading-relaxed text-muted-foreground">
          We have your resume and sent a confirmation to <span className="font-medium text-foreground">{lead.email}</span>. An
          attorney will review your case and reach out.
        </p>
      </div>
      <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 border-t border-border pt-5 text-sm">
        <dt className="eyebrow text-muted-foreground">Name</dt>
        <dd>
          {lead.first_name} {lead.last_name}
        </dd>
        <dt className="eyebrow text-muted-foreground">Resume</dt>
        <dd className="truncate">{lead.resume_name}</dd>
        <dt className="eyebrow text-muted-foreground">Reference</dt>
        <dd className="font-mono text-xs text-muted-foreground">{lead.id}</dd>
      </dl>
      <Button type="button" variant="outline" onClick={onReset}>
        Submit another
      </Button>
    </div>
  );
}
