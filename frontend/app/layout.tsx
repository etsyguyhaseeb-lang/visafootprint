import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "VisaFootprint — Find what USCIS will find. Before they find it.",
  description:
    "AI-powered social media screening for U.S. visa applicants. Scan your profiles against INA §212 grounds of inadmissibility. Free 1-account scan.",
  keywords: "visa screening, social media analysis, US visa, immigration, USCIS, INA 212, visa footprint",
  icons: {
    icon: "/icon.svg",
    shortcut: "/icon.svg",
    apple: "/icon.svg",
  },
  openGraph: {
    title: "VisaFootprint — Find what USCIS will find. Before they find it.",
    description: "AI-powered social media screening for U.S. visa applicants. Free scan in under 3 minutes.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full scroll-smooth">
      <body className="min-h-full flex flex-col antialiased" suppressHydrationWarning>
        <script dangerouslySetInnerHTML={{ __html: `window.rdt=window.rdt||function(){(window.rdt.q=window.rdt.q||[]).push(arguments)};!function(d){var s=d.createElement('script');s.src='https://www.redditstatic.com/ads/v2.js';s.async=1;d.head.appendChild(s);}(document);rdt('init','a2_j6msvpujp3r0');rdt('track','PageVisit');` }} />
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
