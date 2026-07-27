"""Resume-derived profile used to score how well a job matches you.

These keywords were extracted from Ajinkya Kolhe's resumes (Strategy +
Marketing/Branding). Add or remove terms here to tune matching — the more a
job description overlaps with these, the higher it scores.
"""

# Strong signals — weighted heavily when they appear in a job.
CORE_SKILLS = [
    "strategy", "strategic planning", "market research", "competitor benchmarking",
    "annual operating plan", "aop", "budgeting", "forecasting", "fp&a", "mis",
    "kpi", "dashboard", "growth", "cost optimization", "unit economics",
    "financial analysis", "financial modeling", "gtm", "go-to-market",
    "marketing", "brand", "branding", "product marketing", "category",
    "business analyst", "consulting", "planning", "analytics",
    "power bi", "excel", "sql", "python", "positioning", "market sizing",
]

# Softer signals — nice to have, lightly weighted.
SUPPORTING = [
    "mba", "iim", "management", "b2b", "b2c", "fmcg", "retail", "d2c",
    "campaign", "insights", "revenue", "p&l", "stakeholder", "roadmap",
    "cross-functional", "leadership", "presentation", "sales",
]

# If a job title contains any of these, it's clearly in your lane.
TITLE_BOOST = [
    "strategy", "marketing", "brand", "growth", "planning", "category",
    "product marketing", "business analyst", "consultant", "fp&a", "insights",
]

# Jobs with these in the title are almost never a fit — filter them out.
NEGATIVE_TITLE = [
    "sales executive", "telecaller", "telesales", "field sales", "delivery",
    "driver", "nurse", "security guard", "electrician", "plumber",
    "software engineer", "developer", "devops", "qa engineer", "sdet",
    "civil engineer", "mechanical engineer", "data entry", "bpo", "customer support",
]

# Seniority you're targeting (fresher MBA 2026 / early career).
PREFERRED_SENIORITY = ["associate", "analyst", "manager", "specialist", "lead",
                       "executive", "senior", "consultant", "trainee", "graduate"]
