import React from "react";
import { ThemeProvider } from "@/components/layout";
import "./globals.css";

export const metadata = {
  title: "Kuyumbank",
  description: "Jewelry B2B Commerce & Trading Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased selection:bg-muted selection:text-foreground">
        <ThemeProvider defaultTheme="light">
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
