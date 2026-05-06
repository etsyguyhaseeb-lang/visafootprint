"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Shield, Download, AlertTriangle, CheckCircle, Info,
  ChevronDown, ChevronUp, Globe, ArrowLeft, Loader2
} from "lucide-react";
import { getReport, getPdfUrl, type ReportData, type FlaggedPost } from "@/lib/api";

const PLATFORM_ICONS: Record<string, string> = {
  "Twitter/X": "🐦", Instagram: "📷", TikTok: "🎵",
  LinkedIn: "💼", Facebook: "📘", YouTube: "▶️",
};

function riskColor(level: string) {
  const l = level?.toUpperCase();
  if (l === "HIGH")   return "text-red-600 bg-red-50 border-red-200";
  if (l === "MEDIUM") return "text-amber-600 bg-amber-50 border-amber-200";
  return "text-green-600 bg-green-50 border-green-200";
}

function riskDot(level: string) {
  const l = level?.toUpperCase();
  if (l === "HIGH")   return "bg-red-500";
  if (l === "MEDIUM") return "bg-amber-500";
  return "bg-green-500";
}

function scoreColor(score: number) {
  if (score >= 60) return "text-red-600";
  if (score >= 30) return "text-amber-600";
  return "text-green-600";
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  const color = score >= 60 ? "bg-red-500" : score >= 30 ? "bg-amber-500" : "bg-green-500";
  const textColor = score >= 60 ? "text-red-600" : score >= 30 ? "text-amber-600" : "text-green-600";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</span>
        <span className={`text-sm font-extrabold ${textColor}`}>{score}</span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${color}`}
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 1.2, ease: "easeOut", delay: 0.3 }}
        />
      </div>
    </div>
  );
}

function FlaggedCard({ post }: { post: FlaggedPost }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`border rounded-xl overflow-hidden transition-all duration-200 ${riskColor(post.risk_level)} border`}>
      <button onClick={() => setOpen((v) => !v)} className="w-full text-left p-4 flex items-start justify-between gap-3 hover:opacity-90 transition-opacity">
        <div className="flex items-start gap-3 min-w-0">
          <span className={`inline-flex items-center gap-1 text-xs font-bold px-2.5 py-1 rounded-full border flex-shrink-0 ${riskColor(post.risk_level)}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${riskDot(post.risk_level)}`} />
            {post.risk_level}
          </span>
          <div className="min-w-0">
            <div className="font-semibold text-sm truncate">{post.risk_category}</div>
            <div className="text-xs opacity-70 mt-0.5">
              {PLATFORM_ICONS[post.platform] ?? "📱"} {post.platform} {post.date ? `· ${post.date}` : ""}
            </div>
          </div>
        </div>
        {open ? <ChevronUp className="w-4 h-4 flex-shrink-0 mt-0.5" /> : <ChevronDown className="w-4 h-4 flex-shrink-0 mt-0.5" />}
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-current border-opacity-20">
          <blockquote className="bg-white/60 rounded-lg p-3 text-sm italic text-slate-700 leading-relaxed mt-3">
            &ldquo;{post.text}&rdquo;
          </blockquote>
          <p className="text-sm leading-relaxed">{post.explanation}</p>
        </div>
      )}
    </div>
  );
}

function SentimentBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-slate-500 w-16 flex-shrink-0">{label}</span>
      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
        <motion.div className={`h-full rounded-full ${color}`} initial={{ width: 0 }} animate={{ width: `${value}%` }} transition={{ duration: 1, delay: 0.5 }} />
      </div>
      <span className="text-xs font-semibold text-slate-600 w-8 text-right">{value}%</span>
    </div>
  );
}

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  useEffect(() => {
    if (!id) return;
    getReport(id)
      .then((data) => { setReport(data); setLoading(false); })
      .catch((e) => { setErr(e.message); setLoading(false); });
  }, [id]);

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 pt-16">
      <div className="text-center">
        <Loader2 className="w-10 h-10 text-blue-600 animate-spin mx-auto mb-4" />
        <p className="text-slate-500">Loading your report…</p>
      </div>
    </div>
  );

  if (err || !report) return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 pt-16">
      <div className="text-center max-w-sm px-4">
        <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-4" />
        <h2 className="text-lg font-bold text-slate-900 mb-2">Report Not Found</h2>
        <p className="text-slate-500 text-sm mb-4">{err || "This report may still be processing. Please wait a moment and refresh."}</p>
        <Link href="/screen" className="text-blue-600 font-semibold text-sm hover:underline">Start a new screening →</Link>
      </div>
    </div>
  );

  const overall = report.overall_risk ?? "LOW";
  const overallBadge = riskColor(overall);

  return (
    <div className="min-h-screen bg-slate-50 pt-20 pb-16">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Back */}
        <Link href="/" className="inline-flex items-center gap-1 text-slate-500 hover:text-slate-700 text-sm font-medium mb-6 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to Home
        </Link>

        {/* Report header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-600 to-blue-800 rounded-2xl flex items-center justify-center text-white font-extrabold text-xl shadow-lg">
                {(report.name ?? "?")[0].toUpperCase()}
              </div>
              <div>
                <h1 className="text-xl font-extrabold text-slate-900">{report.name}</h1>
                <div className="text-sm text-slate-500 mt-0.5 flex items-center gap-2">
                  <Globe className="w-3.5 h-3.5" /> {report.country}
                  <span className="text-slate-300">·</span>
                  {report.posts_analyzed ?? 0} posts analyzed
                  <span className="text-slate-300">·</span>
                  {(report.platforms_analyzed ?? []).length} platforms
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center gap-2 text-sm font-bold px-4 py-2 rounded-full border ${overallBadge}`}>
                <span className={`w-2 h-2 rounded-full ${riskDot(overall)}`} />
                {overall} RISK
              </span>
              <a href={getPdfUrl(id!)} target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 shadow-lg">
                <Download className="w-4 h-4" /> Download PDF
              </a>
            </div>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column */}
          <div className="lg:col-span-2 space-y-6">

            {/* AI Summary */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-3 flex items-center gap-2">
                <Shield className="w-5 h-5 text-blue-600" /> AI Summary
              </h2>
              <p className="text-slate-600 text-sm leading-relaxed">{report.summary}</p>
              {(report.risk_topics ?? []).length > 0 && (
                <div className="flex flex-wrap gap-2 mt-4">
                  {report.risk_topics.map((t) => (
                    <span key={t} className="bg-slate-100 text-slate-700 text-xs font-medium px-3 py-1 rounded-full">{t}</span>
                  ))}
                </div>
              )}
            </motion.div>

            {/* Flagged posts */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                Flagged Content
                <span className="ml-auto text-xs font-medium bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full">
                  {(report.flagged_posts ?? []).length} posts
                </span>
              </h2>
              {(report.flagged_posts ?? []).length === 0 ? (
                <div className="flex items-center gap-2 text-green-700 bg-green-50 rounded-xl p-4 text-sm">
                  <CheckCircle className="w-4 h-4 flex-shrink-0" />
                  No concerning posts identified. Your profile looks clean.
                </div>
              ) : (
                <div className="space-y-3">
                  {report.flagged_posts.map((fp, i) => <FlaggedCard key={i} post={fp} />)}
                </div>
              )}
            </motion.div>

            {/* Recommendations */}
            {(report.recommendations ?? []).length > 0 && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
                className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
                <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
                  <Info className="w-5 h-5 text-blue-600" /> Recommendations
                </h2>
                <ul className="space-y-3">
                  {report.recommendations.map((r, i) => (
                    <li key={i} className="flex items-start gap-3 text-sm text-slate-700">
                      <span className="w-6 h-6 bg-blue-600 text-white text-xs font-bold rounded-full flex items-center justify-center flex-shrink-0">{i + 1}</span>
                      {r}
                    </li>
                  ))}
                </ul>
              </motion.div>
            )}
          </div>

          {/* Right column */}
          <div className="space-y-6">

            {/* Risk scores */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-base font-bold text-slate-900 mb-4">Risk Scores</h2>
              <div className="space-y-3 mb-4">
                <ScoreBar score={report.scores?.political ?? 0} label="Political" />
                <ScoreBar score={report.scores?.content ?? 0}   label="Content" />
                <ScoreBar score={report.scores?.network ?? 0}   label="Network" />
              </div>
              <div className="pt-4 border-t border-slate-100 text-center">
                <div className={`text-3xl font-extrabold ${scoreColor(report.risk_score ?? 0)}`}>{report.risk_score ?? 0}</div>
                <div className="text-xs text-slate-400 mt-0.5">Overall Risk Score</div>
              </div>
            </motion.div>

            {/* Sentiment */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-base font-bold text-slate-900 mb-4">Content Sentiment</h2>
              <div className="space-y-3">
                <SentimentBar label="Positive" value={report.sentiment?.positive ?? 0} color="bg-green-500" />
                <SentimentBar label="Neutral"  value={report.sentiment?.neutral ?? 0}  color="bg-slate-300" />
                <SentimentBar label="Negative" value={report.sentiment?.negative ?? 0} color="bg-red-500" />
              </div>
            </motion.div>

            {/* Overall assessment */}
            {report.overall_assessment && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }}
                className="bg-[#0A1628] rounded-2xl p-6 text-white">
                <h2 className="text-base font-bold mb-3 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-400" /> Overall Assessment
                </h2>
                <p className="text-slate-300 text-sm leading-relaxed">{report.overall_assessment}</p>
              </motion.div>
            )}

            {/* Download CTA */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
              className="bg-blue-600 rounded-2xl p-5 text-white text-center">
              <Download className="w-6 h-6 mx-auto mb-2 text-blue-200" />
              <div className="font-bold mb-1">Download Full PDF Report</div>
              <div className="text-blue-200 text-xs mb-3">Includes all flagged posts, risk analysis, and recommendations</div>
              <a href={getPdfUrl(id!)} target="_blank" rel="noopener noreferrer"
                className="block bg-white text-blue-700 font-bold py-2.5 rounded-xl text-sm hover:bg-blue-50 transition-colors">
                Download PDF
              </a>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
