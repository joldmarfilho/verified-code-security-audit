"""Generate localized PDF security-audit reports with portable Unicode fonts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")

from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties, findfont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from verified_code_security_audit.markdown import group_actionable_findings

_FONT_REGISTERED = False
_FONT_REGULAR = "VCSA-DejaVu"
_FONT_BOLD = "VCSA-DejaVu-Bold"
_SEVERITY_COLORS = {
    "critical": "#7F1D1D",
    "high": "#DC2626",
    "medium": "#F59E0B",
    "low": "#2563EB",
    "informational": "#64748B",
}


def _register_fonts() -> None:
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return

    regular_path = findfont("DejaVu Sans", fallback_to_default=False)
    bold_path = findfont(
        FontProperties(family="DejaVu Sans", weight="bold"),
        fallback_to_default=False,
    )
    pdfmetrics.registerFont(TTFont(_FONT_REGULAR, regular_path))
    pdfmetrics.registerFont(TTFont(_FONT_BOLD, bold_path))
    pdfmetrics.registerFontFamily(
        "VCSA-DejaVu",
        normal=_FONT_REGULAR,
        bold=_FONT_BOLD,
    )
    _FONT_REGISTERED = True


def _safe_markup(text: object) -> str:
    return escape(str(text)).replace("\n", "<br/>")


def _paragraph(text: object, style: ParagraphStyle) -> Paragraph:
    return Paragraph(_safe_markup(text), style)


def _save_chart(fig: object) -> BytesIO:
    image = BytesIO()
    try:
        fig.savefig(image, format="png", dpi=150, bbox_inches="tight")
        image.seek(0)
        return image
    finally:
        plt.close(fig)


def severity_chart(
    report: Mapping[str, object], strings: Mapping[str, str]
) -> BytesIO:
    """Render a severity distribution, including a safe zero-data state."""

    findings = report["findings"]
    counts = Counter(str(item["severity"]) for item in findings)  # type: ignore[index]
    fig, axis = plt.subplots(figsize=(6.4, 3.4))
    axis.set_title(strings["chart.findings_by_severity"], fontweight="bold")
    if not counts:
        axis.text(
            0.5,
            0.5,
            f"0\n{strings['chart.no_findings']}",
            ha="center",
            va="center",
            fontsize=15,
        )
        axis.set_axis_off()
        return _save_chart(fig)

    labels = list(counts)
    values = [counts[label] for label in labels]
    axis.pie(
        values,
        labels=[strings[f"severity.{label}"] for label in labels],
        colors=[_SEVERITY_COLORS[label] for label in labels],
        autopct=lambda value: f"{value:.0f}%",
        startangle=90,
    )
    axis.axis("equal")
    return _save_chart(fig)


def category_chart(
    report: Mapping[str, object], strings: Mapping[str, str]
) -> BytesIO:
    """Render the finding count by category, including a zero-data state."""

    findings = report["findings"]
    counts = Counter(str(item["category_id"]) for item in findings)  # type: ignore[index]
    fig, axis = plt.subplots(figsize=(6.4, 3.4))
    axis.set_title(strings["chart.findings_by_category"], fontweight="bold")
    if not counts:
        axis.text(
            0.5,
            0.5,
            f"0\n{strings['chart.no_findings']}",
            ha="center",
            va="center",
            fontsize=15,
        )
        axis.set_axis_off()
        return _save_chart(fig)

    labels = list(counts)
    values = [counts[label] for label in labels]
    axis.bar(labels, values, color="#2563EB")
    axis.set_ylabel(strings["summary.total_findings"])
    axis.tick_params(axis="x", rotation=20)
    return _save_chart(fig)


def verify_pdf_structure(path: Path) -> None:
    """Reject missing, truncated, or obviously non-PDF output."""

    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot reopen PDF: {exc}") from exc
    if (
        len(data) < 1024
        or not data.startswith(b"%PDF-")
        or b"%%EOF" not in data[-2048:]
    ):
        raise ValueError("invalid PDF structure")


def _styles() -> dict[str, ParagraphStyle]:
    _register_fonts()
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "VCSATitle",
            parent=base["Title"],
            fontName=_FONT_BOLD,
            fontSize=24,
            leading=29,
            textColor=colors.HexColor("#0F172A"),
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "subtitle": ParagraphStyle(
            "VCSASubtitle",
            parent=base["Normal"],
            fontName=_FONT_REGULAR,
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#475569"),
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "heading": ParagraphStyle(
            "VCSAHeading",
            parent=base["Heading2"],
            fontName=_FONT_BOLD,
            fontSize=15,
            leading=19,
            textColor=colors.HexColor("#0F4C81"),
            spaceBefore=13,
            spaceAfter=7,
        ),
        "body": ParagraphStyle(
            "VCSABody",
            parent=base["BodyText"],
            fontName=_FONT_REGULAR,
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "VCSASmall",
            parent=base["BodyText"],
            fontName=_FONT_REGULAR,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=5,
        ),
    }


def _page_decorations(canvas: object, doc: SimpleDocTemplate, strings: Mapping[str, str]) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
    canvas.setLineWidth(0.5)
    canvas.line(2 * cm, A4[1] - 1.25 * cm, A4[0] - 2 * cm, A4[1] - 1.25 * cm)
    canvas.setFont(_FONT_REGULAR, 7.5)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(2 * cm, A4[1] - 1.05 * cm, strings["report.title"])
    canvas.drawRightString(
        A4[0] - 2 * cm,
        1.05 * cm,
        f"{strings['footer.page']} {doc.page}",
    )
    canvas.restoreState()


def _section(
    story: list[object],
    styles: Mapping[str, ParagraphStyle],
    heading: str,
    body: object,
) -> None:
    story.append(_paragraph(heading, styles["heading"]))
    story.append(_paragraph(body, styles["body"]))


def render_pdf(
    report: Mapping[str, object],
    strings: Mapping[str, str],
    output_path: Path,
) -> None:
    """Render the initial localized audit-report document skeleton."""

    styles = _styles()
    metadata = report["metadata"]  # type: ignore[assignment]
    scope = report["scope"]  # type: ignore[assignment]
    findings = report["findings"]  # type: ignore[assignment]
    strengths = report["strengths"]  # type: ignore[assignment]
    recommendations = report["recommendations"]  # type: ignore[assignment]
    limitations = report["limitations"]  # type: ignore[assignment]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=strings["report.title"],
        author="Verified Code Security Audit",
        subject=strings["report.subtitle"],
        creator="Verified Code Security Audit",
    )

    story: list[object] = [
        Spacer(1, 3.2 * cm),
        _paragraph(strings["report.title"], styles["title"]),
        _paragraph(strings["report.subtitle"], styles["subtitle"]),
        Spacer(1, 0.8 * cm),
        _paragraph(metadata["project_name"], styles["title"]),
        _paragraph(
            f"{metadata['repository']}\n{metadata['revision']}",
            styles["small"],
        ),
        Spacer(1, 0.6 * cm),
        _paragraph(scope["summary"], styles["body"]),
        Spacer(1, 1.0 * cm),
        _paragraph(strings["disclaimer"], styles["small"]),
        PageBreak(),
    ]

    _section(
        story,
        styles,
        strings["section.executive_summary"],
        f"{strings['summary.total_findings']}: {len(findings)} · "
        f"{strings['summary.total_strengths']}: {len(strengths)}",
    )
    _section(
        story,
        styles,
        strings["section.methodology"],
        scope["summary"],
    )
    _section(
        story,
        styles,
        strings["section.stack"],
        f"{len(report['stack'])} component(s) recorded.",
    )
    reviewed = sum(int(item["reviewed"]) for item in report["coverage"])  # type: ignore[index]
    _section(
        story,
        styles,
        strings["section.coverage"],
        f"{reviewed} item(s) reviewed across {len(report['coverage'])} surface(s).",
    )
    _section(
        story,
        styles,
        strings["section.strengths"],
        f"{len(strengths)} {strings['summary.total_strengths'].lower()}.",
    )
    _section(
        story,
        styles,
        strings["section.weaknesses"],
        f"{len(findings)} {strings['summary.total_findings'].lower()}.",
    )
    _section(
        story,
        styles,
        strings["section.findings"],
        strings["chart.no_findings"] if not findings else f"{len(findings)}",
    )
    if findings:
        severity_image = severity_chart(report, strings)
        category_image = category_chart(report, strings)
        story.extend(
            [
                Image(severity_image, width=14.5 * cm, height=7.4 * cm),
                Image(category_image, width=14.5 * cm, height=7.4 * cm),
            ]
        )
    _section(
        story,
        styles,
        strings["section.recommendations"],
        str(len(recommendations)),
    )
    _section(
        story,
        styles,
        strings["section.limitations"],
        str(len(limitations)),
    )
    issue_groups = group_actionable_findings(report)
    _section(
        story,
        styles,
        strings["section.github_issues"],
        strings["issue.none"] if not issue_groups else str(len(issue_groups)),
    )

    decorate = lambda canvas, current_doc: _page_decorations(
        canvas, current_doc, strings
    )
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    verify_pdf_structure(output_path)
