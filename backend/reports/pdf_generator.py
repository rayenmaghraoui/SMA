"""
Générateur de rapport PDF professionnel à partir du rapport JSON.

Utilise reportlab (pur Python — aucune dépendance système, compatible avec
tout type de déploiement, y compris serverless) pour produire un document
clair, blanc et brandé, adapté à un dirigeant de PME et à une soutenance PFE.

Entrée  : le dictionnaire `report` produit par report_agent.
Sortie  : un flux d'octets PDF (bytes).
"""

import io
import logging
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# ── Charte graphique (cohérente avec le frontend violet) ─────────────────────
_VIOLET = colors.HexColor("#6d28d9")
_VIOLET_LIGHT = colors.HexColor("#ede9fe")
_INK = colors.HexColor("#1e1b2e")
_GREY = colors.HexColor("#64748b")
_LINE = colors.HexColor("#e2e8f0")

# Couleurs de priorité des recommandations (1 = critique → 5 = optionnel)
_PRIORITY_COLORS: Dict[int, tuple] = {
    1: (colors.HexColor("#e11d48"), "Critique"),
    2: (colors.HexColor("#ea580c"), "Haute"),
    3: (colors.HexColor("#d97706"), "Moyenne"),
    4: (colors.HexColor("#7c3aed"), "Faible"),
    5: (colors.HexColor("#64748b"), "Optionnel"),
}


def _build_styles() -> Dict[str, ParagraphStyle]:
    """Construit la feuille de styles du document."""
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=22, textColor=colors.white, alignment=TA_LEFT, leading=26,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontName="Helvetica",
            fontSize=10, textColor=_VIOLET_LIGHT, alignment=TA_LEFT,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName="Helvetica-Bold",
            fontSize=14, textColor=_VIOLET, spaceBefore=16, spaceAfter=8,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontName="Helvetica",
            fontSize=10, textColor=_INK, leading=15, alignment=TA_LEFT,
        ),
        "summary": ParagraphStyle(
            "summary", parent=base["Normal"], fontName="Helvetica",
            fontSize=11, textColor=_INK, leading=17, alignment=TA_LEFT,
        ),
        "rec_title": ParagraphStyle(
            "rec_title", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=11, textColor=_INK, leading=14,
        ),
        "rec_body": ParagraphStyle(
            "rec_body", parent=base["Normal"], fontName="Helvetica",
            fontSize=9.5, textColor=_INK, leading=13,
        ),
        "badge": ParagraphStyle(
            "badge", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8, textColor=colors.white, alignment=TA_CENTER,
        ),
        "cell": ParagraphStyle(
            "cell", parent=base["Normal"], fontName="Helvetica",
            fontSize=9, textColor=_INK, leading=12,
        ),
        "cell_head": ParagraphStyle(
            "cell_head", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=9, textColor=colors.white, leading=12,
        ),
        "footer": ParagraphStyle(
            "footer", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.5, textColor=_GREY, alignment=TA_CENTER,
        ),
    }
    return styles


def _format_value(value: Any, fmt: str, unite: str) -> str:
    """Formate une valeur de KPI selon son type (currency, percent, number, text)."""
    try:
        if fmt == "currency":
            return f"{float(value):,.0f} {unite}".replace(",", " ")
        if fmt == "percent":
            return f"{float(value):.1f} %"
        if fmt == "number":
            return f"{float(value):,.0f}".replace(",", " ")
    except (ValueError, TypeError):
        pass
    return f"{value}"


