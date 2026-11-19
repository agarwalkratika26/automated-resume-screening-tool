import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Automated Resume Screening Tool — Recruiter Dashboard",
  description: "AI-powered resume extraction, skill matching, and candidate ranking platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 antialiased selection:bg-blue-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
