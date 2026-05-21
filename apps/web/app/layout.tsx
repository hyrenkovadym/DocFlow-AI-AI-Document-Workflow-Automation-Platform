import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "DocFlow AI",
  description: "AI-powered document intake and workflow automation platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
