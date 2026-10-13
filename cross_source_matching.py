import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

from verifier import normalize_domain


# ============================================================
# CROSS-SOURCE MATCHING
# ============================================================

MATCH_NO_MATCH = "no_match"
MATCH_POSSIBLE = "possible_match"
MATCH_STRONG = "strong_match"

STRONG_MATCH_THRESHOLD = 85
POSSIBLE_MATCH_THRESHOLD = 65


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(value):
    """
    Normalize text for reliable comparison.
    """

    if not value:
        return ""

    text = str(value).lower()

    text = re.sub(
        r"https?://\S+",
        " ",
        text,
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def normalize_project_name(value):
    """
    Normalize a project/airdrop title by removing
    generic opportunity-related words.
    """

    text = normalize_text(value)

    removable_words = {
        "airdrop",
        "token",
        "campaign",
        "rewards",
        "reward",
        "giveaway",
        "claim",
        "launch",
        "crypto",
        "blockchain",
        "official",
        "announcement",
    }

    words = [
        word
        for word in text.split()
        if word not in removable_words
    ]

    return " ".join(words)


# ============================================================
# URL / DOMAIN HELPERS
# ============================================================

def normalize_url(url):
    """
    Normalize a URL for exact URL comparison.
    """

    if not url:
        return ""

    try:
        parsed = urlparse(
            str(url).strip()
        )

        scheme = (
            parsed.scheme.lower()
            if parsed.scheme
            else "https"
        )

        domain = normalize_domain(url)

        path = parsed.path.rstrip("/").lower()

        if not domain:
            return ""

        return f"{scheme}://{domain}{path}"

    except Exception:
        return ""


# ============================================================
# SIMILARITY
# ============================================================

def similarity_score(first, second):
    """
    Return text similarity from 0 to 100.
    """

    first = normalize_text(first)
    second = normalize_text(second)

    if not first or not second:
        return 0

    if first == second:
        return 100

    return round(
        SequenceMatcher(
            None,
            first,
            second,
        ).ratio() * 100
    )


# ============================================================
# DOMAIN COMPARISON
# ============================================================

def domain_match(first_url, second_url):
    """
    Determine whether two URLs share the same domain.

    Note:
    This is supporting evidence only.
    A shared publisher domain must not by itself
    identify two opportunities as the same project.
    """

    first_domain = normalize_domain(
        first_url
    )

    second_domain = normalize_domain(
        second_url
    )

    if not first_domain or not second_domain:
        return False

    return first_domain == second_domain


# ============================================================
# MATCH TWO OPPORTUNITIES
# ============================================================

def compare_opportunities(first, second):
    """
    Compare two discovered opportunities.

    Matching is based primarily on:
    - project name similarity
    - description similarity
    - exact normalized URL

    Publisher domain similarity is recorded as evidence
    but does not determine the project match by itself.
    """

    if not isinstance(first, dict):
        raise TypeError(
            "first must be a dictionary"
        )

    if not isinstance(second, dict):
        raise TypeError(
            "second must be a dictionary"
        )

    first_name = first.get(
        "name",
        "",
    )

    second_name = second.get(
        "name",
        "",
    )

    first_description = first.get(
        "description",
        "",
    )

    second_description = second.get(
        "description",
        "",
    )

    first_url = first.get(
        "url",
        "",
    )

    second_url = second.get(
        "url",
        "",
    )

    evidence = []
    score_components = []

    # --------------------------------------------------------
    # URL NORMALIZATION
    # --------------------------------------------------------

    first_normalized_url = normalize_url(
        first_url
    )

    second_normalized_url = normalize_url(
        second_url
    )

    # --------------------------------------------------------
    # SAME NORMALIZED DOMAIN
    # --------------------------------------------------------
    #
    # Important:
    # Same publisher domain is NOT strong project evidence.
    # It is recorded only as supporting information.
    #

    same_domain = domain_match(
        first_url,
        second_url,
    )

    if same_domain:
        evidence.append(
            "Same normalized publisher domain"
        )

        # --------------------------------------------------------
    # PROJECT NAME SIMILARITY
    # --------------------------------------------------------

    first_project = normalize_project_name(
        first_name
    )

    second_project = normalize_project_name(
        second_name
    )

    name_score = similarity_score(
        first_project,
        second_project,
    )

    # --------------------------------------------------------
    # PROJECT NAME CONTAINMENT
    # --------------------------------------------------------

    project_name_match = False

    if first_project and second_project:
        first_words = set(first_project.split())
        second_words = set(second_project.split())

        if (
            first_words.issubset(second_words)
            or second_words.issubset(first_words)
        ):
            project_name_match = True

        elif (
            len(first_words) == 1
            and first_words.issubset(second_words)
        ):
            project_name_match = True

        elif (
            len(second_words) == 1
            and second_words.issubset(first_words)
        ):
            project_name_match = True

    if project_name_match:
        evidence.append(
            "Project name appears within the other title"
        )

        score_components.append(70)

    if name_score >= 90:
        evidence.append(
            "Very strong project name similarity"
        )

        score_components.append(60)

    elif name_score >= 75:
        evidence.append(
            "Strong project name similarity"
        )

        score_components.append(55)

    elif name_score >= 60:
        evidence.append(
            "Moderate project name similarity"
        )

        score_components.append(25)

    # --------------------------------------------------------
    # DESCRIPTION SIMILARITY
    # --------------------------------------------------------

    description_score = similarity_score(
        first_description,
        second_description,
    )

    if description_score >= 85:
        evidence.append(
            "Very strong description similarity"
        )

        score_components.append(25)

    elif description_score >= 70:
        evidence.append(
            "Strong description similarity"
        )

        score_components.append(20)

    elif description_score >= 55:
        evidence.append(
            "Moderate description similarity"
        )

        score_components.append(8)

    # --------------------------------------------------------
    # EXACT NORMALIZED URL
    # --------------------------------------------------------

    exact_url_match = (
        bool(first_normalized_url)
        and bool(second_normalized_url)
        and first_normalized_url
        == second_normalized_url
    )

    if exact_url_match:
        evidence.append(
            "Same normalized URL"
        )

        score_components.append(100)

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    match_score = min(
        sum(score_components),
        100,
    )

    # --------------------------------------------------------
    # MATCH STATUS
    # --------------------------------------------------------

    if exact_url_match:
        status = MATCH_STRONG

    elif match_score >= STRONG_MATCH_THRESHOLD:
        status = MATCH_STRONG

    elif match_score >= POSSIBLE_MATCH_THRESHOLD:
        status = MATCH_POSSIBLE

    else:
        status = MATCH_NO_MATCH

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    if status == MATCH_STRONG:
        confidence = "high"

    elif status == MATCH_POSSIBLE:
        confidence = "medium"

    else:
        confidence = "low"

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "match_status": status,
        "match_score": match_score,
        "confidence": confidence,
        "evidence": evidence,
        "same_domain": same_domain,
        "name_score": name_score,
        "description_score": description_score,
    }


# ============================================================
# CROSS-SOURCE ANALYSIS
# ============================================================

def analyze_cross_source_match(
    first,
    second,
):
    """
    Public wrapper for comparing two discoveries.
    """

    result = compare_opportunities(
        first,
        second,
    )

    result["sources"] = [
        first.get(
            "source",
            "",
        ),
        second.get(
            "source",
            "",
        ),
    ]

    return result