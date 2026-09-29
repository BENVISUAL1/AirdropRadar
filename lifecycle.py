from datetime import datetime, timezone
import re


# -----------------------------------------
# LIFECYCLE CONSTANTS
# -----------------------------------------

LIFECYCLE_UNKNOWN = "unknown"
LIFECYCLE_UPCOMING = "upcoming"
LIFECYCLE_ACTIVE = "active"
LIFECYCLE_ENDING_SOON = "ending_soon"
LIFECYCLE_ENDED = "ended"

ENDING_SOON_DAYS = 3


# -----------------------------------------
# DATE PATTERNS
# -----------------------------------------

DATE_PATTERNS = [

    # 2026-09-30
    re.compile(
        r"\b("
        r"20\d{2}-\d{1,2}-\d{1,2}"
        r")\b"
    ),

    # September 30, 2026
    re.compile(
        r"\b("
        r"(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+\d{1,2}(?:st|nd|rd|th)?"
        r",?\s+20\d{2}"
        r")\b",
        re.IGNORECASE,
    ),

    # 30 September 2026
    re.compile(
        r"\b("
        r"\d{1,2}(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+20\d{2}"
        r")\b",
        re.IGNORECASE,
    ),

    # 09/30/2026 or 09-30-2026
    re.compile(
        r"\b("
        r"\d{1,2}[/-]\d{1,2}[/-]20\d{2}"
        r")\b"
    ),
]


# -----------------------------------------
# DATE NORMALIZATION
# -----------------------------------------

def normalize_date(value):
    """
    Convert a supported date string into
    YYYY-MM-DD.

    Returns None when the date cannot be
    safely interpreted.
    """

    if not value:
        return None

    value = str(value).strip()

    value = re.sub(
        r"(\d{1,2})(st|nd|rd|th)\b",
        r"\1",
        value,
        flags=re.IGNORECASE,
    )

    formats = [
        "%Y-%m-%d",
        "%B %d, %Y",
        "%B %d %Y",
        "%d %B %Y",
        "%m/%d/%Y",
        "%m-%d-%Y",
    ]

    for date_format in formats:
        try:
            parsed = datetime.strptime(
                value,
                date_format,
            )

            return parsed.strftime("%Y-%m-%d")

        except ValueError:
            continue

    return None


# -----------------------------------------
# DATE EXTRACTION
# -----------------------------------------

def extract_dates(text):
    """
    Extract reliable explicit calendar dates
    from text.

    Returns unique dates in YYYY-MM-DD format.
    """

    if not text:
        return []

    text = str(text)

    found = []

    for pattern in DATE_PATTERNS:

        for match in pattern.findall(text):

            normalized = normalize_date(
                match
            )

            if normalized and normalized not in found:
                found.append(normalized)

    return sorted(found)


# -----------------------------------------
# DATE CONTEXT
# -----------------------------------------

def find_end_date(text):
    """
    Find a date associated with an ending,
    deadline, expiration, closing, or claim
    deadline.

    Returns YYYY-MM-DD or None.
    """

    if not text:
        return None

    text = str(text)

    end_keywords = (
        r"(?:"
        r"ends?|"
        r"ending|"
        r"deadline|"
        r"expires?|"
        r"expiration|"
        r"closes?|"
        r"closing|"
        r"last\s+day|"
        r"until|"
        r"through"
        r")"
    )

    pattern = re.compile(
        end_keywords
        + r".{0,80}?"
        + r"("
        r"20\d{2}-\d{1,2}-\d{1,2}|"
        r"\d{1,2}[/-]\d{1,2}[/-]20\d{2}|"
        r"(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+\d{1,2}(?:st|nd|rd|th)?"
        r",?\s+20\d{2}|"
        r"\d{1,2}(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+20\d{2}"
        r")",
        re.IGNORECASE,
    )

    match = pattern.search(text)

    if not match:
        return None

    return normalize_date(
        match.group(1)
    )


def find_start_date(text):
    """
    Find a date associated with a start,
    launch, opening, beginning, or activation.

    Returns YYYY-MM-DD or None.
    """

    if not text:
        return None

    text = str(text)

    start_keywords = (
        r"(?:"
        r"starts?|"
        r"starting|"
        r"begins?|"
        r"beginning|"
        r"launches?|"
        r"launch|"
        r"opens?|"
        r"opening|"
        r"active\s+from"
        r")"
    )

    pattern = re.compile(
        start_keywords
        + r".{0,80}?"
        + r"("
        r"20\d{2}-\d{1,2}-\d{1,2}|"
        r"\d{1,2}[/-]\d{1,2}[/-]20\d{2}|"
        r"(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+\d{1,2}(?:st|nd|rd|th)?"
        r",?\s+20\d{2}|"
        r"\d{1,2}(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|July|"
        r"August|September|October|November|December)"
        r"\s+20\d{2}"
        r")",
        re.IGNORECASE,
    )

    match = pattern.search(text)

    if not match:
        return None

    return normalize_date(
        match.group(1)
    )


