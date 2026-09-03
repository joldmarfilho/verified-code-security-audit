"""Generate localized PDF security-audit reports with portable Unicode fonts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from io import BytesIO
from pathlib import Path
from textwrap import fill, wrap
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
    Flowable,
    HRFlowable,
    Image,
    CondPageBreak,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    XPreformatted,
)

from verified_code_security_audit.markdown import render_issues

_FONT_REGISTERED = False
_FONT_REGULAR = "VCSA-DejaVu"
_FONT_BOLD = "VCSA-DejaVu-Bold"
_FONT_MONO = "VCSA-DejaVu-Mono"
_SEVERITY_ORDER = ("critical", "high", "medium", "low", "informational")
# Characters that fit the printable width at each monospace size (A4 minus margins).
_CODE_WRAP_WIDTH = 104
_APPENDIX_WRAP_WIDTH = 132
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
    mono_path = findfont("DejaVu Sans Mono", fallback_to_default=False)
    pdfmetrics.registerFont(TTFont(_FONT_REGULAR, regular_path))
    pdfmetrics.registerFont(TTFont(_FONT_BOLD, bold_path))
    pdfmetrics.registerFont(TTFont(_FONT_MONO, mono_path))
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


def _markup_paragraph(markup: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(markup, style)


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
    """Render a modern severity distribution donut chart."""

    findings = report["findings"]
    counts = Counter(str(item["severity"]) for item in findings)  # type: ignore[index]
    fig, axis = plt.subplots(figsize=(5.2, 2.8), dpi=160)
    fig.patch.set_facecolor("#FFFFFF")
    axis.set_facecolor("#FFFFFF")
    axis.set_title(
        strings["chart.findings_by_severity"],
        fontweight="bold",
        fontsize=9.5,
        color="#0F172A",
        pad=8,
    )
    if not counts:
        axis.text(
            0.5,
            0.5,
            f"0\n{strings['chart.no_findings']}",
            ha="center",
            va="center",
            fontsize=12,
            color="#64748B",
            fontweight="bold",
        )
        axis.set_axis_off()
        return _save_chart(fig)

    labels = [severity for severity in _SEVERITY_ORDER if counts[severity]]
    values = [counts[label] for label in labels]
    total = sum(values)

    wedges, texts, autotexts = axis.pie(
        values,
        labels=[strings[f"severity.{label}"] for label in labels],
        colors=[_SEVERITY_COLORS[label] for label in labels],
        autopct=lambda value: f"{value:.0f}%" if value >= 10 else "",
        pctdistance=0.74,
        startangle=90,
        wedgeprops={"width": 0.38, "edgecolor": "#FFFFFF", "linewidth": 2.0},
        textprops={"fontsize": 7.5, "color": "#1E293B"},
    )
    for autotext in autotexts:
        autotext.set_color("#FFFFFF")
        autotext.set_fontsize(7.5)
        autotext.set_fontweight("bold")

    axis.text(
        0,
        0,
        f"{total}",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color="#0F172A",
    )
    axis.axis("equal")
    fig.tight_layout()
    return _save_chart(fig)


def category_chart(
    report: Mapping[str, object], strings: Mapping[str, str]
) -> BytesIO:
    """Render the finding count by category with modern borderless styling."""

    findings = report["findings"]
    counts = Counter(str(item["category_id"]) for item in findings)  # type: ignore[index]
    fig, axis = plt.subplots(figsize=(5.2, 2.8), dpi=160)
    fig.patch.set_facecolor("#FFFFFF")
    axis.set_facecolor("#FFFFFF")
    axis.set_title(
        strings["chart.findings_by_category"],
        fontweight="bold",
        fontsize=9.5,
        color="#0F172A",
        pad=8,
    )
    if not counts:
        axis.text(
            0.5,
            0.5,
            f"0\n{strings['chart.no_findings']}",
            ha="center",
            va="center",
            fontsize=12,
            color="#64748B",
            fontweight="bold",
        )
        axis.set_axis_off()
        return _save_chart(fig)

    category_names = {
        str(item["id"]): str(item["name"])
        for item in report["categories"]  # type: ignore[index]
    }
    severity_rank = {name: index for index, name in enumerate(_SEVERITY_ORDER)}
    worst: dict[str, str] = {}
    for finding in findings:  # type: ignore[assignment]
        category_id = str(finding["category_id"])
        severity = str(finding["severity"])
        current = worst.get(category_id)
        if current is None or severity_rank[severity] < severity_rank[current]:
            worst[category_id] = severity

    category_ids = list(counts)
    labels = [fill(category_names.get(value, value), width=24) for value in category_ids]
    values = [counts[value] for value in category_ids]
    colors_by_category = [_SEVERITY_COLORS[worst[value]] for value in category_ids]

    bars = axis.barh(labels, values, color=colors_by_category, height=0.52, zorder=3)
    axis.bar_label(bars, padding=4, fontsize=7.5, color="#0F172A", fontweight="bold")
    axis.set_xlabel(strings["summary.total_findings"], fontsize=7.5, color="#64748B")
    axis.invert_yaxis()
    axis.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    axis.tick_params(axis="y", labelsize=7.5, colors="#1E293B", left=False)
    axis.tick_params(axis="x", labelsize=7.5, colors="#64748B", bottom=False)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_visible(False)
    axis.spines["bottom"].set_color("#E2E8F0")
    axis.spines["bottom"].set_linewidth(0.8)
    axis.grid(axis="x", color="#F1F5F9", linestyle="-", linewidth=1, zorder=0)
    fig.tight_layout()
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
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "VCSASubtitle",
            parent=base["Normal"],
            fontName=_FONT_REGULAR,
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "heading": ParagraphStyle(
            "VCSAHeading",
            parent=base["Heading2"],
            fontName=_FONT_BOLD,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "VCSABody",
            parent=base["BodyText"],
            fontName=_FONT_REGULAR,
            fontSize=9.0,
            leading=13.5,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=6,
        ),
        "small": ParagraphStyle(
            "VCSASmall",
            parent=base["BodyText"],
            fontName=_FONT_REGULAR,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=4,
        ),
        "finding_title": ParagraphStyle(
            "VCSAFindingTitle",
            parent=base["Heading3"],
            fontName=_FONT_BOLD,
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=7,
            spaceAfter=4,
        ),
        "evidence_location": ParagraphStyle(
            "VCSAEvidenceLocation",
            parent=base["BodyText"],
            fontName=_FONT_BOLD,
            fontSize=7.8,
            leading=10,
            textColor=colors.HexColor("#475569"),
            spaceBefore=8,
            spaceAfter=11,
        ),
        "code": ParagraphStyle(
            "VCSACode",
            parent=base["Code"],
            fontName=_FONT_MONO,
            fontSize=7.0,
            leading=9.0,
            textColor=colors.HexColor("#0F172A"),
            backColor=colors.HexColor("#F8FAFC"),
            borderColor=colors.HexColor("#E2E8F0"),
            borderWidth=0.5,
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "appendix": ParagraphStyle(
            "VCSAAppendix",
            parent=base["Code"],
            fontName=_FONT_MONO,
            fontSize=5.0,
            leading=5.35,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=4,
        ),
        "table_header": ParagraphStyle(
            "VCSATableHeader",
            parent=base["BodyText"],
            fontName=_FONT_BOLD,
            fontSize=7.5,
            leading=9.5,
            textColor=colors.white,
        ),
        "table_cell": ParagraphStyle(
            "VCSATableCell",
            parent=base["BodyText"],
            fontName=_FONT_REGULAR,
            fontSize=7.2,
            leading=9.5,
            textColor=colors.HexColor("#1E293B"),
        ),
        "kpi_cell": ParagraphStyle(
            "VCSAKpiCell",
            parent=base["Normal"],
            fontName=_FONT_REGULAR,
            fontSize=7.5,
            leading=11,
            textColor=colors.HexColor("#1E293B"),
            alignment=TA_CENTER,
        ),
    }


def _page_decorations(canvas: object, doc: SimpleDocTemplate, strings: Mapping[str, str]) -> None:
    if doc.page == 1:
        return
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#E2E8F0"))
    canvas.setLineWidth(0.6)
    canvas.line(2 * cm, A4[1] - 1.25 * cm, A4[0] - 2 * cm, A4[1] - 1.25 * cm)
    canvas.setFont(_FONT_REGULAR, 7.5)
    canvas.setFillColor(colors.HexColor("#64748B"))
    canvas.drawString(2 * cm, A4[1] - 1.05 * cm, strings["report.title"])
    canvas.line(2 * cm, 1.25 * cm, A4[0] - 2 * cm, 1.25 * cm)
    canvas.drawString(2 * cm, 0.95 * cm, "Verified Code Security Audit")
    canvas.drawRightString(
        A4[0] - 2 * cm,
        0.95 * cm,
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


def _table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def _evidence_blocks(
    items: Sequence[Mapping[str, object]],
    styles: Mapping[str, ParagraphStyle],
) -> list[Flowable]:
    blocks: list[Flowable] = []
    for item in items:
        end = item.get("end_line")
        location = f"{item['path']}:{item['start_line']}"
        if end is not None and end != item["start_line"]:
            location += f"-{end}"
        blocks.append(_paragraph(location, styles["evidence_location"]))
        blocks.append(
            XPreformatted(
                escape(_wrap_preformatted(str(item["snippet"]), width=_CODE_WRAP_WIDTH)),
                styles["code"],
            )
        )
    return blocks


def _severity_chip(
    severity: str,
    strings: Mapping[str, str],
    styles: Mapping[str, ParagraphStyle],
) -> Table:
    chip = Table(
        [[_paragraph(strings[f"severity.{severity}"], styles["table_header"])]],
        colWidths=[2.8 * cm],
        hAlign="LEFT",
    )
    chip.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(_SEVERITY_COLORS[severity])),
                ("BOX", (0, 0), (-1, -1), 0, colors.transparent),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ]
        )
    )
    return chip


def _finding_card(
    finding: Mapping[str, object],
    strings: Mapping[str, str],
    styles: Mapping[str, ParagraphStyle],
) -> KeepTogether:
    severity = str(finding["severity"])
    confidence = str(finding["confidence"])
    preconditions = "\n".join(f"- {value}" for value in finding["preconditions"]) or "—"
    acceptance = "\n".join(
        f"- {value}" for value in finding["acceptance_criteria"]
    )
    references = ", ".join(str(value) for value in finding["references"]) or "—"
    blocks: list[Flowable] = [
        _severity_chip(severity, strings, styles),
        _paragraph(
            f"{finding['id']} — {finding['title']}",
            styles["finding_title"],
        ),
        _paragraph(str(finding["description"]), styles["body"]),
        _paragraph(
            f"{strings['label.confidence']}: {strings[f'confidence.{confidence}']}",
            styles["body"],
        ),
        _paragraph(
            f"{strings['label.preconditions']}:\n{preconditions}",
            styles["body"],
        ),
        _paragraph(
            f"{strings['label.exploit_path']}: {finding['exploit_path']}",
            styles["body"],
        ),
        _paragraph(strings["label.evidence"], styles["finding_title"]),
    ]
    blocks.extend(_evidence_blocks(finding["evidence"], styles))
    blocks.extend(
        [
            _paragraph(
                f"{strings['label.impact']}: {finding['impact']}",
                styles["body"],
            ),
            _paragraph(
                f"{strings['label.remediation']}: {finding['remediation']}",
                styles["body"],
            ),
            _paragraph(
                f"{strings['label.acceptance']}:\n{acceptance}",
                styles["body"],
            ),
            _paragraph(
                f"{strings['label.references']}: {references}",
                styles["small"],
            ),
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=colors.HexColor("#E2E8F0"),
                spaceBefore=6,
                spaceAfter=12,
            ),
        ]
    )
    return KeepTogether(blocks)


def _wrap_preformatted(text: str, width: int = _APPENDIX_WRAP_WIDTH) -> str:
    """Wrap long source lines without collapsing explicit Markdown newlines."""

    output: list[str] = []
    for line in text.splitlines():
        if len(line) <= width:
            output.append(line)
            continue
        indentation = line[: len(line) - len(line.lstrip())]
        output.extend(
            wrap(
                line,
                width=width,
                subsequent_indent=f"{indentation}  ",
                replace_whitespace=False,
                drop_whitespace=True,
                break_long_words=True,
                break_on_hyphens=False,
            )
            or [line]
        )
    return "\n".join(output)


def render_pdf(
    report: Mapping[str, object],
    strings: Mapping[str, str],
    output_path: Path,
) -> None:
    """Render a complete localized audit report and verify the output."""

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

    severity_counts = Counter(str(item["severity"]) for item in findings)
    severity_summary = " | ".join(
        f"{strings[f'severity.{severity}']}: {severity_counts[severity]}"
        for severity in _SEVERITY_ORDER
    )

    kpi_cols: list[Flowable] = []
    for sev in _SEVERITY_ORDER:
        count = severity_counts[sev]
        kpi_cols.append(
            _markup_paragraph(
                f"<font size=12><b>{count}</b></font><br/>{strings[f'severity.{sev}']}",
                styles["kpi_cell"],
            )
        )
    kpi_table = Table([kpi_cols], colWidths=[3.4 * cm] * 5, hAlign="LEFT")
    kpi_style: list[tuple[object, ...]] = [
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#F1F5F9")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for idx, sev in enumerate(_SEVERITY_ORDER):
        kpi_style.append(
            ("LINEABOVE", (idx, 0), (idx, 0), 2.5, colors.HexColor(_SEVERITY_COLORS[sev]))
        )
    kpi_table.setStyle(TableStyle(kpi_style))

    meta_table = Table(
        [
            [
                _paragraph(f"{strings['label.project']}: {metadata['project_name']}", styles["finding_title"]),
                _paragraph(f"{strings['label.audit_date']}: {metadata['audited_at']}", styles["body"]),
            ],
            [
                _paragraph(f"{metadata['repository']}", styles["small"]),
                _paragraph(f"{strings['label.revision']}: {metadata['revision']}", styles["small"]),
            ],
        ],
        colWidths=[8.5 * cm, 8.5 * cm],
        hAlign="LEFT",
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#F1F5F9")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    story: list[Flowable] = [
        Spacer(1, 2.5 * cm),
        _paragraph(strings["report.title"], styles["title"]),
        _paragraph(strings["report.subtitle"], styles["subtitle"]),
        Spacer(1, 0.8 * cm),
        meta_table,
        Spacer(1, 0.6 * cm),
        _paragraph(
            f"{strings['label.scope']}: {scope['summary']}",
            styles["body"],
        ),
        Spacer(1, 0.5 * cm),
        kpi_table,
        Spacer(1, 2.5 * cm),
        _paragraph(strings["disclaimer"], styles["small"]),
        PageBreak(),
    ]

    story.append(_paragraph(strings["section.executive_summary"], styles["heading"]))
    story.append(
        _paragraph(
            f"{strings['summary.total_findings']}: {len(findings)} | "
            f"{strings['summary.total_strengths']}: {len(strengths)}",
            styles["body"],
        )
    )
    severity_image = severity_chart(report, strings)
    category_image = category_chart(report, strings)
    chart_table = Table(
        [[
            Image(severity_image, width=8.2 * cm, height=4.4 * cm),
            Image(category_image, width=8.2 * cm, height=4.4 * cm),
        ]],
        colWidths=[8.5 * cm, 8.5 * cm],
    )
    chart_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(chart_table)

    story.append(_paragraph(strings["section.methodology"], styles["heading"]))
    story.append(_paragraph(scope["summary"], styles["body"]))
    included = "\n".join(f"- {value}" for value in scope["included_paths"])
    story.append(_paragraph(included, styles["small"]))
    for excluded in scope["excluded_paths"]:
        story.append(
            _paragraph(
                f"{excluded['path']}: {excluded['reason']}",
                styles["small"],
            )
        )

    story.append(_paragraph(strings["section.stack"], styles["heading"]))
    if not report["stack"]:
        story.append(_paragraph(strings["empty.generic"], styles["body"]))
    for component in report["stack"]:  # type: ignore[assignment]
        version = f" {component['version']}" if component.get("version") else ""
        story.append(
            _paragraph(
                f"{component['name']}{version} — {component['kind']}",
                styles["finding_title"],
            )
        )
        story.extend(_evidence_blocks(component["evidence"], styles))

    story.append(_paragraph(strings["section.coverage"], styles["heading"]))
    coverage_rows: list[list[Flowable]] = [
        [
            _paragraph(strings["table.description"], styles["table_header"]),
            _paragraph(strings["table.status"], styles["table_header"]),
            _paragraph(strings["table.coverage"], styles["table_header"]),
            _paragraph(strings["table.method"], styles["table_header"]),
        ]
    ]
    for item in report["coverage"]:  # type: ignore[assignment]
        discovered = "—" if item["discovered"] is None else str(item["discovered"])
        coverage_value = f"{item['reviewed']} / {discovered}"
        exclusions = "\n".join(str(value) for value in item["exclusions"])
        method = str(item["method"])
        if exclusions:
            method = f"{method}\n{exclusions}"
        coverage_rows.append(
            [
                _paragraph(str(item["surface"]), styles["table_cell"]),
                _paragraph(strings[f"coverage.{item['status']}"], styles["table_cell"]),
                _paragraph(coverage_value, styles["table_cell"]),
                _paragraph(method, styles["table_cell"]),
            ]
        )
    coverage_table = Table(
        coverage_rows,
        colWidths=[4.0 * cm, 2.7 * cm, 2.4 * cm, 7.0 * cm],
        repeatRows=1,
    )
    coverage_table.setStyle(_table_style())
    story.append(coverage_table)

    story.append(_paragraph(strings["section.strengths"], styles["heading"]))
    if not strengths:
        story.append(_paragraph(strings["empty.strengths"], styles["body"]))
    for strength in strengths:
        story.append(_paragraph(str(strength["title"]), styles["finding_title"]))
        story.append(_paragraph(str(strength["description"]), styles["body"]))
        story.extend(_evidence_blocks(strength["evidence"], styles))

    story.append(_paragraph(strings["section.weaknesses"], styles["heading"]))
    if not findings:
        story.append(_paragraph(strings["chart.no_findings"], styles["body"]))
    for finding in findings:
        severity = str(finding["severity"])
        story.append(
            _paragraph(
                f"{finding['id']} | {strings[f'severity.{severity}']} | "
                f"{finding['title']} — {finding['impact']}",
                styles["body"],
            )
        )

    if findings:
        story.append(CondPageBreak(8 * cm))
    story.append(_paragraph(strings["section.findings"], styles["heading"]))
    if not findings:
        story.append(_paragraph(strings["chart.no_findings"], styles["body"]))
    for finding in findings:
        story.append(_finding_card(finding, strings, styles))

    story.append(_paragraph(strings["section.recommendations"], styles["heading"]))
    if not recommendations:
        story.append(_paragraph(strings["empty.recommendations"], styles["body"]))
    else:
        priority_rank = {"P1": 0, "P2": 1, "P3": 2}
        recommendation_rows: list[list[Flowable]] = [
            [
                _paragraph(strings["table.priority"], styles["table_header"]),
                _paragraph(strings["table.id"], styles["table_header"]),
                _paragraph(strings["table.description"], styles["table_header"]),
                _paragraph(strings["table.related_findings"], styles["table_header"]),
            ]
        ]
        ordered_recommendations = sorted(
            recommendations,
            key=lambda value: (
                priority_rank[str(value["priority"])],
                str(value["id"]),
            ),
        )
        for recommendation in ordered_recommendations:
            recommendation_rows.append(
                [
                    _paragraph(str(recommendation["priority"]), styles["table_cell"]),
                    _paragraph(str(recommendation["id"]), styles["table_cell"]),
                    _paragraph(
                        f"{recommendation['title']}\n{recommendation['details']}",
                        styles["table_cell"],
                    ),
                    _paragraph(
                        ", ".join(str(value) for value in recommendation["finding_ids"]),
                        styles["table_cell"],
                    ),
                ]
            )
        recommendation_table = Table(
            recommendation_rows,
            colWidths=[1.8 * cm, 1.6 * cm, 9.0 * cm, 3.7 * cm],
            repeatRows=1,
        )
        recommendation_table.setStyle(_table_style())
        story.append(recommendation_table)

    story.append(_paragraph(strings["section.limitations"], styles["heading"]))
    if not limitations:
        story.append(_paragraph(strings["empty.limitations"], styles["body"]))
    for limitation in limitations:
        affected = ", ".join(str(value) for value in limitation["affected_paths"])
        story.append(
            _paragraph(
                f"{limitation['title']} — {limitation['details']} ({affected})",
                styles["body"],
            )
        )
    story.append(_paragraph(strings["label.categories"], styles["finding_title"]))
    if not report["categories"]:
        story.append(_paragraph(strings["empty.generic"], styles["body"]))
    for category in report["categories"]:  # type: ignore[assignment]
        category_status = strings[f"category.{category['status']}"]
        story.append(
            _paragraph(
                f"{category['id']} | {category['name']} | "
                f"{category_status} — {category['summary']}",
                styles["body"],
            )
        )
        story.extend(_evidence_blocks(category["evidence"], styles))

    story.append(CondPageBreak(14 * cm))
    story.append(_paragraph(strings["section.github_issues"], styles["heading"]))
    issue_text = render_issues(report, strings)
    story.append(
        Preformatted(
            escape(_wrap_preformatted(issue_text)),
            styles["appendix"],
        )
    )

    decorate = lambda canvas, current_doc: _page_decorations(
        canvas, current_doc, strings
    )
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    verify_pdf_structure(output_path)
