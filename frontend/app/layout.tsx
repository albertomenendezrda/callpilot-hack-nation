import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { SessionProvider } from "@/components/providers/SessionProvider";
import { AuthApiProvider } from "@/components/providers/AuthApiProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CallPilot - Autonomous Voice AI Appointment Scheduling",
  description: "AI-powered appointment booking that calls providers, negotiates slots, and finds you the earliest appointment - all autonomously.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <SessionProvider>
          <AuthApiProvider>
            <main className="min-h-screen bg-background">
              {children}
            </main>
          </AuthApiProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
