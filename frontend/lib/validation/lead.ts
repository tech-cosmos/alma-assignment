import { z } from "zod";

/** Mirrors the backend rules in docs/PLAN.md section 5. */
export const RESUME_MAX_BYTES = 5 * 1024 * 1024;
export const RESUME_EXTENSIONS = [".pdf", ".doc", ".docx"] as const;
export const RESUME_MIME_TYPES = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
] as const;
/** Value for `<input accept>`. */
export const RESUME_ACCEPT = [...RESUME_EXTENSIONS, ...RESUME_MIME_TYPES].join(",");

function hasAllowedExtension(name: string): boolean {
  const lower = name.toLowerCase();
  return RESUME_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

function isFile(value: unknown): value is File {
  return typeof File !== "undefined" && value instanceof File;
}

export const resumeFileSchema = z
  .custom<File>(isFile, { message: "Attach your resume or CV." })
  .refine((f) => f.size > 0, { message: "That file is empty." })
  .refine((f) => f.size <= RESUME_MAX_BYTES, { message: "Resume must be 5 MB or smaller." })
  .refine(
    // Browsers sometimes report an empty MIME type; the extension check still applies, and the
    // backend validates magic bytes regardless.
    (f) => hasAllowedExtension(f.name) && (f.type === "" || (RESUME_MIME_TYPES as readonly string[]).includes(f.type)),
    { message: "Resume must be a PDF, DOC, or DOCX file." },
  );

const nameSchema = (label: string) =>
  z
    .string()
    .trim()
    .min(1, { message: `${label} is required.` })
    .max(100, { message: `${label} must be 100 characters or fewer.` });

export const leadFormSchema = z.object({
  first_name: nameSchema("First name"),
  last_name: nameSchema("Last name"),
  email: z
    .string()
    .trim()
    .min(1, { message: "Email is required." })
    .max(254, { message: "Email must be 254 characters or fewer." })
    .pipe(z.email({ message: "Enter a valid email address." })),
  resume: resumeFileSchema,
});

export type LeadFormValues = z.infer<typeof leadFormSchema>;

export const loginFormSchema = z.object({
  email: z.string().trim().min(1, { message: "Email is required." }).pipe(z.email({ message: "Enter a valid email address." })),
  password: z.string().min(1, { message: "Password is required." }),
});

export type LoginFormValues = z.infer<typeof loginFormSchema>;

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
