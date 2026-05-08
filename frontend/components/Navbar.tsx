"use client";
import Link from "next/link";
import { useState } from "react";
import { Menu, X } from "lucide-react";

const links = [
  { href: "/#how",     label: "How it works" },
  { href: "/#why",     label: "Why us" },
  { href: "/#pricing", label: "Pricing" },
  { href: "/#faq",     label: "FAQ" },
];

const BrandMark = () => (
  <span style={{
    width: 34, height: 34,
    display: "grid", placeItems: "center",
    background: "var(--ink)",
    borderRadius: "50%",
    flexShrink: 0,
  }}>
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path d="M9 21c-1.5 0-2.5-1-2.5-2.5 0-1.2.6-2.3 1.4-3.5.9-1.4 1.6-2.5 1.6-4.5 0-3.5 1.5-6 4-6 2 0 3.5 1.8 3.5 4.5 0 2.5-1 4-2 5.5-1 1.5-2 2.8-2 4.5 0 1.3-1 2-2 2H9z" fill="#F5F1E8"/>
      <circle cx="6" cy="6" r="1.4" fill="#F5F1E8"/>
      <circle cx="9" cy="3.5" r="1.2" fill="#F5F1E8"/>
      <circle cx="13" cy="2.8" r="1.1" fill="#F5F1E8"/>
      <circle cx="17" cy="3.8" r="1" fill="#F5F1E8"/>
    </svg>
  </span>
);

export default function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav style={{
      position: "sticky", top: 0, zIndex: 50,
      background: "rgba(245, 241, 232, 0.92)",
      backdropFilter: "blur(12px)",
      borderBottom: "1px solid rgba(14, 23, 38, 0.08)",
    }}>
      <div style={{ maxWidth: 1280, margin: "0 auto", padding: "18px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Link href="/" style={{ display: "flex", alignItems: "center", gap: 12, fontFamily: "'Fraunces', serif", fontWeight: 600, fontSize: 22, letterSpacing: "-0.01em", color: "var(--ink)", textDecoration: "none" }}>
          <BrandMark />
          VisaFootprint
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex" style={{ gap: 28, alignItems: "center" }}>
          {links.map((l) => (
            <Link key={l.href} href={l.href} style={{ color: "var(--ink)", textDecoration: "none", fontSize: 14, fontWeight: 500, transition: "color 0.2s" }}
              onMouseEnter={e => (e.currentTarget.style.color = "var(--oxblood)")}
              onMouseLeave={e => (e.currentTarget.style.color = "var(--ink)")}>
              {l.label}
            </Link>
          ))}
        </div>

        {/* Desktop CTA */}
        <div className="hidden md:flex">
          <Link href="/screen" style={{
            padding: "10px 20px",
            background: "var(--ink)",
            color: "var(--paper)",
            borderRadius: 999,
            fontSize: 14,
            fontWeight: 600,
            textDecoration: "none",
            transition: "background 0.2s",
          }}
            onMouseEnter={e => (e.currentTarget.style.background = "var(--oxblood)")}
            onMouseLeave={e => (e.currentTarget.style.background = "var(--ink)")}>
            Run a scan →
          </Link>
        </div>

        {/* Mobile toggle */}
        <button className="md:hidden" onClick={() => setMobileOpen(v => !v)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--ink)", padding: 8 }} aria-label="Toggle menu">
          {mobileOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div style={{ background: "rgba(245, 241, 232, 0.98)", borderTop: "1px solid rgba(14,23,38,0.08)", padding: "16px 24px 24px" }}>
          {links.map((l) => (
            <Link key={l.href} href={l.href} onClick={() => setMobileOpen(false)}
              style={{ display: "block", padding: "12px 0", color: "var(--ink)", textDecoration: "none", fontWeight: 500, fontSize: 15, borderBottom: "1px solid rgba(14,23,38,0.08)" }}>
              {l.label}
            </Link>
          ))}
          <Link href="/screen" onClick={() => setMobileOpen(false)}
            style={{ display: "block", marginTop: 16, textAlign: "center", padding: "12px 24px", background: "var(--ink)", color: "var(--paper)", borderRadius: 999, fontWeight: 600, fontSize: 14, textDecoration: "none" }}>
            Run a scan →
          </Link>
        </div>
      )}
    </nav>
  );
}
