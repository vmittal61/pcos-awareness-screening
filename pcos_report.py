"""
PCOS Awareness Summary - one-page PDF report generator.

Usage from your app:

    from pcos_report import build_pdf
    build_pdf("summary.pdf", data)          # writes to a path
    # or pass an io.BytesIO() instead of a path for Streamlit's download_button

See the __main__ block at the bottom for the shape of `data`.
Fonts (Caladea + Inter, both open-licensed) live in ./fonts next to this file.
"""
import os
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import Font
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "fonts")

# Use Caladea/Inter when bundled; fall back to ReportLab's built-in fonts on
# Streamlit Cloud so deployment does not depend on external font binaries.
_font_files = {
    "Disp": ("Caladea-Regular.ttf", "Times-Roman"),
    "DispI": ("Caladea-Italic.ttf", "Times-Italic"),
    "DispB": ("Caladea-Bold.ttf", "Times-Bold"),
    "Body": ("Inter-Regular.ttf", "Helvetica"),
    "BodyM": ("Inter-Medium.ttf", "Helvetica"),
    "BodyS": ("Inter-SemiBold.ttf", "Helvetica-Bold"),
}
for _name, (_filename, _fallback) in _font_files.items():
    _font_path = os.path.join(FD, _filename)
    if os.path.exists(_font_path):
        if _name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(_name, _font_path))
    elif _name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(Font(_name, _fallback, "WinAnsiEncoding"))

pdfmetrics.registerFontFamily("Body", normal="Body", bold="BodyS", italic="Body", boldItalic="BodyS")
pdfmetrics.registerFontFamily("BodyM", normal="BodyM", bold="BodyS", italic="BodyM", boldItalic="BodyS")
pdfmetrics.registerFontFamily("BodyS", normal="BodyS", bold="BodyS", italic="BodyM", boldItalic="BodyS")
pdfmetrics.registerFontFamily("Disp", normal="Disp", bold="DispB", italic="DispI", boldItalic="DispB")
pdfmetrics.registerFontFamily("DispI", normal="DispI", bold="DispB", italic="DispI", boldItalic="DispB")
pdfmetrics.registerFontFamily("DispB", normal="DispB", bold="DispB", italic="DispI", boldItalic="DispB")

# palette: warm paper, ink, deep green, clay
PAPER = HexColor("#F6F0E4")
INK = HexColor("#1E2925")
GREEN = HexColor("#1D4B40")
CLAY = HexColor("#B4553A")
MUTED = HexColor("#6E716A")
RULE = HexColor("#CBC1AC")
TINT = HexColor("#EBE3D0")

W, H = A4
M = 46  # side margin
CW = W - 2 * M


def style(font="Body", size=9.5, lead=None, color=INK, **kw):
    return ParagraphStyle("s", fontName=font, fontSize=size, leading=lead or size * 1.5,
                          textColor=color, alignment=TA_LEFT, **kw)


def para(c, text, x, y_top, width, st):
    """Draw a Paragraph with its top at y_top. Returns height used."""
    p = Paragraph(text, st)
    _, h = p.wrap(width, 1000)
    p.drawOn(c, x, y_top - h)
    return h


def spaced(c, text, x, y, font="BodyS", size=7, color=MUTED, tracking=1.4, align="left"):
    c.saveState()
    t = c.beginText()
    t.setFont(font, size)
    t.setFillColor(color)
    t.setCharSpace(tracking)
    w = pdfmetrics.stringWidth(text, font, size) + tracking * len(text)
    if align == "right":
        x = x - w
    t.setTextOrigin(x, y)
    t.textOut(text)
    c.drawText(t)
    c.restoreState()


def rule(c, y, x0=M, x1=W - M, color=RULE, width=0.6):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x0, y, x1, y)


def dots(c, x0, x1, y):
    if x1 <= x0:
        return
    c.setStrokeColor(RULE)
    c.setLineWidth(0.8)
    c.setDash(0.6, 2.6)
    c.line(x0, y + 1.5, x1, y + 1.5)
    c.setDash()


