"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { Shield, Plus, Trash2, ChevronRight, ChevronLeft, CheckCircle, Loader2, AlertCircle, ChevronDown } from "lucide-react";
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
// All platforms are auto-scraped via Apify
const AUTO_SCRAPE_PLATFORMS = new Set(["Twitter/X","Instagram","TikTok","LinkedIn","Facebook","YouTube"]);
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
    if (accounts.length < 10) setAccounts([...accounts, { platform: "Twitter/X", handle: "" }]);
  };
  const removeAccount = (i: number) => {
    setAccounts(accounts.filter((_, idx) => idx !== i));
    setExpandedPaste((prev) => {
      const next = new Set(prev);
      next.delete(i);
      return next;
    });
  };
  const updateAccount = (i: number, field: "platform" | "handle" | "manual_posts", val: string) => {
    setAccounts(accounts.map((a, idx) => idx === i ? { ...a, [field]: val } : a));
  };
  const togglePaste = (i: number) => {
    setExpandedPaste((prev) => {
      const next = new Set(prev);
      next.has(i) ? next.delete(i) : next.add(i);
      return next;
    });
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
      const valid = accounts.filter((a) => a.handle.trim());
      if (!valid.length) { setError("Add at least one social media account."); return false; }
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
    goNext(); // step 3 = processing
    const msgs = [
      "Connecting to social media platforms…",
      "Scraping publicly visible posts…",
      "Running AI risk analysis…",
      "Generating your PDF report…",
      "Finalizing report…",
    ];
    let mi = 0;
    const interval = setInterval(() => {
      mi = (mi + 1) % msgs.length;
      setProcessingMsg(msgs[mi]);
    }, 4000);

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
        if (status.status === "done") {
          clearInterval(interval);
          router.push(`/report/${jobId}`);
        } else if (status.status === "failed") {
          clearInterval(interval);
          setError(status.error ?? "Screening failed. Please try again.");
          setStep(2);
        } else {
          setTimeout(poll, 3000);
        }
      };
      setTimeout(poll, 3000);
    } catch (e: unknown) {
      clearInterval(interval);
      setError(e instanceof Error ? e.message : "Submission failed. Please try again.");
      setStep(2);
    }
  };

  const stepLabels = ["Your Info", "Accounts", "Preferences", "Processing"];
  const totalSteps = 3;

  return (
    <div className="min-h-screen bg-slate-50 pt-24 pb-16 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-600 rounded-2xl mb-4 shadow-lg shadow-blue-600/30">
            <Shield className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 mb-2">Social Media Screening</h1>
          <p className="text-slate-500">Get your AI-powered visa risk report in minutes</p>
        </div>

        {/* Progress */}
        {step < 3 && (
          <div className="relative flex items-start justify-between mb-8 px-4">
            {/* Track line sits at circle centre (16px = half of h-8) */}
            <div className="absolute top-4 left-12 right-12 h-0.5 bg-slate-200" />
            <div
              className="absolute top-4 left-12 h-0.5 bg-blue-600 transition-all duration-500"
              style={{ width: step === 0 ? "0%" : step === 1 ? "50%" : "100%" }}
            />

            {stepLabels.slice(0, 3).map((label, i) => (
              <div key={i} className="relative z-10 flex flex-col items-center gap-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
                  i < step
                    ? "bg-blue-600 text-white"
                    : i === step
                    ? "bg-blue-600 text-white ring-4 ring-blue-100"
                    : "bg-white border-2 border-slate-200 text-slate-400"
                }`}>
                  {i < step ? <CheckCircle className="w-4 h-4" /> : i + 1}
                </div>
                <span className={`text-xs font-medium ${i <= step ? "text-blue-600" : "text-slate-400"}`}>
                  {label}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <AnimatePresence mode="wait" custom={dir}>
            <motion.div
              key={step}
              custom={dir}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              className="p-8"
            >
              {/* Step 0 — Personal info */}
              {step === 0 && (
                <div className="space-y-5">
                  <h2 className="text-xl font-bold text-slate-900">Your Information</h2>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">Full Name *</label>
                    <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your full name"
                      className="w-full border border-slate-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">Email Address *</label>
                    <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="your.email@example.com"
                      className="w-full border border-slate-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-1.5">Country of Origin *</label>
                    <input value={countrySearch} onChange={(e) => { setCountrySearch(e.target.value); setCountry(""); }} placeholder="Search country…"
                      className="w-full border border-slate-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all mb-1" />
                    {countrySearch && !country && (
                      <div className="border border-slate-200 rounded-xl max-h-48 overflow-y-auto shadow-lg bg-white z-10">
                        {filteredCountries.slice(0, 20).map((c) => (
                          <button key={c} onClick={() => { setCountry(c); setCountrySearch(c); }}
                            className="w-full text-left px-4 py-2.5 text-sm hover:bg-blue-50 hover:text-blue-700 transition-colors">{c}</button>
                        ))}
                        {filteredCountries.length === 0 && <div className="px-4 py-3 text-slate-400 text-sm">No matches</div>}
                      </div>
                    )}
                    {country && <div className="text-xs text-green-600 font-medium mt-1 flex items-center gap-1"><CheckCircle className="w-3 h-3" />{country}</div>}
                  </div>
                </div>
              )}

              {/* Step 1 — Social media accounts */}
              {step === 1 && (
                <div className="space-y-5">
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">Social Media Accounts</h2>
                    <p className="text-sm text-slate-500 mt-1">All platforms are automatically scraped. Just enter your username or profile URL and we handle the rest.</p>
                  </div>
                  <div className="space-y-3">
                    {accounts.map((acc, i) => (
                      <div key={i} className="border border-slate-200 rounded-xl overflow-hidden">
                        <div className="flex gap-2 items-center p-3">
                          <select value={acc.platform} onChange={(e) => updateAccount(i, "platform", e.target.value)}
                            className="border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white w-32 flex-shrink-0">
                            {PLATFORMS.map((p) => <option key={p}>{p}</option>)}
                          </select>
                          <input value={acc.handle} onChange={(e) => updateAccount(i, "handle", e.target.value)}
                            placeholder="@handle or profile URL"
                            className="flex-1 border border-slate-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" />
                          {AUTO_SCRAPE_PLATFORMS.has(acc.platform) ? (
                            <span className="text-xs font-medium text-green-700 bg-green-50 border border-green-200 px-2 py-1.5 rounded-lg flex-shrink-0">
                              Auto
                            </span>
                          ) : (
                            <button onClick={() => togglePaste(i)}
                              title="Paste posts — required for this platform"
                              className={`p-2.5 rounded-xl text-xs font-semibold transition-colors flex items-center gap-1 flex-shrink-0 ${expandedPaste.has(i) ? "bg-blue-100 text-blue-700" : "bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100"}`}>
                              Paste posts <ChevronDown className={`w-3 h-3 transition-transform ${expandedPaste.has(i) ? "rotate-180" : ""}`} />
                            </button>
                          )}
                          {accounts.length > 1 && (
                            <button onClick={() => removeAccount(i)} className="p-2.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-colors flex-shrink-0">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                        {expandedPaste.has(i) && (
                          <div className="border-t border-slate-100 bg-slate-50 px-3 pb-3 pt-2">
                            <label className="text-xs font-semibold text-amber-700 mb-1.5 block">
                              {acc.platform} cannot be auto-scraped — paste recent posts below
                            </label>
                            <textarea
                              value={acc.manual_posts ?? ""}
                              onChange={(e) => updateAccount(i, "manual_posts", e.target.value)}
                              rows={5}
                              placeholder={"Paste recent posts, one per line or separated by blank lines.\n\nExample:\nJust landed in New York! Excited for the future.\n\nAttended a community event last week."}
                              className="w-full border border-slate-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-white transition-all"
                            />
                            <p className="text-xs text-slate-400 mt-1">Copy posts from your profile page and paste them here. The AI will analyze these.</p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                  {accounts.length < 10 && (
                    <button onClick={addAccount} className="flex items-center gap-2 text-blue-600 font-semibold text-sm hover:text-blue-700 transition-colors">
                      <Plus className="w-4 h-4" /> Add Another Account ({accounts.length}/10)
                    </button>
                  )}
                  <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 text-xs text-blue-700 leading-relaxed">
                    <strong>Privacy Notice:</strong> We only analyze publicly visible posts. We do not require your passwords or store your credentials.
                    Your information is encrypted and used solely for screening purposes. Each email can be used for up to 3 submissions.
                  </div>
                </div>
              )}

              {/* Step 2 — Reason + timeline + consent */}
              {step === 2 && (
                <div className="space-y-6">
                  <h2 className="text-xl font-bold text-slate-900">Screening Preferences</h2>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-3">What&apos;s your reason for social media screening? *</label>
                    <div className="space-y-2">
                      {REASONS.map((r) => (
                        <label key={r} className={`flex items-center gap-3 p-3.5 rounded-xl border-2 cursor-pointer transition-all duration-200 ${reason === r ? "border-blue-500 bg-blue-50" : "border-slate-200 hover:border-slate-300"}`}>
                          <input type="radio" name="reason" value={r} checked={reason === r} onChange={() => setReason(r)} className="accent-blue-600 w-4 h-4" />
                          <span className="text-sm font-medium text-slate-700">{r}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-3">When are you planning to apply for a visa? *</label>
                    <div className="grid grid-cols-2 gap-2">
                      {TIMELINES.map((t) => (
                        <label key={t} className={`flex items-center gap-2 p-3 rounded-xl border-2 cursor-pointer transition-all duration-200 text-sm font-medium ${timeline === t ? "border-blue-500 bg-blue-50 text-blue-700" : "border-slate-200 hover:border-slate-300 text-slate-700"}`}>
                          <input type="radio" name="timeline" value={t} checked={timeline === t} onChange={() => setTimeline(t)} className="accent-blue-600 w-4 h-4" />
                          {t}
                        </label>
                      ))}
                    </div>
                  </div>
                  <label className={`flex items-start gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 ${consent ? "border-blue-500 bg-blue-50" : "border-slate-200"}`}>
                    <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="accent-blue-600 w-4 h-4 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-slate-600 leading-relaxed">
                      I authorize VisaScreenAI to access and evaluate my submitted profiles for immigration social screening.
                    </span>
                  </label>
                </div>
              )}

              {/* Step 3 — Processing */}
              {step === 3 && (
                <div className="text-center py-8">
                  <div className="relative inline-flex items-center justify-center mb-6">
                    <div className="w-20 h-20 rounded-full border-4 border-blue-100 border-t-blue-600 animate-spin" />
                    <Shield className="absolute w-8 h-8 text-blue-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 mb-3">Analyzing Your Profiles</h2>
                  <p className="text-slate-500 text-sm mb-2">{processingMsg}</p>
                  <p className="text-slate-400 text-xs">This usually takes 1–3 minutes. Please keep this tab open.</p>
                  <div className="mt-8 space-y-2 text-left max-w-xs mx-auto">
                    {["Scraping public posts","Running AI risk analysis","Generating PDF report"].map((m) => (
                      <div key={m} className="flex items-center gap-2 text-sm text-slate-500">
                        <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin flex-shrink-0" />
                        {m}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Error */}
              {error && (
                <div className="mt-4 flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />{error}
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          {step < 3 && (
            <div className="flex justify-between items-center px-8 pb-8 pt-0">
              {step > 0 ? (
                <button onClick={goBack} className="flex items-center gap-1 text-slate-500 hover:text-slate-700 font-medium text-sm transition-colors">
                  <ChevronLeft className="w-4 h-4" /> Back
                </button>
              ) : <div />}
              {step < totalSteps - 1 ? (
                <button onClick={handleNext} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-6 py-3 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg">
                  Continue <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button onClick={handleSubmit} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-bold px-8 py-3 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg shadow-blue-600/30">
                  <Shield className="w-4 h-4" /> Get My Screening Report
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