def _header_footer(canvas, doc, generated_at: str) -> None:
    """Dessine le bandeau d'en-tête et le pied de page sur chaque page."""
    canvas.saveState()
    width, height = A4

    # Bandeau violet en haut
    canvas.setFillColor(_VIOLET)
    canvas.rect(0, height - 3.0 * cm, width, 3.0 * cm, fill=1, stroke=0)

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 18)
    canvas.drawString(2 * cm, height - 1.7 * cm, "AI Business Consultant")
    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(_VIOLET_LIGHT)
    canvas.drawString(2 * cm, height - 2.4 * cm, "Rapport d'Analyse Stratégique")
    canvas.drawRightString(width - 2 * cm, height - 2.4 * cm, generated_at)

    # Pied de page
    canvas.setFillColor(_GREY)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(
        width / 2, 1.0 * cm,
        f"AI Business Consultant — Document généré automatiquement — Page {doc.page}",
    )
    canvas.setStrokeColor(_LINE)
    canvas.line(2 * cm, 1.4 * cm, width - 2 * cm, 1.4 * cm)
    canvas.restoreState()


def _kpi_table(domain: Dict[str, Any], styles: Dict[str, ParagraphStyle]) -> Table:
    """Construit un tableau de KPIs pour un domaine (finance, marketing, catégories)."""
    rows = [[
        Paragraph("Indicateur", styles["cell_head"]),
        Paragraph("Valeur", styles["cell_head"]),
    ]]
    for ind in domain.get("indicateurs", []):
        label = ind.get("label", "")
        value = _format_value(
            ind.get("valeur", ""), ind.get("format", "text"), ind.get("unite", "")
        )
        rows.append([
            Paragraph(label, styles["cell"]),
            Paragraph(f"<b>{value}</b>", styles["cell"]),
        ])

    table = Table(rows, colWidths=[10.5 * cm, 6.0 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _VIOLET),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _VIOLET_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, _LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _recommendation_block(
    rec: Dict[str, Any], styles: Dict[str, ParagraphStyle]
) -> KeepTogether:
    """Construit un bloc de recommandation avec badge de priorité coloré."""
    priorite = rec.get("priorite", 5)
    color, label = _PRIORITY_COLORS.get(priorite, _PRIORITY_COLORS[5])

    badge = Table(
        [[Paragraph(label.upper(), styles["badge"])]],
        colWidths=[2.6 * cm], rowHeights=[0.55 * cm],
    )
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))

    titre = Paragraph(rec.get("titre", ""), styles["rec_title"])
    action = Paragraph(rec.get("action", ""), styles["rec_body"])

    meta_parts = []
    if rec.get("impact"):
        meta_parts.append(f"<b>Impact :</b> {rec['impact']}")
    if rec.get("source"):
        meta_parts.append(f"<b>Source :</b> {rec['source']}")
    meta = (
        Paragraph(" &nbsp;•&nbsp; ".join(meta_parts), styles["rec_body"])
        if meta_parts else None
    )

    inner = [[badge, titre], ["", action]]
    if meta:
        inner.append(["", meta])

    block = Table(inner, colWidths=[2.9 * cm, 13.6 * cm])
    block.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, _LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (1, 0), (1, -1), 4),
    ]))
    return KeepTogether([block, Spacer(1, 0.2 * cm)])


