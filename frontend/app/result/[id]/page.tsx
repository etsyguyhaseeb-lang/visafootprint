"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getReport, getPdfUrl, type ReportData } from "@/lib/api";
import CheckoutButton from "@/components/CheckoutButton";

function shortId(id: string) {
  return "VF-" + id.replace(/-/g, "").slice(0, 6).toUpperCase();
}

function scoreClass(score: number): string {
  if (score >= 60) return "red";
  if (score >= 30) return "amber";
  return "green";
}

function riskVerdict(risk: string): string {
  const r = (risk ?? "").toUpperCase();
  if (r === "HIGH")   return "High risk — immediate action required";
  if (r === "MEDIUM") return "Moderate risk — action recommended";
  return "Low risk — profile looks clean";
}

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!id) return;
    getReport(id as string)
      .then((data) => { setReport(data); setLoading(false); })
      .catch((e) => { setErr(e.message); setLoading(false); });
  }, [id]);

  if (loading) return (
    <div style={{ minHeight: "100vh", background: "var(--paper)", display: "flex", alignItems: "center", justifyContent: "center", paddingTop: 80 }}>
      <div style={{ textAlign: "center" }}>
        <div style={{ width: 44, height: 44, border: "3px solid var(--gold)", borderTopColor: "transparent", borderRadius: "50%", margin: "0 auto 16px", animation: "spin 0.8s linear infinite" }} />
        <p style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, letterSpacing: "0.15em", color: "rgba(14,23,38,0.5)", textTransform: "uppercase" }}>Loading your report…</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    </div>
  );

  if (err || !report) return (
    <div style={{ minHeight: "100vh", background: "var(--paper)", display: "flex", alignItems: "center", justifyContent: "center", paddingTop: 80 }}>
      <div style={{ textAlign: "center", maxWidth: 400, padding: "0 24px" }}>
        <div style={{ width: 52, height: 52, background: "rgba(122,31,31,0.1)", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--oxblood)" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="1" fill="var(--oxblood)" stroke="none"/></svg>
        </div>
        <h2 style={{ fontFamily: "'Fraunces', serif", fontSize: 22, marginBottom: 10 }}>Report Not Found</h2>
        <p style={{ color: "rgba(14,23,38,0.6)", fontSize: 14, marginBottom: 20 }}>{err || "This report may still be processing. Refresh in a moment."}</p>
        <a href="/screen" style={{ color: "var(--oxblood)", fontWeight: 600, fontSize: 14, textDecoration: "none" }}>← Start a new screening</a>
      </div>
    </div>
  );

  const overall = (report.overall_risk ?? "LOW").toUpperCase();
  const score = report.risk_score ?? 0;
  const highFlags = (report.flagged_posts ?? []).filter(f => f.risk_level?.toUpperCase() === "HIGH");
  const medFlags  = (report.flagged_posts ?? []).filter(f => f.risk_level?.toUpperCase() === "MEDIUM");
  const hasFlags  = (report.flagged_posts ?? []).length > 0;
  const rid = shortId(id as string);

  return (
    <div style={{ background: "var(--paper)", minHeight: "100vh" }}>

      {/* ── SUCCESS BANNER ── */}
      <div style={{
        background: "linear-gradient(135deg, var(--ink) 0%, #1B2741 100%)",
        color: "var(--paper)", padding: "56px 32px 64px", position: "relative", overflow: "hidden",
      }}>
        <div style={{ position: "absolute", right: -120, top: "50%", transform: "translateY(-50%)", width: 380, height: 380, background: "radial-gradient(circle, rgba(184,146,74,0.12) 0%, transparent 65%)", pointerEvents: "none" }} />
        <div style={{ maxWidth: 1280, margin: "0 auto", position: "relative", zIndex: 1 }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 10, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, letterSpacing: "0.2em", color: "var(--gold)", textTransform: "uppercase", marginBottom: 18 }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--gold)" strokeWidth="2" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
            Scan complete · {rid}
          </div>
          <h1 style={{ fontFamily: "'Fraunces', serif", fontWeight: 400, fontSize: "clamp(32px, 4.5vw, 54px)", lineHeight: 1.05, letterSpacing: "-0.025em", marginBottom: 16, maxWidth: 880 }}>
            Your report is ready, {report.name.split(" ")[0]}.<br />
            <em style={{ fontStyle: "italic", color: "var(--gold)", fontWeight: 500 }}>Here's what we found.</em>
          </h1>
          <p style={{ fontSize: 15, color: "rgba(245,241,232,0.72)", maxWidth: 640 }}>
            {report.accounts?.length ?? 1} account{(report.accounts?.length ?? 1) !== 1 ? "s" : ""} · 5-year lookback · {report.posts_analyzed ?? 0} posts analyzed · {report.country}
          </p>
        </div>
      </div>

      {/* ── MAIN GRID ── */}
      <div style={{ maxWidth: 1280, margin: "0 auto", padding: "56px 32px 96px", display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 48, alignItems: "flex-start" }}>

        {/* ── LEFT: REPORT CARD ── */}
        <div style={{ background: "var(--paper)", border: "1px solid rgba(14,23,38,0.18)", borderRadius: 4, padding: 40, boxShadow: "0 2px 0 rgba(14,23,38,0.04)" }}>

          {/* Report header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", borderBottom: "2px solid var(--ink)", paddingBottom: 18, marginBottom: 28 }}>
            <div>
              <h2 style={{ fontFamily: "'Fraunces', serif", fontWeight: 600, fontSize: 26, letterSpacing: "-0.01em", marginBottom: 6 }}>Risk Screening Report</h2>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, letterSpacing: "0.05em", color: "#1B2741" }}>
                {report.reason} · {report.country} · Generated {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}
              </div>
            </div>
            <div style={{ border: `1.5px solid var(--oxblood)`, color: "var(--oxblood)", padding: "6px 12px", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.12em", whiteSpace: "nowrap" }}>
              Final
            </div>
          </div>

          {/* Overall verdict */}
          <div style={{ background: "var(--ink)", color: "var(--paper)", padding: "24px 28px", marginBottom: 28, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 24 }}>
            <div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, letterSpacing: "0.2em", color: "var(--gold)", textTransform: "uppercase", marginBottom: 6 }}>Overall Risk</div>
              <div style={{ fontFamily: "'Fraunces', serif", fontWeight: 500, fontSize: 22, letterSpacing: "-0.01em" }}>{riskVerdict(overall)}</div>
            </div>
            <div style={{ textAlign: "right", flexShrink: 0 }}>
              <div style={{ fontFamily: "'Fraunces', serif", fontWeight: 400, fontSize: 64, lineHeight: 1, color: score >= 60 ? "#C83B3B" : score >= 30 ? "#C98B27" : "#3F6B3A", letterSpacing: "-0.03em" }}>{score}</div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "rgba(245,241,232,0.55)" }}>/ 100</div>
            </div>
          </div>

          {/* Category breakdown */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 28 }}>
            {[
              { label: "Political", val: report.scores?.political ?? 0 },
              { label: "Content",   val: report.scores?.content ?? 0 },
              { label: "Network",   val: report.scores?.network ?? 0 },
            ].map(({ label, val }) => {
              const cls = scoreClass(val);
              const clr = cls === "red" ? "#C83B3B" : cls === "amber" ? "#C98B27" : "#3F6B3A";
              const bg  = cls === "red" ? "rgba(200,59,59,0.07)" : cls === "amber" ? "rgba(201,139,39,0.07)" : "rgba(63,107,58,0.07)";
              return (
                <div key={label} style={{ border: "1px solid rgba(14,23,38,0.15)", padding: 16, background: bg }}>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.18em", color: "#1B2741", textTransform: "uppercase", marginBottom: 8 }}>{label}</div>
                  <div style={{ fontFamily: "'Fraunces', serif", fontWeight: 500, fontSize: 38, lineHeight: 1, letterSpacing: "-0.02em", marginBottom: 4, color: clr }}>{val}</div>
                  <div style={{ fontSize: 12, color: "#1B2741" }}>{val >= 60 ? "Flagged" : val >= 30 ? "Watch" : "Clear"}</div>
                </div>
              );
            })}
          </div>

          {/* Risk context alert */}
          {hasFlags && (
            <div style={{ background: "rgba(122,31,31,0.06)", border: "1px solid rgba(122,31,31,0.2)", padding: "18px 20px", marginBottom: 28, display: "flex", gap: 14, alignItems: "flex-start" }}>
              <div style={{ flexShrink: 0, width: 32, height: 32, borderRadius: "50%", background: "var(--oxblood)", color: "var(--paper)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Fraunces', serif", fontWeight: 600, fontSize: 16 }}>!</div>
              <div style={{ fontSize: 14, lineHeight: 1.55, color: "var(--ink)" }}>
                <strong style={{ color: "var(--oxblood)" }}>
                  Your profile has {highFlags.length > 0 ? `${highFlags.length} high-priority item${highFlags.length > 1 ? "s" : ""} requiring immediate action` : `${medFlags.length} item${medFlags.length > 1 ? "s" : ""} requiring attention`}.
                </strong>{" "}
                {report.summary}
              </div>
            </div>
          )}

          {/* HIGH priority flags */}
          {highFlags.length > 0 && (
            <>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, letterSpacing: "0.2em", color: "var(--oxblood)", textTransform: "uppercase", margin: "32px 0 16px", paddingBottom: 10, borderBottom: "1px solid rgba(14,23,38,0.15)" }}>
                ↑ High priority · Take action now
              </div>
              {highFlags.map((post, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 16, padding: "18px 0", borderTop: i === 0 ? "none" : "1px dashed rgba(14,23,38,0.2)", alignItems: "flex-start" }}>
                  <div style={{ width: 36, height: 36, borderRadius: "50%", background: "rgba(200,59,59,0.12)", color: "#C83B3B", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Fraunces', serif", fontWeight: 500, fontSize: 16, flexShrink: 0 }}>{i + 1}</div>
                  <div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.15em", color: "#1B2741", textTransform: "uppercase", marginBottom: 4 }}>{post.platform}{post.date ? ` · ${post.date}` : ""}</div>
                    <div style={{ fontFamily: "'Fraunces', serif", fontStyle: "italic", fontSize: 16, lineHeight: 1.4, color: "var(--ink)", marginBottom: 6 }}>&ldquo;{post.text}&rdquo;</div>
                    <div style={{ fontSize: 13, color: "#1B2741", lineHeight: 1.5 }}>{post.explanation}</div>
                    {post.post_url && (
                      <a href={post.post_url} target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", alignItems: "center", gap: 6, marginTop: 8, fontSize: 11, color: "var(--oxblood)", textDecoration: "none", fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.08em", textTransform: "uppercase", borderBottom: "1px solid rgba(122,31,31,0.3)", paddingBottom: 1 }}>
                        🔗 View original post →
                      </a>
                    )}
                  </div>
                  <div style={{ flexShrink: 0, padding: "6px 12px", background: "#C83B3B", color: "white", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", alignSelf: "flex-start" }}>Delete</div>
                </div>
              ))}
            </>
          )}

          {/* MEDIUM priority flags */}
          {medFlags.length > 0 && (
            <>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, letterSpacing: "0.2em", color: "var(--oxblood)", textTransform: "uppercase", margin: "32px 0 16px", paddingBottom: 10, borderBottom: "1px solid rgba(14,23,38,0.15)" }}>
                → Medium priority · Archive &amp; prepare
              </div>
              {medFlags.map((post, i) => (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 16, padding: "18px 0", borderTop: i === 0 ? "none" : "1px dashed rgba(14,23,38,0.2)", alignItems: "flex-start" }}>
                  <div style={{ width: 36, height: 36, borderRadius: "50%", background: "rgba(201,139,39,0.15)", color: "#C98B27", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'Fraunces', serif", fontWeight: 500, fontSize: 16, flexShrink: 0 }}>{highFlags.length + i + 1}</div>
                  <div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.15em", color: "#1B2741", textTransform: "uppercase", marginBottom: 4 }}>{post.platform}{post.date ? ` · ${post.date}` : ""}</div>
                    <div style={{ fontFamily: "'Fraunces', serif", fontStyle: "italic", fontSize: 16, lineHeight: 1.4, color: "var(--ink)", marginBottom: 6 }}>&ldquo;{post.text}&rdquo;</div>
                    <div style={{ fontSize: 13, color: "#1B2741", lineHeight: 1.5 }}>{post.explanation}</div>
                    {post.post_url && (
                      <a href={post.post_url} target="_blank" rel="noopener noreferrer" style={{ display: "inline-flex", alignItems: "center", gap: 6, marginTop: 8, fontSize: 11, color: "#C98B27", textDecoration: "none", fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.08em", textTransform: "uppercase", borderBottom: "1px solid rgba(201,139,39,0.3)", paddingBottom: 1 }}>
                        🔗 View original post →
                      </a>
                    )}
                  </div>
                  <div style={{ flexShrink: 0, padding: "6px 12px", background: "#C98B27", color: "white", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", alignSelf: "flex-start" }}>Archive</div>
                </div>
              ))}
            </>
          )}

          {/* No flags */}
          {!hasFlags && (
            <div style={{ display: "flex", alignItems: "center", gap: 14, background: "rgba(63,107,58,0.08)", border: "1px solid rgba(63,107,58,0.25)", padding: "20px 22px", marginBottom: 28 }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3F6B3A" strokeWidth="2" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>
              <div style={{ fontSize: 14, color: "var(--ink)" }}><strong style={{ color: "#3F6B3A" }}>No concerning posts identified.</strong> Your public profiles look clean across all platforms scanned.</div>
            </div>
          )}

          {/* Recommendations */}
          {(report.recommendations ?? []).length > 0 && (
            <>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, letterSpacing: "0.2em", color: "var(--oxblood)", textTransform: "uppercase", margin: "32px 0 16px", paddingBottom: 10, borderBottom: "1px solid rgba(14,23,38,0.15)" }}>
                Recommendations
              </div>
              <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
                {report.recommendations.map((r, i) => (
                  <li key={i} style={{ display: "flex", gap: 14, alignItems: "flex-start", padding: "10px 0", borderBottom: "1px dashed rgba(14,23,38,0.15)", fontSize: 14, lineHeight: 1.55, color: "var(--ink)" }}>
                    <span style={{ flexShrink: 0, width: 24, height: 24, borderRadius: "50%", background: "var(--ink)", color: "var(--paper)", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, fontWeight: 600 }}>{i + 1}</span>
                    {r}
                  </li>
                ))}
              </ul>
            </>
          )}

          {/* Download row */}
          <div style={{ marginTop: 36, paddingTop: 28, borderTop: "1px solid rgba(14,23,38,0.15)", display: "flex", gap: 12, flexWrap: "wrap" }}>
            <a href={getPdfUrl(id as string)} target="_blank" rel="noopener noreferrer"
              style={{ display: "inline-flex", alignItems: "center", gap: 10, padding: "14px 28px", background: "var(--ink)", color: "var(--paper)", textDecoration: "none", fontWeight: 600, fontSize: 14, borderRadius: 999, transition: "background 0.2s" }}
              onMouseEnter={e => (e.currentTarget.style.background = "var(--oxblood)")}
              onMouseLeave={e => (e.currentTarget.style.background = "var(--ink)")}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download full PDF report →
            </a>
            <a href="/"
              style={{ display: "inline-flex", alignItems: "center", gap: 10, padding: "14px 28px", background: "transparent", color: "var(--ink)", border: "1px solid rgba(14,23,38,0.25)", textDecoration: "none", fontWeight: 600, fontSize: 14, borderRadius: 999 }}>
              ← Back to home
            </a>
          </div>
        </div>

        {/* ── RIGHT: MONITOR UPSELL ── */}
        <div style={{ position: "sticky", top: 96, display: "flex", flexDirection: "column", gap: 20 }}>

          {/* Upsell card */}
          <div style={{ background: "var(--ink)", color: "var(--paper)", padding: 32, position: "relative", overflow: "hidden", border: "1px solid var(--gold)", boxShadow: "0 0 0 4px rgba(184,146,74,0.12)", animation: "rise 0.7s cubic-bezier(.2,.7,.3,1) backwards", animationDelay: "0.3s" }}>
            <div style={{ position: "absolute", top: -40, right: -40, width: 200, height: 200, background: "radial-gradient(circle, rgba(184,146,74,0.18) 0%, transparent 65%)", pointerEvents: "none" }} />

            <div style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: "'JetBrains Mono', monospace", fontSize: 11, letterSpacing: "0.2em", color: "var(--gold)", textTransform: "uppercase", marginBottom: 18 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "var(--gold)", boxShadow: "0 0 0 0 rgba(184,146,74,0.5)", animation: "pulse 2s infinite", display: "inline-block" }} />
              Recommended for your case
            </div>

            <h3 style={{ fontFamily: "'Fraunces', serif", fontWeight: 500, fontSize: 26, lineHeight: 1.15, letterSpacing: "-0.015em", marginBottom: 14 }}>
              Your visa case stays open for <em style={{ fontStyle: "italic", color: "var(--gold)" }}>9–14 months.</em> Your social media stays active that whole time.
            </h3>

            <div style={{ background: "rgba(245,241,232,0.06)", borderLeft: "3px solid var(--gold)", padding: "16px 18px", margin: "20px 0 24px", fontSize: 14, lineHeight: 1.55, color: "rgba(245,241,232,0.92)" }}>
              <strong style={{ color: "var(--gold)" }}>73%</strong> of applicants whose first scan returned amber or red flags add Monitor. Most cases stay open for <strong style={{ color: "var(--gold)" }}>9 months</strong> on average — every new post is a new risk.
            </div>

            <ul style={{ listStyle: "none", margin: "0 0 28px", padding: 0 }}>
              {[
                ["Weekly automated re-scans", "of your accounts"],
                ["Alerts within 48 hours", "when new flags appear"],
                ["Unlimited pre-interview deep scans", "on demand"],
                ["Quarterly mini-report PDF", "for you or your attorney"],
                ["Cancel anytime", "from your dashboard"],
              ].map(([bold, rest], i) => (
                <li key={i} style={{ padding: "9px 0", fontSize: 13.5, lineHeight: 1.5, display: "flex", gap: 12, alignItems: "flex-start", color: "rgba(245,241,232,0.88)", borderBottom: "1px dashed rgba(245,241,232,0.12)" }}>
                  <span style={{ color: "var(--gold)", fontWeight: 600, flexShrink: 0, marginTop: 2 }}>✓</span>
                  <span><strong style={{ color: "var(--paper)", fontWeight: 600 }}>{bold}</strong> {rest}</span>
                </li>
              ))}
            </ul>

            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", padding: "18px 0 22px", borderTop: "1px solid rgba(245,241,232,0.15)", marginBottom: 18 }}>
              <div style={{ fontFamily: "'Fraunces', serif", fontWeight: 400, display: "flex", alignItems: "baseline", gap: 4 }}>
                <span style={{ fontSize: 22, color: "rgba(184,146,74,0.7)" }}>$</span>
                <span style={{ fontSize: 56, lineHeight: 1, letterSpacing: "-0.03em", color: "var(--gold)" }}>19</span>
                <span style={{ fontSize: 13, color: "rgba(245,241,232,0.6)", marginLeft: 6, fontFamily: "'Inter Tight', sans-serif" }}>/ month</span>
              </div>
              <div style={{ textAlign: "right", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.12em", color: "rgba(245,241,232,0.55)", textTransform: "uppercase" }}>
                No commitment<br />Cancel anytime
              </div>
            </div>

            <CheckoutButton
              tier="monitor"
              block
              style={{ textAlign: "center", padding: "16px 24px", background: "var(--gold)", color: "var(--ink)", fontWeight: 700, fontSize: 15, border: "none", letterSpacing: "0.02em", borderRadius: 0 }}
            >
              Add Monitor — $19/month →
            </CheckoutButton>

            <a href="/" style={{ display: "block", textAlign: "center", width: "100%", padding: 12, background: "transparent", color: "rgba(245,241,232,0.55)", textDecoration: "none", fontSize: 12.5, marginTop: 8, transition: "color 0.2s" }}
              onMouseEnter={e => (e.currentTarget.style.color = "rgba(245,241,232,0.85)")}
              onMouseLeave={e => (e.currentTarget.style.color = "rgba(245,241,232,0.55)")}>
              No thanks · I'll come back if I need it
            </a>

            <div style={{ marginTop: 20, paddingTop: 18, borderTop: "1px solid rgba(245,241,232,0.1)", display: "flex", gap: 16, flexWrap: "wrap", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.1em", color: "rgba(245,241,232,0.5)", textTransform: "uppercase" }}>
              <span>Stripe secure checkout</span>
              <span>·</span>
              <span>30-day data purge on cancel</span>
            </div>
          </div>

          {/* Social proof */}
          <div style={{ background: "var(--paper)", border: "1px solid rgba(14,23,38,0.15)", padding: 24, animation: "rise 0.7s cubic-bezier(.2,.7,.3,1) backwards", animationDelay: "0.5s" }}>
            <blockquote style={{ fontFamily: "'Fraunces', serif", fontStyle: "italic", fontSize: 16, lineHeight: 1.45, color: "var(--ink)", marginBottom: 14 }}>
              <span style={{ color: "var(--oxblood)", fontFamily: "'Fraunces', serif", fontSize: 32, lineHeight: 0, verticalAlign: "-8px", marginRight: 4 }}>"</span>
              I added Monitor right after my first scan. Two months later it caught a friend's tagged post that would've come up in my interview. Worth every dollar.
            </blockquote>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.15em", color: "#1B2741", textTransform: "uppercase" }}>— R.K. · F-1 Visa, Approved</div>
          </div>

        </div>
      </div>

      <style>{`
        @keyframes spin  { to { transform: rotate(360deg); } }
        @keyframes rise  { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse {
          0%   { box-shadow: 0 0 0 0 rgba(184,146,74, 0.5); }
          70%  { box-shadow: 0 0 0 12px rgba(184,146,74, 0); }
          100% { box-shadow: 0 0 0 0 rgba(184,146,74, 0); }
        }
        @media (max-width: 980px) {
          .report-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}
