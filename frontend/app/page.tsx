"use client";
import Link from "next/link";
import { motion, useInView } from "framer-motion";
import { useRef, useState } from "react";
import {
  Shield, FileText, Brain, Globe, Zap, Lock,
  CheckCircle, ChevronDown, Star, ArrowRight,
  AlertTriangle, TrendingUp, Users
} from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};
const stagger = { hidden: {}, show: { transition: { staggerChildren: 0.12 } } };

function InView({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  return (
    <motion.div ref={ref} variants={stagger} initial="hidden" animate={inView ? "show" : "hidden"} className={className}>
      {children}
    </motion.div>
  );
}

function Hero() {
  return (
    <section className="hero-gradient min-h-screen flex items-center justify-center relative overflow-hidden pt-16">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-cyan-400/10 rounded-full blur-3xl pointer-events-none" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10 py-24">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
          <div className="inline-flex items-center gap-2 bg-blue-600/20 border border-blue-500/30 text-blue-300 text-sm font-medium px-4 py-1.5 rounded-full mb-6">
            <Brain className="w-4 h-4" />
            Powered by GPT-4o AI
          </div>
        </motion.div>
        <motion.h1
          initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.1 }}
          className="text-4xl sm:text-5xl lg:text-7xl font-extrabold text-white leading-tight mb-6"
        >
          Know Your Risk<br />
          <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
            Before Your Visa Interview
          </span>
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.2 }}
          className="text-slate-300 text-lg sm:text-xl max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          US visa authorities now screen social media. Our AI analyzes your profiles for red flags
          and generates a detailed risk report — so you can fix issues before they cost you your visa.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-4 justify-center mb-14"
        >
          <Link href="/screen" className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-bold px-8 py-4 rounded-xl text-lg transition-all duration-200 hover:scale-105 active:scale-95 shadow-xl shadow-blue-600/30">
            Get My Free Screening Report <ArrowRight className="w-5 h-5" />
          </Link>
          <Link href="/pricing" className="inline-flex items-center gap-2 border border-white/30 hover:border-white/60 text-white font-semibold px-8 py-4 rounded-xl text-lg transition-all duration-200 hover:bg-white/5">
            View Pricing
          </Link>
        </motion.div>
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.8, delay: 0.5 }}
          className="grid grid-cols-2 sm:grid-cols-4 gap-6 max-w-3xl mx-auto"
        >
          {[["10,000+","Profiles Screened"],["99%","Accuracy Rate"],["< 3 min","Average Report Time"],["50+","Countries Served"]].map(([val,label]) => (
            <div key={label} className="text-center">
              <div className="text-2xl font-extrabold text-white">{val}</div>
              <div className="text-xs text-slate-400 mt-1">{label}</div>
            </div>
          ))}
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.6 }}
          className="mt-16 max-w-sm mx-auto"
        >
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-5 text-left">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="text-white font-bold text-sm">Sample Report Preview</div>
                <div className="text-slate-400 text-xs">John D. · India → USA · B1/B2 Visa</div>
              </div>
              <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 text-xs font-bold px-2.5 py-1 rounded-full">MEDIUM RISK</span>
            </div>
            <div className="grid grid-cols-3 gap-2 mb-3">
              {[["Political",42],["Content",38],["Network",25]].map(([l,v]) => (
                <div key={l as string} className="bg-white/5 rounded-lg p-2 text-center">
                  <div className="text-white font-bold text-lg">{v}</div>
                  <div className="text-slate-400 text-xs">{l}</div>
                </div>
              ))}
            </div>
            <div className="text-xs text-slate-400"><span className="text-amber-400 font-semibold">2 flagged posts</span> · 34 posts analyzed · 3 platforms</div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

type TrustItem = { icon: React.ElementType; text: string };

