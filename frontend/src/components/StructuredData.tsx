import React from 'react';
import { WINDOWS_INSTALLER_URL } from '@/lib/downloads';

export default function StructuredData() {
  const softwareSchema = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "LinkdApply",
    "operatingSystem": "Windows, MacOS",
    "downloadUrl": WINDOWS_INSTALLER_URL,
    "applicationCategory": "BusinessApplication",
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

  const organizationSchema = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "LinkdApply",
    "url": "https://linkdapply.com",
    "logo": "https://linkdapply.com/logo.png",
    "image": "https://linkdapply.com/logo.png",
    "sameAs": [
      "https://twitter.com/linkdapply",
      "https://linkedin.com/company/linkdapply"
    ]
  };

  const faqSchema = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "Is LinkdApply safe to use?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Yes. LinkdApply mimics human behavior with randomized delays and natural movement, making it undetectable by LinkedIn's anti-bot systems."
        }
      },
      {
        "@type": "Question",
        "name": "How many jobs can I apply to per day?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "We recommend a limit of 50-100 applications per day to maintain account health, though the bot can handle more if configured."
        }
      }
    ]
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(softwareSchema) }}
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
