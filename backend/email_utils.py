"""
Transactional email via Resend (https://resend.com).
Set RESEND_API_KEY in .env. Fails silently if key is missing.
"""
import os
import httpx

RESEND_API_KEY   = os.getenv("RESEND_API_KEY", "")
FROM_ADDRESS     = os.getenv("EMAIL_FROM", "VisaFootprint <noreply@visafootprint.com>")
FRONTEND_URL     = os.getenv("FRONTEND_URL", "https://visafootprint.com").rstrip("/")


async def send_email(to: str, subject: str, html: str) -> None:
    if not RESEND_API_KEY or not to:
        print(f"[EMAIL] Skipped (no RESEND_API_KEY) — would send to {to}: {subject}", flush=True)
        return
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
                json={"from": FROM_ADDRESS, "to": [to], "subject": subject, "html": html},
            )
            if r.status_code not in (200, 201):
                print(f"[EMAIL] Resend error {r.status_code}: {r.text[:200]}", flush=True)
            else:
                print(f"[EMAIL] Sent '{subject}' to {to}", flush=True)
    except Exception as e:
        print(f"[EMAIL] Exception sending to {to}: {e}", flush=True)


def _base(content: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F5F1E8;font-family:Georgia,serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F1E8;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#F5F1E8;max-width:600px;width:100%;">
        <tr><td style="border-bottom:2px solid #0E1726;padding-bottom:14px;margin-bottom:0;">
          <span style="font-family:'Helvetica Neue',Arial,sans-serif;font-size:11px;letter-spacing:0.2em;
                text-transform:uppercase;font-weight:700;color:#0E1726;">VisaFootprint</span>
        </td></tr>
        <tr><td style="padding-top:32px;">{content}</td></tr>
        <tr><td style="padding-top:40px;border-top:1px solid rgba(14,23,38,0.12);margin-top:40px;">
          <p style="font-size:12px;color:rgba(14,23,38,0.45);font-family:Helvetica,Arial,sans-serif;margin:0;">
            VisaFootprint · US Visa Social Media Screening<br>
            Questions? Reply to this email and we'll help.
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def payment_confirmed_html(tier: str, screen_url: str) -> str:
    tier_names = {
        "standard": "Standard Scan — 3 accounts",
        "attorney": "Attorney-Reviewed — 10 accounts",
        "monitor":  "VisaFootprint Monitor — monthly",
    }
    tier_label = tier_names.get(tier, tier.title())
    body = f"""
<h1 style="font-size:28px;font-weight:400;color:#0E1726;margin:0 0 16px;line-height:1.2;">
  Payment confirmed.<br>
  <em style="font-style:italic;color:#7A1F1F;">Your screening is ready.</em>
</h1>
<p style="font-size:15px;color:#0E1726;line-height:1.6;margin:0 0 12px;
          font-family:Helvetica,Arial,sans-serif;">
  Thank you for your purchase. Your <strong>{tier_label}</strong> plan is now active.
</p>
<p style="font-size:15px;color:#0E1726;line-height:1.6;margin:0 0 24px;
          font-family:Helvetica,Arial,sans-serif;">
  Use the link below to start your visa risk screening. <strong>Bookmark it</strong> —
  it restores your paid access automatically.
</p>
<a href="{screen_url}"
   style="display:inline-block;background:#0E1726;color:#F5F1E8;padding:14px 28px;
          text-decoration:none;font-weight:700;font-size:14px;
          font-family:Helvetica,Arial,sans-serif;letter-spacing:0.03em;">
  Start Your Screening →
</a>
<p style="font-size:12px;color:rgba(14,23,38,0.5);margin:20px 0 0;
          font-family:Helvetica,Arial,sans-serif;">
  Link not working? Copy and paste this into your browser:<br>
  <a href="{screen_url}" style="color:#7A1F1F;">{screen_url}</a>
</p>"""
    return _base(body)


def report_ready_html(name: str, report_url: str, risk_level: str, score: int) -> str:
    risk_color = "#C83B3B" if risk_level == "HIGH" else "#C98B27" if risk_level == "MEDIUM" else "#3F6B3A"
    first = name.split()[0] if name else "there"
    body = f"""
<h1 style="font-size:28px;font-weight:400;color:#0E1726;margin:0 0 16px;line-height:1.2;">
  Your report is ready, {first}.<br>
  <em style="font-style:italic;color:#7A1F1F;">Here's what we found.</em>
</h1>
<p style="font-size:15px;color:#0E1726;line-height:1.6;margin:0 0 8px;
          font-family:Helvetica,Arial,sans-serif;">
  Your VisaFootprint screening is complete. Your overall risk score is:
</p>
<div style="display:inline-block;margin:8px 0 20px;padding:12px 24px;
            border:2px solid {risk_color};background:rgba(0,0,0,0.03);">
  <span style="font-size:48px;font-weight:400;color:{risk_color};font-family:Georgia,serif;">
    {score}
  </span>
  <span style="font-size:13px;color:rgba(14,23,38,0.5);font-family:Helvetica,Arial,sans-serif;">
    &nbsp;/ 100 &nbsp;·&nbsp; {risk_level} RISK
  </span>
</div>
<p style="font-size:15px;color:#0E1726;line-height:1.6;margin:0 0 24px;
          font-family:Helvetica,Arial,sans-serif;">
  Click below to view your full report and download your PDF.
</p>
<a href="{report_url}"
   style="display:inline-block;background:#0E1726;color:#F5F1E8;padding:14px 28px;
          text-decoration:none;font-weight:700;font-size:14px;
          font-family:Helvetica,Arial,sans-serif;letter-spacing:0.03em;">
  View Full Report & Download PDF →
</a>
<p style="font-size:12px;color:rgba(14,23,38,0.5);margin:16px 0 0;
          font-family:Helvetica,Arial,sans-serif;">
  <a href="{report_url}" style="color:#7A1F1F;">{report_url}</a>
</p>"""
    return _base(body)
