"""Classify a company into a reputation/size tier.

Real headcounts aren't available without a paid data source, so this uses a
curated list of well-known large employers (typically 1,000+ staff) and reputed
mid-size firms (~500+). Everything else falls to "Other". Edit the sets below
to taste — matching is by whole-word so "amazon" hits "Amazon Business".

Tiers:  Premium (large, blue-chip) > Established (reputed mid-size) > Other
"""
from __future__ import annotations

import re

# Large, blue-chip employers (1,000+). Indian conglomerates/IT/BFSI/FMCG,
# global MNCs, consulting, and well-funded unicorns.
_PREMIUM = {
    "tata", "tcs", "infosys", "wipro", "hcl", "tech mahindra", "mahindra",
    "reliance", "jio", "aditya birla", "hindustan unilever", "hul", "unilever",
    "itc", "nestle", "procter", "p&g", "pepsico", "coca-cola", "britannia",
    "dabur", "marico", "godrej", "asian paints", "l&t", "larsen", "bajaj",
    "titan", "hero", "tvs", "maruti", "adani", "vedanta", "jsw", "havells",
    "carrier", "siemens", "bosch", "schneider", "honeywell", "abb",
    "hdfc", "icici", "axis bank", "kotak", "state bank", "sbi", "yes bank",
    "idfc", "citi", "jpmorgan", "goldman", "morgan stanley", "barclays",
    "hsbc", "standard chartered", "american express", "amex", "mastercard",
    "visa", "deloitte", "pwc", "kpmg", "ernst", "ey", "mckinsey", "bcg",
    "bain", "accenture", "capgemini", "cognizant", "genpact", "wns",
    "ibm", "microsoft", "google", "amazon", "flipkart", "myntra", "meta",
    "adobe", "oracle", "sap", "salesforce", "dell", "intel", "qualcomm",
    "nvidia", "samsung", "sony", "walmart", "netflix", "uber", "swiggy",
    "zomato", "paytm", "phonepe", "ola", "oyo", "byju", "unacademy", "nykaa",
    "meesho", "cred", "razorpay", "dream11", "urban company", "great learning",
    "upgrad", "airtel", "vodafone", "star", "disney", "zepto", "zomato",
    "aditya birla", "vedantu", "policybazaar", "groww", "zerodha",
}

# Reputed mid-size / growth firms (~500+). Add names you rate here.
_ESTABLISHED = {
    "postman", "browserstack", "chargebee", "freshworks", "zoho", "innovaccer",
    "gupshup", "aisensy", "clevertap", "moengage", "whatfix", "mindtickle",
    "darwinbox", "razorpay", "leadsquared", "yellow.ai", "haptik", "masai",
    "scaler", "newton", "physicswallah", "pw", "cuemath", "leadschool",
    "acko", "digit", "khatabook", "bharatpe", "slice", "jupiter", "fi money",
}


_SUFFIX_RE = re.compile(
    r"\b(pvt|private|ltd|limited|inc|llp|india|technologies|technology|solutions|services|group|labs|corp|co)\b")
# Compile one alternation regex per tier ONCE (fast over thousands of rows).
_PREMIUM_RE = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in sorted(_PREMIUM, key=len, reverse=True)) + r")\b")
_ESTAB_RE = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in sorted(_ESTABLISHED, key=len, reverse=True)) + r")\b")


def _norm(name: str) -> str:
    n = _SUFFIX_RE.sub(" ", (name or "").lower())
    return re.sub(r"\s+", " ", n).strip()


def company_tier(name: str) -> str:
    n = _norm(name)
    if _PREMIUM_RE.search(n):
        return "Premium"
    if _ESTAB_RE.search(n):
        return "Established"
    return "Other"
