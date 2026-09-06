"use client";

import { useId, useState } from "react";
import { Loader2 } from "lucide-react";

import { type ApiFailure, type LeadNote, addNote } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { FieldError } from "@/components/field-error";
import { cn } from "@/lib/utils";

export const NOTE_MAX_CHARS = 2000;

type Props = {
  leadId: string;
  /** Called with the note the server stored, so the parent can show it without a reload. */
  onAdded: (note: LeadNote) => void;
  /** Non-validation failures (401, 404, network) are handed to the parent. */
  onFailure: (error: ApiFailure) => void;
};

/** Append-only note on a lead. Whitespace-only text is never sent; the server trims and re-checks. */
export function NoteComposer({ leadId, onAdded, onFailure }: Props) {
  const id = useId();
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);

  const trimmed = body.trim();
  const overLimit = trimmed.length > NOTE_MAX_CHARS;
  const disabled = submitting || trimmed.length === 0 || overLimit;

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (disabled) return;
    setFieldError(null);
    setSubmitting(true);
    const result = await addNote(leadId, trimmed);
    setSubmitting(false);
    if (result.ok) {
      setBody("");
      onAdded(result.data);
      return;
    }
    if (result.error.status === 422) {
      setFieldError(result.error.fields.body ?? result.error.message);
      return;
    }
    onFailure(result.error);
  }

  return (
    <form onSubmit={submit} className="space-y-2" aria-label="Add a note">
      <label htmlFor={`${id}-body`} className="sr-only">
        Note
      </label>
      <textarea
        id={`${id}-body`}
        name="body"
        value={body}
        onChange={(e) => {
          setBody(e.target.value);
          if (fieldError) setFieldError(null);
        }}
        rows={3}
        placeholder="Add a note for the team, e.g. “Left voicemail, will retry Thursday.”"
        disabled={submitting}
        aria-invalid={!!fieldError || overLimit}
        aria-describedby={fieldError ? `${id}-body-error` : `${id}-body-count`}
        className={cn(
          "w-full min-w-0 resize-y rounded-lg border border-input bg-transparent px-2.5 py-1.5 text-base transition-colors outline-none",
          "placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50",
          "disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20",
          "md:text-sm dark:bg-input/30",
        )}
      />
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <FieldError id={`${id}-body-error`} message={fieldError ?? undefined} />
          <p id={`${id}-body-count`} className={cn("text-xs tabular-nums", overLimit ? "text-destructive" : "text-muted-foreground")}>
            {trimmed.length.toLocaleString()} / {NOTE_MAX_CHARS.toLocaleString()}
          </p>
        </div>
        <Button type="submit" size="sm" disabled={disabled}>
          {submitting && <Loader2 className="animate-spin" data-icon="inline-start" />}
          Add note
        </Button>
      </div>
    </form>
  );
}
