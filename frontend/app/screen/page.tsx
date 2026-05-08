"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Plus, Trash2, ChevronRight, ChevronLeft, CheckCircle, Loader2, AlertCircle, ChevronDown } from "lucide-react";
import { submitScreening, getStatus, type AccountInput } from "@/lib/api";

const COUNTRIES = [
  "Afghanistan","Albania","Algeria","Andorra","Angola","Antigua and Barbuda","Argentina","Armenia","Australia","Austria",
  "Azerbaijan","Bahamas","Bahrain","Bangladesh","Barbados","Belarus","Belgium","Belize","Benin","Bhutan",
  "Bolivia","Bosnia and Herzegovina","Botswana","Brazil","Brunei","Bulgaria","Burkina Faso","Burundi","Cabo Verde","Cambodia",
  "Cameroon","Canada","Central African Republic","Chad","Chile","China","Colombia","Comoros","Congo","Costa Rica",
  "Croatia","Cuba","Cyprus","Czech Republic","Denmark","Djibouti","Dominica","Dominican Republic","Ecuador","Egypt",
  "El Salvador","Equatorial Guinea","Eritrea","Estonia","Eswatini","Ethiopia","Fiji","Finland","France","Gabon",
  "Gambia","Georgia","Germany","Ghana","Greece","Grenada","Guatemala","Guinea","Guinea-Bissau","Guyana",
  "Haiti","Honduras","Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland","Israel",
  "Italy","Jamaica","Japan","Jordan","Kazakhstan","Kenya","Kiribati","Kuwait","Kyrgyzstan","Laos",
  "Latvia","Lebanon","Lesotho","Liberia","Libya","Liechtenstein","Lithuania","Luxembourg","Madagascar","Malawi",
  "Malaysia","Maldives","Mali","Malta","Marshall Islands","Mauritania","Mauritius","Mexico","Micronesia","Moldova",
  "Monaco","Mongolia","Montenegro","Morocco","Mozambique","Myanmar","Namibia","Nauru","Nepal","Netherlands",
  "New Zealand","Nicaragua","Niger","Nigeria","North Korea","North Macedonia","Norway","Oman","Pakistan","Palau",
  "Palestine","Panama","Papua New Guinea","Paraguay","Peru","Philippines","Poland","Portugal","Qatar","Romania",
  "Russia","Rwanda","Saint Kitts and Nevis","Saint Lucia","Saint Vincent and the Grenadines","Samoa","San Marino",
  "Sao Tome and Principe","Saudi Arabia","Senegal","Serbia","Seychelles","Sierra Leone","Singapore","Slovakia",
  "Slovenia","Solomon Islands","Somalia","South Africa","South Korea","South Sudan","Spain","Sri Lanka","Sudan",
  "Suriname","Sweden","Switzerland","Syria","Taiwan","Tajikistan","Tanzania","Thailand","Timor-Leste","Togo",
  "Tonga","Trinidad and Tobago","Tunisia","Turkey","Turkmenistan","Tuvalu","Uganda","Ukraine","United Arab Emirates",
  "United Kingdom","United States","Uruguay","Uzbekistan","Vanuatu","Vatican City","Venezuela","Vietnam","Yemen",
  "Zambia","Zimbabwe",
];

const PLATFORMS = ["Twitter/X","Instagram","TikTok","LinkedIn","Facebook","YouTube"];
const AUTO_SCRAPE_PLATFORMS = new Set(["Twitter/X","Instagram","TikTok","LinkedIn","Facebook","YouTube"]);

// Account limits per tier — free plan = 1, standard = 3, attorney = 10
const FREE_ACCOUNT_LIMIT = 1;
const REASONS = [
  "To improve my chances of getting a VISA",
  "To detect any objectionable content I may have overlooked",
  "My network could be risky",
  "Others",
];
const TIMELINES = [
  "Within a month",
  "1–3 months",
  "Beyond 3 months",
  "Already applied",
];

const slideVariants = {
  enter: (dir: number) => ({ x: dir > 0 ? 60 : -60, opacity: 0 }),
  center: { x: 0, opacity: 1, transition: { duration: 0.35 } },
  exit: (dir: number) => ({ x: dir > 0 ? -60 : 60, opacity: 0, transition: { duration: 0.25 } }),
};

