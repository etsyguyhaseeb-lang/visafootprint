import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "VisaScreenAI – Social Media Screening for US Visa Applicants",
  description:
    "AI-powered social media risk analysis for US visa applicants. Know your risk before your visa interview. Get a comprehensive PDF screening report in minutes.",
  keywords: "visa screening, social media analysis, US visa, immigration, AI screening",
  openGraph: {
    title: "VisaScreenAI – Know Your Risk Before Your Visa Interview",
    description: "AI-powered social media screening for US visa applicants.",
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
        <Navbar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
