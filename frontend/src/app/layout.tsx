import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "RAGentic — Agentic RAG",
  description:
    "Ask questions about your documents. RAGentic retrieves the most relevant context using hybrid dense+sparse retrieval and cites its sources.",
  keywords: ["RAG", "retrieval augmented generation", "document QA", "AI"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased">{children}</body>
    </html>
  );
}
