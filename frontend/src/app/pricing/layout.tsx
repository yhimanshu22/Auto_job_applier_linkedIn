import { Metadata } from 'next';

export const metadata: Metadata = {
  title: "Pricing & Plans | Affordable AI LinkedIn Job Application Bot",
  description: "Explore LinkdApply pricing. Flexible and affordable plans for automated LinkedIn Easy Apply applications, AI cover letters, and custom question answers.",
};

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
