import { Metadata } from 'next';

export const metadata: Metadata = {
  title: "Pricing | Choose Your Automation Plan",
  description: "Flexible plans for every job seeker. From free trials to agency-scale automation, find the plan that fits your job search volume.",
};

export default function PricingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
