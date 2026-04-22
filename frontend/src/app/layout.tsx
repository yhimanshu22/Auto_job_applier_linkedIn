import type { Metadata } from "next";
import { Inter, EB_Garamond } from "next/font/google";
import "./globals.css";

const interSizeAdjust = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const ebGaramond = EB_Garamond({
  variable: "--font-eb-garamond",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LinkdApply - AI Superpowers for Job Seekers",
  description: "Automate your LinkedIn job applications with the most advanced AI bot.",
};

import AuthContext from "@/components/AuthContext";
import DeepLinkHandler from "@/components/DeepLinkHandler";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${interSizeAdjust.variable} ${ebGaramond.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <meta
          httpEquiv="Content-Security-Policy"
          content="default-src 'self' http://127.0.0.1:3000 http://localhost:3000; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com; connect-src 'self' http://127.0.0.1:3000 http://localhost:3000 ws://127.0.0.1:3000 ws://localhost:3000 http://127.0.0.1:8000 http://localhost:8000 https://accounts.google.com; frame-src 'self' https://accounts.google.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:;"
        />
      </head>
      <body className="min-h-full flex flex-col">
        <AuthContext>
          <DeepLinkHandler />
          {children}
        </AuthContext>
      </body>
    </html>
  );
}
