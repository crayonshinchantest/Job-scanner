"""Pick which of Ajinkya's tailored resumes best fits a given job.

Each entry maps a resume file (inside your "Resumes all" folder) to the kind of
role it was tailored for. For every job we score all resumes by how well the
job's title/description/company matches their keywords, and recommend the best.
General resumes win when no specialist resume clearly fits.

Paths are relative to your local "Resumes all/" folder — the resumes stay on
your machine; this just tells you which one to attach.
"""
from __future__ import annotations

# weight 1 = broad/general resume, weight 2 = specialist (wins when relevant)
CATALOG = [
    # ── Strategy family ────────────────────────────────────────────────
    {"label": "Strategy (general)", "weight": 1,
     "path": "Strategy/Ajinkya_Kolhe_Resume.pdf",
     "kw": ["strategy", "strategic", "planning", "corporate strategy",
            "business analyst", "chief of staff", "business strategy"]},
    {"label": "Strategy — Aditya Birla (corporate/group strategy)", "weight": 2,
     "path": "Strategy/Ajinkya_Kolhe_Resume_Strategy_Planning_AdityaBirla.pdf",
     "kw": ["corporate strategy", "group strategy", "conglomerate", "m&a",
            "chairman", "business head", "diversified", "strategic planning"]},
    {"label": "Strategy — Consulting (Accenture)", "weight": 2,
     "path": "Strategy/OLX/Ajinkya Kolhe IIM Visakhapatnam_Accenture .pdf",
     "kw": ["consulting", "consultant", "advisory", "management consulting",
            "transformation", "strategy&", "associate consultant"]},
    {"label": "Strategy — Banking/BFSI (Kotak)", "weight": 2,
     "path": "Strategy/KOTAK/Ajinkya_Kolhe_Kotak_GTS_APM.pdf",
     "kw": ["bank", "banking", "bfsi", "financial services", "transaction banking",
            "treasury", "wealth", "cash management", "credit", "nbfc", "fintech bank"]},
    {"label": "Strategy — Internet/Marketplace (OLX)", "weight": 2,
     "path": "Strategy/OLX/Ajinkya Kolhe IIM Visakhapatnam_OLX.docx",
     "kw": ["marketplace", "classifieds", "consumer internet", "tech platform",
            "internet", "aggregator", "platform strategy"]},
    {"label": "Strategy — Consumer services (Tumbledry)", "weight": 2,
     "path": "Strategy/Ajinkya_Kolhe_Tumbledry_ACM.pdf",
     "kw": ["franchise", "consumer services", "expansion", "unit economics",
            "retail operations", "store", "outlet", "network expansion"]},

    # ── Marketing & branding family ────────────────────────────────────
    {"label": "Marketing (general)", "weight": 1,
     "path": "Marketing and branding/Ajinkya Kolhe IIM Visakhapatnam.pdf",
     "kw": ["marketing", "brand", "branding", "digital marketing", "campaign",
            "communications", "advertising", "media"]},
    {"label": "Marketing — FMCG/CPG (P&G)", "weight": 2,
     "path": "Marketing and branding/P&G/Ajinkya Kolhe IIM Visakhapatnam.pdf",
     "kw": ["fmcg", "cpg", "consumer goods", "personal care", "home care",
            "foods", "beverages", "nielsen", "brand manager", "abm", "assistant brand"]},
    {"label": "Marketing — E-commerce category (Myntra)", "weight": 2,
     "path": "Marketing and branding/Myntra category/Ajinkya Kolhe IIM Visakhapatnam.pdf",
     "kw": ["category", "category manager", "e-commerce", "ecommerce", "merchandising",
            "buying", "private label", "fashion", "catalogue", "marketplace seller"]},
    {"label": "Marketing — Growth/Fintech (Upstox)", "weight": 2,
     "path": "Marketing and branding/Growth Marketing at Upstox/Ajinkya_Kolhe_Resume.pdf",
     "kw": ["growth", "performance marketing", "user acquisition", "fintech",
            "funnel", "retention", "cac", "ltv", "d2c", "app marketing", "seo", "sem"]},
    {"label": "Marketing — Business development (Walmart)", "weight": 2,
     "path": "Marketing and branding/Walmart business development/Ajinkya_Kolhe_IIM_Visakhapatnam.pdf",
     "kw": ["business development", "sourcing", "supplier", "procurement",
            "wholesale", "partnerships", "vendor", "retail buying", "b2b sales"]},

    # ── Other specialist tracks ────────────────────────────────────────
    {"label": "Finance / FP&A", "weight": 1,
     "path": "Finance/Ajinkya Kolhe Resume.pdf",
     "kw": ["finance", "fp&a", "financial analyst", "investment", "equity research",
            "valuation", "budgeting", "controller", "accounting", "financial modeling"]},
    {"label": "Consumer Insights / Research", "weight": 2,
     "path": "Consumer Insights/Ajinkya_Kolhe_IIM Visakhapatnam.pdf",
     "kw": ["consumer insights", "market research", "insights", "research executive",
            "survey", "brand health", "consumer research", "mrx"]},
    {"label": "Product Management", "weight": 2,
     "path": "Prodman/Ajinkya Kolhe IIM Visakhapatnam.docx",
     "kw": ["product manager", "product management", "product owner", "roadmap",
            "user stories", "associate product", "apm", "product analyst"]},
    {"label": "Data / Analytics", "weight": 2,
     "path": "It and analytics /Ajinkya Kolhe IIM Visakhapatnam.docx",
     "kw": ["data analyst", "analytics", "business intelligence", "tableau",
            "power bi", "sql", "reporting analyst", "data analytics"]},
]

_FALLBACK = CATALOG[0]  # Strategy (general)


def recommend(title: str, description: str, company: str = "") -> tuple[str, str]:
    """Return (resume_label, resume_path) best suited to this job."""
    text = f"{title} {description} {company}".lower()
    best = _FALLBACK
    best_score = 0
    for entry in CATALOG:
        score = sum(entry["weight"] for kw in entry["kw"] if kw in text)
        if score > best_score:
            best_score, best = score, entry
    return best["label"], best["path"]
