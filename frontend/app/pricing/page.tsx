"use client";
import Link from "next/link";
import { motion } from "framer-motion";
import { CheckCircle, Zap, Shield, Crown } from "lucide-react";

const plans = [
  {
    name: "Essential",
    icon: Shield,
    price: "$29",
    oldPrice: null,
    period: "/account",
    tagline: "Per social media account",
    highlight: false,
    cta: "Get Started",
    href: "/screen",
    badge: null,
    savingText: null,
    features: [
      "1 social media account",
      "Advanced AI analysis",
      "Essential risk report",
      "Risk scoring",
      "2–3 working days delivery",
    ],
  },
  {
    name: "3-Account Bundle",
    icon: Zap,
    price: "$75",
    oldPrice: "$87",
    period: "",
    tagline: "Best value for most applicants",
    highlight: true,
    cta: "Choose AI Scan",
    href: "/screen",
    badge: "MOST POPULAR",
    savingText: "Save $12 with the bundle",
    features: [
      "Up to 3 social media accounts",
      "Advanced AI analysis",
      "Comprehensive PDF report",
      "Risk scoring & flagged posts",
      "Post links & screenshots in report",
      "2–3 working days delivery",
    ],
  },
  {
    name: "Extensive Human Review",
    icon: Crown,
    price: "$200",
    oldPrice: "$250",
    period: "",
    tagline: "Expert human + AI screening",
    highlight: false,
    cta: "Express Interest – Save $50",
    href: "/screen",
    badge: null,
    savingText: "20% OFF – Limited Time",
    features: [
      "Unlimited social media accounts",
      "Everything in AI Scan",
      "Expert human review",
      "Immigration specialist insights",
      "Personalized action plan",
      "Priority support",
    ],
  },
];

const faqs = [
  { q: "Is my payment secure?", a: "Payments are processed via Stripe with 256-bit encryption. We never store your card details." },
  { q: "Do I get a refund if I'm not satisfied?", a: "Yes. If the report fails to generate due to a technical error, we'll refund you in full within 24 hours." },
  { q: "Can I buy multiple reports?", a: "Yes. Each email can submit up to 3 reports. For team or bulk use, contact us for enterprise pricing." },
  { q: "How quickly do I get my report?", a: "AI Scan reports are typically ready within 2–3 working days. Human Review reports take 3–5 working days." },
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
              No subscriptions. No hidden fees. Pay once, get your professional screening report.
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
                  ? "bg-white border-amber-400 shadow-2xl shadow-amber-400/20"
                  : "bg-white border-slate-200 hover:border-blue-300 shadow-sm"
              }`}
            >
              {plan.badge && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="bg-amber-400 text-slate-900 text-xs font-bold px-5 py-1.5 rounded-full shadow-lg tracking-wide">
                    {plan.badge}
                  </span>
                </div>
              )}

              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-5 ${
                plan.highlight ? "bg-amber-50" : "bg-blue-50"
              }`}>
                <plan.icon className={`w-6 h-6 ${plan.highlight ? "text-amber-500" : "text-blue-600"}`} />
              </div>

              <div className="text-slate-900 flex-1 flex flex-col">
                <div className="font-bold text-sm uppercase tracking-widest text-slate-500 mb-1">{plan.name}</div>

                <div className="flex items-baseline gap-2 mb-0.5">
                  {plan.oldPrice && (
                    <span className="text-xl font-bold text-slate-400 line-through">{plan.oldPrice}</span>
                  )}
                  <span className={`text-4xl font-extrabold ${plan.highlight ? "text-amber-500" : "text-slate-900"}`}>
                    {plan.price}
                  </span>
                  {plan.period && (
                    <span className="text-base font-normal text-slate-400">{plan.period}</span>
                  )}
                </div>

                {plan.savingText && (
                  <div className={`text-sm font-semibold mb-2 ${plan.highlight ? "text-amber-600" : "text-blue-600"}`}>
                    {plan.savingText}
                  </div>
                )}

                <p className="text-sm mt-1 mb-6 text-slate-500">{plan.tagline}</p>

                <ul className="space-y-2.5 mb-8 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm">
                      <CheckCircle className={`w-4 h-4 flex-shrink-0 mt-0.5 ${plan.highlight ? "text-amber-500" : "text-green-500"}`} />
                      <span className={`font-medium ${plan.features.indexOf(f) === 0 ? "font-bold text-slate-900" : "text-slate-700"}`}>{f}</span>
                    </li>
                  ))}
                </ul>

                <Link
                  href={plan.href}
                  className={`block text-center font-bold py-3.5 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 ${
                    plan.highlight
                      ? "bg-amber-400 hover:bg-amber-300 text-slate-900 shadow-lg"
                      : plan.name === "Extensive Human Review"
                      ? "bg-blue-600 hover:bg-blue-500 text-white shadow-lg"
                      : "bg-green-600 hover:bg-green-500 text-white shadow-lg"
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
            className="flex-shrink-0 bg-[#0A1628] text-white font-bold px-6 py-3 rounded-xl hover:bg-slate-800 transition-colors hover:scale-105 active:scale-95 duration-200">
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
          <p className="text-slate-500 text-sm mb-4">Starting at $29 per account — professional AI screening before your visa interview.</p>
          <Link href="/screen" className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-bold px-8 py-4 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 shadow-xl shadow-blue-600/20">
            <Shield className="w-5 h-5" /> Screen My Profile — From $29
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
