import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Primitives Playground",
  description: "Learn core AI application primitives through interactive examples",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header className="border-b bg-background">
          <div className="mx-auto flex h-14 max-w-5xl items-center gap-6 px-4">
            <Link href="/" className="font-semibold">
              AI Playground
            </Link>
            <nav className="flex gap-4 text-sm">
              <Link href="/brief-parser" className="text-muted-foreground hover:text-foreground transition-colors">
                Brief Parser
              </Link>
              <Link href="/form-assistant" className="text-muted-foreground hover:text-foreground transition-colors">
                Form Assistant
              </Link>
              <Link href="/tool-playground" className="text-muted-foreground hover:text-foreground transition-colors">
                Tool Playground
              </Link>
              <Link href="/document-qa" className="text-muted-foreground hover:text-foreground transition-colors">
                Document QA
              </Link>
            </nav>
          </div>
        </header>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
