"""
Generate a professional PDF screening report matching Social Screen Pro visual style.
"""

import os
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, KeepTogether, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

try:
    from reportlab.graphics.shapes import (
        Drawing, Rect as GRect, String as GString, Circle as GCircle,
    )
    from reportlab.graphics.charts.piecharts import Pie
    _HAS_CHARTS = True
except ImportError:
    _HAS_CHARTS = False

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0A1628")
BLUE_ACC   = colors.HexColor("#1E40AF")
BLUE_LIGHT = colors.HexColor("#3B82F6")
PURPLE     = colors.HexColor("#7C3AED")
RED_HIGH   = colors.HexColor("#DC2626")
RED_BG     = colors.HexColor("#FEF2F2")
RED_BORDER = colors.HexColor("#FECACA")
ORANGE     = colors.HexColor("#D97706")
ORANGE_BG  = colors.HexColor("#FFFBEB")
ORG_BORDER = colors.HexColor("#FDE68A")
GREEN      = colors.HexColor("#16A34A")
GREEN_BG   = colors.HexColor("#F0FDF4")
GRN_BORDER = colors.HexColor("#BBF7D0")
GRAY_50    = colors.HexColor("#F8FAFC")
GRAY_100   = colors.HexColor("#F1F5F9")
GRAY_200   = colors.HexColor("#E2E8F0")
GRAY_300   = colors.HexColor("#CBD5E1")
GRAY_500   = colors.HexColor("#64748B")
GRAY_700   = colors.HexColor("#334155")
WHITE      = colors.white
BLACK      = colors.HexColor("#0F172A")

AVATAR_COLORS = [
    colors.HexColor("#DC2626"),
    colors.HexColor("#7C3AED"),
    colors.HexColor("#1D4ED8"),
    colors.HexColor("#059669"),
    colors.HexColor("#D97706"),
    colors.HexColor("#DB2777"),
    colors.HexColor("#0891B2"),
]

W, H      = A4
MARGIN    = 18 * mm
CONTENT_W = W - 2 * MARGIN


# ── Color helpers ─────────────────────────────────────────────────────────────

def risk_color(level: str) -> colors.Color:
    return {"HIGH": RED_HIGH, "MEDIUM": ORANGE, "LOW": GREEN}.get(
        (level or "LOW").upper(), GRAY_500)

def risk_bg(level: str) -> colors.Color:
    return {"HIGH": RED_BG, "MEDIUM": ORANGE_BG, "LOW": GREEN_BG}.get(
        (level or "LOW").upper(), GRAY_100)

def risk_border(level: str) -> colors.Color:
    return {"HIGH": RED_BORDER, "MEDIUM": ORG_BORDER, "LOW": GRN_BORDER}.get(
        (level or "LOW").upper(), GRAY_200)

def score_color(v: int) -> colors.Color:
    return RED_HIGH if v >= 60 else (ORANGE if v >= 30 else GREEN)

def score_bg(v: int) -> colors.Color:
    return RED_BG if v >= 60 else (ORANGE_BG if v >= 30 else GREEN_BG)

def score_border(v: int) -> colors.Color:
    return RED_BORDER if v >= 60 else (ORG_BORDER if v >= 30 else GRN_BORDER)

def _swatch(col: colors.Color) -> Table:
    t = Table([[""]], colWidths=[4*mm], rowHeights=[4*mm])
    t.setStyle(TableStyle([("BACKGROUND", (0,0),(0,0), col)]))
    return t


# ── Charts ────────────────────────────────────────────────────────────────────

def _sentiment_pie(pos: int, neu: int, neg: int):
    if not _HAS_CHARTS:
        return Spacer(1, 45*mm)
    size = 45 * mm
    d = Drawing(size, size)
    pie = Pie()
    pie.x = 2*mm; pie.y = 2*mm
    pie.width = size - 4*mm; pie.height = size - 4*mm
    pie.data = [max(pos, 1), max(neu, 1), max(neg, 1)]
    pie.startAngle = 90
    for i, col in enumerate([GREEN, BLUE_LIGHT, RED_HIGH]):
        pie.slices[i].fillColor   = col
        pie.slices[i].strokeColor = WHITE
        pie.slices[i].strokeWidth = 1.5
    d.add(pie)
    return d


def _activity_chart(flagged_posts: list, risk_score: int):
    if not _HAS_CHARTS:
        return Spacer(1, 45*mm)
    now = datetime.now()
    months = []
    for i in range(5, -1, -1):
        m = now.month - i; y = now.year
        while m <= 0: m += 12; y -= 1
        months.append(datetime(y, m, 1).strftime("%b'%y"))

    counts = {m: 0 for m in months}
    for fp in flagged_posts:
        ds = str(fp.get("date") or fp.get("posted_at") or "")[:10]
        try:
            dt  = datetime.strptime(ds, "%Y-%m-%d")
            key = dt.strftime("%b'%y")
            if key in counts:
                counts[key] += 1
        except Exception:
            pass

    vals   = [counts[m] for m in months]
    no_data = max(vals) == 0

    dw = float(CONTENT_W); dh = 45 * mm
    d  = Drawing(dw, dh)
    d.add(GRect(0, 0, dw, dh, fillColor=GRAY_50, strokeColor=GRAY_200, strokeWidth=0.5))

    pad_l, pad_r, pad_b = 15, 10, 18
    area_w = dw - pad_l - pad_r
    area_h = dh - pad_b - 8
    slot_w = area_w / len(months)

    if no_data:
        d.add(GString(dw / 2, dh / 2 + 4, "No flagged post activity in this period",
                      fontSize=7.5, fontName="Helvetica-Oblique",
                      fillColor=GRAY_500, textAnchor="middle"))
        for i, m in enumerate(months):
            bx = pad_l + i * slot_w + slot_w * 0.5
            d.add(GString(bx, 4, m, fontSize=6, fontName="Helvetica",
                          fillColor=GRAY_500, textAnchor="middle"))
        return d

    max_v  = max(vals) + 1
    bar_w  = slot_w * 0.5
    for i, v in enumerate(vals):
        bh_px = v / max_v * area_h
        bx    = pad_l + i * slot_w + (slot_w - bar_w) / 2
        col   = RED_HIGH if v >= 3 else (ORANGE if v >= 1 else GRAY_300)
        d.add(GRect(bx, pad_b, bar_w, max(bh_px, 2), fillColor=col, strokeColor=None))
        d.add(GString(bx + bar_w/2, 4, months[i],
                      fontSize=6, fontName="Helvetica", fillColor=GRAY_700, textAnchor="middle"))
        if v > 0:
            d.add(GString(bx + bar_w/2, pad_b + bh_px + 2, str(v),
                          fontSize=7, fontName="Helvetica-Bold",
                          fillColor=GRAY_700, textAnchor="middle"))
    return d


