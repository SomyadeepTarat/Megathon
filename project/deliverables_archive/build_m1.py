"""Build Team 254's two-page M1 approach; no personal/team-name identifiers."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle

ROOT = Path(__file__).resolve().parent
styles = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=colors.HexColor("#173D34"), spaceAfter=12),
    "h": ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=colors.HexColor("#173D34"), spaceBefore=11, spaceAfter=5),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=7),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=9, leading=12, spaceAfter=5),
    "flow": ParagraphStyle("flow", fontName="Helvetica-Bold", fontSize=10, leading=16, alignment=TA_LEFT, textColor=colors.HexColor("#173D34")),
}
story = []
def paragraph(text, style="body"):
    story.append(Paragraph(text, styles[style]))


paragraph("Explainable Home Sustainability<br/>and Retrofit Decision Support", "title")
paragraph("M1 APPROACH | Lloyds Problem Statement 2", "small")
paragraph("1. Problem statement and understanding", "h")
paragraph("Homeowners and financial institutions need a transparent way to identify inefficient residential properties and choose practical improvements. An energy rating alone does not explain actual purchased-energy use, installation feasibility, affordability or the trade-offs between upgrades. The challenge is to assess a home, recommend suitable measures, estimate energy and carbon effects, and communicate potential property-value associations responsibly.")
paragraph("We interpret the problem as decision support under incomplete information. Electricity and gas must be modeled separately: a heat pump can increase electricity while reducing gas. Combined measures must account for interactions. Missing readings, unknown suitability and unsupported valuations must remain explicitly unavailable. Numerical estimates must come from validated rules or fitted models; an LLM only interprets intent and explains verified evidence.")
paragraph("2. Idea / abstract", "h")
paragraph("Our proposed platform combines an explainable Green Home Score, a feasibility-aware retrofit planner, a deterministic energy/carbon simulator, an indicative valuation model and a grounded conversational advisor. A homeowner can compare their current home with a selected package or ask, 'Which improvements should I prioritize within my budget?' The system evaluates complete feasible packages rather than adding independent percentage savings. Each output includes its assumptions, units, provenance and availability status.")
paragraph("3. High-level approach and architecture", "h")
flow = Paragraph("Property details + monthly readings<br/> &darr; validation, coverage checks and annual fuel totals<br/> &darr; weighted score + efficiency issues<br/> &darr; feasibility filtering + budget-aware package search<br/> &darr; sequential energy simulation + carbon + indicative valuation<br/> &darr; structured API results &rarr; dashboard + grounded advisor", styles["flow"])
table = Table([[flow]], colWidths=[495])
table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#EDF4F0")),
                          ("BOX", (0,0), (-1,-1), .5, colors.HexColor("#CCDCD4")),
                          ("LEFTPADDING", (0,0), (-1,-1), 12), ("RIGHTPADDING", (0,0), (-1,-1), 12),
                          ("TOPPADDING", (0,0), (-1,-1), 10), ("BOTTOMPADDING", (0,0), (-1,-1), 10)]))
story.append(table)
story.append(Spacer(1, 8))
paragraph("<b>Implementation:</b> Python/FastAPI and validated schemas for numerical APIs; pandas and scikit-learn for data processing and valuation; SQLite for local persistence; a planned Next.js dashboard for comparisons. Local Ollama supports intent extraction and evidence selection, with deterministic explanation fallback. Core calculations remain independent of the LLM and remote services.")
story.append(PageBreak())

paragraph("Modeling, Validation and Roadmap", "title")
paragraph("4. Numerical methodology and data plan", "h")
paragraph("<b>Scoring:</b> The 0-100 score uses EPC 25%, purchased-energy intensity 20%, insulation 15%, heating 15%, glazing 10%, renewable contribution 10% and smart controls 5%. Component mappings are documented modeling assumptions. Intensity uses annual purchased electricity plus gas divided by floor area and a sourced applicable benchmark. Report every component and round only the final score.")
paragraph("<b>Retrofits and carbon:</b> Check eligibility for loft insulation, heat pumps, solar, double glazing and smart controls. Apply envelope improvements sequentially to thermal demand; model heating with boiler efficiency or heat-pump SCOP while preserving other loads. Bound solar self-consumption by generation and demand. For five options, enumerate feasible subsets within the budget and rank by a documented objective. Use versioned, fuel-specific official emissions factors with explicit accounting boundaries.")
paragraph("<b>Valuation and provenance:</b> Compare Ridge with histogram gradient boosting using property/customer-separated splits. Fit preprocessing on training data only, select on validation data, and calibrate uncertainty using separate held-out residuals. Use observed sales and EPC information known at sale when obtainable. Synthetic properties/readings support development and demonstration; synthetic prices are never presented as market evidence. Hold unrelated characteristics fixed for a scenario, and return unavailable if credible energy-efficiency evidence is absent. Associations are not causal premiums.")
paragraph("5. Planned testing methodology", "h")
paragraph("<b>Data and scoring:</b> Validate schemas, ranges, duplicates, property/month links and per-fuel coverage. Test missing versus known-zero consumption, all seven weights, subscore bounds, monotonic mappings, benchmark applicability, final rounding and reproducibility.")
paragraph("<b>Simulation and integration:</b> Test each measure and interacting packages; include infeasible/conditional eligibility, duplicate installations, budget limits, zero/missing baselines, solar bounds and heat pumps increasing electricity use. Verify fuel arithmetic, carbon calculations and updated property state. Compare against independently prepared reference cases where available; label simulator self-agreement as implementation verification. Exercise the real API flow, startup, error responses and latency.")
paragraph("<b>ML and advisor:</b> Report held-out MAE, RMSE, R-squared, baseline comparison, interval coverage/width, sample counts and leakage checks; add temporal/subgroup evaluation where data supports it. Run 25 advisor questions covering explanations, what-if requests, unavailable inputs and infeasible measures. Check tool invocation, numerical grounding, negation, malformed JSON and model outages. Human-review factual accuracy and completeness; evaluate the challenge targets without claiming success before measurement.")
paragraph("6. Potential future features (outside the initial MVP)", "h")
paragraph("<b>Live-data connections:</b> EPC and consent-based meter ingestion, provenance-aware refreshes and weather-normalized demand. <b>Personalized planning:</b> saved budgets/preferences, staged renovation plans and sensitivity analysis for tariffs, costs and heat-pump performance. <b>Portfolio support:</b> prioritize homes by modeled improvement potential and provide informational green-finance readiness views using verified criteria. <b>Stronger evidence:</b> geographically richer valuation data, better-calibrated intervals, and measured before/after monitoring to validate savings and investigate causal effects.")
paragraph("These are proposed extensions, not claims of completed implementation, financial eligibility or validated real-world performance.", "small")


def decorate(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.HexColor("#173D34"))
    canvas.drawString(50, height - 32, "TEAM NUMBER: 254")
    canvas.setStrokeColor(colors.HexColor("#CCDCD4"))
    canvas.line(50, height - 40, width - 50, height - 40)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#59655E"))
    canvas.drawString(50, 27, "M1 | Proposed approach | Megathon X: Singularity")
    canvas.drawRightString(width - 50, 27, f"{doc.page} / 2")
    canvas.restoreState()


SimpleDocTemplate(str(ROOT / "M1.pdf"), pagesize=A4, rightMargin=50, leftMargin=50,
                  topMargin=58, bottomMargin=45, title="Team 254 - M1 Approach",
                  author="", subject="Proposed approach, testing methodology and future features").build(
                      story, onFirstPage=decorate, onLaterPages=decorate)
