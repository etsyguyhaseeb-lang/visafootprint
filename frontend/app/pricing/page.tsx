"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { CheckCircle, X, Zap, Shield, Crown } from "lucide-react";

const plans = [
  {
    name: "Free",
    icon: Shield,
    price: "$0",
    period: "",
    tagline: "Try before you buy",
    highlight: false,
    cta: "Get Started Free",
    href: "/screen",
    features: [
      { text: "1 social media account", included: true },
      { text: "Basic AI risk analysis", included: true },
      { text: "Overall risk score", included: true },
      { text: "Summary report", included: true },
      { text: "PDF report download", included: false },
      { text: "Flagged post details", included: false },
      { text: "Network analysis", included: false },
      { text: "Actionable recommendations", included: false },
      { text: "Priority processing", included: false },
    ],
  },
  {
    name: "Basic",
    icon: Zap,
    price: "$19",
    period: "/report",
    tagline: "Everything most applicants need",
    highlight: true,
    cta: "Buy Report – $19",
    href: "/screen",
    badge: "Most Popular",
    features: [
      { text: "Up to 3 social media accounts", included: true },
      { text: "Full GPT-4o AI risk analysis", included: true },
      { text: "Overall + sub-risk scores", included: true },
      { text: "Detailed AI summary", included: true },
      { text: "PDF report download", included: true },
      { text: "Flagged post details", included: true },
      { text: "Network analysis", included: false },
      { text: "Actionable recommendations", included: true },
      { text: "Priority processing", included: false },
    ],
  },
  {
    name: "Pro",
    icon: Crown,
    price: "$49",
    period: "/report",
    tagline: "Maximum coverage and depth",
    highlight: false,
    cta: "Go Pro – $49",
    href: "/screen",
    features: [
      { text: "Up to 10 social media accounts", included: true },
      { text: "Full GPT-4o AI risk analysis", included: true },
      { text: "Overall + sub-risk scores", included: true },
      { text: "Detailed AI summary", included: true },
      { text: "PDF report download", included: true },
      { text: "Flagged post details", included: true },
      { text: "Network risk analysis", included: true },
      { text: "Actionable recommendations", included: true },
      { text: "Priority processing", included: true },
    ],
  },
];

const faqs = [
  { q: "Is my payment secure?", a: "Payments are processed via Stripe with 256-bit encryption. We never store your card details." },
  { q: "Do I get a refund if I'm not satisfied?", a: "Yes. If the report fails to generate due to a technical error, we'll refund you in full within 24 hours." },
  { q: "Can I buy multiple reports?", a: "Yes. Each email can submit up to 3 reports. For team or bulk use, contact us for enterprise pricing." },
  { q: "How quickly do I get my report?", a: "Free and Basic reports are typically ready in 1–3 minutes. Pro reports with 10 accounts may take up to 8 minutes." },
];

export default function PricingPage() {
  return (
    <div className="min-h-screen bg-white pt-20">
      {/* Hero */}
      <div className="hero-gradient py-20">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <h1 className="text-4xl sm:text-5xl font-extrabold text-white mb-4">Simple, Transparent Pricing</h1>
            <p className="text-slate-300 text-lg max-w-xl mx-auto">
              No subscriptions. No hidden fees. Pay once, get your report instantly.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Plans */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 -mt-12 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan, i) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className={`relative rounded-2xl p-8 border-2 flex flex-col transition-all duration-300 hover:-translate-y-1 hover:shadow-xl ${
                plan.highlight
                  ? "bg-[#0A1628] border-blue-600 shadow-2xl shadow-blue-600/20"
                  : "bg-white border-slate-200 hover:border-blue-300 shadow-sm"
              }`}
            >
              {plan.badge && (
                <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                  <span className="bg-blue-600 text-white text-xs font-bold px-4 py-1.5 rounded-full shadow-lg">{plan.badge}</span>
                </div>
              )}

              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-5 ${plan.highlight ? "bg-blue-600/30" : "bg-blue-50"}`}>
                <plan.icon className={`w-6 h-6 ${plan.highlight ? "text-blue-400" : "text-blue-600"}`} />
              </div>

              <div className={plan.highlight ? "text-white" : "text-slate-900"}>
                <div className="font-bold text-sm uppercase tracking-widest opacity-60 mb-1">{plan.name}</div>
                <div className="text-4xl font-extrabold mb-0.5">
                  {plan.price}<span className="text-base font-normal opacity-50">{plan.period}</span>
                </div>
                <p className={`text-sm mt-1 mb-6 ${plan.highlight ? "text-slate-400" : "text-slate-500"}`}>{plan.tagline}</p>

                <ul className="space-y-2.5 mb-8 flex-1">
                  {plan.features.map((f) => (
                    <li key={f.text} className={`flex items-center gap-2.5 text-sm ${f.included ? "" : "opacity-40"}`}>
                      {f.included
                        ? <CheckCircle className={`w-4 h-4 flex-shrink-0 ${plan.highlight ? "text-blue-400" : "text-green-500"}`} />
                        : <X className="w-4 h-4 flex-shrink-0 text-slate-400" />}
                      <span className={plan.highlight ? "text-slate-200" : "text-slate-700"}>{f.text}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href={plan.href}
                  className={`block text-center font-bold py-3.5 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 ${
                    plan.highlight
                      ? "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-600/30"
                      : "bg-slate-900 hover:bg-slate-700 text-white"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Enterprise */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8 bg-slate-50 border border-slate-200 rounded-2xl p-8 flex flex-col sm:flex-row items-center justify-between gap-4"
        >
          <div>
            <h3 className="text-lg font-bold text-slate-900">Enterprise / Law Firms</h3>
            <p className="text-slate-500 text-sm mt-1">Volume screening for immigration attorneys and HR teams. Custom pricing, API access, white-label reports.</p>
          </div>
          <a href="mailto:enterprise@visascreenai.com"
            className="flex-shrink-0 bg-[#0A1628] text-white font-bold px-6 py-3 rounded-xl hover:bg-navy-mid transition-colors hover:scale-105 active:scale-95 duration-200">
            Contact Sales
          </a>
        </motion.div>

        {/* FAQ */}
        <div className="mt-16">
          <h2 className="text-2xl font-extrabold text-slate-900 text-center mb-8">Pricing FAQ</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 max-w-4xl mx-auto">
            {faqs.map((faq, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + i * 0.05 }}
                className="bg-white border border-slate-200 rounded-xl p-5"
              >
                <h4 className="font-bold text-slate-900 text-sm mb-2">{faq.q}</h4>
                <p className="text-slate-500 text-sm leading-relaxed">{faq.a}</p>
              </motion.div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.7 }}
          className="text-center mt-14"
        >
          <p className="text-slate-500 text-sm mb-4">Start with the free report — no credit card required.</p>
          <Link href="/screen" className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-bold px-8 py-4 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 shadow-xl shadow-blue-600/20">
            <Shield className="w-5 h-5" /> Get My Free Report
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
