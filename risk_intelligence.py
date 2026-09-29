# ============================================================
# AIRDROP RADAR — RISK INTELLIGENCE
# ============================================================

"""
Risk Intelligence for AirdropRadar V1.1.

Purpose:
    Convert verifier and stored intelligence signals into
    structured risk intelligence.

Important:
    A detected risk signal does NOT automatically mean an
    opportunity is a scam.

Evidence states:
    supported = directly detected from available evidence
    inferred  = derived from multiple available signals
    unknown   = insufficient evidence

Important design rule:
    Missing data is NOT the same as negative evidence.

    Example:
        project_domains missing
            !=
        project_domains explicitly checked and empty
"""


# ============================================================
# RISK SEVERITY
# ============================================================

SEVERITY_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3,
}


# ============================================================
# RISK SIGNAL BUILDER
# ============================================================

def build_risk_item(
    category,
    value,
    evidence,
    severity="medium",
    status="supported",
):
    """
    Build one structured risk signal.
    """

    return {
        "category": category,
        "value": value,
        "evidence": evidence,
        "severity": severity,
        "status": status,
    }


# ============================================================
# UTILITY
# ============================================================

def unique_risk_items(items):
    """
    Remove duplicate risk items while preserving order.
    """

    unique = []
    seen = set()

    for item in items:

        if not isinstance(item, dict):
            continue

        key = (
            item.get("category"),
            item.get("value"),
            item.get("evidence"),
            item.get("severity"),
            item.get("status"),
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(item)

    return unique


def normalize_list(value):
    """
    Safely normalize a value into a list.

    Missing/invalid values become an empty list.
    """

    if isinstance(value, list):
        return value

    return []


def normalize_dict(value):
    """
    Safely normalize a value into a dictionary.

    Missing/invalid values become an empty dictionary.
    """

    if isinstance(value, dict):
        return value

    return {}


# ============================================================
# SUSPICIOUS CONTENT RISK
# ============================================================

HIGH_RISK_WARNINGS = {
    "private key",
    "seed phrase",
    "recovery phrase",
    "send crypto",
    "send us crypto",
    "double your crypto",
    "double your bitcoin",
}


MEDIUM_RISK_WARNINGS = {
    "guaranteed profit",
    "guaranteed return",
    "deposit crypto",
    "pay fee to claim",
    "withdrawal fee",
    "activate your wallet",
}


def analyze_warning_risks(warnings):
    """
    Convert verifier warnings into structured risk signals.

    Warnings are treated as evidence detected by the verifier.

    An unknown warning is still recorded as a medium signal
    because the verifier explicitly detected suspicious content.
    """

    warnings = normalize_list(warnings)

    if not warnings:
        return []

    risks = []

    for warning in warnings:

        normalized = str(
            warning or ""
        ).strip().lower()

        if not normalized:
            continue

        if normalized in HIGH_RISK_WARNINGS:

            severity = "high"

        elif normalized in MEDIUM_RISK_WARNINGS:

            severity = "medium"

        else:

            severity = "medium"

        risks.append(
            build_risk_item(
                category="suspicious_content",
                value=warning,
                evidence=warning,
                severity=severity,
                status="supported",
            )
        )

    return unique_risk_items(risks)


# ============================================================
# VERIFICATION RISK
# ============================================================

def analyze_verification_risks(verification):
    """
    Analyze verification-related signals.

    Missing verification fields are ignored.

    Explicit verifier states such as:
        verification_available=False
        verification_status="unavailable"
        source_access="failed"

    are treated as evidence limitations.

    They are NOT automatic scam classifications.
    """

    if not isinstance(verification, dict):
        return []

    risks = []

    # --------------------------------------------------------
    # FIELD PRESENCE
    # --------------------------------------------------------

    verification_status_present = (
        "verification_status" in verification
    )

    verification_level_present = (
        "verification_level" in verification
    )

    verification_available_present = (
        "verification_available" in verification
    )

    source_access_present = (
        "source_access" in verification
    )

    verified_present = (
        "verified" in verification
    )

    # --------------------------------------------------------
    # VALUES
    # --------------------------------------------------------

    verification_status = str(
        verification.get(
            "verification_status",
            ""
        )
        or ""
    ).lower()

    verification_level = str(
        verification.get(
            "verification_level",
            ""
        )
        or ""
    ).lower()

    verification_available = verification.get(
        "verification_available"
    )

    source_access = str(
        verification.get(
            "source_access",
            ""
        )
        or ""
    ).lower()

    verified = verification.get(
        "verified"
    )

    # --------------------------------------------------------
    # VERIFICATION UNAVAILABLE
    # --------------------------------------------------------

    if (
        (
            verification_available_present
            and verification_available is False
        )
        or
        (
            verification_status_present
            and verification_status == "unavailable"
        )
    ):

        evidence = (
            verification_status
            or "verification_available=False"
        )

        risks.append(
            build_risk_item(
                category="verification",
                value="Verification unavailable",
                evidence=evidence,
                severity="medium",
                status="supported",
            )
        )

    # --------------------------------------------------------
    # SOURCE ACCESS
    # --------------------------------------------------------

    if (
        source_access_present
        and source_access in {
            "unavailable",
            "failed",
            "blocked",
            "error",
        }
    ):

        risks.append(
            build_risk_item(
                category="source_access",
                value="Source could not be reliably accessed",
                evidence=source_access,
                severity="medium",
                status="supported",
            )
        )

    # --------------------------------------------------------
    # UNKNOWN VERIFICATION LEVEL
    # --------------------------------------------------------

    if (
        verification_level_present
        and verification_level in {
            "",
            "unknown",
        }
        and (
            not verified_present
            or verified is not True
        )
    ):

        risks.append(
            build_risk_item(
                category="verification",
                value="Verification level unknown",
                evidence=verification_level or "unknown",
                severity="low",
                status="supported",
            )
        )

    return unique_risk_items(risks)


# ============================================================
# DOMAIN / OFFICIAL-SOURCE RISK
# ============================================================

def analyze_domain_risks(verification):
    """
    Analyze project-domain and official-source evidence.

    Important distinction:

        project_domains missing
            ->
        insufficient data, no risk signal

        project_domains explicitly present as []
            ->
        verifier checked and found no project-owned domain

    The same rule applies to official_links.
    """

    if not isinstance(verification, dict):
        return []

    risks = []

    # --------------------------------------------------------
    # FIELD PRESENCE
    # --------------------------------------------------------

    project_domains_present = (
        "project_domains" in verification
    )

    official_links_present = (
        "official_links" in verification
    )

    project_domains = normalize_list(
        verification.get(
            "project_domains",
            []
        )
    )

    official_links = normalize_list(
        verification.get(
            "official_links",
            []
        )
    )

    # --------------------------------------------------------
    # NO PROJECT-OWNED DOMAIN
    # --------------------------------------------------------

    if (
        project_domains_present
        and not project_domains
    ):

        risks.append(
            build_risk_item(
                category="official_source",
                value="No project-owned domain detected",
                evidence="project_domains=[]",
                severity="medium",
                status="supported",
            )
        )

    # --------------------------------------------------------
    # NO OFFICIAL LINKS
    # --------------------------------------------------------

    if (
        official_links_present
        and project_domains_present
        and not official_links
        and not project_domains
    ):

        risks.append(
            build_risk_item(
                category="official_source",
                value="No official project links detected",
                evidence="official_links=[]",
                severity="medium",
                status="supported",
            )
        )

    return unique_risk_items(risks)


# ============================================================
# MARKET / DEFI INTELLIGENCE RISK
# ============================================================

def analyze_intelligence_risks(verification):
    """
    Analyze market and DeFi intelligence signals.

    Important:

        Missing status
            !=
        unavailable

        signal = "no_match"
            !=
        risk

    Intelligence limitations are recorded only when the
    verifier explicitly reports unavailable/failed/error.
    """

    if not isinstance(verification, dict):
        return []

    risks = []

    # --------------------------------------------------------
    # FIELD PRESENCE
    # --------------------------------------------------------

    market_status_present = (
        "market_status" in verification
    )

    defi_status_present = (
        "defi_status" in verification
    )

    intelligence_status_present = (
        "intelligence_status" in verification
    )

    # --------------------------------------------------------
    # VALUES
    # --------------------------------------------------------

    market_status = str(
        verification.get(
            "market_status",
            ""
        )
        or ""
    ).lower()

    defi_status = str(
        verification.get(
            "defi_status",
            ""
        )
        or ""
    ).lower()

    intelligence_status = str(
        verification.get(
            "intelligence_status",
            ""
        )
        or ""
    ).lower()

    market_signal = normalize_dict(
        verification.get(
            "market_signal",
            {}
        )
    )

    defi_signal = normalize_dict(
        verification.get(
            "defi_signal",
            {}
        )
    )

    # --------------------------------------------------------
    # MARKET INTELLIGENCE UNAVAILABLE
    # --------------------------------------------------------

    if (
        market_status_present
        and market_status in {
            "unavailable",
            "failed",
            "error",
        }
    ):

        risks.append(
            build_risk_item(
                category="market_intelligence",
                value="Market intelligence unavailable",
                evidence=market_status,
                severity="low",
                status="supported",
            )
        )

    # --------------------------------------------------------
    # DEFI INTELLIGENCE UNAVAILABLE
    # --------------------------------------------------------

    if (
        defi_status_present
        and defi_status in {
            "unavailable",
            "failed",
            "error",
        }
    ):

        risks.append(
            build_risk_item(
                category="defi_intelligence",
                value="DeFi intelligence unavailable",
                evidence=defi_status,
                severity="low",
                status="supported",
            )
        )

    # --------------------------------------------------------
    # COMPLETE INTELLIGENCE UNAVAILABLE
    # --------------------------------------------------------

    if (
        intelligence_status_present
        and intelligence_status in {
            "unavailable",
            "failed",
            "error",
        }
    ):

        risks.append(
            build_risk_item(
                category="intelligence",
                value="Project intelligence unavailable",
                evidence=intelligence_status,
                severity="low",
                status="supported",
            )
        )

    # --------------------------------------------------------
    # NO-MATCH SIGNALS
    # --------------------------------------------------------
    #
    # "no_match" means the intelligence provider did not find
    # a matching market/DeFi record.
    #
    # It is NOT treated as a risk signal.
    # --------------------------------------------------------

    _ = market_signal
    _ = defi_signal

    return unique_risk_items(risks)


# ============================================================
# RISK AGGREGATION
# ============================================================

def calculate_risk_level(risks):
    """
    Calculate overall risk level from structured risk signals.

    Important:
        Risk signals are evidence, not a scam verdict.
    """

    if not risks:
        return "low"

    highest_severity = "low"

    for risk in risks:

        if not isinstance(risk, dict):
            continue

        severity = str(
            risk.get(
                "severity",
                "low"
            )
            or "low"
        ).lower()

        if (
            severity in SEVERITY_ORDER
            and SEVERITY_ORDER[severity]
            > SEVERITY_ORDER[highest_severity]
        ):

            highest_severity = severity

    return highest_severity


def summarize_risks(risks):
    """
    Create a human-readable risk summary.
    """

    if not risks:
        return "No specific risk signals detected."

    risk_level = calculate_risk_level(risks)

    if risk_level == "high":

        return (
            "High-severity risk signals detected. "
            "Review the evidence carefully."
        )

    if risk_level == "medium":

        return (
            "Medium-severity risk signals detected. "
            "Review the available evidence."
        )

    return (
        "Low-severity risk or evidence limitations detected."
    )


def aggregate_risks(risks):
    """
    Deduplicate and summarize risk signals.
    """

    if not isinstance(risks, list):
        risks = []

    risks = unique_risk_items(risks)

    risk_level = calculate_risk_level(
        risks
    )

    return {
        "signals": risks,
        "risk_level": risk_level,
        "signal_count": len(risks),
        "summary": summarize_risks(
            risks
        ),
    }


# ============================================================
# MAIN RISK INTELLIGENCE PIPELINE
# ============================================================

def analyze_risk(verification):
    """
    Run the complete Risk Intelligence pipeline.

    Combines:

        1. Suspicious-content risks
        2. Verification risks
        3. Domain / official-source risks
        4. Market / DeFi intelligence risks
        5. Risk aggregation
    """

    if not isinstance(verification, dict):
        verification = {}

    risks = []

    # --------------------------------------------------------
    # SUSPICIOUS CONTENT
    # --------------------------------------------------------

    risks.extend(
        analyze_warning_risks(
            verification.get(
                "warnings",
                []
            )
        )
    )

    # --------------------------------------------------------
    # VERIFICATION
    # --------------------------------------------------------

    risks.extend(
        analyze_verification_risks(
            verification
        )
    )

    # --------------------------------------------------------
    # DOMAIN / OFFICIAL SOURCE
    # --------------------------------------------------------

    risks.extend(
        analyze_domain_risks(
            verification
        )
    )

    # --------------------------------------------------------
    # MARKET / DEFI INTELLIGENCE
    # --------------------------------------------------------

    risks.extend(
        analyze_intelligence_risks(
            verification
        )
    )

    # --------------------------------------------------------
    # AGGREGATE
    # --------------------------------------------------------

    return aggregate_risks(
        risks
    )