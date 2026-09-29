"""
AirdropRadar Scorer v2.3

Purpose:
    Score qualified airdrop opportunities using evidence-sensitive signals.

v2.3 changes:
    - Keeps verifier v9 availability states.
    - Unavailable verification is neutral, not negative.
    - Unavailable market intelligence is neutral.
    - Unavailable DeFi intelligence is neutral.
    - Stored official/project links remain usable evidence.
    - URLs embedded inside descriptions can contribute link evidence.
    - Separates source/evidence quality from direct verification.
    - Confidence better reflects strong opportunity evidence when
      external verification services are unavailable.
    - Keeps evidence-sensitive Action and Reward scoring.
    - Keeps strict risk penalties.
    - Keeps pipeline-compatible public function names.
"""

import re


MAX_SCORE = 100


# ============================================================
# CATEGORY WEIGHTS
# ============================================================

CATEGORY_WEIGHTS = {
    "Points": {
        "opportunity": 25,
        "action": 15,
        "reward": 15,
    },

    "Testnet": {
        "opportunity": 25,
        "action": 15,
        "reward": 15,
    },

    "Retroactive": {
        "opportunity": 25,
        "action": 15,
        "reward": 15,
    },

    "Bounty": {
        "opportunity": 25,
        "action": 15,
        "reward": 15,
    },

    "Holder": {
        "opportunity": 25,
        "action": 15,
        "reward": 15,
    },

    "Liquidity": {
        "opportunity": 25,
        "action": 15,
        "reward": 15,
    },

    "Activity": {
        "opportunity": 25,
        "action": 15,
        "reward": 15,
    },

    "Other": {
        "opportunity": 20,
        "action": 15,
        "reward": 10,
    },
}


# ============================================================
# RISK PENALTIES
# ============================================================

RISK_PENALTIES = {
    "guaranteed profit": 25,
    "guaranteed return": 25,
    "send crypto": 30,
    "send us crypto": 30,
    "double your crypto": 40,
    "double your bitcoin": 40,
    "limited time guaranteed": 15,
    "seed phrase": 50,
    "private key": 50,
    "recovery phrase": 50,
    "deposit crypto": 20,
    "pay fee to claim": 20,
    "withdrawal fee": 15,
    "activate your wallet": 20,
}


# ============================================================
# POSITIVE SIGNALS
# ============================================================

POSITIVE_KEYWORDS = [
    "airdrop",
    "token",
    "claim",
    "testnet",
    "mainnet",
    "points",
    "rewards",
    "reward",
    "community",
    "eligibility",
    "snapshot",
    "retroactive",
    "allocation",
    "distribution",
    "campaign",
    "bounty",
    "holder",
    "liquidity",
    "bridge",
    "swap",
    "trading",
    "transactions",
    "interactions",
    "users",
    "early adopters",
    "participate",
    "participation",
]


# ============================================================
# CATEGORY SIGNALS
# ============================================================

CATEGORY_SIGNALS = {
    "Points": [
        "points",
        "point system",
        "points campaign",
        "points program",
        "points season",
        "earn points",
        "farm points",
        "points farming",
        "xp points",
        "xp",
    ],

    "Testnet": [
        "testnet",
        "test net",
        "test network",
        "devnet",
        "developer network",
        "testnet campaign",
        "testnet rewards",
        "testnet incentive",
        "testnet incentives",
        "testnet points",
    ],

    "Retroactive": [
        "retroactive",
        "retroactive airdrop",
        "retroactive rewards",
        "past users",
        "early users",
        "early adopters",
        "historical users",
        "previous users",
        "users who interacted",
        "interaction history",
        "activity history",
    ],

    "Bounty": [
        "bounty",
        "bug bounty",
        "social bounty",
        "content bounty",
        "referral bounty",
        "translation bounty",
        "community bounty",
        "task bounty",
        "complete tasks",
    ],

    "Holder": [
        "holder",
        "holders",
        "token holders",
        "nft holders",
        "snapshot",
        "snapshot date",
        "holding requirement",
        "hold tokens",
        "hold nft",
        "eligible holders",
    ],

    "Liquidity": [
        "liquidity",
        "liquidity provider",
        "liquidity providers",
        "provide liquidity",
        "liquidity mining",
        "yield farming",
        "amm",
        "pool liquidity",
        "liquidity pool",
        "staking liquidity",
        "lp",
    ],

    "Activity": [
        "activity",
        "on-chain activity",
        "onchain activity",
        "user activity",
        "transaction activity",
        "transactions",
        "interactions",
        "interact with",
        "bridge",
        "bridging",
        "swap",
        "swaps",
        "trade",
        "trading activity",
        "deposit",
        "withdraw",
        "volume",
        "volume requirement",
        "use the protocol",
        "use the app",
    ],
}


# ============================================================
# ACTION SIGNALS
# ============================================================

LOW_ACTION_SIGNALS = [
    "join",
    "follow",
    "register",
    "sign up",
    "signup",
    "connect wallet",
    "connect your wallet",
    "complete profile",
    "join community",
    "join discord",
    "join telegram",
    "follow twitter",
    "follow x",
]


MEDIUM_ACTION_SIGNALS = [
    "complete tasks",
    "complete task",
    "daily tasks",
    "quests",
    "quest",
    "social tasks",
    "refer friends",
    "referral",
    "invite users",
    "bridge",
    "bridging",
    "swap",
    "swaps",
    "trade",
    "trading",
    "make transactions",
    "transactions",
    "interact",
    "interactions",
    "use the protocol",
    "use the app",
    "provide liquidity",
    "liquidity",
    "stake",
    "staking",
    "deposit",
    "withdraw",
]