const inputCls = `
  w-full border border-[rgba(14,23,38,0.2)] rounded-lg px-4 py-3 text-sm
  bg-[var(--paper)] text-[var(--ink)] placeholder-[rgba(14,23,38,0.4)]
  focus:outline-none focus:border-[var(--ink)] focus:ring-1 focus:ring-[var(--ink)]
  transition-all font-[Inter_Tight,system-ui,sans-serif]
`.trim();

const VisaFootprintMark = () => (
  <div style={{
    width: 52, height: 52, background: "var(--ink)", borderRadius: 13,
    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
  }}>
    <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
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
  </div>
);

export default function ScreenPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [dir, setDir] = useState(1);
  const [error, setError] = useState("");
  const [processingMsg, setProcessingMsg] = useState("Analyzing your profiles…");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [country, setCountry] = useState("");
  const [countrySearch, setCountrySearch] = useState("");
  const [accounts, setAccounts] = useState<AccountInput[]>([{ platform: "Twitter/X", handle: "" }]);
  const [expandedPaste, setExpandedPaste] = useState<Set<number>>(new Set());
  const [reason, setReason] = useState("");
  const [timeline, setTimeline] = useState("");
  const [consent, setConsent] = useState(false);

  const filteredCountries = COUNTRIES.filter((c) =>
    c.toLowerCase().includes(countrySearch.toLowerCase())
  );

  const addAccount = () => {
    if (accounts.length < FREE_ACCOUNT_LIMIT) setAccounts([...accounts, { platform: "Twitter/X", handle: "" }]);
  };
  const removeAccount = (i: number) => {
    setAccounts(accounts.filter((_, idx) => idx !== i));
    setExpandedPaste((prev) => { const n = new Set(prev); n.delete(i); return n; });
  };
  const updateAccount = (i: number, field: "platform" | "handle" | "manual_posts", val: string) => {
    setAccounts(accounts.map((a, idx) => idx === i ? { ...a, [field]: val } : a));
  };
  const togglePaste = (i: number) => {
    setExpandedPaste((prev) => { const n = new Set(prev); n.has(i) ? n.delete(i) : n.add(i); return n; });
  };

  const goNext = () => { setDir(1); setError(""); setStep((s) => s + 1); };
  const goBack = () => { setDir(-1); setError(""); setStep((s) => s - 1); };

  const validateStep = (): boolean => {
    if (step === 0) {
      if (!name.trim()) { setError("Please enter your full name."); return false; }
      if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { setError("Please enter a valid email."); return false; }
      if (!country) { setError("Please select your country of origin."); return false; }
    }
    if (step === 1) {
      if (!accounts.filter((a) => a.handle.trim()).length) { setError("Add at least one social media account."); return false; }
    }
    if (step === 2) {
      if (!reason) { setError("Please select a reason for screening."); return false; }
      if (!timeline) { setError("Please select your visa timeline."); return false; }
      if (!consent) { setError("You must authorize the screening to proceed."); return false; }
    }
    return true;
  };

  const handleNext = () => { if (validateStep()) goNext(); };

  const handleSubmit = async () => {
    if (!validateStep()) return;
    goNext();
    const msgs = [
      "Connecting to social media platforms…",
      "Scraping publicly visible posts…",
      "Running AI risk analysis…",
      "Generating your PDF report…",
      "Finalizing report…",
    ];
    let mi = 0;
    const interval = setInterval(() => { mi = (mi + 1) % msgs.length; setProcessingMsg(msgs[mi]); }, 4000);
    try {
      const validAccounts = accounts.filter((a) => a.handle.trim()).map((a) => ({
        platform: a.platform.toLowerCase().replace("/", "").replace("twitter", "twitter").replace("x", "twitter"),
        handle: a.handle.trim(),
        ...(a.manual_posts?.trim() ? { manual_posts: a.manual_posts.trim() } : {}),
      }));
      const res = await submitScreening({ name, email, country, accounts: validAccounts, reason, timeline, consent });
      const jobId = res.job_id;
      const poll = async () => {
        const status = await getStatus(jobId);
        if (status.status === "done") { clearInterval(interval); router.push(`/report/${jobId}`); }
        else if (status.status === "failed") { clearInterval(interval); setError(status.error ?? "Screening failed. Please try again."); setStep(2); }
        else { setTimeout(poll, 3000); }
      };
      setTimeout(poll, 3000);
    } catch (e: unknown) {
      clearInterval(interval);
      setError(e instanceof Error ? e.message : "Submission failed. Please try again.");
      setStep(2);
    }
  };

  const stepLabels = ["Your Info", "Accounts", "Preferences"];
  const totalSteps = 3;

  return (
    <div style={{ minHeight: "100vh", background: "var(--paper)", color: "var(--ink)", paddingTop: 80, paddingBottom: 80 }}>
      <div style={{ maxWidth: 640, margin: "0 auto", padding: "0 24px" }}>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 48 }}>
          <div style={{ display: "flex", justifyContent: "center", marginBottom: 20 }}>
            <VisaFootprintMark />
          </div>
          <div style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11, fontWeight: 500, letterSpacing: "0.15em",
            textTransform: "uppercase", color: "var(--oxblood)",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 10, marginBottom: 16,
          }}>
            <span style={{ width: 24, height: 1, background: "var(--oxblood)", display: "inline-block" }} />
            Social Media Screening
            <span style={{ width: 24, height: 1, background: "var(--oxblood)", display: "inline-block" }} />
          </div>
          <h1 style={{
            fontFamily: "'Fraunces', serif", fontWeight: 400,
            fontSize: "clamp(32px, 5vw, 52px)", lineHeight: 1.0,
            letterSpacing: "-0.03em", margin: "0 0 16px",
          }}>
            Know what USCIS<br />
            <span style={{ fontStyle: "italic", color: "var(--oxblood)" }}>will find — first.</span>
          </h1>
          <p style={{ fontSize: 16, color: "var(--ink-soft)", lineHeight: 1.55, margin: 0 }}>
            Get your AI-powered visa risk report in under 3 minutes.
          </p>
        </div>

        {/* Progress stepper */}
        {step < 3 && (
          <div style={{ position: "relative", display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 40, padding: "0 16px" }}>
            {/* track */}
            <div style={{ position: "absolute", top: 16, left: 48, right: 48, height: 1, background: "rgba(14,23,38,0.15)" }} />
            <div style={{
              position: "absolute", top: 16, left: 48, height: 1,
              background: "var(--ink)",
              width: step === 0 ? "0%" : step === 1 ? "50%" : "100%",
              transition: "width 0.5s cubic-bezier(.4,0,.2,1)",
            }} />
            {stepLabels.map((label, i) => (
              <div key={i} style={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: "50%",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 13, fontWeight: 700,
                  background: i <= step ? "var(--ink)" : "var(--paper)",
                  color: i <= step ? "var(--paper)" : "rgba(14,23,38,0.35)",
                  border: i <= step ? "none" : "1.5px solid rgba(14,23,38,0.2)",
                  transition: "all 0.3s",
                  outline: i === step ? "3px solid rgba(14,23,38,0.12)" : "none",
                  outlineOffset: 2,
                }}>
                  {i < step ? <CheckCircle style={{ width: 14, height: 14 }} /> : i + 1}
                </div>
                <span style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase",
                  color: i <= step ? "var(--ink)" : "rgba(14,23,38,0.4)",
                  fontWeight: 500,
                }}>
                  {label}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Card */}
        <div style={{
          background: "var(--paper-soft)",
          border: "1px solid rgba(14,23,38,0.12)",
          borderRadius: 16,
          overflow: "hidden",
        }}>
          <AnimatePresence mode="wait" custom={dir}>
            <motion.div
              key={step}
              custom={dir}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              style={{ padding: "36px 36px 28px" }}
            >

              {/* Step 0 — Personal Info */}
              {step === 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                  <div>
                    <h2 style={{ fontFamily: "'Fraunces', serif", fontWeight: 400, fontSize: 26, letterSpacing: "-0.02em", margin: "0 0 4px" }}>
                      Your Information
                    </h2>
                    <p style={{ fontSize: 14, color: "var(--ink-soft)", margin: 0 }}>Tell us about yourself — your report will be emailed here.</p>
                  </div>
                  <div>
                    <label style={{ display: "block", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--ink-soft)", marginBottom: 8 }}>Full Name *</label>
                    <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your full name" className={inputCls} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--ink-soft)", marginBottom: 8 }}>Email Address *</label>
                    <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="your.email@example.com" className={inputCls} />
                  </div>
                  <div>
                    <label style={{ display: "block", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--ink-soft)", marginBottom: 8 }}>Country of Origin *</label>
                    <input
                      value={countrySearch}
                      onChange={(e) => { setCountrySearch(e.target.value); setCountry(""); }}
                      placeholder="Search country…"
                      className={inputCls}
                      style={{ marginBottom: 4 }}
                    />
                    {countrySearch && !country && (
                      <div style={{ border: "1px solid rgba(14,23,38,0.15)", borderRadius: 10, maxHeight: 200, overflowY: "auto", background: "var(--paper)", boxShadow: "0 8px 24px rgba(14,23,38,0.1)" }}>
                        {filteredCountries.slice(0, 20).map((c) => (
                          <button key={c} onClick={() => { setCountry(c); setCountrySearch(c); }}
                            style={{ width: "100%", textAlign: "left", padding: "10px 16px", fontSize: 14, background: "none", border: "none", cursor: "pointer", color: "var(--ink)", fontFamily: "Inter Tight, system-ui, sans-serif" }}
                            onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "rgba(14,23,38,0.06)"; }}
                            onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "none"; }}
                          >{c}</button>
                        ))}
                        {filteredCountries.length === 0 && <div style={{ padding: "12px 16px", fontSize: 13, color: "rgba(14,23,38,0.4)" }}>No matches</div>}
                      </div>
                    )}
                    {country && (
                      <div style={{ fontSize: 12, color: "var(--flag-green)", fontWeight: 600, marginTop: 6, display: "flex", alignItems: "center", gap: 5 }}>
                        <CheckCircle style={{ width: 12, height: 12 }} /> {country}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Step 1 — Social media accounts */}
              {step === 1 && (
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                  <div>
                    <h2 style={{ fontFamily: "'Fraunces', serif", fontWeight: 400, fontSize: 26, letterSpacing: "-0.02em", margin: "0 0 4px" }}>
                      Social Media Accounts
                    </h2>
                    <p style={{ fontSize: 14, color: "var(--ink-soft)", margin: 0 }}>Enter your username or profile URL — we automatically scrape all major platforms.</p>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    {accounts.map((acc, i) => (
                      <div key={i} style={{ border: "1px solid rgba(14,23,38,0.15)", borderRadius: 12, overflow: "hidden", background: "var(--paper)" }}>
                        <div style={{ display: "flex", gap: 8, alignItems: "center", padding: 12 }}>
                          <select
                            value={acc.platform}
                            onChange={(e) => updateAccount(i, "platform", e.target.value)}
                            style={{ border: "1px solid rgba(14,23,38,0.2)", borderRadius: 8, padding: "8px 10px", fontSize: 13, background: "var(--paper-soft)", color: "var(--ink)", width: 128, flexShrink: 0, fontFamily: "Inter Tight, system-ui, sans-serif", cursor: "pointer" }}
                          >
                            {PLATFORMS.map((p) => <option key={p}>{p}</option>)}
                          </select>
                          <input
                            value={acc.handle}
                            onChange={(e) => updateAccount(i, "handle", e.target.value)}
                            placeholder="@handle or profile URL"
                            style={{ flex: 1, border: "1px solid rgba(14,23,38,0.2)", borderRadius: 8, padding: "8px 12px", fontSize: 13, background: "var(--paper)", color: "var(--ink)", fontFamily: "Inter Tight, system-ui, sans-serif", outline: "none" }}
                          />
                          {AUTO_SCRAPE_PLATFORMS.has(acc.platform) ? (
                            <span style={{ fontSize: 11, fontWeight: 600, color: "var(--flag-green)", background: "rgba(63,107,58,0.1)", border: "1px solid rgba(63,107,58,0.25)", padding: "5px 10px", borderRadius: 6, flexShrink: 0, fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.05em" }}>
                              AUTO
                            </span>
                          ) : (
                            <button onClick={() => togglePaste(i)}
                              style={{ padding: "5px 10px", borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: "pointer", border: "1px solid rgba(185,131,39,0.4)", background: expandedPaste.has(i) ? "rgba(184,146,74,0.15)" : "rgba(184,146,74,0.08)", color: "var(--gold)", display: "flex", alignItems: "center", gap: 4, flexShrink: 0, fontFamily: "'JetBrains Mono', monospace" }}>
                              Paste <ChevronDown style={{ width: 11, height: 11, transform: expandedPaste.has(i) ? "rotate(180deg)" : "none", transition: "transform 0.2s" }} />
                            </button>
                          )}
                          {accounts.length > 1 && (
                            <button onClick={() => removeAccount(i)} style={{ padding: 8, borderRadius: 8, background: "none", border: "none", cursor: "pointer", color: "rgba(14,23,38,0.35)", display: "flex", flexShrink: 0 }}
                              onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "var(--flag-red)"; (e.currentTarget as HTMLButtonElement).style.background = "rgba(200,59,59,0.07)"; }}
                              onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.color = "rgba(14,23,38,0.35)"; (e.currentTarget as HTMLButtonElement).style.background = "none"; }}>
                              <Trash2 style={{ width: 15, height: 15 }} />
                            </button>
                          )}
                        </div>
                        {expandedPaste.has(i) && (
                          <div style={{ borderTop: "1px solid rgba(14,23,38,0.08)", background: "var(--paper-soft)", padding: "12px 12px 14px" }}>
                            <label style={{ display: "block", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--gold)", marginBottom: 8 }}>
                              {acc.platform} — paste recent posts below
                            </label>
                            <textarea
                              value={acc.manual_posts ?? ""}
                              onChange={(e) => updateAccount(i, "manual_posts", e.target.value)}
                              rows={5}
                              placeholder={"Paste recent posts, one per line.\n\nExample:\nJust landed in New York! Excited for the future.\n\nAttended a community event last week."}
                              style={{ width: "100%", border: "1px solid rgba(14,23,38,0.2)", borderRadius: 8, padding: "10px 12px", fontSize: 13, background: "var(--paper)", color: "var(--ink)", fontFamily: "Inter Tight, system-ui, sans-serif", resize: "none", outline: "none", lineHeight: 1.5 }}
                            />
                            <p style={{ fontSize: 11, color: "rgba(14,23,38,0.45)", marginTop: 6 }}>Copy posts from your profile and paste here. The AI will analyze these.</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  {accounts.length < FREE_ACCOUNT_LIMIT ? (
                    <button onClick={addAccount} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, fontWeight: 600, color: "var(--ink)", background: "none", border: "1px dashed rgba(14,23,38,0.25)", borderRadius: 10, padding: "10px 16px", cursor: "pointer", fontFamily: "Inter Tight, system-ui, sans-serif", width: "fit-content" }}>
                      <Plus style={{ width: 14, height: 14 }} /> Add Account ({accounts.length}/{FREE_ACCOUNT_LIMIT})
                    </button>
                  ) : (
                    <div style={{ border: "1px solid rgba(184,146,74,0.35)", borderRadius: 10, padding: "12px 16px", background: "rgba(184,146,74,0.06)", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
                      <span style={{ fontSize: 13, color: "var(--ink-soft)" }}>
                        <strong style={{ color: "var(--ink)" }}>Free plan:</strong> 1 account included.
                      </span>
                      <a href="/#pricing" style={{ fontSize: 12, fontWeight: 700, color: "var(--gold)", textDecoration: "none", fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.05em", whiteSpace: "nowrap" }}>
                        Upgrade → 3 accounts
                      </a>
                    </div>
                  )}
                  <div style={{ background: "rgba(14,23,38,0.04)", border: "1px solid rgba(14,23,38,0.1)", borderRadius: 10, padding: "14px 16px", fontSize: 12, color: "var(--ink-soft)", lineHeight: 1.6 }}>
                    <strong style={{ color: "var(--ink)" }}>Privacy Notice:</strong> We only analyze publicly visible posts. We do not require passwords or store credentials. Your data is encrypted and used solely for screening. Each email allows up to 3 submissions.
                  </div>
                </div>
              )}

              {/* Step 2 — Preferences + consent */}
              {step === 2 && (
                <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                  <div>
                    <h2 style={{ fontFamily: "'Fraunces', serif", fontWeight: 400, fontSize: 26, letterSpacing: "-0.02em", margin: "0 0 4px" }}>
                      Screening Preferences
                    </h2>
                    <p style={{ fontSize: 14, color: "var(--ink-soft)", margin: 0 }}>Help us tailor your report to your situation.</p>
                  </div>

                  <div>
                    <label style={{ display: "block", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--ink-soft)", marginBottom: 12 }}>
                      Reason for screening *
                    </label>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {REASONS.map((r) => (
                        <label key={r} style={{
                          display: "flex", alignItems: "center", gap: 12, padding: "12px 16px",
                          borderRadius: 10, border: reason === r ? "1.5px solid var(--ink)" : "1.5px solid rgba(14,23,38,0.15)",
                          background: reason === r ? "rgba(14,23,38,0.05)" : "var(--paper)",
                          cursor: "pointer", transition: "all 0.2s",
                        }}>
                          <input type="radio" name="reason" value={r} checked={reason === r} onChange={() => setReason(r)}
                            style={{ accentColor: "var(--ink)", width: 15, height: 15, flexShrink: 0 }} />
                          <span style={{ fontSize: 14, fontWeight: 500, color: "var(--ink)" }}>{r}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label style={{ display: "block", fontFamily: "'JetBrains Mono', monospace", fontSize: 10, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--ink-soft)", marginBottom: 12 }}>
                      Visa application timeline *
                    </label>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                      {TIMELINES.map((t) => (
                        <label key={t} style={{
                          display: "flex", alignItems: "center", gap: 10, padding: "11px 14px",
                          borderRadius: 10, border: timeline === t ? "1.5px solid var(--ink)" : "1.5px solid rgba(14,23,38,0.15)",
                          background: timeline === t ? "rgba(14,23,38,0.05)" : "var(--paper)",
                          cursor: "pointer", transition: "all 0.2s",
                        }}>
                          <input type="radio" name="timeline" value={t} checked={timeline === t} onChange={() => setTimeline(t)}
                            style={{ accentColor: "var(--ink)", width: 14, height: 14, flexShrink: 0 }} />
                          <span style={{ fontSize: 13, fontWeight: 500, color: "var(--ink)" }}>{t}</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <label style={{
                    display: "flex", alignItems: "flex-start", gap: 12, padding: "16px",
                    borderRadius: 10, border: consent ? "1.5px solid var(--ink)" : "1.5px solid rgba(14,23,38,0.15)",
                    background: consent ? "rgba(14,23,38,0.05)" : "var(--paper)",
                    cursor: "pointer", transition: "all 0.2s",
                  }}>
                    <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)}
                      style={{ accentColor: "var(--ink)", width: 15, height: 15, marginTop: 2, flexShrink: 0 }} />
                    <span style={{ fontSize: 13, color: "var(--ink-soft)", lineHeight: 1.6 }}>
                      I authorize <strong style={{ color: "var(--ink)" }}>VisaFootprint</strong> to access and evaluate my submitted profiles for immigration social media screening purposes.
                    </span>
                  </label>
                </div>
              )}

              {/* Step 3 — Processing */}
              {step === 3 && (
                <div style={{ textAlign: "center", padding: "40px 0" }}>
                  <div style={{ position: "relative", display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: 28 }}>
                    <div style={{ width: 80, height: 80, borderRadius: "50%", border: "3px solid rgba(14,23,38,0.1)", borderTopColor: "var(--ink)", animation: "spin 1s linear infinite" }} />
                    <div style={{ position: "absolute" }}>
                      <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                        <line x1="12" y1="4.5" x2="12" y2="20" stroke="var(--ink)" strokeWidth="1.6" strokeLinecap="round"/>
                        <line x1="5" y1="8" x2="19" y2="8" stroke="var(--ink)" strokeWidth="1.6" strokeLinecap="round"/>
                        <line x1="7.5" y1="8" x2="7.5" y2="13" stroke="var(--ink)" strokeWidth="1.1" strokeLinecap="round"/>
                        <line x1="16.5" y1="8" x2="16.5" y2="13" stroke="var(--ink)" strokeWidth="1.1" strokeLinecap="round"/>
                        <path d="M4.5 13 Q7.5 16.5 10.5 13" stroke="var(--ink)" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
                        <path d="M13.5 13 Q16.5 16.5 19.5 13" stroke="var(--ink)" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
                        <line x1="9.5" y1="20" x2="14.5" y2="20" stroke="var(--ink)" strokeWidth="1.6" strokeLinecap="round"/>
                        <circle cx="12" cy="4.5" r="1.1" fill="var(--ink)"/>
                      </svg>
                    </div>
                  </div>
                  <h2 style={{ fontFamily: "'Fraunces', serif", fontWeight: 400, fontSize: 28, letterSpacing: "-0.02em", margin: "0 0 12px" }}>
                    Analyzing Your Profiles
                  </h2>
                  <p style={{ fontSize: 14, color: "var(--ink-soft)", margin: "0 0 6px" }}>{processingMsg}</p>
                  <p style={{ fontSize: 12, color: "rgba(14,23,38,0.4)", margin: "0 0 36px" }}>This usually takes 1–3 minutes. Please keep this tab open.</p>
                  <div style={{ display: "flex", flexDirection: "column", gap: 10, textAlign: "left", maxWidth: 260, margin: "0 auto" }}>
                    {["Scraping public posts", "Running AI risk analysis", "Generating PDF report"].map((m) => (
                      <div key={m} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13, color: "var(--ink-soft)" }}>
                        <Loader2 style={{ width: 13, height: 13, color: "var(--ink)", flexShrink: 0, animation: "spin 1s linear infinite" }} />
                        {m}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Error */}
              {error && (
                <div style={{ marginTop: 16, display: "flex", alignItems: "flex-start", gap: 10, background: "rgba(200,59,59,0.08)", border: "1px solid rgba(200,59,59,0.25)", color: "var(--flag-red)", padding: "12px 16px", borderRadius: 10, fontSize: 13 }}>
                  <AlertCircle style={{ width: 15, height: 15, flexShrink: 0, marginTop: 1 }} />
                  {error}
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          {step < 3 && (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0 36px 32px" }}>
              {step > 0 ? (
                <button onClick={goBack} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 14, fontWeight: 600, color: "var(--ink-soft)", background: "none", border: "none", cursor: "pointer", fontFamily: "Inter Tight, system-ui, sans-serif" }}>
                  <ChevronLeft style={{ width: 16, height: 16 }} /> Back
                </button>
              ) : <div />}
              {step < totalSteps - 1 ? (
                <button onClick={handleNext} style={{
                  display: "inline-flex", alignItems: "center", gap: 10,
                  padding: "14px 28px", borderRadius: 999,
                  background: "var(--ink)", color: "var(--paper)",
                  fontSize: 15, fontWeight: 600, border: "none", cursor: "pointer",
                  fontFamily: "Inter Tight, system-ui, sans-serif",
                  transition: "background 0.2s, transform 0.15s",
                }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "var(--oxblood)"; (e.currentTarget as HTMLButtonElement).style.transform = "translateY(-1px)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "var(--ink)"; (e.currentTarget as HTMLButtonElement).style.transform = "none"; }}
                >
                  Continue <ChevronRight style={{ width: 16, height: 16 }} />
                </button>
              ) : (
                <button onClick={handleSubmit} style={{
                  display: "inline-flex", alignItems: "center", gap: 10,
                  padding: "14px 32px", borderRadius: 999,
                  background: "var(--ink)", color: "var(--paper)",
                  fontSize: 15, fontWeight: 600, border: "none", cursor: "pointer",
                  fontFamily: "Inter Tight, system-ui, sans-serif",
                  transition: "background 0.2s, transform 0.15s",
                }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "var(--oxblood)"; (e.currentTarget as HTMLButtonElement).style.transform = "translateY(-1px)"; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLButtonElement).style.background = "var(--ink)"; (e.currentTarget as HTMLButtonElement).style.transform = "none"; }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                    <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z" fill="var(--paper)" opacity="0.9"/>
                    <path d="M9 12l2 2 4-4" stroke="var(--ink)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  Get My Screening Report
                </button>
              )}
            </div>
          )}
        </div>

        {/* Footer note */}
        <p style={{ textAlign: "center", fontSize: 12, color: "rgba(14,23,38,0.4)", marginTop: 24, fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.05em" }}>
          Powered by VisaFootprint · INA §212-grounded AI · No passwords required
        </p>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
