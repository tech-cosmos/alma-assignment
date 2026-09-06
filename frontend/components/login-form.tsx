"use client";

import { useId, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";

import { login } from "@/lib/api";
import { loginFormSchema, type LoginFormValues } from "@/lib/validation/lead";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { FieldError } from "@/components/field-error";

/** Only allow same-origin relative paths as a post-login destination. */
function safeNext(next: string | undefined): string {
  if (!next || !next.startsWith("/") || next.startsWith("//")) return "/leads";
  return next;
}

export function LoginForm({ next }: { next?: string }) {
  const id = useId();
  const router = useRouter();
  const [formError, setFormError] = useState<string | null>(null);
  const { register, handleSubmit, setError, formState } = useForm<LoginFormValues>({
    resolver: zodResolver(loginFormSchema),
    defaultValues: { email: "", password: "" },
  });
  const { errors, isSubmitting, isSubmitSuccessful } = formState;

  const onSubmit = handleSubmit(async ({ email, password }) => {
    setFormError(null);
    const result = await login(email, password);
    if (result.ok) {
      router.replace(safeNext(next));
      router.refresh();
      return;
    }
    const { error } = result;
    if (error.status === 401) {
      setFormError("Incorrect email or password.");
      return;
    }
    let placed = false;
    for (const [field, message] of Object.entries(error.fields)) {
      if (field === "email" || field === "password") {
        setError(field, { type: "server", message });
        placed = true;
      }
    }
    if (!placed) setFormError(error.message);
  });

  const busy = isSubmitting || (isSubmitSuccessful && !formError);

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-5">
      {formError && (
        <Alert variant="destructive" className="rise">
          <AlertDescription>{formError}</AlertDescription>
        </Alert>
      )}
      <div className="space-y-1.5">
        <Label htmlFor={`${id}-email`} className="eyebrow text-foreground/80">
          Email
        </Label>
        <Input
          id={`${id}-email`}
          type="email"
          autoComplete="username"
          placeholder="attorney@example.com"
          aria-invalid={!!errors.email}
          aria-describedby={errors.email ? `${id}-email-error` : undefined}
          {...register("email")}
        />
        <FieldError id={`${id}-email-error`} message={errors.email?.message} />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor={`${id}-password`} className="eyebrow text-foreground/80">
          Password
        </Label>
        <Input
          id={`${id}-password`}
          type="password"
          autoComplete="current-password"
          aria-invalid={!!errors.password}
          aria-describedby={errors.password ? `${id}-password-error` : undefined}
          {...register("password")}
        />
        <FieldError id={`${id}-password-error`} message={errors.password?.message} />
      </div>
      <Button type="submit" size="lg" className="w-full" disabled={busy}>
        {busy ? (
          <>
            <Loader2 className="animate-spin" data-icon="inline-start" /> Signing in
          </>
        ) : (
          "Sign in"
        )}
      </Button>
    </form>
  );
}
