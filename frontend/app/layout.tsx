import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Navigation } from "@/components/Navigation";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "AI Email Response System",
  description:
    "Production-ready AI email response system with RAG pipeline and multi-metric evaluation engine",
  keywords: ["AI", "email", "RAG", "Gemini", "evaluation", "customer service"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-zinc-950 text-zinc-100 antialiased">
        <div className="flex min-h-screen">
          <Navigation />
          <main className="flex-1 ml-64 min-h-screen">
            <div className="p-8">{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