HIGH_ACTION_SIGNALS = [
    "trading volume",
    "volume requirement",
    "minimum volume",
    "provide liquidity",
    "liquidity mining",
    "yield farming",
    "multiple transactions",
    "on-chain activity",
    "onchain activity",
    "transaction history",
    "complete multiple quests",
    "complete all tasks",
]


# ============================================================
# REWARD SIGNALS
# ============================================================

WEAK_REWARD_SIGNALS = [
    "reward",
    "rewards",
    "incentive",
    "incentives",
    "benefits",
    "earn",
]


MEDIUM_REWARD_SIGNALS = [
    "airdrop",
    "airdrop rewards",
    "token rewards",
    "community rewards",
    "points rewards",
    "testnet rewards",
    "campaign rewards",
    "eligible for rewards",
    "reward campaign",
    "reward program",
]


STRONG_REWARD_SIGNALS = [
    "token allocation",
    "token allocation for users",
    "airdrop allocation",
    "token distribution",
    "reward distribution",
    "points convert to tokens",
    "points conversion",
    "claim tokens",
    "claim rewards",
    "claim your allocation",
    "token claim",
    "eligible for airdrop",
    "eligible for tokens",
    "eligible for allocation",
    "receive tokens",
    "receive rewards",
]


REWARD_PATTERNS = [
    r"\b\d+(?:\.\d+)?\s*%\s*(?:of\s*)?(?:the\s*)?(?:token|tokens|supply|allocation|rewards?)\b",
    r"\b\d+(?:\.\d+)?\s*(?:million|billion|m|b)\s+(?:tokens?|points?|rewards?)\b",
    r"\b(?:up\s*to|worth|valued\s*at)\s+\$?\d+(?:\.\d+)?(?:\s*[km])?\b",
    r"\b\d+(?:\.\d+)?\s*(?:usd|usdt|usdc)\b",
]


ALLOCATION_PATTERNS = [
    r"\b\d+(?:\.\d+)?\s*%\s*(?:token|tokens|supply|allocation|rewards?)\b",
    r"\b(?:allocate|allocated|allocation|distribute|distributed|distribution)\b",
]


# ============================================================
# EFFORT / PARTICIPATION COMPLEXITY
# ============================================================

LOW_EFFORT_SIGNALS = [
    "follow",
    "join",
    "register",
    "sign up",
    "signup",
    "connect wallet",
    "join community",
    "join discord",
    "join telegram",
]


MEDIUM_EFFORT_SIGNALS = [
    "complete task",
    "complete tasks",
    "quest",
    "quests",
    "refer",
    "referral",
    "bridge",
    "swap",
    "trade",
    "stake",
    "staking",
    "interact",
    "transactions",
]


HIGH_EFFORT_SIGNALS = [
    "provide liquidity",
    "liquidity mining",
    "yield farming",
    "trading volume",
    "volume requirement",
    "minimum volume",
    "multiple transactions",
    "on-chain activity",
    "onchain activity",
    "transaction history",
    "daily activity",
]


# ============================================================
# URL / LINK HELPERS
# ============================================================

URL_PATTERN = re.compile(
    r"https?://[^\s<>\"]+",
    re.IGNORECASE,
)


def extract_urls(text):
    """
    Extract URLs from arbitrary text.
    """

    if not text:
        return []

    matches = URL_PATTERN.findall(
        str(text)
    )

    cleaned = []

    for url in matches:
        url = url.rstrip(
            ".,);]}>'\""
        )

        if url and url not in cleaned:
            cleaned.append(url)

    return cleaned