# ── Cover page ────────────────────────────────────────────────────────────────

def draw_cover_page(c: canvas.Canvas, data: dict):
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Confidential top bar
    c.setFillColor(colors.HexColor("#0D1F3C"))
    c.rect(0, H - 9*mm, W, 9*mm, fill=1, stroke=0)
    c.setFillColor(GRAY_300); c.setFont("Helvetica", 6)
    c.drawCentredString(W/2, H - 5.5*mm,
        "Confidential – For authorized use only  |  AI-generated social media screening report  |  VisaScreenAI")

    # Logo
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(W/2, H - 45*mm, "VisaScreenAI")
    c.setFillColor(BLUE_LIGHT); c.setFont("Helvetica", 8.5)
    c.drawCentredString(W/2, H - 53*mm, "Social Media Screening Report")
    c.setStrokeColor(colors.HexColor("#1E3A5F")); c.setLineWidth(1)
    c.line(MARGIN, H - 59*mm, W - MARGIN, H - 59*mm)

    # Avatar circle
    name     = data.get("name", "Unknown")
    initials = "".join(w[0].upper() for w in name.split()[:2]) or "?"
    cx, cy   = W/2, H - 86*mm
    c.setFillColor(PURPLE); c.circle(cx, cy, 17*mm, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(cx, cy - 3.5*mm, initials)

    # Name
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(W/2, H - 112*mm, name.upper())

    # Risk pill
    overall = (data.get("overall_risk") or "LOW").upper()
    flagged = len(data.get("flagged_posts", []))
    score   = data.get("risk_score", 0)
    rc      = risk_color(overall)
    pw = 148; px = W/2 - pw/2; py = H - 124*mm
    c.setFillColor(rc); c.roundRect(px, py, pw, 12, 5, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(W/2, py + 4,
        f"● {overall} RISK   {score}/100   {flagged} flagged post{'s' if flagged != 1 else ''}")

    c.setStrokeColor(colors.HexColor("#1E3A5F"))
    c.line(MARGIN, H - 133*mm, W - MARGIN, H - 133*mm)

    # Meta grid (2 columns × 3 rows)
    meta = [
        ("Full Name",      name),
        ("Country",        data.get("country", "—")),
        ("Visa Purpose",   (data.get("reason") or "—")[:55]),
        ("Accounts",       f'{len(data.get("accounts", []))} account(s)'),
        ("Posts Analyzed", str(data.get("posts_analyzed", 0))),
        ("Report Date",    datetime.now().strftime("%d %b, %Y")),
    ]
    lx = [MARGIN + 4*mm, W/2 + 6*mm]
    vx = [MARGIN + 36*mm, W/2 + 42*mm]
    sy = H - 149*mm
    for i, (k, v) in enumerate(meta):
        col, row = i % 2, i // 2
        y = sy - row * 10*mm
        c.setFillColor(GRAY_500); c.setFont("Helvetica", 6.5)
        c.drawString(lx[col], y, k.upper())
        c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 8)
        c.drawString(vx[col], y, str(v))

    # Score gauge cards
    gy = H - 208*mm
    for px_pos, lbl, key in [
        (W*0.22, "POLITICAL RISK", "political"),
        (W*0.50, "CONTENT RISK",   "content"),
        (W*0.78, "NETWORK RISK",   "network"),
    ]:
        val = int((data.get("scores") or {}).get(key, 0))
        col = score_color(val)
        bw, bh = 46*mm, 28*mm
        bx, by = px_pos - bw/2, gy - bh/2
        c.setFillColor(colors.HexColor("#0D2040"))
        c.roundRect(bx, by, bw, bh, 5, fill=1, stroke=0)
        c.setStrokeColor(col); c.setLineWidth(1)
        c.roundRect(bx, by, bw, bh, 5, fill=0, stroke=1)
        c.setFillColor(col); c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(px_pos, gy + 2, str(val))
        c.setFillColor(GRAY_500); c.setFont("Helvetica", 6.5)
        c.drawCentredString(px_pos, gy - 4.5, "/100")
        bar_w = bw - 8*mm; bar_x = px_pos - bar_w/2; bar_y = by + 6
        c.setFillColor(colors.HexColor("#0A1628"))
        c.roundRect(bar_x, bar_y, bar_w, 3.5, 1.5, fill=1, stroke=0)
        c.setFillColor(col)
        c.roundRect(bar_x, bar_y, bar_w * max(val, 2)/100, 3.5, 1.5, fill=1, stroke=0)
        c.setFillColor(GRAY_300); c.setFont("Helvetica-Bold", 5.5)
        c.drawCentredString(px_pos, by + bh - 8, lbl)

    # Footer
    c.setStrokeColor(colors.HexColor("#1E3A5F")); c.setLineWidth(0.5)
    c.line(MARGIN, 20*mm, W - MARGIN, 20*mm)
    c.setFillColor(GRAY_500); c.setFont("Helvetica", 6.5)
    c.drawCentredString(W/2, 13*mm,
        "Generated by AI analysis of publicly available social media data. For informational purposes only.")
    c.drawCentredString(W/2, 7*mm,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}   |   VisaScreenAI")


# ── Page header/footer ────────────────────────────────────────────────────────

def _page_template(c: canvas.Canvas, doc):
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, H - 14*mm, W, 14*mm, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 8.5)
    c.drawString(MARGIN, H - 8.5*mm, "VisaScreenAI")
    c.setFillColor(BLUE_LIGHT); c.setFont("Helvetica", 7.5)
    c.drawRightString(W - MARGIN, H - 8.5*mm, "Confidential Social Media Screening Report")
    c.setStrokeColor(GRAY_200); c.setLineWidth(0.5)
    c.line(MARGIN, 12*mm, W - MARGIN, 12*mm)
    c.setFillColor(GRAY_500); c.setFont("Helvetica", 6.5)
    c.drawString(MARGIN, 6*mm, "VisaScreenAI — For authorized use only")
    c.drawRightString(W - MARGIN, 6*mm, f"Page {doc.page}")
    c.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────