def generate_report_pdf(report: Dict[str, Any]) -> bytes:
    """
    Génère un PDF professionnel à partir d'un rapport d'analyse.

    Args:
        report: Rapport structuré (sortie de report_agent).

    Returns:
        Le contenu binaire du PDF (bytes).
    """
    styles = _build_styles()
    buffer = io.BytesIO()

    # Date de génération
    raw_date = report.get("metadata", {}).get("date_generation", "")
    try:
        generated_at = datetime.fromisoformat(raw_date).strftime("%d/%m/%Y à %H:%M")
    except (ValueError, TypeError):
        generated_at = datetime.now().strftime("%d/%m/%Y à %H:%M")

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=3.6 * cm, bottomMargin=1.8 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="Rapport d'Analyse — AI Business Consultant",
    )

    story: List[Any] = []

    # ── Résumé exécutif ──────────────────────────────────────────────────────
    story.append(Paragraph("Résumé Exécutif", styles["h2"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_VIOLET, spaceAfter=8))
    resume = report.get("resume_executif") or "Aucun résumé disponible."
    story.append(Paragraph(resume, styles["summary"]))
    story.append(Spacer(1, 0.3 * cm))

    # ── KPIs par domaine ─────────────────────────────────────────────────────
    kpis = report.get("kpis", {})
    if kpis:
        story.append(Paragraph("Indicateurs Clés de Performance", styles["h2"]))
        story.append(HRFlowable(width="100%", thickness=1.5, color=_VIOLET, spaceAfter=8))
        for domain in kpis.values():
            if not isinstance(domain, dict) or not domain.get("indicateurs"):
                continue
            story.append(Paragraph(domain.get("titre", ""), styles["body"]))
            story.append(Spacer(1, 0.15 * cm))
            story.append(_kpi_table(domain, styles))
            story.append(Spacer(1, 0.35 * cm))

    # ── Analyse détaillée ────────────────────────────────────────────────────
    interpretation = report.get("interpretation", "").strip()
    if interpretation:
        story.append(Paragraph("Analyse Détaillée", styles["h2"]))
        story.append(HRFlowable(width="100%", thickness=1.5, color=_VIOLET, spaceAfter=8))
        for para in interpretation.split("\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), styles["body"]))
                story.append(Spacer(1, 0.12 * cm))
        story.append(Spacer(1, 0.2 * cm))

    # ── Recommandations ──────────────────────────────────────────────────────
    recommendations = report.get("recommendations", [])
    if recommendations:
        story.append(Paragraph("Recommandations Stratégiques", styles["h2"]))
        story.append(HRFlowable(width="100%", thickness=1.5, color=_VIOLET, spaceAfter=8))
        # Trier par priorité croissante (1 = plus urgent)
        for rec in sorted(recommendations, key=lambda r: r.get("priorite", 5)):
            story.append(_recommendation_block(rec, styles))

    # ── Anomalies ────────────────────────────────────────────────────────────
    anomalies = report.get("anomalies", {})
    details = anomalies.get("details", []) if isinstance(anomalies, dict) else []
    if details:
        story.append(Paragraph(
            f"Anomalies Détectées ({anomalies.get('total', len(details))})",
            styles["h2"],
        ))
        story.append(HRFlowable(width="100%", thickness=1.5, color=_VIOLET, spaceAfter=8))
        rows = [[
            Paragraph("Dataset", styles["cell_head"]),
            Paragraph("Colonne", styles["cell_head"]),
            Paragraph("Valeur", styles["cell_head"]),
            Paragraph("Type", styles["cell_head"]),
        ]]
        for a in details[:15]:
            type_label = "Élevée" if a.get("type") == "high" else "Basse"
            rows.append([
                Paragraph(str(a.get("dataset", "")), styles["cell"]),
                Paragraph(str(a.get("colonne", "")), styles["cell"]),
                Paragraph(str(a.get("valeur", "")), styles["cell"]),
                Paragraph(type_label, styles["cell"]),
            ])
        table = Table(rows, colWidths=[4 * cm, 5 * cm, 4 * cm, 3.5 * cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _VIOLET),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _VIOLET_LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.5, _LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.3 * cm))

    # ── Sources RAG ──────────────────────────────────────────────────────────
    sources = report.get("sources_rag", [])
    if sources:
        story.append(Paragraph("Sources Consultées", styles["h2"]))
        story.append(HRFlowable(width="100%", thickness=1.5, color=_VIOLET, spaceAfter=8))
        for s in sources:
            doc_name = s.get("document", "")
            section = s.get("section", "")
            text = f"• <b>{doc_name}</b>" + (f" — {section}" if section else "")
            story.append(Paragraph(text, styles["body"]))
            story.append(Spacer(1, 0.08 * cm))

    if len(story) <= 3:
        story.append(Paragraph(
            "Le rapport ne contient pas encore de données. "
            "Lancez une analyse depuis l'application.", styles["body"],
        ))

    # Construction avec en-tête/pied de page sur chaque page
    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, generated_at),
        onLaterPages=lambda c, d: _header_footer(c, d, generated_at),
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()
    logger.info("PDF généré : %d octets", len(pdf_bytes))
    return pdf_bytes