def section_head(c, y, num, title):
    spaced(c, num, M, y, color=CLAY, size=7.5)
    c.setFont("Disp", 15)
    c.setFillColor(INK)
    c.drawString(M + 26, y - 1, title)
    rule(c, y - 9, color=INK, width=0.8)
    return y - 25


def page_base(c, created_str):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(GREEN)
    c.rect(0, H - 9, W, 9, stroke=0, fill=1)
    spaced(c, "PCOS AWARENESS  ·  PERSONAL CHECK-IN", M, H - 32, color=GREEN)
    spaced(c, created_str.upper(), W - M, H - 32, color=MUTED, align="right")
    rule(c, 38)
    c.setFont("Body", 7)
    c.setFillColor(MUTED)
    c.drawString(M, 26, "Educational research prototype. Not a diagnosis and not medical advice.")
    c.drawRightString(W - M, 26, "Keep this for your own reference")


def marker(c, cx, cy, kind, r=4.0):
    """yes = solid clay dot, no = open ring, unsure = half-filled."""
    c.setLineWidth(1)
    c.setStrokeColor(CLAY if kind == "yes" else MUTED)
    if kind == "yes":
        c.setFillColor(CLAY)
        c.circle(cx, cy, r, stroke=0, fill=1)
    elif kind == "no":
        c.setFillColor(PAPER)
        c.circle(cx, cy, r, stroke=1, fill=1)
    else:
        c.setFillColor(PAPER)
        c.circle(cx, cy, r, stroke=1, fill=1)
        p = c.beginPath()
        p.moveTo(cx, cy - r)
        p.arcTo(cx - r, cy - r, cx + r, cy + r, startAng=-90, extent=180)
        p.close()
        c.setFillColor(MUTED)
        c.drawPath(p, stroke=0, fill=1)


def fmt_num(v):
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return f"{v:g}" if isinstance(v, float) else str(v)


