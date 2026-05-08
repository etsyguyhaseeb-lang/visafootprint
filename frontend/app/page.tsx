import Link from "next/link";
import s from "./home.module.css";
import CheckoutButton from "@/components/CheckoutButton";

export default function HomePage() {
  return (
    <div className={s.wrapper}>

      {/* HERO */}
      <div className={s.hero}>
        <div>
          <div className={s.eyebrow}>AI screening · INA §212-grounded · Trusted in 50+ countries</div>
          <h1 className={s.heroH1}>
            Find what USCIS<br />
            will find. <span className={s.accent}>Before<br />they find it.</span>
          </h1>
          <p className={s.lede}>
            Consular officers and USCIS adjudicators screen your social media as part of every visa
            decision. We scan it the same way they do — flag the posts that could deny your visa,
            and tell you exactly what to do about each one.
          </p>
          <div className={s.heroCtas}>
            <Link href="/screen" className={`${s.btn} ${s.btnPrimary}`}>
              Start with a free scan<span className={s.arrow}>→</span>
            </Link>
            <Link href="#pricing" className={`${s.btn} ${s.btnGhost}`}>
              See pricing
            </Link>
          </div>
          <div className={s.trustRow}>
            <div className={s.trustItem}>
              <span className={s.trustLabel}>Lookback</span>
              <span className={s.trustValue}>5 years</span>
            </div>
            <div className={s.trustItem}>
              <span className={s.trustLabel}>Turnaround</span>
              <span className={s.trustValue}>Under 3 min</span>
            </div>
            <div className={s.trustItem}>
              <span className={s.trustLabel}>Privacy</span>
              <span className={s.trustValue}>No passwords</span>
            </div>
          </div>
        </div>

        <div className={s.heroRight}>
          <div className={s.reportCard}>
            <div className={s.reportHeader}>
              <div>
                <div className={s.reportTitle}>Risk Screening Report</div>
                <div className={s.reportSubtitle}>Applicant 03B · India → USA · F-1 Student Visa</div>
              </div>
              <div className={s.reportStamp}>Reviewed</div>
            </div>
            <div className={s.riskMeter}>
              <div className={`${s.riskCell} ${s.amber}`}>
                <div className={s.riskCellLabel}>Political</div>
                <div className={s.riskScore}>42</div>
              </div>
              <div className={`${s.riskCell} ${s.red}`}>
                <div className={s.riskCellLabel}>Content</div>
                <div className={s.riskScore}>68</div>
              </div>
              <div className={`${s.riskCell} ${s.green}`}>
                <div className={s.riskCellLabel}>Network</div>
                <div className={s.riskScore}>21</div>
              </div>
            </div>
            <div className={s.flagRow}>
              <span className={`${s.flagDot} ${s.dotRed}`} />
              <div className={s.flagText}>
                <span className={s.flagPost}>&ldquo;Can&apos;t wait to work under the table when I land lol&rdquo;</span>
                <span className={`${s.flagAction} ${s.actionDelete}`}>Action: Delete · Conflicts with F-1 status</span>
              </div>
            </div>
            <div className={s.flagRow}>
              <span className={`${s.flagDot} ${s.dotAmber}`} />
              <div className={s.flagText}>
                <span className={s.flagPost}>Tagged photo at protest, 2022</span>
                <span className={`${s.flagAction} ${s.actionArchive}`}>Action: Archive · Prep talking point</span>
              </div>
            </div>
            <div className={s.flagRow}>
              <span className={`${s.flagDot} ${s.dotAmber}`} />
              <div className={s.flagText}>
                <span className={s.flagPost}>LinkedIn says &ldquo;Software Engineer,&rdquo; IG says &ldquo;DJ&rdquo;</span>
                <span className={`${s.flagAction} ${s.actionArchive}`}>Action: Reconcile before interview</span>
              </div>
            </div>
          </div>
          <div className={s.annotation}>Address items 1 &amp; 3 before DS-160 submission.</div>
        </div>
      </div>

      {/* STAT STRIP */}
      <div className={s.statStrip}>
        <div className={s.statStripInner}>
          <div className={s.stat}>
            <div className={s.statNum}>10K+</div>
            <div className={s.statText}><strong>Profiles screened</strong>Across every major platform</div>
          </div>
          <div className={s.stat}>
            <div className={s.statNum}>50+</div>
            <div className={s.statText}><strong>Countries served</strong>Applicants from every region</div>
          </div>
          <div className={s.stat}>
            <div className={s.statNum}>§212</div>
            <div className={s.statText}><strong>INA-grounded</strong>DS-160 &amp; inadmissibility analysis</div>
          </div>
          <div className={s.stat}>
            <div className={s.statNum}>&lt;3m</div>
            <div className={s.statText}><strong>To first report</strong>Free scan delivered fast</div>
          </div>
        </div>
      </div>

      {/* HOW IT WORKS */}
      <section id="how" className={s.howSection}>
        <div className={s.sectionInner}>
          <div className={s.sectionLabel}>— How it works</div>
          <h2 className={s.sectionTitle}>Three steps. <em>One clear plan.</em></h2>
          <div className={s.steps}>
            <div className={s.step}>
              <div className={s.stepNum}>i.</div>
              <h3 className={s.stepH3}>Submit your handles</h3>
              <p className={s.stepP}>Paste your public social URLs — Instagram, X, TikTok, LinkedIn, Facebook, YouTube. We never ask for passwords. Same scope a consular officer can see.</p>
              <span className={s.stepTag}>No login required</span>
            </div>
            <div className={s.step}>
              <div className={s.stepNum}>ii.</div>
              <h3 className={s.stepH3}>AI scan, attorney-grade rules</h3>
              <p className={s.stepP}>Our system analyzes up to 5 years of content against the actual grounds of inadmissibility under INA §212 and DS-160 disclosure questions.</p>
              <span className={s.stepTag}>INA §212 rule set</span>
            </div>
            <div className={s.step}>
              <div className={s.stepNum}>iii.</div>
              <h3 className={s.stepH3}>Get a plan, not just flags</h3>
              <p className={s.stepP}>PDF report with every flagged post, why it&apos;s flagged, and a specific action — delete, archive, leave, or be ready to explain at your interview.</p>
              <span className={s.stepTag}>Delivered in 24–48hrs</span>
            </div>
          </div>
        </div>
      </section>

      {/* WHY */}
      <section id="why" className={s.whySection}>
        <div className={s.sectionInner}>
          <div className={s.sectionLabel}>— Why VisaFootprint</div>
          <h2 className={s.sectionTitle}>Other tools spot keywords.<br /><em>We spot legal risk.</em></h2>
          <div className={s.whyGrid}>
            <div className={s.whyCard}>
              <div className={s.whyEyebrow}>01 — Built on real cases</div>
              <h3>Trained on what actually <em>triggers RFEs and refusals.</em></h3>
              <p>Our risk model isn&apos;t a generic LLM guess. It&apos;s tuned on the patterns that show up in real-world 214(b) refusals, 221(g) administrative processing, and RFEs — categorized against INA §212 grounds.</p>
            </div>
            <div className={`${s.whyCard} ${s.dark}`}>
              <div className={s.whyEyebrow}>02 — Action, not anxiety</div>
              <h3>We tell you <em>what to do</em>, not just what&apos;s wrong.</h3>
              <p>Every flagged post comes with a specific action. Delete it. Archive it. Add it to your interview prep document. No vague &ldquo;this might be risky&rdquo; — actual decisions you can execute today.</p>
            </div>
            <div className={`${s.whyCard} ${s.dark}`}>
              <div className={s.whyEyebrow}>03 — Human review available</div>
              <h3>Pro reports include <em>licensed-attorney review.</em></h3>
              <p>For prior denials, RFEs, O-1 cases, EB filings, or any high-stakes interview, a U.S. immigration attorney personally reviews your flagged content and provides a written memo plus a 30-minute consultation.</p>
            </div>
            <div className={s.whyCard}>
              <div className={s.whyEyebrow}>04 — Your privacy</div>
              <h3>No passwords. <em>No selling data.</em> Ever.</h3>
              <p>We only analyze publicly visible content — the same scope an officer can see. We don&apos;t ask for logins, don&apos;t store posts after your report is delivered, and never sell your data to third parties.</p>
            </div>
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className={s.pricingSection}>
        <div className={s.sectionInner}>
          <div className={s.sectionLabel}>— Pricing</div>
          <h2 className={s.sectionTitle}>Start free. <em>Upgrade when it counts.</em></h2>
          <p className={s.priceIntro}>One-time scans. No subscriptions unless you choose Monitor. Three tiers built around what your case actually needs — not artificial feature gates.</p>
          <div className={s.tiers}>
            <div className={s.tier}>
              <div className={s.tierName}>Free Scan</div>
              <div className={s.tierTag}>Try the tool · 1 account</div>
              <div className={s.tierPrice}>
                <span className={s.tierCurrency}>$</span>
                <span className={s.tierNum}>0</span>
                <span className={s.tierUnit}>/ one-time</span>
              </div>
              <p className={s.tierPitch}>Quick risk check before you file. No credit card. See the format and decide if you need more.</p>
              <ul className={s.tierList}>
                <li>1 social account</li>
                <li>Last 12 months of public posts</li>
                <li>AI risk summary, 3 categories</li>
                <li>Email-delivered summary</li>
                <li>Sample of flagged posts</li>
              </ul>
              <Link href="/screen" className={s.tierCta}>Get my free scan</Link>
            </div>

            <div className={`${s.tier} ${s.featured}`}>
              <div className={s.tierBadge}>Most popular</div>
              <div className={s.tierName}>Standard Scan</div>
              <div className={s.tierTag}>Most visa applicants · 3 accounts</div>
              <div className={s.tierPrice}>
                <span className={s.tierCurrency}>$</span>
                <span className={s.tierNum}>49</span>
                <span className={s.tierUnit}>/ one-time</span>
              </div>
              <p className={s.tierPitch}>Full screening across your real digital footprint. Built for B1/B2, F-1, H-1B, AOS, and family-based applicants.</p>
              <ul className={s.tierList}>
                <li>Up to 3 accounts</li>
                <li>5-year lookback (DS-160 match)</li>
                <li>Cross-platform consistency check</li>
                <li>Full PDF report with risk scores</li>
                <li>Post-by-post action plan</li>
                <li>Priority processing · 48hr turnaround</li>
              </ul>
              <CheckoutButton tier="standard" className={s.tierCta}>Run Standard Scan — $49</CheckoutButton>
            </div>

            <div className={s.tier}>
              <div className={s.tierName}>Attorney-Reviewed</div>
              <div className={s.tierTag}>High-stakes cases · 10 accounts</div>
              <div className={s.tierPrice}>
                <span className={s.tierCurrency}>$</span>
                <span className={s.tierNum}>199</span>
                <span className={s.tierUnit}>/ one-time</span>
              </div>
              <p className={s.tierPitch}>For prior denials, RFEs, O-1, EB cases, or anyone with prior immigration history. Reviewed by a licensed U.S. immigration attorney.</p>
              <ul className={s.tierList}>
                <li>Up to 10 accounts + Google &amp; web mentions</li>
                <li>10-year lookback</li>
                <li className={s.highlight}>Written memo by U.S. immigration attorney</li>
                <li className={s.highlight}>30-min attorney consultation included</li>
                <li>Mock interview prep tied to your footprint</li>
                <li>Free re-scan within 60 days</li>
                <li>5-business-day turnaround · Rush available</li>
              </ul>
              <CheckoutButton tier="attorney" className={s.tierCta}>Get Attorney Review — $199</CheckoutButton>
            </div>
          </div>

          <div className={s.monitorStrip}>
            <div>
              <strong className={s.msLabel}>+ Add VisaFootprint Monitor</strong>
              <span className={s.msDesc}>Visa cases take 6–18 months. We watch your accounts the whole time and alert you to new risks. Cancel anytime.</span>
            </div>
            <div className={s.msCta}>
              <div className={s.msPrice}>$19<small>/mo</small></div>
              <CheckoutButton tier="monitor" className={s.monitorCta}>Add monitoring</CheckoutButton>
            </div>
          </div>
        </div>
      </section>

      {/* QUOTE */}
      <section className={s.quoteSection}>
        <blockquote>A bad post can cost a visa as easily as a missing document. The difference is, you can fix the post.</blockquote>
        <div className={s.quoteAttr}>— The VisaFootprint principle</div>
      </section>

      {/* FAQ */}
      <section id="faq" className={s.faqSection}>
        <div className={s.sectionInner}>
          <div className={s.sectionLabel}>— Questions</div>
          <h2 className={s.sectionTitle}>Things people ask <em>before they file.</em></h2>
          <div className={s.faqList}>
            <details className={s.faqItem}>
              <summary>Do U.S. visa authorities actually check social media?</summary>
              <p>Yes. Since 2019, DS-160 and DS-260 forms require disclosure of social media identifiers. Consular officers and USCIS adjudicators routinely review public profiles as part of security and credibility screening. Posts that contradict your application can trigger 214(b) refusals, 221(g) administrative processing, or RFEs.</p>
            </details>
            <details className={s.faqItem}>
              <summary>Is this legal advice?</summary>
              <p>The Free and Standard reports are AI-generated risk analysis and are not legal advice. The Attorney-Reviewed tier includes a written memo and consultation with a licensed U.S. immigration attorney — that engagement <em>is</em> legal advice within its defined scope.</p>
            </details>
            <details className={s.faqItem}>
              <summary>Why use this if I already have a lawyer?</summary>
              <p>Most immigration lawyers don&apos;t have time to go post-by-post through 5+ years of your content. We do that work and hand the results to you (or your lawyer) in a format that&apos;s easy to act on. We also offer white-label and bulk plans for firms.</p>
            </details>
            <details className={s.faqItem}>
              <summary>Do you store my passwords or private content?</summary>
              <p>Never. We only analyze publicly visible content — the same scope an officer can see at your interview. No logins, no DMs, no private posts. Source data is purged after your report is delivered.</p>
            </details>
            <details className={s.faqItem}>
              <summary>I already filed. Is it too late?</summary>
              <p>No. Run a scan now. If we find issues, you can clean them up before your interview or before USCIS issues an RFE. Many problems are recoverable if you catch them early.</p>
            </details>
            <details className={s.faqItem}>
              <summary>I had a prior visa denial. Can you help?</summary>
              <p>Yes. Choose Attorney-Reviewed. A licensed immigration attorney will flag issues that connect to your prior denial and help you build a clean explanation framework for your next interview.</p>
            </details>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <div className={s.finalCta}>
        <svg className={s.finalCtaMark} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <line x1="12" y1="2" x2="12" y2="22" stroke="#B8924A" strokeWidth="1.2" strokeLinecap="round"/>
          <line x1="3" y1="7" x2="21" y2="7" stroke="#B8924A" strokeWidth="1.2" strokeLinecap="round"/>
          <line x1="6" y1="7" x2="6" y2="14" stroke="#B8924A" strokeWidth="0.9" strokeLinecap="round"/>
          <line x1="18" y1="7" x2="18" y2="14" stroke="#B8924A" strokeWidth="0.9" strokeLinecap="round"/>
          <path d="M2.5 14 Q6 18.5 9.5 14" stroke="#B8924A" strokeWidth="1.2" fill="none" strokeLinecap="round"/>
          <path d="M14.5 14 Q18 18.5 21.5 14" stroke="#B8924A" strokeWidth="1.2" fill="none" strokeLinecap="round"/>
          <line x1="9" y1="22" x2="15" y2="22" stroke="#B8924A" strokeWidth="1.2" strokeLinecap="round"/>
          <circle cx="12" cy="2" r="0.9" fill="#B8924A"/>
        </svg>
        <h2>Your application is one post away from a problem.<br /><em>Find it before they do.</em></h2>
        <p>Free scan in under 3 minutes. No credit card. No account.</p>
        <Link href="/screen" className={s.finalCtaBtn}>Run my free scan →</Link>
      </div>

    </div>
  );
}
