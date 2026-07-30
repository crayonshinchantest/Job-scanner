"""Job sources. Each exposes fetch(keyword, location, max_age_hours) -> list[Job]."""
from dataclasses import dataclass, field


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    posted: str = ""          # human-readable "posted" label from the site
    description: str = ""
    score: int = 0
    matched: list = field(default_factory=list)
    experience_req: str = ""  # e.g. "0-2 yrs" or "not stated"
    exp_years: object = None  # parsed minimum years required (int) or None
    tier: str = "Other"       # company tier: Premium | Established | Other
    resume: str = ""          # recommended resume label
    resume_path: str = ""     # path within "Resumes all/" to that resume
