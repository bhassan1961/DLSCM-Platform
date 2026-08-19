import re

DISASTER_KEYWORDS = {
    "earthquake": [
        "earthquake",
        "seismic",
        "tremor",
        "aftershock",
        "magnitude",
        "richter",
    ],
    "flood": [
        "flood",
        "flooding",
        "inundation",
        "deluge",
        "monsoon",
        "flash flood",
        "water level",
    ],
    "cyclone": [
        "cyclone",
        "hurricane",
        "typhoon",
        "tropical storm",
        "storm surge",
        "wind speed",
    ],
    "drought": [
        "drought",
        "dry spell",
        "water scarcity",
        "failed rains",
        "famine",
        "food insecurity",
    ],
    "conflict": [
        "conflict",
        "armed",
        "displacement",
        "IDP",
        "refugees",
        "fighting",
        "violence",
    ],
    "epidemic": [
        "cholera",
        "outbreak",
        "epidemic",
        "pandemic",
        "disease",
        "infection",
        "cases reported",
    ],
}

NEED_KEYWORDS = {
    "food": [
        "food",
        "nutrition",
        "rations",
        "feeding",
        "malnutrition",
        "hunger",
        "RUTF",
    ],
    "water": ["water", "WASH", "sanitation", "hygiene", "purification", "latrine"],
    "medical": [
        "medical",
        "health",
        "hospital",
        "clinic",
        "doctor",
        "nurse",
        "medicine",
        "surgical",
    ],
    "shelter": [
        "shelter",
        "tent",
        "tarpaulin",
        "housing",
        "displaced",
        "homeless",
        "camp",
    ],
    "protection": ["protection", "GBV", "child protection", "safety", "security"],
    "logistics": [
        "logistics",
        "transport",
        "road",
        "access",
        "supply chain",
        "warehouse",
    ],
}

URGENCY_INDICATORS = {
    "critical": [
        "immediate",
        "urgent",
        "critical",
        "emergency",
        "life-threatening",
        "dire",
        "desperate",
    ],
    "high": [
        "high priority",
        "rapidly",
        "deteriorating",
        "significant",
        "severe",
        "escalating",
    ],
    "medium": ["moderate", "ongoing", "continued", "sustained"],
    "low": ["stable", "improving", "minor", "limited"],
}


def parse_sitrep(text: str) -> dict:
    """
    Parse a situation report text and extract structured information.

    Returns:
        dict with disaster_type, identified_needs, affected_population, urgency, summary
    """
    text_lower = text.lower()

    # Identify disaster type
    disaster_type = "unknown"
    max_score = 0
    for dtype, keywords in DISASTER_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > max_score:
            max_score = score
            disaster_type = dtype

    # Identify needs
    identified_needs = []
    for need, keywords in NEED_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            identified_needs.append(need)

    # Extract affected population (look for numbers near population keywords)
    affected_population = None
    pop_patterns = [
        r"(\d[\d,]*)\s*(?:people|persons|individuals|affected|displaced|refugees|IDPs|beneficiaries|population)",
        r"(?:affected|displaced|impacting|reaching)\s*(?:approximately|about|nearly|over|more than)?\s*(\d[\d,]*)",
        r"(\d[\d,]*)\s*(?:families|households)",
    ]
    for pattern in pop_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace(",", "")
            affected_population = int(num_str)
            # If families/households, multiply by 5
            if (
                "famil" in match.group(0).lower()
                or "household" in match.group(0).lower()
            ):
                affected_population *= 5
            break

    # Determine urgency
    urgency = "medium"
    for level in ["critical", "high", "medium", "low"]:
        if any(indicator in text_lower for indicator in URGENCY_INDICATORS[level]):
            urgency = level
            break

    # Generate summary (first two sentences or first 200 chars)
    sentences = re.split(r"[.!?]+", text.strip())
    summary_parts = [s.strip() for s in sentences[:2] if s.strip()]
    summary = ". ".join(summary_parts)
    if summary and not summary.endswith("."):
        summary += "."
    if len(summary) > 300:
        summary = summary[:297] + "..."

    return {
        "disaster_type": disaster_type,
        "identified_needs": identified_needs,
        "affected_population": affected_population,
        "urgency": urgency,
        "summary": summary,
    }
