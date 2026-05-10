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
  metadataBase: new URL('https://linkdapply.com'),
  title: {
    default: "LinkdApply | #1 AI LinkedIn Job Application Automation Bot",
    template: "%s | LinkdApply"
  },
  description: "Automate your LinkedIn job search with LinkdApply. The most advanced, undetectable AI bot that applies to hundreds of jobs, tailors cover letters, and handles custom questions while you sleep.",
  keywords: ["LinkedIn Bot", "Job Application Automation", "AI Job Search", "Automate LinkedIn Applications", "LinkedIn Easy Apply Bot", "Job Hunting AI", "LinkdApply"],
  authors: [{ name: "LinkdApply Team" }],
  creator: "LinkdApply",
  publisher: "LinkdApply",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://linkdapply.com",
    siteName: "LinkdApply",
    title: "LinkdApply | AI-Powered LinkedIn Job Automation",
    description: "Land your dream job faster. Automate applications with the world's most human-like AI bot.",
    images: [
      {
        url: "/logo.png",
        width: 1200,
        height: 630,
        alt: "LinkdApply",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "LinkdApply | AI Job Search Automation",
    description: "Stop filling forms. Start interviewing. The #1 AI bot for LinkedIn applications.",
    images: ["/logo.png"],
    creator: "@linkdapply",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  alternates: {
    canonical: 'https://linkdapply.com',
  },
  icons: {
    icon: "/icon.png",
    apple: "/icon.png",
  },
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