# -----------------------------------------
# LIFECYCLE STATUS
# -----------------------------------------

def calculate_lifecycle_status(
    end_date,
    now=None,
    start_date=None,
):
    """
    Determine lifecycle status from explicit
    start/end dates.

    Conservative:
    missing dates produce unknown.
    """

    if now is None:
        now = datetime.now(timezone.utc)

    if start_date:
        try:
            start = datetime.strptime(
                start_date,
                "%Y-%m-%d",
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            start = None
    else:
        start = None

    if end_date:
        try:
            end = datetime.strptime(
                end_date,
                "%Y-%m-%d",
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            end = None
    else:
        end = None

    if end is None:
        if start and now < start:
            return LIFECYCLE_UPCOMING

        return LIFECYCLE_UNKNOWN

    if start and now < start:
        return LIFECYCLE_UPCOMING

    if now.date() > end.date():
        return LIFECYCLE_ENDED

    days_remaining = (
        end.date() - now.date()
    ).days

    if days_remaining <= ENDING_SOON_DAYS:
        return LIFECYCLE_ENDING_SOON

    return LIFECYCLE_ACTIVE


# -----------------------------------------
# MAIN LIFECYCLE ANALYSIS
# -----------------------------------------

def analyze_lifecycle(
    candidate,
    now=None,
):
    """
    Analyze one AirdropRadar candidate.

    Returns structured lifecycle intelligence.
    """

    if not isinstance(candidate, dict):
        candidate = {}

    name = str(
        candidate.get("name") or ""
    )

    description = str(
        candidate.get("description") or ""
    )

    text = (
        f"{name} "
        f"{description}"
    ).strip()

    dates = extract_dates(text)

    start_date = find_start_date(text)

    end_date = find_end_date(text)

    status = calculate_lifecycle_status(
        end_date=end_date,
        start_date=start_date,
        now=now,
    )

    evidence = []

    if start_date:
        evidence.append(
            f"Start date detected: {start_date}"
        )

    if end_date:
        evidence.append(
            f"End date detected: {end_date}"
        )

    if not start_date and not end_date and dates:
        evidence.append(
            "Calendar date detected, but no "
            "reliable lifecycle context was found."
        )

    if not dates:
        evidence.append(
            "No explicit calendar date detected."
        )

    return {
        "status": status,
        "start_date": start_date,
        "end_date": end_date,
        "dates_detected": dates,
        "evidence": evidence,
    }


# -----------------------------------------
# TEST
# -----------------------------------------

if __name__ == "__main__":

    now = datetime(
        2026,
        9,
        18,
        tzinfo=timezone.utc,
    )

    tests = [

        {
            "name": "Upcoming Airdrop",
            "description": (
                "Campaign starts October 1, 2026 "
                "and ends October 15, 2026."
            ),
        },

        {
            "name": "Ending Soon Airdrop",
            "description": (
                "Campaign ends September 20, 2026."
            ),
        },

        {
            "name": "Active Airdrop",
            "description": (
                "Campaign ends September 30, 2026."
            ),
        },

        {
            "name": "Expired Airdrop",
            "description": (
                "Campaign ended September 10, 2026."
            ),
        },

        {
            "name": "Date Without Context",
            "description": (
                "Snapshot happened September 20, 2026."
            ),
        },

        {
            "name": "No Date",
            "description": (
                "Complete quests and earn points."
            ),
        },
    ]

    print(
        "\n🕐 AirdropRadar Lifecycle Intelligence"
    )

    print("=" * 55)

    for candidate in tests:

        result = analyze_lifecycle(
            candidate,
            now=now,
        )

        print(
            f"\n{candidate['name']}"
        )

        print(
            f"Status: {result['status']}"
        )

        print(
            f"Start date: {result['start_date']}"
        )

        print(
            f"End date: {result['end_date']}"
        )

        print(
            f"Dates: {result['dates_detected']}"
        )

        print(
            f"Evidence: {result['evidence']}"
        )