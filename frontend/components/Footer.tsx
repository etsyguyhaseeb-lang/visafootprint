"use client";
import Link from "next/link";

const BrandMark = () => (
  <span style={{ width: 34, height: 34, display: "grid", placeItems: "center", background: "var(--ink)", borderRadius: "50%", flexShrink: 0 }}>
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path d="M9 21c-1.5 0-2.5-1-2.5-2.5 0-1.2.6-2.3 1.4-3.5.9-1.4 1.6-2.5 1.6-4.5 0-3.5 1.5-6 4-6 2 0 3.5 1.8 3.5 4.5 0 2.5-1 4-2 5.5-1 1.5-2 2.8-2 4.5 0 1.3-1 2-2 2H9z" fill="#F5F1E8"/>
      <circle cx="6" cy="6" r="1.4" fill="#F5F1E8"/>
      <circle cx="9" cy="3.5" r="1.2" fill="#F5F1E8"/>
      <circle cx="13" cy="2.8" r="1.1" fill="#F5F1E8"/>
      <circle cx="17" cy="3.8" r="1" fill="#F5F1E8"/>
    </svg>
  </span>
);

export default function Footer() {
  return (
    <footer style={{ background: "var(--ink)", color: "rgba(245,241,232,0.7)", padding: "56px 32px 40px", borderTop: "1px solid rgba(245,241,232,0.1)" }}>
      <div style={{ maxWidth: 1280, margin: "0 auto", display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr", gap: 48 }} className="footer-grid">
        {/* Brand */}
        <div>
          <Link href="/" style={{ display: "flex", alignItems: "center", gap: 12, fontFamily: "'Fraunces', serif", fontWeight: 600, fontSize: 22, color: "var(--paper)", textDecoration: "none", marginBottom: 14 }}>
            <BrandMark />
            VisaFootprint
          </Link>
          <p style={{ fontSize: 14, lineHeight: 1.6, maxWidth: 360 }}>
            AI-powered social media screening for U.S. visa applicants. Find what USCIS will find — before they find it.
          </p>
          <div style={{ display: "flex", gap: 14, marginTop: 20 }}>
            <a href="#" style={{ color: "rgba(245,241,232,0.7)", transition: "color 0.2s" }} aria-label="X / Twitter"
              onMouseEnter={e => (e.currentTarget.style.color = "var(--gold)")}
              onMouseLeave={e => (e.currentTarget.style.color = "rgba(245,241,232,0.7)")}>
              <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            </a>
            <a href="#" style={{ color: "rgba(245,241,232,0.7)", transition: "color 0.2s" }} aria-label="LinkedIn"
              onMouseEnter={e => (e.currentTarget.style.color = "var(--gold)")}
              onMouseLeave={e => (e.currentTarget.style.color = "rgba(245,241,232,0.7)")}>
              <svg width="16" height="16" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
            </a>
            <a href="mailto:haseebabplus@gmail.com" style={{ color: "rgba(245,241,232,0.7)", transition: "color 0.2s" }} aria-label="Email"
              onMouseEnter={e => (e.currentTarget.style.color = "var(--gold)")}
              onMouseLeave={e => (e.currentTarget.style.color = "rgba(245,241,232,0.7)")}>
              <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
            </a>
          </div>
        </div>

        {/* Product */}
        <div>
          <h5 style={{ color: "var(--paper)", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, letterSpacing: "0.2em", marginBottom: 18, fontWeight: 500, textTransform: "uppercase" }}>Product</h5>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {[["/#how","How it works"],["/#pricing","Pricing"],["/screen","Free scan"],["/#faq","FAQ"]].map(([href,label]) => (
              <li key={href} style={{ marginBottom: 10 }}>
                <Link href={href} style={{ color: "rgba(245,241,232,0.7)", textDecoration: "none", fontSize: 14, transition: "color 0.2s" }}
                  onMouseEnter={e => (e.currentTarget.style.color = "var(--gold)")}
                  onMouseLeave={e => (e.currentTarget.style.color = "rgba(245,241,232,0.7)")}>
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* For Firms */}
        <div>
          <h5 style={{ color: "var(--paper)", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, letterSpacing: "0.2em", marginBottom: 18, fontWeight: 500, textTransform: "uppercase" }}>For Firms</h5>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {[["#","White-label plan"],["#","API access"],["#","Contact sales"]].map(([href,label]) => (
              <li key={label} style={{ marginBottom: 10 }}>
                <Link href={href} style={{ color: "rgba(245,241,232,0.7)", textDecoration: "none", fontSize: 14, transition: "color 0.2s" }}
                  onMouseEnter={e => (e.currentTarget.style.color = "var(--gold)")}
                  onMouseLeave={e => (e.currentTarget.style.color = "rgba(245,241,232,0.7)")}>
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Legal */}
        <div>
          <h5 style={{ color: "var(--paper)", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, letterSpacing: "0.2em", marginBottom: 18, fontWeight: 500, textTransform: "uppercase" }}>Legal</h5>
          <ul style={{ listStyle: "none", padding: 0 }}>
            {[["#","Privacy policy"],["#","Terms of service"],["#","Disclaimer"],["#","Contact us"]].map(([href,label]) => (
              <li key={label} style={{ marginBottom: 10 }}>
                <Link href={href} style={{ color: "rgba(245,241,232,0.7)", textDecoration: "none", fontSize: 14, transition: "color 0.2s" }}
                  onMouseEnter={e => (e.currentTarget.style.color = "var(--gold)")}
                  onMouseLeave={e => (e.currentTarget.style.color = "rgba(245,241,232,0.7)")}>
                  {label}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Bottom */}
      <div style={{ maxWidth: 1280, margin: "48px auto 0", paddingTop: 24, borderTop: "1px solid rgba(245,241,232,0.1)", display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 16, fontSize: 12, color: "rgba(245,241,232,0.5)" }}>
        <div>© 2026 VisaFootprint · All rights reserved</div>
        <div style={{ maxWidth: 540, fontFamily: "'JetBrains Mono', monospace", fontSize: 10.5, letterSpacing: "0.05em", lineHeight: 1.6 }}>
          VisaFootprint provides risk analysis and informational reports. Free and Standard tiers are not legal advice. The Attorney-Reviewed tier includes a limited-scope engagement with a licensed U.S. immigration attorney.
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .footer-grid { grid-template-columns: 1fr 1fr !important; gap: 32px !important; }
        }
        @media (max-width: 480px) {
          .footer-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </footer>
  );
}
