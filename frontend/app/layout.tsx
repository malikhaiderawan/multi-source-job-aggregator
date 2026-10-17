import type { Metadata } from "next";
import { Navbar } from "@/components/Navbar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Opportunity Gateway | Premium Job Aggregator & ATS",
  description: "Professional job discovery, regional matching engine, and application tracker.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning className="h-full antialiased bg-slate-50">
      <body suppressHydrationWarning className="min-h-full flex flex-col text-slate-900 bg-slate-50 selection:bg-blue-100 selection:text-blue-900">
        <Navbar />
        <div className="flex-1">
          {children}
        </div>
      </body>
    </html>
  );
}