def _styles() -> dict:
    return {
        "sec":      ParagraphStyle("sec",  fontName="Helvetica-Bold", fontSize=11,
                                    textColor=NAVY, spaceAfter=3, spaceBefore=10),
        "h2":       ParagraphStyle("h2",   fontName="Helvetica-Bold", fontSize=9.5,
                                    textColor=NAVY, spaceAfter=2, spaceBefore=5),
        "body":     ParagraphStyle("body", fontName="Helvetica", fontSize=8.5,
                                    textColor=GRAY_700, spaceAfter=3, leading=13),
        "small":    ParagraphStyle("sml",  fontName="Helvetica", fontSize=7.5,
                                    textColor=GRAY_500, spaceAfter=2, leading=11),
        "bold":     ParagraphStyle("bld",  fontName="Helvetica-Bold", fontSize=8.5,
                                    textColor=BLACK, spaceAfter=2),
        "lbl":      ParagraphStyle("lbl",  fontName="Helvetica-Bold", fontSize=6.5,
                                    textColor=GRAY_500, spaceAfter=1, leading=9),
        "val":      ParagraphStyle("val",  fontName="Helvetica-Bold", fontSize=8.5,
                                    textColor=BLACK, spaceAfter=1, leading=11),
        "ctr":      ParagraphStyle("ctr",  fontName="Helvetica", fontSize=8.5,
                                    textColor=GRAY_700, alignment=TA_CENTER),
        "quote":    ParagraphStyle("qte",  fontName="Helvetica-Oblique", fontSize=8.5,
                                    textColor=GRAY_700, leading=13),
        "disc":     ParagraphStyle("dsc",  fontName="Helvetica", fontSize=6.5,
                                    textColor=GRAY_500, leading=10),
        "net_name": ParagraphStyle("nn",   fontName="Helvetica-Bold", fontSize=9,
                                    textColor=BLACK, spaceAfter=1, leading=11),
        "net_role": ParagraphStyle("nr",   fontName="Helvetica", fontSize=7.5,
                                    textColor=GRAY_500, spaceAfter=2, leading=10),
        "net_body": ParagraphStyle("nb",   fontName="Helvetica", fontSize=8,
                                    textColor=GRAY_700, spaceAfter=2, leading=12),
    }


def _hr(col=GRAY_200, t=0.5, sp=4):
    return HRFlowable(width="100%", thickness=t, color=col, spaceAfter=sp, spaceBefore=sp)

def _sec(text, S):
    return [Paragraph(text, S["sec"]), _hr(GRAY_300, 0.8, 3)]


# ── Risk topic pills ──────────────────────────────────────────────────────────

def _topic_pills(topics: list, S: dict) -> list:
    if not topics:
        return []
    PILL_BG     = colors.HexColor("#EFF6FF")
    PILL_BORDER = colors.HexColor("#BFDBFE")

    cols_per_row = min(len(topics), 5)
    per          = CONTENT_W / cols_per_row
    rows         = [topics[i:i+cols_per_row] for i in range(0, len(topics), cols_per_row)]
    out          = []

    for row in rows:
        cells  = [Paragraph(t, ParagraphStyle(
                     "pill", fontName="Helvetica-Bold", fontSize=7,
                     textColor=BLUE_ACC, alignment=TA_CENTER))
                  for t in row]
        widths = [per] * len(cells)
        # Pad shorter rows
        while len(cells) < cols_per_row:
            cells.append(""); widths.append(per)

        tbl = Table([cells], colWidths=widths)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(len(row)-1,0), PILL_BG),
            ("BOX",           (0,0),(len(row)-1,0), 0.5, PILL_BORDER),
            ("INNERGRID",     (0,0),(len(row)-1,0), 0.5, PILL_BORDER),
            ("TOPPADDING",    (0,0),(-1,-1), 4),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ]))
        out.append(tbl)
    return out


# ── Flagged content card ──────────────────────────────────────────────────────

