import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

// Fonts are shipped with the repo so `next build` never needs network access.
const display = localFont({
  src: [
    { path: "./fonts/fraunces-normal.woff2", style: "normal" },
    { path: "./fonts/fraunces-italic.woff2", style: "italic" },
  ],
  variable: "--font-display",
  display: "swap",
});

const body = localFont({
  src: [
    { path: "./fonts/instrumentsans-normal.woff2", style: "normal" },
    { path: "./fonts/instrumentsans-italic.woff2", style: "italic" },
  ],
  variable: "--font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: { default: "Alma · Immigration case assessment", template: "%s · Alma" },
  description: "Submit your details and resume to start an immigration case assessment with Alma.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body className="min-h-dvh antialiased">{children}</body>
    </html>
  );
}