function TrustBar() {
  const items: TrustItem[] = [
    { icon: Lock,     text: "256-bit Encrypted" },
    { icon: Shield,   text: "GDPR Compliant" },
    { icon: Brain,    text: "GPT-4o Powered" },
    { icon: Globe,    text: "6 Platforms" },
    { icon: FileText, text: "PDF Report" },
    { icon: Zap,      text: "Results in Minutes" },
  ];
  return (
    <section className="bg-slate-50 border-y border-slate-200 py-5">
      <div className="max-w-7xl mx-auto px-4 overflow-hidden">
        <div className="flex flex-wrap justify-center gap-6 sm:gap-10">
          {items.map(({ icon: Icon, text }) => (
            <div key={text} className="flex items-center gap-2 text-slate-600 text-sm font-medium">
              <Icon className="w-4 h-4 text-blue-600" />{text}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { n:"01", icon:FileText, title:"Submit Your Details", desc:"Fill in your name, country, and paste your social media profile URLs. Supports Twitter, Instagram, TikTok, LinkedIn, Facebook and more." },
    { n:"02", icon:Brain, title:"AI Analyzes Your Content", desc:"GPT-4o scrapes publicly visible posts and evaluates them against USCIS screening criteria and INA §212 grounds of inadmissibility." },
    { n:"03", icon:FileText, title:"Get Your PDF Report", desc:"Receive a detailed risk report with flagged posts, risk scores, network analysis and actionable recommendations to improve your chances." },
  ];
  return (
    <section id="how-it-works" className="py-20 lg:py-28 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <InView>
          <motion.div variants={fadeUp} className="text-center mb-14">
            <div className="text-blue-600 font-semibold text-sm uppercase tracking-widest mb-3">Simple Process</div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 mb-4">How It Works</h2>
            <p className="text-slate-500 max-w-xl mx-auto">From submission to report in under 3 minutes. No account required.</p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {steps.map((s) => (
              <motion.div key={s.n} variants={fadeUp} className="relative bg-white border border-slate-200 rounded-2xl p-8 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
                <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mb-5"><s.icon className="w-6 h-6 text-white" /></div>
                <div className="absolute top-6 right-6 text-5xl font-extrabold text-slate-100 select-none">{s.n}</div>
                <h3 className="text-lg font-bold text-slate-900 mb-3">{s.title}</h3>
                <p className="text-slate-500 text-sm leading-relaxed">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </InView>
      </div>
    </section>
  );
}

function Features() {
  const features = [
    { icon:Brain, title:"GPT-4o AI Analysis", desc:"Deep semantic analysis of posts — not just keyword matching." },
    { icon:AlertTriangle, title:"INA §212 Risk Screening", desc:"Checks against all grounds of inadmissibility including security, extremism, and criminal activity." },
    { icon:FileText, title:"Professional PDF Report", desc:"Branded PDF with risk scores, flagged posts, network analysis and recommendations." },
    { icon:Globe, title:"Multi-Platform Coverage", desc:"Twitter/X, Instagram, TikTok, LinkedIn, Facebook, YouTube — up to 10 accounts." },
    { icon:TrendingUp, title:"Risk Score Breakdown", desc:"Separate Political, Content, and Network risk scores with a composite overall rating." },
    { icon:Lock, title:"Privacy First", desc:"No passwords needed. Analysis is based on publicly visible content only." },
    { icon:Zap, title:"Fast Results", desc:"Most reports ready in under 3 minutes, before your interview not after." },
    { icon:Users, title:"Network Analysis", desc:"Analyze the risk profile of your public social connections and interactions." },
    { icon:Shield, title:"Actionable Recommendations", desc:"Specific advice on which posts to remove or privatize before your visa interview." },
  ];
  return (
    <section id="features" className="py-20 lg:py-28 bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <InView>
          <motion.div variants={fadeUp} className="text-center mb-14">
            <div className="text-blue-600 font-semibold text-sm uppercase tracking-widest mb-3">Why VisaScreenAI</div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 mb-4">Everything You Need to Screen With Confidence</h2>
          </motion.div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <motion.div key={f.title} variants={fadeUp} className="bg-white rounded-2xl p-6 border border-slate-200 hover:border-blue-300 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group">
                <div className="w-10 h-10 bg-blue-50 group-hover:bg-blue-600 rounded-xl flex items-center justify-center mb-4 transition-colors duration-300">
                  <f.icon className="w-5 h-5 text-blue-600 group-hover:text-white transition-colors duration-300" />
                </div>
                <h3 className="font-bold text-slate-900 mb-2">{f.title}</h3>
                <p className="text-slate-500 text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </InView>
      </div>
    </section>
  );
}

function PricingPreview() {
  const plans = [
    { name:"Free", price:"$0", period:"", highlight:false, cta:"Get Started Free", href:"/screen",
      features:["1 social media account","Basic AI analysis","Summary report only","Email delivery"] },
    { name:"Basic", price:"$19", period:"/report", highlight:true, cta:"Buy Report", href:"/pricing",
      features:["Up to 3 accounts","Full AI risk analysis","PDF report download","All platforms","Flagged post details"] },
    { name:"Pro", price:"$49", period:"/report", highlight:false, cta:"Go Pro", href:"/pricing",
      features:["Up to 10 accounts","Priority processing","Network risk analysis","Full PDF report","Recommendations","Email support"] },
  ];
  return (
    <section className="py-20 lg:py-28 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <InView>
          <motion.div variants={fadeUp} className="text-center mb-14">
            <div className="text-blue-600 font-semibold text-sm uppercase tracking-widest mb-3">Pricing</div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 mb-4">Simple, Transparent Pricing</h2>
            <p className="text-slate-500 max-w-xl mx-auto">No subscription. Pay per report. Your privacy is not a product.</p>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {plans.map((plan) => (
              <motion.div key={plan.name} variants={fadeUp}
                className={`relative rounded-2xl p-8 border-2 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl ${plan.highlight ? "bg-[#0A1628] border-blue-600 shadow-xl shadow-blue-600/20" : "bg-white border-slate-200 hover:border-blue-300"}`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-blue-600 text-white text-xs font-bold px-4 py-1 rounded-full">MOST POPULAR</span>
                  </div>
                )}
                <div className={plan.highlight ? "text-white" : "text-slate-900"}>
                  <div className="font-bold text-sm mb-2 uppercase tracking-wide opacity-60">{plan.name}</div>
                  <div className="text-4xl font-extrabold mb-1">{plan.price}<span className="text-base font-normal opacity-60">{plan.period}</span></div>
                  <ul className="mt-6 space-y-3 mb-8">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-center gap-2 text-sm">
                        <CheckCircle className={`w-4 h-4 flex-shrink-0 ${plan.highlight ? "text-blue-400" : "text-green-500"}`} />
                        <span className="opacity-80">{f}</span>
                      </li>
                    ))}
                  </ul>
                  <Link href={plan.href} className={`block text-center font-bold py-3 rounded-xl transition-all duration-200 hover:scale-105 active:scale-95 ${plan.highlight ? "bg-blue-600 hover:bg-blue-500 text-white shadow-lg" : "bg-slate-100 hover:bg-slate-200 text-slate-900"}`}>
                    {plan.cta}
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        </InView>
      </div>
    </section>
  );
}

const faqs = [
  { q:"Do US visa authorities actually check social media?", a:"Yes. USCIS and consular officers have been screening social media since 2019. They check Twitter/X, Facebook, Instagram, YouTube, LinkedIn and more." },
  { q:"What content can get my visa denied?", a:"Content flagged under INA §212 includes: terrorism-related speech, threats of violence, support for illegal immigration facilitation, certain political extremism, and connections to criminal networks." },
  { q:"Do you store my social media passwords?", a:"Never. We only analyze publicly visible content from profile URLs you provide. We do not require, request, or store any credentials." },
  { q:"How accurate is the AI analysis?", a:"Our GPT-4o model is calibrated to match the judgment of immigration compliance experts. It is not a substitute for legal advice, but it gives you a reliable pre-screening baseline." },
  { q:"How long does it take to get my report?", a:"Most reports are ready in under 3 minutes. Larger submissions with 10 accounts may take up to 8 minutes." },
  { q:"What should I do if I have HIGH risk posts?", a:"Your report includes specific recommendations. Generally: set the post to private, delete it, or be prepared to address it with a consular officer. Consult an immigration attorney for serious flags." },
];

function FAQ() {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <section id="faq" className="py-20 lg:py-28 bg-slate-50">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <InView>
          <motion.div variants={fadeUp} className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 mb-4">Frequently Asked Questions</h2>
          </motion.div>
          <div className="space-y-3">
            {faqs.map((faq, i) => (
              <motion.div key={i} variants={fadeUp} className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                <button onClick={() => setOpen(open === i ? null : i)} className="w-full flex items-center justify-between px-6 py-5 text-left font-semibold text-slate-900 hover:bg-slate-50 transition-colors">
                  {faq.q}
                  <ChevronDown className={`w-5 h-5 text-slate-400 flex-shrink-0 ml-4 transition-transform duration-300 ${open === i ? "rotate-180" : ""}`} />
                </button>
                {open === i && <div className="px-6 pb-5 text-slate-600 text-sm leading-relaxed">{faq.a}</div>}
              </motion.div>
            ))}
          </div>
        </InView>
      </div>
    </section>
  );
}

function CTABanner() {
  return (
    <section className="hero-gradient py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <InView>
          <motion.div variants={fadeUp}>
            <div className="flex justify-center mb-4">{[...Array(5)].map((_,i) => <Star key={i} className="w-5 h-5 text-yellow-400 fill-yellow-400" />)}</div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4">Don&apos;t Let a Tweet Cost You Your Visa</h2>
            <p className="text-slate-300 text-lg mb-8 max-w-xl mx-auto">Join thousands of applicants who screened their profiles before their US visa interview. Your free report takes under 3 minutes.</p>
            <Link href="/screen" className="inline-flex items-center gap-2 bg-white text-[#0A1628] font-bold px-8 py-4 rounded-xl text-lg hover:bg-blue-50 transition-all duration-200 hover:scale-105 active:scale-95 shadow-xl">
              Get My Free Report Now <ArrowRight className="w-5 h-5" />
            </Link>
          </motion.div>
        </InView>
      </div>
    </section>
  );
}

export default function HomePage() {
  return (
    <>
      <Hero />
      <TrustBar />
      <HowItWorks />
      <Features />
      <PricingPreview />
      <FAQ />
      <CTABanner />
    </>
  );
}