def _flagged_card(fp: dict, S: dict) -> Table:
    lvl  = (fp.get("risk_level") or "LOW").upper()
    cat  = fp.get("risk_category", "General")
    plat = fp.get("platform", "Unknown")
    date = fp.get("date") or "Unknown date"
    url  = fp.get("post_url") or fp.get("url") or ""
    text = (fp.get("text") or "")[:500]
    expl = fp.get("explanation", "")

    rc_fp  = risk_color(lvl)
    rbd_fp = risk_border(lvl)
    emoji  = "🚨" if lvl == "HIGH" else "⚠️"

    link_line = f'<font color="#64748B">📱 Posted on {plat} • {date}</font>'
    if url:
        link_line += (f'   <link href="{url}">'
                      f'<font color="#1E40AF">  Check original post →</font></link>')

    badge_para = Paragraph(
        f'{emoji} {lvl} RISK: {cat}',
        ParagraphStyle("badge", fontName="Helvetica-Bold", fontSize=8,
                       textColor=WHITE, leading=11))

    cw = CONTENT_W - 2

    card = Table([
        [Paragraph(f'"{text}"', S["quote"])],
        [Paragraph(link_line, S["small"])],
        [badge_para],
        [Paragraph(expl, S["body"])],
    ], colWidths=[cw])

    card.setStyle(TableStyle([
        # Quote row — light bg
        ("BACKGROUND",    (0,0),(0,0), GRAY_50),
        ("TOPPADDING",    (0,0),(0,0), 8),
        ("BOTTOMPADDING", (0,0),(0,0), 8),
        ("LEFTPADDING",   (0,0),(0,0), 10),
        ("RIGHTPADDING",  (0,0),(0,0), 10),
        # Link row
        ("BACKGROUND",    (0,1),(0,1), WHITE),
        ("TOPPADDING",    (0,1),(0,1), 4),
        ("BOTTOMPADDING", (0,1),(0,1), 3),
        ("LEFTPADDING",   (0,1),(0,1), 10),
        ("RIGHTPADDING",  (0,1),(0,1), 8),
        # Badge row — colored bg
        ("BACKGROUND",    (0,2),(0,2), rc_fp),
        ("TOPPADDING",    (0,2),(0,2), 5),
        ("BOTTOMPADDING", (0,2),(0,2), 5),
        ("LEFTPADDING",   (0,2),(0,2), 10),
        ("RIGHTPADDING",  (0,2),(0,2), 8),
        # Explanation row
        ("BACKGROUND",    (0,3),(0,3), WHITE),
        ("TOPPADDING",    (0,3),(0,3), 6),
        ("BOTTOMPADDING", (0,3),(0,3), 6),
        ("LEFTPADDING",   (0,3),(0,3), 10),
        ("RIGHTPADDING",  (0,3),(0,3), 10),
        # Outer border
        ("BOX",           (0,0),(0,-1), 1, rbd_fp),
    ]))
    return card


# ── Network connection card ───────────────────────────────────────────────────

def _network_card(conn: dict, idx: int, S: dict) -> Table:
    name    = conn.get("name", "Unknown")
    handle  = conn.get("handle", "")
    role    = conn.get("role", "")
    loc     = conn.get("location", "")
    post    = conn.get("post_text", "")
    date    = conn.get("posted_at", "")
    plat    = conn.get("platform", "")
    risk    = conn.get("risk_factor", "")

    initials = "".join(w[0].upper() for w in name.split()[:2]) or "?"
    av_col   = AVATAR_COLORS[idx % len(AVATAR_COLORS)]

    av_cell = Table(
        [[Paragraph(f'<font color="white"><b>{initials}</b></font>',
                    ParagraphStyle("ca", fontName="Helvetica-Bold", fontSize=12,
                                   textColor=WHITE, alignment=TA_CENTER))]],
        colWidths=[12*mm], rowHeights=[12*mm])
    av_cell.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,0), av_col),
        ("ALIGN",      (0,0),(0,0), "CENTER"),
        ("VALIGN",     (0,0),(0,0), "MIDDLE"),
    ]))

    name_line = name + (f" ({handle})" if handle else "")
    role_line = " • ".join(filter(None, [role, loc]))

    info_rows = [
        [Paragraph(name_line, S["net_name"])],
        [Paragraph(role_line, S["net_role"])],
    ]
    if post:
        info_rows.append([Paragraph(f'"{post}"', S["quote"])])
    if plat or date:
        info_rows.append([Paragraph(
            f'<font color="#64748B">Posted on {plat} • {date}</font>',
            S["small"])])
    if risk:
        info_rows.append([Paragraph(f'<b>Risk Factor:</b> {risk}', S["net_body"])])

    info_w   = CONTENT_W - 18*mm
    info_tbl = Table(info_rows, colWidths=[info_w])
    info_tbl.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))

    card = Table([[av_cell, info_tbl]], colWidths=[16*mm, info_w + 2*mm])
    card.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), GRAY_50),
        ("BOX",           (0,0),(-1,-1), 0.5, GRAY_200),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ("TOPPADDING",    (0,0),(0,0), 10),
    ]))
    return card


# ── Story ─────────────────────────────────────────────────────────────────────

