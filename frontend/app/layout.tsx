import type { Metadata } from "next";
import Script from "next/script";
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
        <Script
          id="reddit-pixel"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `!function(w,d){if(!w.rdt){var p=w.rdt=function(){p.sendEvent?p.sendEvent.apply(p,arguments):p.callQueue.push(arguments)};p.callQueue=[];var t=d.createElement("script");t.src="https://www.redditstatic.com/ads/v2.js",t.async=!0;var s=d.getElementsByTagName("script")[0];s.parentNode.insertBefore(t,s)}}(window,document);rdt('init','a2_j6msvpujp3r0');rdt('track','PageVisit');`
          }}
        />
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
