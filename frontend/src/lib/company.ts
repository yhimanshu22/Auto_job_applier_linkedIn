/**
 * Central company / legal information used across the website
 * (Contact Us, About Us, policy pages, footer).
 *
 * IMPORTANT (PayU website verification):
 * - `legalName` must exactly match the name on the PAN card.
 * - `registeredAddress` must match the Aadhar address.
 */
export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.trim() ||
  "https://frontend-pink-phi-37.vercel.app";

export const COMPANY = {
  brandName: "LinkdApply",
  legalName: "Himanshu Yadav",
  registeredAddress: "Pindari, Mohammadabad, District Ghazipur, Uttar Pradesh - 233222, India",
  email: "himu09854@gmail.com",
  phone: "+91 81142 45060",
  phoneHref: "tel:+918114245060",
  websiteUrl: SITE_URL,
  supportHours: "Monday to Friday, 9:00 AM - 6:00 PM IST",
} as const;