def build_report_story(data: dict, S: dict) -> list:
    story    = []
    overall  = (data.get("overall_risk") or "LOW").upper()
    score    = data.get("risk_score", 0)
    flagged  = data.get("flagged_posts", [])
    accounts = data.get("accounts", [])
    scores   = data.get("scores", {})
    sentiment= data.get("sentiment", {})
    recs     = data.get("recommendations", [])
    topics   = data.get("risk_topics", [])
    network  = data.get("network_connections", [])

    # ── Profile Summary ───────────────────────────────────────────────────────
    story += _sec("Profile Summary", S)

    name     = data.get("name", "—")
    initials = "".join(w[0].upper() for w in name.split()[:2]) or "?"

    av = Table(
        [[Paragraph(f'<font color="white"><b>{initials}</b></font>',
                    ParagraphStyle("av", fontName="Helvetica-Bold", fontSize=16,
                                   textColor=WHITE, alignment=TA_CENTER))]],
        colWidths=[15*mm], rowHeights=[15*mm])
    av.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,0), PURPLE),
        ("ALIGN",      (0,0),(0,0), "CENTER"),
        ("VALIGN",     (0,0),(0,0), "MIDDLE"),
    ]))

    rc       = risk_color(overall)
    rb_badge = Table(
        [[Paragraph(f'<font color="white"><b>● {overall} RISK</b></font>',
                    ParagraphStyle("rb", fontName="Helvetica-Bold", fontSize=7.5,
                                   textColor=WHITE, alignment=TA_CENTER))]],
        colWidths=[26*mm], rowHeights=[8*mm])
    rb_badge.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,0), rc),
        ("ALIGN",      (0,0),(0,0), "CENTER"),
        ("VALIGN",     (0,0),(0,0), "MIDDLE"),
    ]))

    fields = [
        ("Full Name",      name),
        ("Country",        data.get("country", "—")),
        ("Visa Purpose",   (data.get("reason") or "—")[:55]),
        ("Report Date",    datetime.now().strftime("%d %b, %Y")),
        ("Posts Analyzed", str(data.get("posts_analyzed", 0))),
        ("Flagged Posts",  str(len(flagged))),
    ]
    frows = []
    for i in range(0, len(fields), 2):
        l, r = fields[i], (fields[i+1] if i+1 < len(fields) else ("", ""))
        frows.append([
            Paragraph(l[0].upper(), S["lbl"]), Paragraph(str(l[1]), S["val"]),
            Paragraph(r[0].upper(), S["lbl"]), Paragraph(str(r[1]), S["val"]),
        ])
    ftbl = Table(frows, colWidths=[20*mm, 48*mm, 20*mm, 48*mm])
    ftbl.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
    ]))

    card = Table([[av, ftbl, rb_badge]], colWidths=[19*mm, 118*mm, 27*mm])
    card.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), GRAY_50),
        ("BOX",           (0,0),(-1,-1), 0.8, GRAY_300),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
        ("LEFTPADDING",   (0,0),(-1,-1), 7),
        ("RIGHTPADDING",  (0,0),(-1,-1), 7),
    ]))
    story.append(card)
    story.append(Spacer(1, 8))

    # ── AI Summary ────────────────────────────────────────────────────────────
    story += _sec("🤖 AI Summary", S)
    story.append(Paragraph(data.get("summary", "No summary available."), S["body"]))

    if topics:
        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>Risk Topics</b>", S["lbl"]))
        story.append(Spacer(1, 2))
        story.extend(_topic_pills(topics, S))

    story.append(Spacer(1, 8))

    # ── Social Media Accounts ─────────────────────────────────────────────────
    if accounts:
        story += _sec("Social Media Accounts", S)
        story.append(Paragraph(
            "The following social media accounts were analyzed for risk assessment. "
            "Multiple platforms were assessed for content patterns and network associations.",
            S["small"]))
        story.append(Spacer(1, 4))

        plat_map = {
            "twitter": "Twitter/X", "x": "Twitter/X",
            "instagram": "Instagram", "tiktok": "TikTok",
            "linkedin": "LinkedIn",   "facebook": "Facebook",
            "youtube": "YouTube",
        }

        hdr  = ["PLATFORM", "HANDLE / URL", "POSTS", "STATUS"]
        rows = [hdr]
        for acc in accounts:
            plat    = plat_map.get((acc.get("platform") or "").lower(),
                                   (acc.get("platform") or "—").title())
            handle  = acc.get("handle", "—")
            n_posts = str(acc.get("posts_count", "—"))
            status  = "Manual (pasted)" if acc.get("manual_posts") else "Auto-scraped"
            rows.append([plat, handle, n_posts, status])

        atbl = Table(rows, colWidths=[32*mm, 88*mm, 18*mm, 32*mm])
        atbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), NAVY),
            ("TEXTCOLOR",     (0,0),(-1,0), WHITE),
            ("FONTNAME",      (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),(-1,0), 7.5),
            ("FONTNAME",      (0,1),(-1,-1), "Helvetica"),
            ("FONTSIZE",      (0,1),(-1,-1), 8),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, GRAY_50]),
            ("GRID",          (0,0),(-1,-1), 0.4, GRAY_200),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("LEFTPADDING",   (0,0),(-1,-1), 7),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        story.append(atbl)
        story.append(Spacer(1, 10))

    # ── Risk Analysis ─────────────────────────────────────────────────────────
    story += _sec("Risk Analysis and Threat Assessment", S)

    story.append(Paragraph("<b>📊 Activity Escalation (Last 6 months)</b>", S["h2"]))
    story.append(_activity_chart(flagged, score))
    story.append(Paragraph(
        "Escalating political activity and increasingly concerning content sharing patterns observed."
        if flagged else "No flagged post activity detected in this period.",
        S["small"]))
    story.append(Spacer(1, 8))

    # Risk Score Breakdown
    story.append(Paragraph("<b>⚠️ Risk Score Breakdown</b>", S["h2"]))

    # card_w × 3 + gap × 2 = CONTENT_W  →  54mm × 3 + 6mm × 2 = 174mm
    _CARD_W = 54 * mm
    _GAP_W  =  6 * mm

    def _score_card(lbl: str, val: int) -> Table:
        col        = score_color(val)
        bar_total  = _CARD_W - 8 * mm
        filled_w   = max(bar_total * val / 100, 1)
        empty_w    = max(bar_total - filled_w, 1)

        bar = Table([["", ""]], colWidths=[filled_w, empty_w], rowHeights=[4])
        bar.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(0,0), col),
            ("BACKGROUND",    (1,0),(1,0), colors.HexColor("#1A2F50")),
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
            ("LEFTPADDING",   (0,0),(-1,-1), 0),
            ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ]))

        t = Table([
            [Paragraph(lbl.upper(),
                       ParagraphStyle("sl", fontName="Helvetica-Bold", fontSize=6.5,
                                      textColor=col, alignment=TA_CENTER))],
            [Paragraph(str(val),
                       ParagraphStyle("sv", fontName="Helvetica-Bold", fontSize=30,
                                      textColor=col, alignment=TA_CENTER, leading=36))],
            [Paragraph("/100",
                       ParagraphStyle("ss", fontName="Helvetica", fontSize=7,
                                      textColor=GRAY_500, alignment=TA_CENTER))],
            [bar],
        ], colWidths=[_CARD_W], rowHeights=[12, 36, 10, 10])

        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), NAVY),
            ("BOX",           (0,0),(-1,-1), 1.5, col),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ("VALIGN",        (0,0),(0,2), "MIDDLE"),
            ("VALIGN",        (0,3),(0,3), "MIDDLE"),
            ("TOPPADDING",    (0,0),(0,0), 8),
            ("BOTTOMPADDING", (0,0),(0,0), 2),
            ("TOPPADDING",    (0,1),(0,1), 0),
            ("BOTTOMPADDING", (0,1),(0,1), 0),
            ("TOPPADDING",    (0,2),(0,2), 0),
            ("BOTTOMPADDING", (0,2),(0,2), 4),
            ("TOPPADDING",    (0,3),(0,3), 0),
            ("BOTTOMPADDING", (0,3),(0,3), 8),
            ("LEFTPADDING",   (0,3),(0,3), 4*mm),
            ("RIGHTPADDING",  (0,3),(0,3), 4*mm),
        ]))
        return t

    pol = int(scores.get("political", 0))
    con = int(scores.get("content",   0))
    net = int(scores.get("network",   0))

    sr = Table([[_score_card("Political Risk", pol), Spacer(_GAP_W, 1),
                 _score_card("Content Risk",   con), Spacer(_GAP_W, 1),
                 _score_card("Network Risk",   net)]],
               colWidths=[_CARD_W, _GAP_W, _CARD_W, _GAP_W, _CARD_W])
    sr.setStyle(TableStyle([("VALIGN", (0,0),(-1,-1), "TOP")]))
    story.append(sr)
    story.append(Spacer(1, 10))

    # Content Sentiment
    story.append(Paragraph("<b>Content Sentiment</b>", S["h2"]))
    pos = int(sentiment.get("positive", 50))
    neu = int(sentiment.get("neutral",  40))
    neg = int(sentiment.get("negative", 10))
    pie = _sentiment_pie(pos, neu, neg)

    legend = Table([
        [_swatch(GREEN),      Paragraph("Positive", S["small"]),
         Paragraph(f"<b>{pos}%</b>", S["bold"])],
        [_swatch(BLUE_LIGHT), Paragraph("Neutral",  S["small"]),
         Paragraph(f"<b>{neu}%</b>", S["bold"])],
        [_swatch(RED_HIGH),   Paragraph("Negative", S["small"]),
         Paragraph(f"<b>{neg}%</b>", S["bold"])],
    ], colWidths=[6*mm, 20*mm, 12*mm], rowHeights=14)
    legend.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
    ]))

    sdesc = (
        "Predominantly negative sentiment with aggressive language and inflammatory rhetoric patterns."
        if neg > 40 else
        "Mixed sentiment detected. Some concerning negative content alongside neutral posts."
        if neg > 20 else
        "Mostly positive and neutral content. Sentiment profile presents low risk indicators."
    )

    sent_layout = Table([[pie, legend, Paragraph(sdesc, S["body"])]],
                        colWidths=[50*mm, 42*mm, CONTENT_W - 92*mm])
    sent_layout.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
        ("RIGHTPADDING",  (0,0),(-1,-1), 5),
        ("BOX",           (0,0),(-1,-1), 0.5, GRAY_200),
        ("BACKGROUND",    (0,0),(-1,-1), GRAY_50),
    ]))
    story.append(sent_layout)
    story.append(Spacer(1, 10))

    # ── Security Threat Assessment ────────────────────────────────────────────
    story += _sec("Security Threat Assessment", S)

    if flagged:
        cat_map: dict = {}
        for fp in flagged:
            cat = fp.get("risk_category", "General")
            if cat not in cat_map:
                cat_map[cat] = {
                    "count": 0,
                    "level": fp.get("risk_level", "LOW"),
                    "concern": (fp.get("explanation", ""))[:100],
                }
            cat_map[cat]["count"] += 1

        # Column widths: 50+20+26+78 = 174mm = CONTENT_W
        _CW = [50*mm, 20*mm, 26*mm, 78*mm]

        _hdr_s = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=7.5,
                                 textColor=WHITE, leading=10)
        _cat_s = ParagraphStyle("tc", fontName="Helvetica",      fontSize=8,
                                 textColor=GRAY_700, leading=11)
        _cnt_s = ParagraphStyle("tct",fontName="Helvetica",      fontSize=8,
                                 textColor=GRAY_700, alignment=TA_CENTER, leading=11)
        _con_s = ParagraphStyle("tco",fontName="Helvetica",      fontSize=8,
                                 textColor=GRAY_700, leading=11)

        rows = [[
            Paragraph("CATEGORY",        _hdr_s),
            Paragraph("FLAGGED\nCONTENT",_hdr_s),
            Paragraph("RISK LEVEL",      _hdr_s),
            Paragraph("SECURITY CONCERN",_hdr_s),
        ]]
        for cat, info in cat_map.items():
            lvl = (info["level"] or "LOW").upper()
            lvl_para = Paragraph(
                lvl,
                ParagraphStyle("tl", fontName="Helvetica-Bold", fontSize=7.5,
                               textColor=risk_color(lvl), alignment=TA_CENTER,
                               leading=10))
            rows.append([
                Paragraph(cat, _cat_s),
                Paragraph(f'{info["count"]} Post{"s" if info["count"]>1 else ""}', _cnt_s),
                lvl_para,
                Paragraph(info["concern"], _con_s),
            ])

        ttbl = Table(rows, colWidths=_CW)
        ts = TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), NAVY),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, GRAY_50]),
            ("GRID",          (0,0),(-1,-1), 0.4, GRAY_200),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("LEFTPADDING",   (0,0),(-1,-1), 7),
            ("RIGHTPADDING",  (0,0),(-1,-1), 5),
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ])
        for ri, (_, info) in enumerate(cat_map.items(), 1):
            lvl = (info["level"] or "LOW").upper()
            ts.add("BACKGROUND", (2, ri),(2, ri), risk_bg(lvl))
        ttbl.setStyle(ts)
        story.append(ttbl)
    else:
        story.append(Paragraph(
            "No security threats identified. Profile appears clean across all analyzed platforms.",
            S["body"]))

    story.append(Spacer(1, 10))

    # ── Flagged Content ───────────────────────────────────────────────────────
    if flagged:
        story += _sec(f"🚩 High-Risk Flagged Content   ({len(flagged)} concerning posts)", S)
        for fp in flagged:
            story.append(KeepTogether(_flagged_card(fp, S)))
            story.append(Spacer(1, 6))

    # ── Network Risk Analysis ─────────────────────────────────────────────────
    story += _sec("🌐 High-Risk Network Analysis", S)

    if network:
        first = data.get("name", "The applicant").split()[0]
        story.append(Paragraph(
            f"{first}'s social network contains multiple individuals with concerning activity patterns. "
            "These connections significantly elevate the risk profile and suggest coordinated activity "
            "across platforms and geographic locations.",
            S["body"]))
        story.append(Spacer(1, 6))

        for idx, conn in enumerate(network):
            story.append(KeepTogether(_network_card(conn, idx, S)))
            story.append(Spacer(1, 5))

        # Network Risk Summary paragraph
        if net >= 60:
            net_summary = (
                "Network Risk Summary: This profile maintains active connections with individuals flagged for "
                "concerning political activity, extremist associations, or illegal activities. "
                "The network demonstrates coordination across platforms and geographic locations. "
                "Multiple contacts reference the applicant's position as strategically significant. "
                "A thorough network investigation is strongly recommended before any visa decision."
            )
        elif net >= 30:
            net_summary = (
                "Network Risk Summary: Some network associations warrant review. Profile interactions include "
                "accounts sharing concerning content, though confirmed high-risk connections were limited. "
                "Monitor for evolving network patterns prior to the interview."
            )
        else:
            net_summary = (
                "Network Risk Summary: No significant high-risk network connections identified based on "
                "available public data. Public interactions appear consistent with the stated visa purpose."
            )
        story.append(Paragraph(net_summary, S["body"]))

    else:
        net_col_str = "#DC2626" if net >= 60 else "#D97706" if net >= 30 else "#16A34A"
        net_col_obj = score_color(net)
        net_bg_obj  = score_bg(net)

        net_txt = (
            "HIGH network risk detected. Profile shows potential connections to high-risk accounts, "
            "extremist communities, or individuals flagged by security databases."
            if net >= 60 else
            "MEDIUM network risk. Some network associations warrant monitoring. "
            "Profile interactions include accounts sharing concerning content."
            if net >= 30 else
            "LOW network risk based on available public data. "
            "No significant connections to high-risk individuals or organizations identified."
        )

        net_card = Table([
            [Paragraph("<b>Network Risk Score</b>", S["lbl"]),
             Paragraph(f'<font color="{net_col_str}"><b>{net}/100</b></font>', S["bold"])],
            [Paragraph(net_txt, S["body"]), ""],
        ], colWidths=[110*mm, 54*mm])
        net_card.setStyle(TableStyle([
            ("SPAN",          (0,1),(1,1)),
            ("BACKGROUND",    (0,0),(-1,-1), net_bg_obj if net >= 30 else GRAY_50),
            ("BOX",           (0,0),(-1,-1), 0.8,
             net_col_obj if net >= 30 else GRAY_200),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("RIGHTPADDING",  (0,0),(-1,-1), 10),
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ]))
        story.append(net_card)

    story.append(Spacer(1, 10))

    # ── Recommendations ───────────────────────────────────────────────────────
    if recs:
        story += _sec("Recommendations", S)
        for i, rec in enumerate(recs, 1):
            row = Table([[
                Paragraph(f'<font color="white"><b>{i}</b></font>',
                          ParagraphStyle("rn", fontName="Helvetica-Bold", fontSize=9,
                                         textColor=WHITE, alignment=TA_CENTER)),
                Paragraph(rec, S["body"]),
            ]], colWidths=[9*mm, CONTENT_W - 9*mm])
            row.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(0,0), BLUE_ACC),
                ("BACKGROUND",    (1,0),(1,0), colors.HexColor("#EFF6FF")),
                ("ALIGN",         (0,0),(0,0), "CENTER"),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
                ("TOPPADDING",    (0,0),(-1,-1), 6),
                ("BOTTOMPADDING", (0,0),(-1,-1), 6),
                ("LEFTPADDING",   (1,0),(1,0), 9),
                ("BOX",           (0,0),(-1,-1), 0.4, GRAY_200),
            ]))
            story.append(row)
            story.append(Spacer(1, 2))
        story.append(Spacer(1, 8))

    # ── Overall Assessment ────────────────────────────────────────────────────
    assessment = data.get("overall_assessment", "")
    if assessment:
        story += _sec("Overall Assessment", S)
        verdict = Table(
            [[Paragraph(assessment,
                        ParagraphStyle("v", fontName="Helvetica-Bold", fontSize=9,
                                       textColor=WHITE, leading=13))]],
            colWidths=[CONTENT_W])
        verdict.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(0,0), NAVY),
            ("BOX",           (0,0),(0,0), 1.5, BLUE_ACC),
            ("TOPPADDING",    (0,0),(0,0), 11),
            ("BOTTOMPADDING", (0,0),(0,0), 11),
            ("LEFTPADDING",   (0,0),(0,0), 14),
            ("RIGHTPADDING",  (0,0),(0,0), 14),
        ]))
        story.append(verdict)
        story.append(Spacer(1, 12))

    # ── Disclaimer ────────────────────────────────────────────────────────────
    story.append(_hr(GRAY_300, 0.5, 3))
    story.append(Paragraph(
        "DISCLAIMER: This report is generated by AI analysis of publicly available social media content. "
        "It is intended for informational purposes only and does not constitute legal advice. "
        "VisaScreenAI does not guarantee visa approval or denial outcomes. "
        "Consult a qualified immigration attorney for legal guidance.",
        S["disc"]))

    return story


