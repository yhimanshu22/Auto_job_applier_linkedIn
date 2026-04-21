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
      <body className="min-h-full flex flex-col">
        <AuthContext>
          <DeepLinkHandler />
          {children}
        </AuthContext>
      </body>
    </html>
  );
}
