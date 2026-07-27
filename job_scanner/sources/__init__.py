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