def get_all_links(result):
    """
    Collect link evidence from:

        - official_links
        - description
        - url
        - links

    This is especially useful when the verifier source page
    is temporarily unavailable but stored project links remain.
    """

    if not isinstance(result, dict):
        return []

    links = []

    official_links = result.get(
        "official_links",
        [],
    )

    if isinstance(
        official_links,
        str,
    ):
        official_links = [
            official_links
        ]

    if isinstance(
        official_links,
        list,
    ):
        links.extend(
            official_links
        )

    description = result.get(
        "description",
        "",
    )

    links.extend(
        extract_urls(
            description
        )
    )

    stored_links = result.get(
        "links",
        [],
    )

    if isinstance(
        stored_links,
        str,
    ):
        stored_links = [
            stored_links
        ]

    if isinstance(
        stored_links,
        list,
    ):
        links.extend(
            stored_links
        )

    candidate_url = result.get(
        "url",
        "",
    )

    if candidate_url:
        links.append(
            candidate_url
        )

    unique_links = []

    for link in links:
        if not link:
            continue

        link = str(link).strip()

        if link and link not in unique_links:
            unique_links.append(
                link
            )

    return unique_links


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text):
    """
    Normalize text for reliable signal matching.
    """

    if text is None:
        return ""

    text = str(text).lower()

    text = text.replace(
        "\n",
        " ",
    )

    text = text.replace(
        "\r",
        " ",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def get_search_text(airdrop):
    """
    Build searchable text from an airdrop result.
    """

    if not isinstance(
        airdrop,
        dict,
    ):
        return ""

    parts = [
        airdrop.get(
            "name",
            "",
        ),
        airdrop.get(
            "description",
            "",
        ),
        airdrop.get(
            "source",
            "",
        ),
        airdrop.get(
            "url",
            "",
        ),
    ]

    official_links = airdrop.get(
        "official_links",
        [],
    )

    if isinstance(
        official_links,
        list,
    ):
        parts.extend(
            official_links
        )

    elif isinstance(
        official_links,
        str,
    ):
        parts.append(
            official_links
        )

    return normalize_text(
        " ".join(
            str(part)
            for part in parts
            if part
        )
    )


def contains_signal(text, signal):
    """
    Signal matcher.

    Multi-word phrases:
        direct substring matching.

    Single words:
        word-boundary matching.
    """

    text = normalize_text(
        text
    )

    signal = normalize_text(
        signal
    )

    if not text or not signal:
        return False

    if " " in signal:
        return signal in text

    return (
        re.search(
            rf"\b{re.escape(signal)}\b",
            text,
        )
        is not None
    )


def count_signals(text, signals):
    """
    Count unique matching signals.
    """

    text = normalize_text(
        text
    )

    matches = 0

    for signal in signals:
        if contains_signal(
            text,
            signal,
        ):
            matches += 1

    return matches


# ============================================================
# CATEGORY SCORE
# ============================================================

def category_score(result):
    """
    Score how clearly the opportunity belongs to its category.
    """

    text = get_search_text(
        result
    )

    category = result.get(
        "airdrop_type",
        "Other",
    )

    if category not in CATEGORY_WEIGHTS:
        category = "Other"

    signals = CATEGORY_SIGNALS.get(
        category,
        [],
    )

    if not signals:
        return 0

    matched = count_signals(
        text,
        signals,
    )

    if category == "Other":

        if matched >= 5:
            return 15

        if matched >= 3:
            return 10

        if matched >= 1:
            return 5

        return 0

    if matched >= 6:
        return 25

    if matched >= 4:
        return 20

    if matched >= 2:
        return 16

    if matched == 1:
        return 11

    return 0


# ============================================================
# ACTION SCORE
# ============================================================

def action_score(result):
    """
    Evidence-sensitive participation/action score.

    Generic words such as "activity" do not automatically
    produce a high score.

    Specific participation mechanisms receive more weight.
    """

    text = get_search_text(
        result
    )

    low_matches = count_signals(
        text,
        LOW_ACTION_SIGNALS,
    )

    medium_matches = count_signals(
        text,
        MEDIUM_ACTION_SIGNALS,
    )

    high_matches = count_signals(
        text,
        HIGH_ACTION_SIGNALS,
    )

    score = 0

    # Low-effort actions
    if low_matches >= 4:
        score += 3

    elif low_matches >= 2:
        score += 2

    elif low_matches == 1:
        score += 1

    # Medium actions
    if medium_matches >= 5:
        score += 8

    elif medium_matches >= 4:
        score += 7

    elif medium_matches >= 3:
        score += 6

    elif medium_matches >= 2:
        score += 5

    elif medium_matches == 1:
        score += 3

    # High-specificity actions
    if high_matches >= 3:
        score += 6

    elif high_matches >= 2:
        score += 5

    elif high_matches == 1:
        score += 4

    # Numeric activity requirements
    numeric_activity_patterns = [
        r"\bminimum\s+\d+\s+(?:transactions?|swaps?|trades?)\b",
        r"\b\d+\s+(?:transactions?|swaps?|trades?)\b",
        r"\bminimum\s+\$?\d+(?:\.\d+)?\s+(?:volume|trading volume)\b",
        r"\bvolume\s+(?:of|above|over|greater than)\s+\$?\d+(?:\.\d+)?\b",
    ]

    for pattern in numeric_activity_patterns:

        if re.search(
            pattern,
            text,
        ):
            score += 2
            break

    return min(
        score,
        15,
    )


# ============================================================
# REWARD SCORE
# ============================================================

def reward_score(result):
    """
    Evidence-sensitive reward score.

    Generic "reward" language is deliberately weak.

    Explicit allocations, distributions and claimable rewards
    receive much stronger scores.
    """

    text = get_search_text(
        result
    )

    weak_matches = count_signals(
        text,
        WEAK_REWARD_SIGNALS,
    )

    medium_matches = count_signals(
        text,
        MEDIUM_REWARD_SIGNALS,
    )

    strong_matches = count_signals(
        text,
        STRONG_REWARD_SIGNALS,
    )

    score = 0

    # Weak reward language
    if weak_matches >= 4:
        score += 3

    elif weak_matches >= 2:
        score += 2

    elif weak_matches == 1:
        score += 1

    # Medium reward evidence
    if medium_matches >= 5:
        score += 7

    elif medium_matches >= 4:
        score += 6

    elif medium_matches >= 3:
        score += 5

    elif medium_matches >= 2:
        score += 4

    elif medium_matches == 1:
        score += 3

    # Strong reward evidence
    if strong_matches >= 4:
        score += 9

    elif strong_matches >= 3:
        score += 8

    elif strong_matches >= 2:
        score += 7

    elif strong_matches == 1:
        score += 5

    # Numeric reward evidence
    numeric_reward_found = False

    for pattern in REWARD_PATTERNS:

        if re.search(
            pattern,
            text,
        ):
            numeric_reward_found = True
            break

    if numeric_reward_found:
        score += 4

    # Allocation/distribution evidence
    allocation_found = False

    for pattern in ALLOCATION_PATTERNS:

        if re.search(
            pattern,
            text,
        ):
            allocation_found = True
            break

    if allocation_found:
        score += 3

    return min(
        score,
        15,
    )


# ============================================================
# EFFORT / PARTICIPATION COMPLEXITY
# ============================================================

def effort_value_score(result):
    """
    Measure participation complexity.

    This is not a free-points bonus.

    It represents how substantial the participation process is.
    """

    text = get_search_text(
        result
    )

    low_matches = count_signals(
        text,
        LOW_EFFORT_SIGNALS,
    )

    medium_matches = count_signals(
        text,
        MEDIUM_EFFORT_SIGNALS,
    )

    high_matches = count_signals(
        text,
        HIGH_EFFORT_SIGNALS,
    )

    score = 0

    if low_matches >= 1:
        score += 1

    if medium_matches >= 4:
        score += 3

    elif medium_matches >= 2:
        score += 2

    elif medium_matches == 1:
        score += 1

    if high_matches >= 3:
        score += 4

    elif high_matches >= 2:
        score += 3

    elif high_matches == 1:
        score += 2

    return min(
        score,
        10,
    )


# ============================================================
# VERIFICATION STATE HELPERS
# ============================================================

def get_verification_status(result):
    """
    Return verifier v9 status.

    Possible states:

        verified
        available
        failed
        unavailable

    Legacy results without verification_status are supported.
    """

    status = normalize_text(
        result.get(
            "verification_status",
            "",
        )
    )

    if status:
        return status

    level = normalize_text(
        result.get(
            "verification_level",
            "",
        )
    )

    if level in {
        "strong_signals",
        "some_signals",
        "no_warnings",
    }:
        return "available"

    if level in {
        "warnings_found",
    }:
        return "failed"

    if level in {
        "source_unavailable",
        "unknown",
    }:
        return "unavailable"

    if result.get(
        "verified"
    ) is True:
        return "verified"

    return "unavailable"


# ============================================================
# VERIFICATION SCORE
# ============================================================

def verification_score(result):
    """
    Score direct verification evidence.

    Important:

        unavailable = 0

    This does NOT mean the opportunity is bad.

    It means verification evidence was unavailable.

    Stored links are handled separately by link_score().
    """

    status = get_verification_status(
        result
    )

    if status == "unavailable":
        return 0

    if status == "failed":
        return 0

    if status == "verified":
        return 15

    if status == "available":

        level = normalize_text(
            result.get(
                "verification_level",
                "",
            )
        )

        if level == "strong_signals":
            return 15

        if level == "some_signals":
            return 12

        if level == "no_warnings":
            return 10

        if result.get(
            "verified"
        ) is True:
            return 15

        return 8

    return 0


# ============================================================
# LINK SCORE
# ============================================================

def link_score(result):
    """
    Score useful project/link evidence.

    v2.3 improvement:

    Links are collected from:
        - official_links
        - description
        - links
        - candidate URL

    Therefore a temporarily unavailable source page does not
    automatically erase stored project-link evidence.
    """

    links = get_all_links(
        result
    )

    if not links:
        return 0

    # Separate obvious source/listing links from project links.
    source_domains = {
        "airdropalert.com",
        "cointelegraph.com",
        "coindesk.com",
        "decrypt.co",
        "theblock.co",
        "coinmarketcap.com",
    }

    project_links = []

    for link in links:

        lowered = normalize_text(
            link
        )

        if any(
            domain in lowered
            for domain in source_domains
        ):
            continue

        if link not in project_links:
            project_links.append(
                link
            )

    count = len(
        project_links
    )

    if count >= 5:
        return 5

    if count >= 3:
        return 4

    if count >= 2:
        return 3

    if count == 1:
        return 2

    # If only source/listing links exist, do not award
    # project-link evidence.
    return 0


# ============================================================
# EVIDENCE QUALITY
# ============================================================

def evidence_quality_score(result):
    """
    Small supporting score for the quality of available evidence.

    This is NOT verification.

    It recognizes that an opportunity may have useful stored
    project evidence even while an external source is unavailable.

    Maximum: 5
    """

    links = link_score(
        result
    )

    verification_status = (
        get_verification_status(
            result
        )
    )

    description = normalize_text(
        result.get(
            "description",
            "",
        )
    )

    source = normalize_text(
        result.get(
            "source",
            "",
        )
    )

    score = 0

    # Stored project links are meaningful evidence.
    if links >= 4:
        score += 2

    elif links >= 2:
        score += 1

    # Detailed descriptions are better than empty headlines.
    if len(description) >= 400:
        score += 2

    elif len(description) >= 200:
        score += 1

    # Recognized specialized opportunity source.
    if (
        "airdropalert"
        in source
    ):
        score += 1

    # Direct verification already carries its own score.
    # This prevents double-counting.
    if verification_status in {
        "verified",
        "available",
    }:
        score = min(
            score,
            2,
        )

    return min(
        score,
        5,
    )


# ============================================================
# MARKET SCORE
# ============================================================

def market_score(result):
    """
    Score market intelligence.

    unavailable:
        0 points, neutral.

    checked_no_match:
        0 points, neutral.

    Actual recognized market evidence can add points.
    """

    status = normalize_text(
        result.get(
            "market_status",
            "",
        )
    )

    if status == "unavailable":
        return 0

    signal = result.get(
        "market_signal",
        {},
    )

    if not isinstance(
        signal,
        dict,
    ):
        return 0

    if status == "checked_no_match":
        return 0

    found = signal.get(
        "found"
    )

    if found is False:
        return 0

    score = 0

    recognized = signal.get(
        "recognized"
    )

    if recognized is True:
        score += 3

    match_percentage = signal.get(
        "match_percentage",
        signal.get(
            "match",
            0,
        ),
    )

    try:
        match_percentage = float(
            match_percentage
        )

    except (
        TypeError,
        ValueError,
    ):
        match_percentage = 0

    if match_percentage >= 90:
        score += 3

    elif match_percentage >= 70:
        score += 2

    elif match_percentage >= 50:
        score += 1

    rank = signal.get(
        "rank"
    )

    try:
        rank = int(
            rank
        )

    except (
        TypeError,
        ValueError,
    ):
        rank = None

    if rank is not None:

        if rank <= 10:
            score += 2

        elif rank <= 50:
            score += 1

    return min(
        score,
        7,
    )


# ============================================================
# DEFI SCORE
# ============================================================

def defi_score(result):
    """
    Score DeFi ecosystem intelligence.

    unavailable:
        0 points, neutral.

    checked_no_match:
        0 points, neutral.
    """

    status = normalize_text(
        result.get(
            "defi_status",
            "",
        )
    )

    if status == "unavailable":
        return 0

    signal = result.get(
        "defi_signal",
        {},
    )

    if not isinstance(
        signal,
        dict,
    ):
        return 0

    if status == "checked_no_match":
        return 0

    found = signal.get(
        "found"
    )

    if found is False:
        return 0

    score = 0

    recognized = signal.get(
        "recognized"
    )

    if recognized is True:
        score += 3

    match_percentage = signal.get(
        "match_percentage",
        signal.get(
            "match",
            0,
        ),
    )

    try:
        match_percentage = float(
            match_percentage
        )

    except (
        TypeError,
        ValueError,
    ):
        match_percentage = 0

    if match_percentage >= 90:
        score += 2

    elif match_percentage >= 70:
        score += 1

    category = normalize_text(
        signal.get(
            "category",
            "",
        )
    )

    if category:
        score += 1

    tvl = signal.get(
        "tvl"
    )

    try:
        tvl = float(
            tvl
        )

    except (
        TypeError,
        ValueError,
    ):
        tvl = 0

    if tvl > 0:
        score += 1

    return min(
        score,
        7,
    )


# ============================================================
# WARNING SCORE
# ============================================================

def warning_score(result):
    """
    Warnings are actual negative evidence.

    Availability failures are NOT warnings.
    """

    warnings = result.get(
        "warnings",
        [],
    )

    if not warnings:
        return 0

    if isinstance(
        warnings,
        str,
    ):
        warnings = [
            warnings
        ]

    return -min(
        len(warnings) * 5,
        10,
    )


# ============================================================
# POSITIVE SIGNAL SCORE
# ============================================================

def positive_signal_score(result):
    """
    Small supporting bonus.

    Prevents keyword density from dominating the score.
    """

    text = get_search_text(
        result
    )

    matched = count_signals(
        text,
        POSITIVE_KEYWORDS,
    )

    if matched >= 8:
        return 3

    if matched >= 5:
        return 2

    if matched >= 2:
        return 1

    return 0


# ============================================================
# RISK SCORE
# ============================================================

def risk_score(result):
    """
    Calculate risk penalty from suspicious phrases.

    Availability is never treated as risk.
    """

    text = get_search_text(
        result
    )

    warnings = result.get(
        "warnings",
        [],
    )

    if isinstance(
        warnings,
        list,
    ):
        warning_text = " ".join(
            str(warning)
            for warning in warnings
        )

    else:
        warning_text = str(
            warnings
        )

    combined_text = normalize_text(
        f"{text} {warning_text}"
    )

    total_penalty = 0

    for phrase, penalty in RISK_PENALTIES.items():

        if contains_signal(
            combined_text,
            phrase,
        ):
            total_penalty += penalty

    return -total_penalty


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(result):
    """
    Calculate confidence from evidence quality.

    Important:

        unavailable data != negative evidence

    Confidence is not the same thing as opportunity score.

    A project can have:
        - strong opportunity evidence
        - unavailable external verification

    and therefore receive Medium confidence rather than
    automatically Low confidence.
    """

    evidence = 0

    category = category_score(
        result
    )

    actions = action_score(
        result
    )

    rewards = reward_score(
        result
    )

    verification = verification_score(
        result
    )

    links = link_score(
        result
    )

    evidence_quality = (
        evidence_quality_score(
            result
        )
    )

    market = market_score(
        result
    )

    defi = defi_score(
        result
    )

    warnings = result.get(
        "warnings",
        [],
    )

    # Category evidence
    if category >= 20:
        evidence += 2

    elif category >= 11:
        evidence += 1

    # Action evidence
    if actions >= 12:
        evidence += 2

    elif actions >= 6:
        evidence += 1

    # Reward evidence
    if rewards >= 12:
        evidence += 2

    elif rewards >= 6:
        evidence += 1

    # Direct verification
    if verification >= 12:
        evidence += 2

    elif verification >= 8:
        evidence += 1

    # Official/project links
    if links >= 4:
        evidence += 1

    # Additional evidence quality
    evidence += evidence_quality

    # Market intelligence
    if market >= 4:
        evidence += 1

    # DeFi intelligence
    if defi >= 4:
        evidence += 1

    # Warnings reduce confidence
    if warnings:
        evidence -= 2

    # Actual risk reduces confidence
    risk = risk_score(
        result
    )

    if risk <= -50:
        evidence -= 4

    elif risk < 0:
        evidence -= 2

    if evidence >= 9:
        return "High"

    if evidence >= 4:
        return "Medium"

    return "Low"


# ============================================================
# SCORE LEVEL
# ============================================================

def score_level(score):

    if score >= 80:
        return "High"

    if score >= 50:
        return "Medium"

    return "Low"


# ============================================================
# RISK LEVEL
# ============================================================

def risk_level(result):

    penalty = abs(
        risk_score(
            result
        )
    )

    if penalty >= 50:
        return "High"

    if penalty >= 20:
        return "Medium"

    return "Low"


# ============================================================
# RECOMMENDATION
# ============================================================

def recommendation(score, risk):

    if risk == "High":
        return "🚫 Avoid"

    if score >= 75:
        return "🔥 Worth farming"

    if score >= 60:
        return "⚡ Strong opportunity"

    if score >= 50:
        return "🟡 Consider"

    if score >= 35:
        return "👀 Watch"

    return "⚪ Low priority"


# ============================================================
# REASONS
# ============================================================

def get_score_reasons(result):

    reasons = []

    category = result.get(
        "airdrop_type",
        "Other",
    )

    category_points = category_score(
        result
    )

    actions = action_score(
        result
    )

    rewards = reward_score(
        result
    )

    effort = effort_value_score(
        result
    )

    verification = verification_score(
        result
    )

    links = link_score(
        result
    )

    evidence_quality = (
        evidence_quality_score(
            result
        )
    )

    market = market_score(
        result
    )

    defi = defi_score(
        result
    )

    warnings = warning_score(
        result
    )

    risk = risk_score(
        result
    )

    verification_status = (
        get_verification_status(
            result
        )
    )

    market_status = normalize_text(
        result.get(
            "market_status",
            "",
        )
    )

    defi_status = normalize_text(
        result.get(
            "defi_status",
            "",
        )
    )

    # Category
    if category_points >= 20:

        reasons.append(
            f"Clear {category} opportunity signals"
        )

    elif category_points >= 10:

        reasons.append(
            f"Moderate {category} opportunity signals"
        )

    # Actions
    if actions >= 12:

        reasons.append(
            "Strong participation mechanism detected"
        )

    elif actions >= 6:

        reasons.append(
            "Clear participation mechanism detected"
        )

    elif actions > 0:

        reasons.append(
            "Limited participation evidence detected"
        )

    # Rewards
    if rewards >= 12:

        reasons.append(
            "Strong explicit reward evidence detected"
        )

    elif rewards >= 6:

        reasons.append(
            "Moderate reward evidence detected"
        )

    elif rewards > 0:

        reasons.append(
            "Limited reward evidence detected"
        )

    # Effort
    if effort >= 7:

        reasons.append(
            "High participation effort detected"
        )

    elif effort >= 3:

        reasons.append(
            "Moderate participation effort detected"
        )

    elif effort > 0:

        reasons.append(
            "Low participation effort detected"
        )

    # Verification
    if verification >= 12:

        reasons.append(
            "Strong verification signals"
        )

    elif verification >= 8:

        reasons.append(
            "Some verification signals"
        )

    elif verification_status == "unavailable":

        reasons.append(
            "Verification unavailable; "
            "no verification penalty applied"
        )

    elif verification_status == "failed":

        reasons.append(
            "Verification checks did not establish "
            "positive evidence"
        )

    # Links
    if links >= 4:

        reasons.append(
            "Multiple project/official links found"
        )

    elif links > 0:

        reasons.append(
            "Project/official link evidence found"
        )

    # Evidence quality
    if evidence_quality >= 3:

        reasons.append(
            "Strong stored evidence quality"
        )

    elif evidence_quality > 0:

        reasons.append(
            "Additional stored evidence available"
        )

    # Market
    if market >= 4:

        reasons.append(
            "Useful market intelligence detected"
        )

    elif market_status == "unavailable":

        reasons.append(
            "Market intelligence unavailable; "
            "no penalty applied"
        )

    # DeFi
    if defi >= 4:

        reasons.append(
            "Useful DeFi ecosystem intelligence detected"
        )

    elif defi_status == "unavailable":

        reasons.append(
            "DeFi intelligence unavailable; "
            "no penalty applied"
        )

    # Warnings
    if warnings < 0:

        reasons.append(
            "Warnings detected"
        )

       # Risk
    risk_intelligence = result.get(
        "risk_intelligence",
        {},
    )

    risk_signals = []

    if isinstance(risk_intelligence, dict):

        risk_signals = risk_intelligence.get(
            "signals",
            [],
        )

    if isinstance(risk_signals, list) and risk_signals:

        for signal in risk_signals:

            if not isinstance(signal, dict):
                continue

            category = str(
                signal.get(
                    "category",
                    "",
                )
            ).strip()

            value = str(
                signal.get(
                    "value",
                    "",
                )
            ).strip()

            severity = str(
                signal.get(
                    "severity",
                    "",
                )
            ).strip().lower()

            status = str(
                signal.get(
                    "status",
                    "",
                )
            ).strip().lower()

            if value:

                if severity:

                    reasons.append(
                        f"Risk signal ({severity}): {value}"
                    )

                else:

                    reasons.append(
                        f"Risk signal: {value}"
                    )

            elif category:

                reasons.append(
                    f"Risk signal: {category}"
                )

    elif risk < 0:

        reasons.append(
            "Risk signals detected"
        )

    return reasons

# ============================================================
# SCORE BREAKDOWN
# ============================================================

def get_score_breakdown(result):
    """
    Return score component breakdown.

    Kiept for compatibility with:
        live_pipeline_test.py
        other pipeline modules
    """

    if not isinstance(
        result,
        dict,
    ):
        return {
            "category_opportunity": 0,
            "actions": 0,
            "rewards": 0,
            "effort_value": 0,
            "verification": 0,
            "links": 0,
            "evidence_quality": 0,
            "market": 0,
            "defi": 0,
            "positive_signals": 0,
            "warnings": 0,
            "risk": 0,
        }

    breakdown = result.get(
        "score_breakdown"
    )

    if isinstance(
        breakdown,
        dict,
    ):
        return breakdown

    return {
        "category_opportunity": category_score(
            result
        ),

        "actions": action_score(
            result
        ),

        "rewards": reward_score(
            result
        ),

        "effort_value": effort_value_score(
            result
        ),

        "verification": verification_score(
            result
        ),

        "links": link_score(
            result
        ),

        "evidence_quality": evidence_quality_score(
            result
        ),

        "market": market_score(
            result
        ),

        "defi": defi_score(
            result
        ),

        "positive_signals": positive_signal_score(
            result
        ),

        "warnings": warning_score(
            result
        ),

        "risk": risk_score(
            result
        ),
    }


# ============================================================
# SCORE CALCULATION
# ============================================================

def calculate_score(result):
    """
    Calculate score and return enriched result.

    Availability failures are neutral.

    Stored evidence can still contribute where it is actually
    present.
    """

    if not isinstance(
        result,
        dict,
    ):
        raise ValueError(
            "Scorer expected a dictionary result."
        )

    enriched = dict(
        result
    )

    category_points = category_score(
        result
    )

    actions = action_score(
        result
    )

    rewards = reward_score(
        result
    )

    effort = effort_value_score(
        result
    )

    verification = verification_score(
        result
    )

    links = link_score(
        result
    )

    evidence_quality = (
        evidence_quality_score(
            result
        )
    )

    market = market_score(
        result
    )

    defi = defi_score(
        result
    )

    positive = positive_signal_score(
        result
    )

    warnings = warning_score(
        result
    )

    risk = risk_score(
        result
    )

    raw_score = (
        category_points
        + actions
        + rewards
        + effort
        + verification
        + links
        + evidence_quality
        + market
        + defi
        + positive
        + warnings
        + risk
    )

    score = max(
        0,
        min(
            MAX_SCORE,
            raw_score,
        ),
    )

    confidence = calculate_confidence(
        result
    )

    level = score_level(
        score
    )

    risk_status = risk_level(
        result
    )

    enriched["score"] = score

    enriched["confidence"] = confidence

    enriched["score_level"] = level

    enriched["risk_level"] = risk_status

    enriched["recommendation"] = recommendation(
        score,
        risk_status,
    )

    enriched["score_reasons"] = (
        get_score_reasons(
            result
        )
    )

    enriched["score_breakdown"] = {
        "category_opportunity": category_points,
        "actions": actions,
        "rewards": rewards,
        "effort_value": effort,
        "verification": verification,
        "links": links,
        "evidence_quality": evidence_quality,
        "market": market,
        "defi": defi,
        "positive_signals": positive,
        "warnings": warnings,
        "risk": risk,
    }

    enriched["data_quality"] = {
        "verification_status": (
            get_verification_status(
                result
            )
        ),

        "verification_available": (
            result.get(
                "verification_available"
            )
        ),

        "source_access": (
            result.get(
                "source_access"
            )
        ),

        "market_status": (
            result.get(
                "market_status"
            )
        ),

        "defi_status": (
            result.get(
                "defi_status"
            )
        ),

        "intelligence_status": (
            result.get(
                "intelligence_status"
            )
        ),

        "stored_link_count": len(
            get_all_links(
                result
            )
        ),

        "project_link_count": len([
            link
            for link in get_all_links(
                result
            )
            if not any(
                domain in normalize_text(link)
                for domain in {
                    "airdropalert.com",
                    "cointelegraph.com",
                    "coindesk.com",
                    "decrypt.co",
                    "theblock.co",
                    "coinmarketcap.com",
                }
            )
        ]),
    }

    return enriched


# ============================================================
# PIPELINE COMPATIBILITY
# ============================================================

def score_candidate(result):
    """
    Pipeline-compatible scoring function.
    """

    return calculate_score(
        result
    )


def score_airdrop(result):
    """
    Alias for compatibility with possible
    pipeline usage.
    """

    return calculate_score(
        result
    )


# ============================================================
# SUMMARY
# ============================================================

def scoring_summary(result):
    """
    Return concise scoring summary.
    """

    if not isinstance(
        result,
        dict,
    ):
        return "Invalid scoring result."

    score = result.get(
        "score",
        0,
    )

    level = result.get(
        "score_level",
        "Low",
    )

    confidence = result.get(
        "confidence",
        "Low",
    )

    risk = result.get(
        "risk_level",
        "Low",
    )

    recommendation_text = result.get(
        "recommendation",
        "⚪ Low priority",
    )

    return (
        f"Score: {score}/100 | "
        f"Level: {level} | "
        f"Confidence: {confidence} | "
        f"Risk: {risk} | "
        f"Recommendation: {recommendation_text}"
    )


# ============================================================
# STANDALONE TESTS
# ============================================================

def run_test(name, result):

    scored = calculate_score(
        result
    )

    print(
        f"\n🪂 {name}"
    )

    print(
        f"   Category: "
        f"{scored.get('airdrop_type')}"
    )

    print(
        f"   Score: "
        f"{scored.get('score')}/100"
    )

    print(
        f"   Level: "
        f"{scored.get('score_level')}"
    )

    print(
        f"   Confidence: "
        f"{scored.get('confidence')}"
    )

    print(
        f"   Risk: "
        f"{scored.get('risk_level')}"
    )

    print(
        f"   Recommendation: "
        f"{scored.get('recommendation')}"
    )

    print(
        "   Breakdown:"
    )

    breakdown = get_score_breakdown(
        scored
    )

    print(
        f"      Category opportunity: "
        f"{breakdown.get('category_opportunity', 0)}"
    )

    print(
        f"      Actions: "
        f"{breakdown.get('actions', 0)}"
    )

    print(
        f"      Rewards: "
        f"{breakdown.get('rewards', 0)}"
    )

    print(
        f"      Effort/value: "
        f"{breakdown.get('effort_value', 0)}"
    )

    print(
        f"      Verification: "
        f"{breakdown.get('verification', 0)}"
    )

    print(
        f"      Links: "
        f"{breakdown.get('links', 0)}"
    )

    print(
        f"      Evidence quality: "
        f"{breakdown.get('evidence_quality', 0)}"
    )

    print(
        f"      Market: "
        f"{breakdown.get('market', 0)}"
    )

    print(
        f"      DeFi: "
        f"{breakdown.get('defi', 0)}"
    )

    print(
        f"      Positive signals: "
        f"{breakdown.get('positive_signals', 0)}"
    )

    print(
        f"      Warnings: "
        f"{breakdown.get('warnings', 0)}"
    )

    print(
        f"      Risk: "
        f"{breakdown.get('risk', 0)}"
    )

    return scored


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "🧠 AirdropRadar Scorer v2.3"
    )

    # ========================================================
    # TEST 1: POINTS
    # ========================================================

    points_campaign = {

        "name": "Points Campaign",

        "url": "https://example.com",

        "description": (
            "Users can connect wallet, complete quests, "
            "earn points and receive token rewards. "
            "Points may convert to an airdrop allocation."
        ),

        "source": "Official project campaign",

        "airdrop_type": "Points",

        "official_links": [
            "https://example.com",
            "https://example.com/docs",
        ],

        "warnings": [],

        "verified": True,

        "verification_level": "strong_signals",

        "verification_status": "verified",

        "verification_available": True,

        "market_status": "checked_no_match",

        "defi_status": "checked_no_match",

        "market_signal": {},

        "defi_signal": {},
    }

    run_test(
        "Points Campaign",
        points_campaign,
    )


    # ========================================================
    # TEST 2: TESTNET
    # ========================================================

    testnet_campaign = {

        "name": "Testnet Campaign",

        "url": "https://example.com",

        "description": (
            "Join the testnet, connect wallet and complete "
            "tasks to earn testnet rewards."
        ),

        "source": "Official project campaign",

        "airdrop_type": "Testnet",

        "official_links": [
            "https://example.com",
            "https://example.com/docs",
        ],

        "warnings": [],

        "verified": True,

        "verification_level": "strong_signals",

        "verification_status": "verified",

        "verification_available": True,

        "market_status": "checked_no_match",

        "defi_status": "checked_no_match",

        "market_signal": {},

        "defi_signal": {},
    }

    run_test(
        "Testnet Campaign",
        testnet_campaign,
    )


    # ========================================================
    # TEST 3: LIQUIDITY
    # ========================================================

    liquidity_campaign = {

        "name": "Liquidity Campaign",

        "url": "https://example.com",

        "description": (
            "Provide liquidity to the protocol and participate "
            "in liquidity mining. LP users earn token rewards "
            "and receive a share of the token allocation."
        ),

        "source": "Official project campaign",

        "airdrop_type": "Liquidity",

        "official_links": [
            "https://example.com",
            "https://example.com/docs",
            "https://example.com/app",
        ],

        "warnings": [],

        "verified": True,

        "verification_level": "strong_signals",

        "verification_status": "verified",

        "verification_available": True,

        "market_status": "available",

        "defi_status": "available",

        "market_signal": {
            "found": True,
            "recognized": True,
            "match_percentage": 100,
            "rank": 20,
        },

        "defi_signal": {
            "found": True,
            "recognized": True,
            "match_percentage": 100,
            "category": "DeFi",
            "tvl": 5000000,
        },
    }

    run_test(
        "Liquidity Campaign",
        liquidity_campaign,
    )


    # ========================================================
    # TEST 4: GENERIC AIRDROP
    # ========================================================

    generic_airdrop = {

        "name": "Generic Airdrop",

        "url": "https://example.com",

        "description": (
            "A community airdrop is available."
        ),

        "source": "Unknown source",

        "airdrop_type": "Other",

        "official_links": [],

        "warnings": [],

        "verified": False,

        "verification_level": "unknown",

        "verification_status": "unavailable",

        "verification_available": False,

        "source_access": "unavailable",

        "market_status": "unavailable",

        "defi_status": "unavailable",

        "intelligence_status": "unavailable",

        "market_signal": {},

        "defi_signal": {},
    }

    run_test(
        "Generic Airdrop",
        generic_airdrop,
    )


    # ========================================================
    # TEST 5: ALLOCATION WITHOUT ACTION
    # ========================================================

    allocation_campaign = {

        "name": "Allocation Campaign",

        "url": "https://example.com",

        "description": (
            "The project has announced a token allocation "
            "and future token distribution for eligible users."
        ),

        "source": "Project announcement",

        "airdrop_type": "Activity",

        "official_links": [
            "https://project.example",
        ],

        "warnings": [],

        "verified": True,

        "verification_level": "strong_signals",

        "verification_status": "verified",

        "verification_available": True,

        "market_status": "checked_no_match",

        "defi_status": "checked_no_match",

        "market_signal": {},

        "defi_signal": {},
    }

    run_test(
        "Allocation Campaign",
        allocation_campaign,
    )


    # ========================================================
    # TEST 6: RISKY CAMPAIGN
    # ========================================================

    risky_campaign = {

        "name": "Risky Campaign",

        "url": "https://example.com",

        "description": (
            "Send crypto to activate your wallet and "
            "pay fee to claim guaranteed profit."
        ),

        "source": "Suspicious source",

        "airdrop_type": "Other",

        "official_links": [],

        "warnings": [
            "Suspicious claim mechanism detected."
        ],

        "verified": False,

        "verification_level": "warnings_found",

        "verification_status": "failed",

        "verification_available": True,

        "market_status": "unavailable",

        "defi_status": "unavailable",

        "intelligence_status": "unavailable",

        "market_signal": {},

        "defi_signal": {},
    }

    run_test(
        "Risky Campaign",
        risky_campaign,
    )


    # ========================================================
    # TEST 7: SOURCE/API UNAVAILABLE WITH STORED EVIDENCE
    # ========================================================

    unavailable_but_promising = {

        "name": "Unavailable Source Campaign",

        "url": (
            "https://airdropalert.com/example"
        ),

        "description": (
            "Users can complete quests, bridge assets, "
            "swap tokens and earn points. Eligible users "
            "will receive token rewards and an allocation. "
            "Official project: https://project.example "
            "Documentation: https://project.example/docs"
        ),

        "source": "AirdropAlert",

        "airdrop_type": "Points",

        "official_links": [
            "https://project.example",
            "https://project.example/docs",
        ],

        "warnings": [],

        "verified": False,

        "verification_level": "source_unavailable",

        "verification_status": "unavailable",

        "verification_available": False,

        "source_access": "unavailable",

        "market_status": "unavailable",

        "defi_status": "unavailable",

        "intelligence_status": "unavailable",

        "market_signal": {},

        "defi_signal": {},
    }

    run_test(
        "Unavailable Source With Stored Evidence",
        unavailable_but_promising,
    )


    print(
        "\n✅ Scorer v2.3 ready!"
    )


