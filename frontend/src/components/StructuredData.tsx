import React from 'react';
import { SITE_URL } from '@/lib/company';
import { LANDING_FAQS } from '@/lib/faq';
import { DEFAULT_WINDOWS_INSTALLER_URL, DESKTOP_VERSION, getDesktopDownloadUrl } from '@/lib/install';

export default function StructuredData() {
  const softwareSchema = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "LinkdApply",
    "operatingSystem": "Windows 10+, macOS (Apple Silicon), Linux",
    "downloadUrl": [
      DEFAULT_WINDOWS_INSTALLER_URL,
      getDesktopDownloadUrl("mac"),
      getDesktopDownloadUrl("linux"),
    ],
    "installUrl": DEFAULT_WINDOWS_INSTALLER_URL,
    "softwareVersion": DESKTOP_VERSION,
    "applicationCategory": "BusinessApplication",
    "applicationSubCategory": "Job Search Assistant",
    "featureList": "Automatic LinkedIn applications, AI-powered question answering, human-like activity simulation, cover letter customization, multi-account dashboard support",
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.9",
      "ratingCount": "1240"
    },
    "offers": {
      "@type": "Offer",
      "price": "19.00",
      "priceCurrency": "USD"
    }
  };

  const websiteSchema = {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "LinkdApply",
    "url": SITE_URL,
  };

  const navigationSchema = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "itemListElement": [
      {
        "@type": "SiteNavigationElement",
        "position": 1,
        "name": "Pricing",
        "url": `${SITE_URL}/pricing`
      },
      {
        "@type": "SiteNavigationElement",
        "position": 2,
        "name": "About Us",
        "url": `${SITE_URL}/about`
      },
      {
        "@type": "SiteNavigationElement",
        "position": 3,
        "name": "Contact Support",
        "url": `${SITE_URL}/contact`
      },
      {
        "@type": "SiteNavigationElement",
        "position": 4,
        "name": "Community Forum",
        "url": `${SITE_URL}/community`
      }
    ]
  };

  const organizationSchema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "LinkdApply",
    "url": SITE_URL,
    "sameAs": [
      "https://twitter.com/linkdapply",
      "https://linkedin.com/company/linkdapply"
    ]
  };

  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": LANDING_FAQS.map((item) => ({
      "@type": "Question",
      "name": item.q,
      "acceptedAnswer": {
        "@type": "Answer",
        "text": item.a,
      },
    })),
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(navigationSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationSchema) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqSchema) }}
      />
    </>
  );
}