def build_page(c, d, created_str):
    y = H - 50

    # ---- title (one line) + subtitle
    c.setFont("Disp", 29)
    c.setFillColor(INK)
    t1 = "What you’ve noticed, "
    c.drawString(M, y - 24, t1)
    c.setFont("DispI", 29)
    c.setFillColor(GREEN)
    c.drawString(M + pdfmetrics.stringWidth(t1, "Disp", 29), y - 24, "written down.")
    sub = "Prepared " + created_str
    if d.get("age"):
        sub += f"  ·  Age {int(d['age'])}"
    sub += "  ·  A plain-language record to keep or hand to a clinician"
    c.setFont("Body", 8)
    c.setFillColor(MUTED)
    c.drawString(M, y - 42, sub)
    y -= 72

    # ---- 01 symptoms (two columns)
    y = section_head(c, y, "01", "What you told us")
    syms = d["symptoms"]
    per = (len(syms) + 1) // 2
    gap = 26
    colw = (CW - gap) / 2
    for col in range(2):
        yy = y
        x0 = M + col * (colw + gap)
        x1 = x0 + colw
        for label, ans in syms[col * per:(col + 1) * per]:
            kind = {"yes": "yes", "no": "no"}.get(ans.lower(), "unsure")
            c.setFont("Body", 8.8)
            c.setFillColor(INK)
            c.drawString(x0, yy, label)
            lw = pdfmetrics.stringWidth(label, "Body", 8.8)
            dots(c, x0 + lw + 5, x1 - 58, yy)
            marker(c, x1 - 50, yy + 3, kind)
            c.setFont("BodyM" if kind == "yes" else "Body", 8.4)
            c.setFillColor(INK if kind == "yes" else MUTED)
            c.drawString(x1 - 41, yy, ans)
            yy -= 18
    y -= per * 18 - 2
    lx = M
    for kind, txt in (("yes", "noticed"), ("no", "not noticed"), ("unsure", "not sure")):
        marker(c, lx + 4, y + 3, kind, r=3.2)
        c.setFont("Body", 7.2)
        c.setFillColor(MUTED)
        c.drawString(lx + 12, y, txt)
        lx += 18 + pdfmetrics.stringWidth(txt, "Body", 7.2) + 10
    y -= 26

    # ---- 02 score
    y = section_head(c, y, "02", "The experimental score")
    score = float(d["score"])
    c.setFont("Disp", 46)
    c.setFillColor(INK)
    c.drawString(M, y - 36, f"{score:.1f}")
    sw = pdfmetrics.stringWidth(f"{score:.1f}", "Disp", 46)
    c.setFont("Disp", 18)
    c.setFillColor(CLAY)
    c.drawString(M + sw + 3, y - 36, "%")
    spaced(c, "UNCALIBRATED MODEL OUTPUT", M, y - 52, color=CLAY, size=6.4)
    tx = M + 185
    h = para(c, "<b>This is not the chance that you have PCOS.</b> It is a raw number from a small experimental "
                "model. A higher score does not confirm anything, and a lower one does not rule anything out.",
             tx, y - 2, W - M - tx, style(size=8.6, lead=12.6))
    para(c, "Only a clinician, looking at your history, examination and tests together, can say what is going on.",
         tx, y - 2 - h - 4, W - M - tx, style(size=8.6, lead=12.6, color=MUTED))
    y -= 82

    x0, x1 = M, W - M
    ry = y - 6
    c.setStrokeColor(INK)
    c.setLineWidth(0.9)
    c.line(x0, ry, x1, ry)
    for i in range(0, 101, 5):
        xx = x0 + (x1 - x0) * i / 100
        tl = 7 if i % 50 == 0 else (4.5 if i % 10 == 0 else 2.5)
        c.setLineWidth(0.6)
        c.line(xx, ry, xx, ry - tl)
    c.setFont("Body", 6.8)
    c.setFillColor(MUTED)
    for i in (0, 50, 100):
        c.drawCentredString(x0 + (x1 - x0) * i / 100, ry - 15, str(i))
    mx = x0 + (x1 - x0) * score / 100
    c.setFillColor(CLAY)
    p = c.beginPath()
    p.moveTo(mx, ry + 1)
    p.lineTo(mx - 5.5, ry + 12)
    p.lineTo(mx + 5.5, ry + 12)
    p.close()
    c.drawPath(p, stroke=0, fill=1)
    c.setStrokeColor(CLAY)
    c.setLineWidth(1.4)
    c.line(mx, ry + 1, mx, ry - 9)
    y = ry - 28

    meta = f"{d.get('model_name', 'Model')}.  "
    ns = d.get("not_sure_count", 0)
    if ns:
        meta += (f"{ns} answer{'s were' if ns > 1 else ' was'} marked ‘Not sure’, so the model was run under "
                 "each possible response and the outputs averaged; a workaround, not a validated method.  ")
    meta += "Blank report fields were filled in by the model’s own imputation, not treated as normal results."
    h = para(c, meta, M, y, CW, style(size=7.2, lead=10.2, color=MUTED))
    y -= h + 18

    # ---- 03 clinical values (three columns)
    y = section_head(c, y, "03", "Values from your reports")
    items = d["clinical"]
    ncol = 3
    rows = (len(items) + ncol - 1) // ncol
    cg = 20
    cw = (CW - cg * (ncol - 1)) / ncol
    for col in range(ncol):
        yy = y
        for label, val, unit in items[col * rows:(col + 1) * rows]:
            x0c = M + col * (cw + cg)
            x1c = x0c + cw
            c.setFont("Body", 8.2)
            c.setFillColor(INK)
            c.drawString(x0c, yy, label)
            lw = pdfmetrics.stringWidth(label, "Body", 8.2)
            if val is None:
                rt, f, sz, colr = "–", "Body", 8.2, MUTED
            else:
                rt, f, sz, colr = f"{fmt_num(val)} {unit}".strip(), "BodyS", 8.6, GREEN
            rw = pdfmetrics.stringWidth(rt, f, sz)
            dots(c, x0c + lw + 4, x1c - rw - 4, yy)
            c.setFont(f, sz)
            c.setFillColor(colr)
            c.drawRightString(x1c, yy, rt)
            yy -= 16
    y -= rows * 16 + 2
    c.setFont("Body", 7.2)
    c.setFillColor(MUTED)
    c.drawString(M, y, "A dash means the field was left blank. Values are shown as entered, not interpreted or compared with reference ranges.")
    y -= 26

    # ---- 04 next steps
    y = section_head(c, y, "04", "What to do next")
    for i, s in enumerate(d["steps"], 1):
        c.setFont("Disp", 20)
        c.setFillColor(CLAY)
        c.drawString(M, y - 14, str(i))
        h = para(c, s, M + 28, y + 1, CW - 28, style(size=8.7, lead=12.4))
        y -= max(h, 20) + 8
    y -= 6

    # ---- urgent box
    bh = 44
    c.setStrokeColor(CLAY)
    c.setLineWidth(1.1)
    c.setFillColor(TINT)
    c.rect(M, y - bh, CW, bh, stroke=1, fill=1)
    c.setFillColor(CLAY)
    c.rect(M, y - bh, 5, bh, stroke=0, fill=1)
    spaced(c, "GET URGENT CARE, DON’T WAIT FOR AN APPOINTMENT, IF YOU HAVE", M + 18, y - 15, color=CLAY, size=6.3)
    para(c, "Severe or sudden pelvic pain, fainting, very heavy bleeding, or you feel acutely unwell.",
         M + 18, y - 21, CW - 34, style("BodyM", 8.8, 12))
    y -= bh + 16

    # ---- important
    spaced(c, "IMPORTANT", M, y, color=MUTED, size=6.4)
    para(c, d["important"], M, y - 5, CW, style(size=7.2, lead=10.2, color=MUTED))