# ── Entry point ───────────────────────────────────────────────────────────────

def generate_pdf(report_data: dict, output_path: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cv = canvas.Canvas(output_path, pagesize=A4)
    draw_cover_page(cv, report_data)
    cv.showPage(); cv.save()

    body_path = output_path.replace(".pdf", "_body.pdf")
    styles    = _styles()
    story     = build_report_story(report_data, styles)

    doc = BaseDocTemplate(
        body_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=18*mm, bottomMargin=16*mm,
    )
    frame    = Frame(MARGIN, 16*mm, CONTENT_W, H - 34*mm, id="normal")
    template = PageTemplate(id="main", frames=[frame], onPage=_page_template)
    doc.addPageTemplates([template])
    doc.build(story)

    try:
        from pypdf import PdfWriter, PdfReader
        writer = PdfWriter()
        for path in [output_path, body_path]:
            for page in PdfReader(path).pages:
                writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
        os.remove(body_path)
    except ImportError:
        import shutil
        shutil.move(body_path, output_path)

    return output_path


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample = {
        "name": "Priya Sharma",
        "country": "India",
        "reason": "H1-B Visa – Software Engineer",
        "accounts": [
            {"platform": "twitter",   "handle": "@PriyaActivist"},
            {"platform": "instagram", "handle": "priya.radical"},
            {"platform": "tiktok",    "handle": "priyaspeaksout"},
        ],
        "overall_risk": "HIGH",
        "risk_score": 82,
        "scores": {"political": 82, "content": 74, "network": 89},
        "summary": (
            "Priya Sharma exhibits significant risk factors including association with politically extreme "
            "networks, sharing of anti-establishment content, and concerning connections to individuals with "
            "radical viewpoints. Her social media presence shows patterns of political radicalization, "
            "support for disruptive activities, and amplification of divisive content.\n\n"
            "Network analysis reveals connections to individuals promoting extreme political views both in "
            "the US and internationally, raising concerns about potential security risks and workplace disruption."
        ),
        "flagged_posts": [
            {
                "text": "The system is broken beyond repair. Time for real action, not just voting. Join us at the Federal Building this weekend - let's make them LISTEN. Revolution starts with us! 🔥 #SystemChange #DirectAction #RevolutionNow",
                "platform": "Twitter",
                "date": "2025-03-20",
                "post_url": "https://x.com/PriyaActivist/status/123",
                "risk_level": "HIGH",
                "risk_category": "Political Extremism & Protest Organization",
                "explanation": "This post advocates for revolutionary action and organizes potentially unlawful demonstrations at federal facilities. Language suggests intent to disrupt government operations.",
            },
            {
                "text": "Proud of my Mexican friends leading the resistance! Their courage in fighting ICE raids shows what real solidarity looks like. Borders are just lines drawn by oppressors. #OpenBorders #DefundICE",
                "platform": "Instagram",
                "date": "2025-03-15",
                "post_url": "",
                "risk_level": "HIGH",
                "risk_category": "Immigration Law Violation Support",
                "explanation": "Openly supports resistance to federal immigration enforcement and promotes illegal border crossing. Demonstrates allegiance to foreign nationals over US law.",
            },
            {
                "text": "Corporate America exploits immigrant workers while pretending to care about diversity. Time to organize from within. Tech workers have power - we should use it to shut down the machine. #TechStrike",
                "platform": "Twitter",
                "date": "2025-02-18",
                "post_url": "",
                "risk_level": "MEDIUM",
                "risk_category": "Workplace Disruption Advocacy",
                "explanation": "Promotes organized workplace disruption and strikes within the technology sector. Suggests intent to use employment position for political activism.",
            },
            {
                "text": "The American dream is a lie sold to immigrants like us. This country was built on genocide and slavery - why should we respect its laws? My ancestors were colonized, now it's time for payback. #Decolonize",
                "platform": "TikTok",
                "date": "2025-02-10",
                "post_url": "",
                "risk_level": "MEDIUM",
                "risk_category": "Anti-American Sentiment",
                "explanation": "Expresses hostility toward American institutions and laws. Frames relationship with host country in adversarial terms with concerning retribution language.",
            },
        ],
        "network_connections": [
            {
                "name": "Carlos Rodriguez",
                "handle": "@carlosresistance",
                "platform": "Twitter",
                "role": "Activist Leader",
                "location": "Mexico City",
                "post_text": "Time to escalate our tactics. Peaceful protest is just permission to be ignored. The system only understands force. Priya and our crew know what needs to be done. #RevolutionNow",
                "posted_at": "March 18, 2025",
                "risk_factor": "Promotes violent escalation tactics and directly mentions coordination with Priya. Known organizer of anti-government demonstrations.",
            },
            {
                "name": "Miguel Perez",
                "handle": "@miguel_borderless",
                "platform": "Instagram",
                "role": "Immigration Activist",
                "location": "Tijuana/San Diego",
                "post_text": "Border patrol can't stop what's coming. Thanks to allies like @PriyaActivist spreading the word - solidarity knows no borders. Meet at the usual spot this weekend.",
                "posted_at": "March 12, 2025",
                "risk_factor": "Coordinates cross-border activities and references clandestine meetings. Suggests involvement in illegal immigration facilitation networks.",
            },
            {
                "name": "Valentina Castro",
                "handle": "@vale_antifa_mx",
                "platform": "Telegram",
                "role": "Antifa Organizer",
                "location": "Mexico City",
                "post_text": "Priya's doing important work in Silicon Valley - disrupting the tech-industrial complex from inside. Solidarity with our comrades fighting US imperialism from within! #TechSabotage",
                "posted_at": "February 8, 2025",
                "risk_factor": "Known Antifa organizer coordinating with Priya on workplace disruption. References sabotage activities within the technology sector.",
            },
        ],
        "risk_topics": [
            "Political Extremism", "Anti-Government Rhetoric",
            "Protest Organization", "Immigration Issues",
            "International Politics", "Workplace Activism",
        ],
        "sentiment": {"positive": 15, "neutral": 30, "negative": 55},
        "recommendations": [
            "Review all posts containing political commentary before your visa interview.",
            "Consider making sensitive posts private or removing them entirely.",
            "Ensure your social media profile clearly reflects your professional objectives.",
            "Consult an immigration attorney to discuss how your social media history may affect your application.",
        ],
        "overall_assessment": "HIGH RISK — Content identified that may trigger scrutiny under INA §212 grounds of inadmissibility. Recommend immediate review and consultation with immigration counsel before proceeding.",
        "posts_analyzed": 156,
        "platforms_analyzed": ["Twitter/X", "Instagram", "TikTok"],
    }

    Path(".tmp/reports").mkdir(parents=True, exist_ok=True)
    out = generate_pdf(sample, ".tmp/reports/test_report.pdf")
    print(f"PDF saved: {out}")
