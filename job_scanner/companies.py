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


def _norm(name: str) -> str:
    n = (name or "").lower()
    n = re.sub(r"\b(pvt|private|ltd|limited|inc|llp|india|technologies|technology|solutions|services|group|labs|corp|co)\b", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def _hit(name: str, tokens: set) -> bool:
    n = _norm(name)
    for t in tokens:
        if re.search(r"\b" + re.escape(t) + r"\b", n):
            return True
    return False


def company_tier(name: str) -> str:
    if _hit(name, _PREMIUM):
        return "Premium"
    if _hit(name, _ESTABLISHED):
        return "Established"
    return "Other"