def build_pdf(target, d):
    created = d.get("created") or date.today()
    created_str = f"{created.day} {created.strftime('%B %Y')}"
    c = canvas.Canvas(target, pagesize=A4)
    c.setTitle("PCOS Awareness Summary")
    c.setAuthor("PCOS Awareness check-in")
    c.setSubject("Personal symptom and report summary")
    page_base(c, created_str)
    build_page(c, d, created_str)
    c.showPage()
    c.save()


# ------------------------------------------------------------------ demo
IMPORTANT = (
    "This prototype has not been clinically or externally validated. The dataset’s original diagnosis-label "
    "process is not fully documented, and clinical fields may overlap with criteria used to assign labels. Do not "
    "use this result to diagnose, rule out PCOS, choose treatment, or delay care. Do not start hormones or "
    "supplements without medical advice.")

if __name__ == "__main__":
    demo = {
        "created": date(2026, 10, 30),
        "age": 25.2,
        "score": 54.0,
        "model_name": "Enhanced RBF-SVM",
        "not_sure_count": 1,
        "symptoms": [
            ("Changes in menstrual cycles", "Yes"),
            ("Darker skin around neck or folds", "Yes"),
            ("Unexplained weight gain", "Yes"),
            ("Scalp hair thinning or hair loss", "No"),
            ("Increased facial or body hair", "Not sure"),
            ("Persistent acne", "No"),
        ],
        "clinical": [
            ("BMI", 24.0, "kg/m²"), ("Cycle length", None, "days"),
            ("FSH", None, "mIU/mL"), ("LH", None, "mIU/mL"),
            ("FSH-to-LH ratio", None, ""), ("TSH", None, "mIU/L"),
            ("AMH", None, "ng/mL"), ("Prolactin", None, "ng/mL"),
            ("Vitamin D", None, "ng/mL"), ("Left follicle count", None, ""),
            ("Right follicle count", None, ""), ("Avg. left follicle size", None, "mm"),
            ("Avg. right follicle size", None, "mm"), ("Endometrial thickness", None, "mm"),
        ],
        "steps": [
            "If your weight has changed unexpectedly, note the timeline and anything else that changed around "
            "then. Avoid crash diets and unprescribed weight-loss products.",
            "Take your original blood-test or ultrasound reports to a clinician so the values can be read against "
            "their reference ranges and your clinical context.",
            "Book a routine appointment with a gynaecologist or another qualified healthcare professional if "
            "symptoms persist, cycles are irregular, or you simply want a proper assessment.",
            "Ask what other explanations should be considered and whether any follow-up tests are appropriate.",
        ],
        "important": IMPORTANT,
    }
    out = os.path.join(HERE, "sample_report.pdf")
    build_pdf(out, demo)
    print("wrote", out)