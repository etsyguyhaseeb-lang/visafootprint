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
      {/* pillar */}
      <line x1="12" y1="4.5" x2="12" y2="20" stroke="#F5F1E8" strokeWidth="1.6" strokeLinecap="round"/>
      {/* beam */}
      <line x1="5" y1="8" x2="19" y2="8" stroke="#F5F1E8" strokeWidth="1.6" strokeLinecap="round"/>
      {/* left chain */}
      <line x1="7.5" y1="8" x2="7.5" y2="13" stroke="#F5F1E8" strokeWidth="1.1" strokeLinecap="round"/>
      {/* right chain */}
      <line x1="16.5" y1="8" x2="16.5" y2="13" stroke="#F5F1E8" strokeWidth="1.1" strokeLinecap="round"/>
      {/* left pan */}
      <path d="M4.5 13 Q7.5 16.5 10.5 13" stroke="#F5F1E8" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
      {/* right pan */}
      <path d="M13.5 13 Q16.5 16.5 19.5 13" stroke="#F5F1E8" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
      {/* base */}
      <line x1="9.5" y1="20" x2="14.5" y2="20" stroke="#F5F1E8" strokeWidth="1.6" strokeLinecap="round"/>
      {/* top knob */}
      <circle cx="12" cy="4.5" r="1.1" fill="#F5F1E8"/>
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
