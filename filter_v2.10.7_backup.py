
"""
AirdropRadar — Category Classifier
Version: 2.10.7

Purpose:
    Classify airdrop opportunities by their PRIMARY participation mechanism.

Categories:
    1. Retroactive
    2. Holder
    3. Bounty
    4. Testnet
    5. Points
    6. Liquidity
    7. Activity
    8. Other

Calibration:
    - Deterministic
    - Explainable
    - Regression tested
    - Database is NEVER modified by this file
"""

import re

from scanner import scan
from qualifier import qualify_candidate


# ============================================================
# VERSION
# ============================================================

CLASSIFIER_VERSION = "2.10.7"


# ============================================================
# CATEGORY PRIORITY
# ============================================================

AIRDROP_TYPE_PRIORITY = [
    "Retroactive",
    "Holder",
    "Bounty",
    "Points",
    "Testnet",
    "Liquidity",
    "Activity",
    "Other",
]


CATEGORY_ICONS = {
    "Retroactive": "🔄",
    "Holder": "👑",
    "Bounty": "🏆",
    "Testnet": "🧪",
    "Points": "🎯",
    "Liquidity": "💧",
    "Activity": "🔗",
    "Other": "📦",
}


# ============================================================
# RETROACTIVE SIGNALS
# ============================================================

RETROACTIVE_SIGNALS = [
    "past users qualify",
    "past users are eligible",
    "past users will receive",
    "past users received",
    "past users can claim",

    "previous users qualify",
    "previous users are eligible",
    "previous users will receive",
    "previous users received",
    "previous users can claim",

    "past participants qualify",
    "past participants are eligible",
    "past participants will receive",
    "past participants received",
    "past participants can claim",

    "previous participants qualify",
    "previous participants are eligible",
    "previous participants will receive",
    "previous participants received",
    "previous participants can claim",

    "past activity qualifies",
    "previous activity qualifies",
    "historical activity qualifies",

    "past participation qualifies",
    "previous participation qualifies",
    "historical participation qualifies",

    "users who previously participated",
    "users who previously used",
    "users who previously traded",
    "users who previously provided liquidity",

    "users who used the protocol before",
    "users who used the platform before",
    "users who interacted before",

    "previously interacted",
    "previously used the protocol",
    "previously used the platform",
    "previously traded",
    "previously provided liquidity",

    "historical snapshot",
    "snapshot of past users",
    "snapshot of historical users",
    "snapshot of previous users",

    "historical users are eligible",
    "historical users qualify",
    "historical users will receive",
    "historical users received",

    "early users are eligible",
    "early users qualify",
    "early users will receive",
    "early users can claim",
    "early users can receive",

    "early adopters are eligible",
    "early adopters qualify",
    "early adopters will receive",
    "early adopters can claim",
    "early adopters can receive",

    "early participants are eligible",
    "early participants qualify",
    "early participants can claim",
]


HISTORICAL_SIGNALS = [
    "past users",
    "previous users",
    "historical users",
    "past activity",
    "previous activity",
    "historical activity",
    "past participation",
    "previous participation",
    "historical participation",
    "users who previously",
    "previously used",
    "previously interacted",
    "previously participated",
    "early users",
    "early user",
    "early adopters",
    "early adopter",
    "early participants",
    "early participant",
]


RETROACTIVE_REWARD_CONTEXT = [
    "airdrop",
    "reward",
    "rewards",
    "allocation",
    "distribution",
    "eligible",
    "eligibility",
    "qualify",
    "qualified",
    "claim",
    "claimable",
    "receive",
    "received",
    "token allocation",
    "token distribution",
]


SPECULATIVE_MARKERS = [
    "future",
    "potential",
    "possibly",
    "possible",
    "speculative",
    "speculation",
    "could",
    "may",
    "might",
    "if",
    "when",
    "once",
    "not confirmed",
    "not yet confirmed",
    "unconfirmed",
    "has not confirmed",
    "have not confirmed",
    "no confirmed",
    "rumored",
    "rumour",
    "rumor",
    "expected",
    "likely",
]


CONFIRMED_RETROACTIVE_MARKERS = [
    "is eligible",
    "are eligible",
    "is qualified",
    "are qualified",
    "can claim",
    "can receive",
    "will receive",
    "received",
    "qualify for",
    "qualified for",
    "eligible for",
    "allocation for",
    "distribution to",
]


# ============================================================
# HOLDER SIGNALS
# ============================================================

HOLDER_SIGNALS = [
    "holder snapshot",
    "holders snapshot",
    "snapshot for holders",
    "snapshot of holders",
    "holding snapshot",
    "wallet snapshot",

    "token holders are eligible",
    "token holders will receive",
    "token holders qualify",
    "holders are eligible",
    "holders will receive",
    "holders qualify",

    "holding requirement",
    "hold the token",
    "hold tokens",
    "hold at least",
    "minimum balance",
    "minimum token balance",
    "balance requirement",
    "must hold",
    "must be holding",
    "eligible holders",
    "eligible holder",
    "token holder eligibility",
    "holding requirement for",
]


# ============================================================
# BOUNTY SIGNALS
# ============================================================

BOUNTY_SIGNALS = [
    "bug bounty",
    "bug bounty program",
    "bounty program",
    "bounty campaign",
    "security bounty",
    "developer bounty",
    "community bounty",
    "bug bounties",
    "bounties",
    "bounty rewards",
    "earn rewards for bugs",
    "reward for finding bugs",
    "reward for reporting bugs",
    "paid bug reports",
    "paid for bug reports",
    "submit bugs for rewards",
    "submit vulnerabilities for rewards",
    "find vulnerabilities for rewards",
    "security researchers",
    "security research bounty",
    "code bounty",
    "translation bounty",
    "content bounty",
    "marketing bounty",
    "referral bounty",
    "quest bounty",
]


BOUNTY_WORK_SIGNALS = [
    "complete bounty",
    "complete bounties",
    "bounty task",
    "bounty tasks",
    "bounty mission",
    "bounty missions",
    "bounty hunters",
    "submit a bounty",
    "submit your work",
    "submit work",
    "earn tokens for completing",
    "earn tokens for contributions",
    "earn rewards for contributions",
    "rewards for contributions",
    "rewarded for contributions",
]


# ============================================================
# TESTNET SIGNALS
# ============================================================

TESTNET_SIGNALS = [
    "testnet",
    "test net",
    "testnet campaign",
    "testnet rewards",
    "testnet reward",
    "testnet points",
    "testnet xp",
    "testnet participation",
    "testnet participants",
    "testnet users",
    "testnet launch",
    "testnet is live",
    "testnet live",
    "public testnet",
    "public testnet is live",
    "join the testnet",
    "join testnet",
    "participate in the testnet",
    "participate in testnet",
    "use the testnet",
    "use testnet",
    "test tokens",
    "test token",
    "claim test tokens",
    "claim testnet tokens",
]


# ============================================================
# POINTS SIGNALS
# ============================================================

POINTS_SIGNALS = [
    "points",
    "point system",
    "points system",
    "points campaign",
    "points program",
    "points season",
    "points leaderboard",
    "earn points",
    "earning points",
    "collect points",
    "accumulate points",
    "points earned",
    "reward points",

    "xp",
    "xp system",
    "experience points",
    "earn xp",
    "earning xp",
    "collect xp",
    "accumulate xp",
    "xp earned",
]


POINTS_ALLOCATION_SIGNALS = [
    "points determine",
    "points will determine",
    "points determine your allocation",
    "points determine allocation",
    "points-based allocation",
    "points based allocation",
    "points allocation",
    "allocation based on points",
    "allocation depends on points",
    "allocation is based on points",
    "allocation determined by points",
    "allocation determined based on points",
    "allocation determined by your points",

    "points convert into",
    "points converted into",
    "points will convert into",
    "points convert to tokens",
    "points convert into tokens",
    "points converted to tokens",
    "points can be converted into",
    "points are converted into",

    "points translate into",
    "points translate to",

    "points qualify you for",
    "points determine eligibility",
    "points decide",
    "points will decide",
    "points decide your allocation",
    "points decide allocation",
    "your points determine",
    "your points will determine",
    "your points decide",
    "your points will decide",

    "points determine rewards",
    "points determine your rewards",
    "points determine reward",
    "points determine the reward",
    "points determine token allocation",
    "points determine token rewards",
    "points determine your share",
    "points determine your token allocation",

    "points count toward allocation",
    "points count towards allocation",

    "points lead to rewards",
    "points lead to reward",
    "points lead to allocation",
    "points result in rewards",
    "points result in reward",
    "points result in allocation",
    "points result in an allocation",
    "points map to rewards",
    "points map to allocation",

    "xp determines",
    "xp will determine",
    "xp determines your reward",
    "xp determines reward",
    "xp determines eligibility",
    "xp determines your eligibility",
    "xp determines your allocation",
    "xp determines allocation",
    "xp determines your share",
    "xp determines your token allocation",
    "xp determines token allocation",
    "xp determines token rewards",
    "xp determines rewards",
    "xp determines the reward",
    "xp will determine rewards",
    "xp will determine your rewards",
]


POINTS_REWARD_CONTEXT = [
    "points for rewards",
    "points for the airdrop",
    "points for an airdrop",
    "points for allocation",
    "points for token allocation",
    "points for eligibility",
    "points make you eligible",
    "points make users eligible",
    "points used for eligibility",
    "points used to determine",

    "xp for rewards",
    "xp for the airdrop",
    "xp for an airdrop",
    "xp for allocation",
    "xp for token allocation",
    "xp for eligibility",
    "xp make you eligible",
    "xp makes you eligible",
    "xp make users eligible",
    "xp used for eligibility",
    "xp used to determine",
]


# ============================================================
# LIQUIDITY SIGNALS
# ============================================================

LIQUIDITY_SIGNALS = [
    "provide liquidity",
    "providing liquidity",
    "provide liquidity to",
    "provide liquidity on",
    "liquidity provider",
    "liquidity providers",
    "liquidity pool",
    "liquidity pools",

    "lp position",
    "lp positions",
    "lp token",
    "lp tokens",
    "lp rewards",
    "lp incentives",
    "lp farming",
    "lp farming rewards",

    "liquidity mining",
    "liquidity mining rewards",
    "yield farming",
    "yield farm",
    "yield farms",
    "yield strategy",
    "yield strategies",
    "yield vault",
    "yield vaults",

    "liquidity vault",
    "liquidity vaults",
    "deposit liquidity",

    "deposit assets into the vault",
    "deposit assets into vault",
    "deposit into the vault",
    "deposit into vault",

    "earn yield",
    "earn yield on",
    "earn yield from",
    "yield rewards",

    "staking rewards",
    "stake tokens for rewards",
    "staking for rewards",
    "stake to earn",
    "staking to earn",
    "stake assets",
    "stake tokens",

    "liquidity rewards",
    "liquidity incentives",
    "liquidity incentive",
]


STAKING_CONTEXT_SIGNALS = [
    "stake for rewards",
    "stake to earn rewards",
    "stake to earn",
    "staking rewards",
    "staking incentive",
    "staking incentives",
    "staking campaign",
    "staking program",
    "staking points",
    "stake for points",
    "stake to receive",
    "stake to qualify",
    "staking qualifies",
    "staking eligibility",
]


# ============================================================
# ACTIVITY SIGNALS
# ============================================================

ACTIVITY_SIGNALS = [
    "use the protocol",
    "use protocol",
    "use the platform",
    "use platform",
    "use the app",
    "use app",
    "use the dapp",
    "use dapp",

    "trade",
    "trading",
    "swap",
    "swapping",
    "bridge",
    "bridging",
    "lend",
    "lending",
    "borrow",
    "borrowing",
    "mint",
    "minting",
    "deposit",
    "withdraw",
    "withdrawal",

    "complete quests",
    "complete quest",
    "quests",
    "quest",
    "tasks",
    "task",
    "missions",
    "mission",
    "daily tasks",
    "daily task",
    "daily quest",
    "daily quests",

    "referrals",
    "referral",
    "invite friends",
    "invite users",

    "play games",
    "play game",
    "play the game",
    "gaming",
    "gameplay",
    "play-to-earn",
    "play to earn",

    "use the mini app",
    "use mini app",
    "mini app",

    "connect wallet",
    "connect your wallet",
    "wallet connect",

    "run the client",
    "run client",
    "run the core client",
    "core client",
    "run a node",
    "run node",
    "run nodes",

    "contribute bandwidth",
    "internet bandwidth",
    "contribute internet bandwidth",

    "upload photos",
    "upload photo",
    "upload videos",
    "upload video",
    "upload original photos",
    "upload original videos",
    "upload media",
    "submit media",

    "create content",
    "post content",

    "complete activities",
    "continue using",
    "continue to use",
    "continue using the protocol",
    "continue using the platform",
    "continue using the app",
    "continue to use the protocol",
    "continue to use the platform",
    "continue to use the app",

    "current activities",
    "current activity",
    "current tasks",
    "current quests",
    "current missions",
    "ongoing activities",
    "ongoing activity",
    "ongoing tasks",
    "ongoing quests",

    "daily streak",
    "daily streaks",
    "watch ads",
    "reward wheel",

    "chop",
    "mining",
    "mine",
    "fish",
    "fishing",
    "fight",
    "fighting",
    "combat",
    "wager",
    "wagering",

    "early users",
    "early user",
    "early activity",

    # Calibration additions:
    "claim faucet tokens",
    "claim faucet token",
    "complete transactions",
    "complete transaction",
]


CONCRETE_ACTIVITY_SIGNALS = [
    "trade",
    "trading",
    "swap",
    "swapping",
    "bridge",
    "bridging",
    "lend",
    "lending",
    "borrow",
    "borrowing",
    "mint",
    "minting",
    "deposit",
    "withdraw",
    "complete quests",
    "complete quest",
    "quests",
    "quest",
    "tasks",
    "task",
    "missions",
    "mission",
    "daily tasks",
    "daily quest",
    "daily quests",
    "referral",
    "referrals",
    "invite friends",
    "invite users",
    "play games",
    "play game",
    "play the game",
    "gaming",
    "gameplay",
    "play-to-earn",
    "play to earn",
    "run the client",
    "run client",
    "run the core client",
    "core client",
    "run a node",
    "run node",
    "contribute bandwidth",
    "internet bandwidth",
    "upload photos",
    "upload videos",
    "upload media",
    "submit media",
    "create content",
    "post content",
    "daily streak",
    "daily streaks",
    "watch ads",
    "reward wheel",
    "chop",
    "mine",
    "mining",
    "fish",
    "fishing",
    "fight",
    "fighting",
    "combat",
    "wager",
    "wagering",
    "early users",
    "early user",
    "early activity",

    # Calibration additions:
    "claim faucet tokens",
    "claim faucet token",
    "complete transactions",
    "complete transaction",
]


# ============================================================
# NEWS / PRODUCT SIGNALS
# ============================================================

NEWS_SIGNALS = [
    "funding",
    "raises",
    "raised",
    "investment",
    "investor",
    "investors",
    "partnership",
    "acquisition",
    "launches",
    "announces",
    "announced",
    "announcement",
    "interview",
    "price",
    "bitcoin price",
    "market",
    "markets",
    "trump",
    "powell",
    "etf",
    "etfs",
    "bull market",
    "bear market",
]


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text):
    if text is None:
        return ""

    text = str(text).lower()

    replacements = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "–": "-",
        "—": "-",
        "\r": "\n",
        "\t": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Normalize repeated whitespace while preserving newlines.
    text = re.sub(r"[ ]+", " ", text)

    return text.strip()


def keyword_matches(text, signals):
    """
    Match:
        - single words with word boundaries
        - phrases literally

    This prevents:
        trade -> matching trader
        mine -> matching something unrelated
    """

    text = normalize_text(text)

    matches = []

    for raw_signal in signals:
        signal = normalize_text(raw_signal).strip()

        if not signal:
            continue

        if " " in signal or "-" in signal or "'" in signal:
            if signal in text:
                matches.append(signal)
        else:
            pattern = r"\b" + re.escape(signal) + r"\b"

            if re.search(pattern, text):
                matches.append(signal)

    return matches


def contains_any(text, signals):
    return bool(keyword_matches(text, signals))


def contains_all(text, signals):
    text = normalize_text(text)

    for signal in signals:
        signal = normalize_text(signal)

        if signal and signal not in text:
            return False

    return True


def split_sentences(text):
    """
    Safe sentence splitting.

    Correct raw-string regex:
        (?<=[.!?])\s+|\n+
    """

    text = normalize_text(text)

    if not text:
        return []

    parts = re.split(
        r"(?<=[.!?])\s+|\n+",
        text,
    )

    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def unique(values):
    seen = set()
    result = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


# ============================================================
# RETROACTIVE HELPERS
# ============================================================

def sentence_is_speculative(sentence):
    return contains_any(
        sentence,
        SPECULATIVE_MARKERS,
    )


def sentence_is_confirmed_retroactive(sentence):
    return contains_any(
        sentence,
        CONFIRMED_RETROACTIVE_MARKERS,
    )


def has_confirmed_retroactive_sentence(text):
    for sentence in split_sentences(text):

        historical = contains_any(
            sentence,
            HISTORICAL_SIGNALS,
        )

        reward = contains_any(
            sentence,
            RETROACTIVE_REWARD_CONTEXT,
        )

        if not historical or not reward:
            continue

        if not sentence_is_speculative(sentence):
            return True

        if sentence_is_confirmed_retroactive(sentence):
            return True

    return False


def has_historical_distribution_only(text):
    """
    Detect references to old distributions that do not establish
    current eligibility.
    """

    for sentence in split_sentences(text):

        historical = contains_any(
            sentence,
            [
                "historical distribution",
                "historical reward",
                "historical rewards",
                "historical airdrop",
                "past distribution",
                "previous distribution",
                "distributed in",
                "distributed previously",
            ],
        )

        if historical and not sentence_is_confirmed_retroactive(
            sentence
        ):
            return True

    return False


def has_real_retroactive_requirement(text):
    """
    Genuine Retroactive classification requires historical
    participation connected to actual eligibility, reward,
    claim, allocation, or distribution.

    Speculative future retroactive mentions do NOT qualify.
    """

    text = normalize_text(text)

    if has_confirmed_retroactive_sentence(text):
        return True

    for sentence in split_sentences(text):

        historical = contains_any(
            sentence,
            HISTORICAL_SIGNALS,
        )

        reward = contains_any(
            sentence,
            RETROACTIVE_REWARD_CONTEXT,
        )

        if not historical or not reward:
            continue

        if sentence_is_speculative(sentence):
            continue

        return True

    return False


# ============================================================
# HOLDER
# ============================================================

def has_real_holder_requirement(text):
    text = normalize_text(text)

    return contains_any(
        text,
        HOLDER_SIGNALS,
    )


# ============================================================
# BOUNTY
# ============================================================

def has_real_bounty_requirement(text):
    text = normalize_text(text)

    if contains_any(text, BOUNTY_SIGNALS):
        return True

    if contains_any(text, BOUNTY_WORK_SIGNALS):
        return True

    return False


# ============================================================
# TESTNET
# ============================================================

def has_explicit_testnet_context(text):
    text = normalize_text(text)

    return contains_any(
        text,
        TESTNET_SIGNALS,
    )


# ============================================================
# POINTS
# ============================================================

def has_points_allocation(text):
    text = normalize_text(text)

    if contains_any(
        text,
        POINTS_ALLOCATION_SIGNALS,
    ):
        return True

    for sentence in split_sentences(text):

        has_points = contains_any(
            sentence,
            ["points", "xp"],
        )

        has_conversion = contains_any(
            sentence,
            [
                "convert into",
                "converted into",
                "convert to",
                "converted to",
                "translate into",
                "translate to",
                "determine",
                "determines",
                "determine your",
                "lead to",
                "leads to",
                "result in",
                "results in",
                "map to",
                "maps to",
                "count toward",
                "count towards",
            ],
        )

        has_reward = contains_any(
            sentence,
            [
                "allocation",
                "reward",
                "rewards",
                "token",
                "tokens",
                "airdrop",
                "eligibility",
                "eligible",
            ],
        )

        if has_points and has_conversion and has_reward:
            return True

    return contains_any(
        text,
        POINTS_REWARD_CONTEXT,
    )


def has_points_campaign(text):
    text = normalize_text(text)

    if not contains_any(
        text,
        POINTS_SIGNALS,
    ):
        return False

    strong_campaign_context = [
        "points campaign",
        "points program",
        "points season",
        "points system",
        "points leaderboard",
        "earn points",
        "earning points",
        "collect points",
        "accumulate points",
        "points earned",
        "reward points",
        "xp system",
        "earn xp",
        "earning xp",
        "collect xp",
        "accumulate xp",
        "xp earned",
        "experience points",
    ]

    if contains_any(
        text,
        strong_campaign_context,
    ):
        return True

    action_context = [
        "points for completing",
        "points by completing",
        "earn points by",
        "earn xp by",
        "collect points by",
        "accumulate points by",
        "points through trading",
        "points through swaps",
        "points through activity",
        "points through quests",
        "points through referrals",
        "points through liquidity",
        "points through staking",
    ]

    return contains_any(
        text,
        action_context,
    )


# ============================================================
# LIQUIDITY
# ============================================================

def has_real_liquidity_requirement(text):
    text = normalize_text(text)

    if contains_any(
        text,
        LIQUIDITY_SIGNALS,
    ):
        return True

    if contains_any(
        text,
        STAKING_CONTEXT_SIGNALS,
    ):
        return True

    staking = contains_any(
        text,
        [
            "staking",
            "stake",
            "staked",
        ],
    )

    reward = contains_any(
        text,
        [
            "reward",
            "rewards",
            "earn",
            "earning",
            "eligible",
            "eligibility",
            "points",
            "airdrop",
        ],
    )

    if staking and reward:
        return True

    vault = contains_any(
        text,
        [
            "vault",
            "vaults",
        ],
    )

    vault_context = contains_any(
        text,
        [
            "yield",
            "liquidity",
            "deposit assets",
            "deposit into",
            "earn yield",
            "apy",
            "apr",
            "strategy",
            "strategies",
            "farm",
            "farming",
        ],
    )

    if vault and vault_context:
        return True

    return False


# ============================================================
# ACTIVITY
# ============================================================

def has_current_activity_requirement(text):
    text = normalize_text(text)

    return contains_any(
        text,
        ACTIVITY_SIGNALS,
    )


def has_concrete_activity(text):
    text = normalize_text(text)

    return bool(
        keyword_matches(
            text,
            CONCRETE_ACTIVITY_SIGNALS,
        )
    )


def activity_match_count(text):
    return len(
        unique(
            keyword_matches(
                text,
                ACTIVITY_SIGNALS,
            )
        )
    )


# ============================================================
# NEWS
# ============================================================

def is_incidental_news_activity(text):
    """
    Detect activity keywords that are only being mentioned
    as part of market/news commentary rather than as a
    participation requirement.
    """

    text = normalize_text(text)

    news_context = contains_any(
        text,
        NEWS_SIGNALS,
    )

    if not news_context:
        return False

    incidental_patterns = [
        "trading activity",
        "increased trading activity",
        "decreased trading activity",
        "trading volume",
        "trading volumes",
        "market trading",
        "market activity",
        "trading conditions",
        "trading environment",
        "investors are trading",
        "investors traded",
        "investors discuss trading",
        "market reacts to trading",
        "market reacting to trading",
    ]

    return contains_any(
        text,
        incidental_patterns,
    )


def is_news_only(text):
    text = normalize_text(text)

    if not text:
        return False

    if not contains_any(
        text,
        NEWS_SIGNALS,
    ):
        return False

    # Trading/activity mentioned only as part of market/news
    # commentary is not a participation mechanism.
    if is_incidental_news_activity(text):
        return True

    opportunity_signals = (
        RETROACTIVE_SIGNALS
        + HISTORICAL_SIGNALS
        + HOLDER_SIGNALS
        + BOUNTY_SIGNALS
        + BOUNTY_WORK_SIGNALS
        + TESTNET_SIGNALS
        + POINTS_ALLOCATION_SIGNALS
        + POINTS_REWARD_CONTEXT
        + LIQUIDITY_SIGNALS
        + STAKING_CONTEXT_SIGNALS
    )

    if contains_any(
        text,
        opportunity_signals,
    ):
        return False

    if has_concrete_activity(text):
        return False

    return True


# ============================================================
# SHARED ANALYSIS
# ============================================================

def candidate_text(candidate):
    if not isinstance(candidate, dict):
        return ""

    return normalize_text(
        " ".join(
            [
                str(candidate.get("name") or ""),
                str(candidate.get("description") or ""),
            ]
        )
    )


def analyze_candidate(candidate):
    """
    Shared analysis object.

    Classification decisions are generated from this single
    analysis layer.
    """

    text = candidate_text(candidate)

    evidence = {
        "Retroactive": [],
        "Holder": [],
        "Bounty": [],
        "Testnet": [],
        "Points": [],
        "Liquidity": [],
        "Activity": [],
        "Other": [],
    }

    retro = unique(
        keyword_matches(
            text,
            RETROACTIVE_SIGNALS,
        )
        + keyword_matches(
            text,
            HISTORICAL_SIGNALS,
        )
    )

    holder = keyword_matches(
        text,
        HOLDER_SIGNALS,
    )

    bounty = unique(
        keyword_matches(
            text,
            BOUNTY_SIGNALS,
        )
        + keyword_matches(
            text,
            BOUNTY_WORK_SIGNALS,
        )
    )

    testnet = keyword_matches(
        text,
        TESTNET_SIGNALS,
    )

    points = unique(
        keyword_matches(
            text,
            POINTS_ALLOCATION_SIGNALS,
        )
        + keyword_matches(
            text,
            POINTS_REWARD_CONTEXT,
        )
    )

    if not points and has_points_campaign(text):
        points = keyword_matches(
            text,
            POINTS_SIGNALS,
        )

    liquidity = unique(
        keyword_matches(
            text,
            LIQUIDITY_SIGNALS,
        )
        + keyword_matches(
            text,
            STAKING_CONTEXT_SIGNALS,
        )
    )

    activity = keyword_matches(
        text,
        ACTIVITY_SIGNALS,
    )

    retroactive = has_real_retroactive_requirement(text)
    holder_requirement = has_real_holder_requirement(text)
    bounty_requirement = has_real_bounty_requirement(text)
    testnet_context = has_explicit_testnet_context(text)
    points_allocation = has_points_allocation(text)
    points_campaign = has_points_campaign(text)
    liquidity_requirement = has_real_liquidity_requirement(text)
    activity_requirement = has_current_activity_requirement(text)

    evidence["Retroactive"] = (
        retro if retroactive else []
    )

    evidence["Holder"] = (
        holder if holder_requirement else []
    )

    evidence["Bounty"] = (
        bounty if bounty_requirement else []
    )

    evidence["Testnet"] = (
        testnet if testnet_context else []
    )

    evidence["Points"] = (
        points
        if (
            points_allocation
            or points_campaign
        )
        else []
    )

    evidence["Liquidity"] = (
        liquidity
        if liquidity_requirement
        else []
    )

    evidence["Activity"] = (
        activity
        if activity_requirement
        else []
    )

    return {
        "text": text,
        "evidence": evidence,

        "retroactive": retroactive,
        "holder": holder_requirement,
        "bounty": bounty_requirement,
        "testnet": testnet_context,

        "points_allocation": points_allocation,
        "points_campaign": points_campaign,

        "liquidity": liquidity_requirement,
        "activity": activity_requirement,

        "concrete_activity": has_concrete_activity(text),
        "activity_count": activity_match_count(text),

        "news_only": is_news_only(text),
        "historical_distribution_only": (
            has_historical_distribution_only(text)
        ),
    }


# ============================================================
# CATEGORY SCORING
# ============================================================

def calculate_scores_from_analysis(analysis):
    scores = {
        "Retroactive": 0,
        "Holder": 0,
        "Bounty": 0,
        "Testnet": 0,
        "Points": 0,
        "Liquidity": 0,
        "Activity": 0,
        "Other": 0,
    }

    if analysis["retroactive"]:
        scores["Retroactive"] = 100

    if analysis["holder"]:
        scores["Holder"] = 100

    if analysis["bounty"]:
        scores["Bounty"] = 100

    if analysis["testnet"]:
        scores["Testnet"] = 75

        if contains_any(
            analysis["text"],
            [
                "join the testnet",
                "participate in the testnet",
                "public testnet",
                "testnet campaign",
                "testnet rewards",
            ],
        ):
            scores["Testnet"] += 25

    if analysis["points_allocation"]:
        scores["Points"] = 100

    elif analysis["points_campaign"]:
        scores["Points"] = 60

    if analysis["liquidity"]:
        scores["Liquidity"] = 80

        if contains_any(
            analysis["text"],
            [
                "provide liquidity",
                "liquidity provider",
                "liquidity mining",
                "yield farming",
                "earn yield",
                "liquidity pool",
                "staking rewards",
            ],
        ):
            scores["Liquidity"] += 20

    if analysis["activity"]:
        if analysis["activity_count"] >= 3:
            scores["Activity"] = 65
        else:
            scores["Activity"] = 45

        if analysis["concrete_activity"]:
            scores["Activity"] = max(
                scores["Activity"],
                70,
            )

    if analysis["news_only"]:
        scores["Other"] = 100

    elif sum(scores.values()) == 0:
        scores["Other"] = 1

    return scores


def calculate_category_scores(text):
    analysis = analyze_candidate(
        {
            "name": "",
            "description": text,
        }
    )

    return calculate_scores_from_analysis(
        analysis
    )


# ============================================================
# CATEGORY RESOLUTION
# ============================================================

def resolve_category(analysis, scores):
    text = analysis["text"]

    # --------------------------------------------------------
    # NEWS ONLY
    # --------------------------------------------------------

    if analysis["news_only"]:
        return "Other"

    # --------------------------------------------------------
    # CONFIRMED RETROACTIVE
    # --------------------------------------------------------

    if analysis["retroactive"]:
        return "Retroactive"

    # --------------------------------------------------------
    # BOUNTY
    # --------------------------------------------------------

    if analysis["bounty"]:

        strong_bounty = contains_any(
            text,
            [
                "bug bounty program",
                "bounty program",
                "bounty campaign",
                "security bounty",
                "developer bounty",
                "community bounty",
                "bounty rewards",
                "paid bug reports",
                "paid for bug reports",
                "earn rewards for bugs",
                "reward for finding bugs",
                "reward for reporting bugs",
                "submit vulnerabilities for rewards",
            ],
        )

        if strong_bounty:
            return "Bounty"

        # Testnet can be primary if bounty is merely incidental.
        if not analysis["testnet"]:
            return "Bounty"

    # --------------------------------------------------------
    # HOLDER
    # --------------------------------------------------------

    if analysis["holder"]:
        return "Holder"

    # --------------------------------------------------------
    # POINTS ALLOCATION
    # --------------------------------------------------------

    if analysis["points_allocation"]:
        return "Points"

    # --------------------------------------------------------
    # TESTNET
    # --------------------------------------------------------

    if analysis["testnet"]:

        if not analysis["points_allocation"]:

            explicit_testnet_campaign = contains_any(
                text,
                [
                    "testnet campaign",
                    "join the testnet",
                    "participate in the testnet",
                    "use the testnet",
                    "testnet participation",
                    "testnet rewards",
                    "public testnet",
                    "test tokens",
                    "test token",
                ],
            )

            # If testnet is merely the environment and the
            # actual qualification mechanism is liquidity,
            # Liquidity wins.
            if (
                analysis["liquidity"]
                and not explicit_testnet_campaign
            ):
                return "Liquidity"

            return "Testnet"

    # --------------------------------------------------------
    # BOUNTY + TESTNET
    # --------------------------------------------------------

    if analysis["bounty"]:
        return "Bounty"

    # --------------------------------------------------------
    # POINTS CAMPAIGN
    # --------------------------------------------------------

    if analysis["points_campaign"]:

        # Points explicitly described as a secondary reward
        # do not replace the primary participation mechanism.
        side_reward_context = contains_any(
            text,
            [
                "as a side reward",
                "as side rewards",
                "side reward",
                "secondary reward",
                "additional reward",
                "extra reward",
                "bonus points",
                "points as a bonus",
                "points as an extra",
            ],
        )

        if (
            analysis["concrete_activity"]
            and side_reward_context
        ):
            return "Activity"

        # Direct activity normally wins when points are only
        # mentioned as an incidental reward.
        if analysis["concrete_activity"]:

            points_context = contains_any(
                text,
                [
                    "points campaign",
                    "points program",
                    "points season",
                    "points system",
                    "points leaderboard",
                    "points determine",
                    "points allocation",
                    "points convert",
                    "points converted",
                    "points translate",
                    "points lead to",
                    "points result in",

                    # Calibration fix:
                    # Direct point-earning language means
                    # Points remains the primary mechanism.
                    "earn points",
                    "earning points",
                    "collect points",
                    "accumulate points",
                    "points earned",
                    "reward points",
                    "earn xp",
                    "earning xp",
                    "collect xp",
                    "accumulate xp",
                    "xp earned",
                ],
            )

            if not points_context:
                return "Activity"

        return "Points"

    # --------------------------------------------------------
    # LIQUIDITY
    # --------------------------------------------------------

    if analysis["liquidity"]:
        return "Liquidity"

    # --------------------------------------------------------
    # ACTIVITY
    # --------------------------------------------------------

    if analysis["concrete_activity"]:
        return "Activity"

    if analysis["activity"]:
        return "Activity"

    # --------------------------------------------------------
    # OTHER
    # --------------------------------------------------------

    return "Other"


# Backward-compatible alias.
def select_category(text, scores=None):
    analysis = analyze_candidate(
        {
            "name": "",
            "description": text,
        }
    )

    if scores is None:
        scores = calculate_scores_from_analysis(
            analysis
        )

    return resolve_category(
        analysis,
        scores,
    )


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(category, scores):
    if category == "Other":
        return "Low"

    category_score = scores.get(
        category,
        0,
    )

    competing = [
        value
        for key, value in scores.items()
        if key != category
    ]

    second_score = (
        max(competing)
        if competing
        else 0
    )

    difference = (
        category_score
        - second_score
    )

    if category_score >= 100 and difference >= 30:
        return "High"

    if category_score >= 70:
        return "Medium"

    return "Low"


# ============================================================
# PUBLIC CLASSIFIER
# ============================================================

def classify_with_details(result):
    if not isinstance(result, dict):
        return {
            "category": "Other",
            "confidence": "Low",
            "mechanism": "Invalid candidate",
            "evidence": [],
            "scores": {},
        }

    analysis = analyze_candidate(
        result
    )

    scores = calculate_scores_from_analysis(
        analysis
    )

    category = resolve_category(
        analysis,
        scores,
    )

    confidence = calculate_confidence(
        category,
        scores,
    )

    mechanism_map = {
        "Retroactive": "Historical reward eligibility",
        "Holder": "Holder/snapshot eligibility",
        "Bounty": "Explicit bounty/work mechanism",
        "Testnet": "Testnet participation",
        "Points": "Points/XP-based reward mechanism",
        "Liquidity": "Liquidity/yield/staking participation",
        "Activity": "Current product/activity participation",
        "Other": "No clear primary airdrop mechanism",
    }

    return {
        "category": category,
        "confidence": confidence,
        "mechanism": mechanism_map.get(
            category,
            "Unknown mechanism",
        ),
        "evidence": analysis["evidence"].get(
            category,
            [],
        ),
        "scores": scores,
    }


def classify_airdrop(result):
    return classify_with_details(
        result
    )["category"]


def detect_airdrop_type(result):
    return classify_airdrop(
        result
    )


# ============================================================
# PROCESS RESULTS
# ============================================================

def process_results(results):
    processed = []

    for result in results:

        if not isinstance(result, dict):
            continue

        details = classify_with_details(
            result
        )

        enriched = dict(result)

        enriched["airdrop_type"] = details[
            "category"
        ]

        enriched["category_confidence"] = details[
            "confidence"
        ]

        enriched["category_mechanism"] = details[
            "mechanism"
        ]

        enriched["category_evidence"] = details[
            "evidence"
        ]

        enriched["category_scores"] = details[
            "scores"
        ]

        processed.append(
            enriched
        )

    return processed


def get_category_distribution(results):
    distribution = {
        category: 0
        for category in AIRDROP_TYPE_PRIORITY
    }

    for result in results:

        if not isinstance(result, dict):
            continue

        category = result.get(
            "airdrop_type",
            "Other",
        )

        if category not in distribution:
            category = "Other"

        distribution[category] += 1

    return distribution


# ============================================================
# REGRESSION TESTS
# ============================================================

REGRESSION_TESTS = [

    (
        "Historical Users",
        {
            "name": "Historical Users",
            "description": (
                "Historical users are eligible for the airdrop."
            ),
        },
        "Retroactive",
    ),

    (
        "Early Users Alone",
        {
            "name": "Early Users",
            "description": (
                "Early users can participate in the program."
            ),
        },
        "Activity",
    ),

    (
        "Retroactive Word Alone",
        {
            "name": "Retroactive",
            "description": (
                "The project mentions a retroactive mechanism."
            ),
        },
        "Other",
    ),

    (
        "Retroactive Airdrop",
        {
            "name": "Retroactive Airdrop",
            "description": (
                "Users who previously used the protocol "
                "are eligible for the retroactive airdrop."
            ),
        },
        "Retroactive",
    ),

    (
        "Holder Snapshot",
        {
            "name": "Holder Snapshot",
            "description": (
                "A snapshot will determine eligible token holders."
            ),
        },
        "Holder",
    ),

    (
        "Minimum Balance",
        {
            "name": "Holder",
            "description": (
                "Users must hold at least 100 tokens."
            ),
        },
        "Holder",
    ),

    (
        "Generic Holder",
        {
            "name": "Holder",
            "description": (
                "The project has token holders."
            ),
        },
        "Other",
    ),

    (
        "Snapshot Alone",
        {
            "name": "Snapshot",
            "description": (
                "A snapshot date was announced."
            ),
        },
        "Other",
    ),

    (
        "Token Snapshot Alone",
        {
            "name": "Snapshot",
            "description": (
                "The token snapshot is scheduled."
            ),
        },
        "Other",
    ),

    (
        "Holder Can Claim",
        {
            "name": "Holder Airdrop",
            "description": (
                "Eligible holders can claim their allocation."
            ),
        },
        "Holder",
    ),

    (
        "Bug Bounty",
        {
            "name": "Bug Bounty",
            "description": (
                "Join the bug bounty program and earn rewards."
            ),
        },
        "Bounty",
    ),

    (
        "Content Bounty",
        {
            "name": "Content Bounty",
            "description": (
                "Complete the content bounty campaign."
            ),
        },
        "Bounty",
    ),

    (
        "Testnet Campaign",
        {
            "name": "Testnet",
            "description": (
                "Join the public testnet and complete transactions."
            ),
        },
        "Testnet",
    ),

    (
        "Testnet",
        {
            "name": "Testnet",
            "description": (
                "The public testnet is live."
            ),
        },
        "Testnet",
    ),

    (
        "Test Tokens",
        {
            "name": "Testnet",
            "description": (
                "Claim test tokens and use the testnet."
            ),
        },
        "Testnet",
    ),

    (
        "Testnet Points",
        {
            "name": "Testnet",
            "description": (
                "Join the testnet and earn points."
            ),
        },
        "Testnet",
    ),

    (
        "Testnet Liquidity Points",
        {
            "name": "Testnet",
            "description": (
                "Join the testnet, provide liquidity and "
                "earn points for participation."
            ),
        },
        "Testnet",
    ),

    (
        "Faucet Alone",
        {
            "name": "Faucet",
            "description": (
                "A faucet is available for users."
            ),
        },
        "Other",
    ),

    (
        "Faucet With Activity",
        {
            "name": "Faucet",
            "description": (
                "Claim faucet tokens and complete transactions."
            ),
        },
        "Activity",
    ),

    (
        "Points Allocation",
        {
            "name": "Points",
            "description": (
                "Earn points. Your points determine your "
                "token allocation."
            ),
        },
        "Points",
    ),

    (
        "Points Program",
        {
            "name": "Points Program",
            "description": (
                "Earn points throughout the points program."
            ),
        },
        "Points",
    ),

    (
        "Earn Points",
        {
            "name": "Points",
            "description": (
                "Earn points by completing tasks."
            ),
        },
        "Points",
    ),

    (
        "Checkpoint XP Reward",
        {
            "name": "Checkpoint",
            "description": (
                "Complete quests and earn XP. "
                "XP determines your reward eligibility."
            ),
        },
        "Points",
    ),

    (
        "Limitless Points",
        {
            "name": "Limitless",
            "description": (
                "Trade and provide liquidity to earn points. "
                "Points convert into token allocation."
            ),
        },
        "Points",
    ),

    (
        "Points Campaign",
        {
            "name": "Points Campaign",
            "description": (
                "Earn points by completing tasks and referrals "
                "during the points campaign."
            ),
        },
        "Points",
    ),

    (
        "Trade Then Earn Points",
        {
            "name": "Trading",
            "description": (
                "Trade assets and earn points as a side reward."
            ),
        },
        "Activity",
    ),

    (
        "Points Determine Allocation",
        {
            "name": "Points",
            "description": (
                "Points determine the token allocation."
            ),
        },
        "Points",
    ),

    (
        "Liquidity",
        {
            "name": "Liquidity",
            "description": (
                "Provide liquidity to the pool."
            ),
        },
        "Liquidity",
    ),

    (
        "Liquidity Provider",
        {
            "name": "LP",
            "description": (
                "Become a liquidity provider."
            ),
        },
        "Liquidity",
    ),

    (
        "Liquidity Vault",
        {
            "name": "Vault",
            "description": (
                "Deposit assets into the vault to earn yield."
            ),
        },
        "Liquidity",
    ),

    (
        "Staking Rewards",
        {
            "name": "Staking",
            "description": (
                "Stake tokens to earn staking rewards."
            ),
        },
        "Liquidity",
    ),

    (
        "Yield Farming",
        {
            "name": "Yield",
            "description": (
                "Participate in yield farming."
            ),
        },
        "Liquidity",
    ),

    (
        "Trading",
        {
            "name": "Trading",
            "description": (
                "Trade assets on the platform."
            ),
        },
        "Activity",
    ),

    (
        "Swapping",
        {
            "name": "Swap",
            "description": (
                "Swap tokens using the application."
            ),
        },
        "Activity",
    ),

    (
        "Quest",
        {
            "name": "Quest",
            "description": (
                "Complete quests and activities."
            ),
        },
        "Activity",
    ),

    (
        "Referral",
        {
            "name": "Referral",
            "description": (
                "Invite friends and earn rewards."
            ),
        },
        "Activity",
    ),

    (
        "Gaming",
        {
            "name": "Game",
            "description": (
                "Play games and complete gameplay activities."
            ),
        },
        "Activity",
    ),

    (
        "Wallet",
        {
            "name": "Wallet",
            "description": (
                "Connect your wallet and use the application."
            ),
        },
        "Activity",
    ),

    (
        "News Article",
        {
            "name": "Crypto News",
            "description": (
                "Bitcoin rises as investors discuss ETF flows "
                "and market conditions."
            ),
        },
        "Other",
    ),

    (
        "Funding News",
        {
            "name": "Protocol",
            "description": (
                "The company raised funding from investors."
            ),
        },
        "Other",
    ),

    (
        "Market Update",
        {
            "name": "Market",
            "description": (
                "Bitcoin price rises as the crypto market reacts."
            ),
        },
        "Other",
    ),

    (
        "Activity With News",
        {
            "name": "Trading Platform",
            "description": (
                "The company raised funding, but users can "
                "trade and complete activities on the platform."
            ),
        },
        "Activity",
    ),
]


# ============================================================
# CALIBRATION EDGE TESTS
# ============================================================

CALIBRATION_EDGE_TESTS = [

    (
        "Speculative Retroactive",
        {
            "name": "Future Airdrop",
            "description": (
                "Early users may receive a future retroactive airdrop."
            ),
        },
        "Activity",
    ),

    (
        "Historical Distribution Speculation",
        {
            "name": "Protocol",
            "description": (
                "The protocol had a historical distribution. "
                "Future users could potentially benefit from another one."
            ),
        },
        "Other",
    ),

    (
        "Gaming Activity",
        {
            "name": "Game",
            "description": (
                "Play games, complete daily quests, maintain streaks "
                "and earn rewards."
            ),
        },
        "Activity",
    ),

    (
        "DePIN Activity",
        {
            "name": "DePIN",
            "description": (
                "Run the Core Client and contribute internet bandwidth "
                "to earn rewards."
            ),
        },
        "Activity",
    ),

    (
        "Media Activity",
        {
            "name": "Scout",
            "description": (
                "Upload original photos and videos, submit them and "
                "enter your payout wallet."
            ),
        },
        "Activity",
    ),

    (
        "Points Conversion",
        {
            "name": "Points",
            "description": (
                "Users earn points. Points convert into token allocation."
            ),
        },
        "Points",
    ),

    (
        "Points Translate",
        {
            "name": "Points",
            "description": (
                "Points translate into token rewards."
            ),
        },
        "Points",
    ),

    (
        "Liquidity Supporting Points",
        {
            "name": "Points",
            "description": (
                "Provide liquidity and trade to earn points. "
                "Points determine your token allocation."
            ),
        },
        "Points",
    ),

    (
        "Testnet Environment Liquidity",
        {
            "name": "Testnet",
            "description": (
                "The application is on testnet and users must "
                "provide liquidity to participate."
            ),
        },
        "Liquidity",
    ),

    (
        "News With Concrete Activity",
        {
            "name": "Protocol",
            "description": (
                "The protocol raised funding. Users can trade, "
                "complete quests and earn rewards."
            ),
        },
        "Activity",
    ),

    (
        "Market News",
        {
            "name": "Market Update",
            "description": (
                "The market reacts to Bitcoin price movements."
            ),
        },
        "Other",
    ),

    (
        "Product Promotion",
        {
            "name": "Product",
            "description": (
                "Our new product launches with a beautiful platform "
                "for users."
            ),
        },
        "Other",
    ),

    (
        "Early Users Activity",
        {
            "name": "Protocol",
            "description": (
                "Early users can continue using the protocol."
            ),
        },
        "Activity",
    ),
]


# ============================================================
# SEMANTIC GUARD TESTS
# ============================================================

SEMANTIC_GUARD_TESTS = [

    (
        "Early Users + Confirmed Retroactive",
        {
            "name": "Airdrop",
            "description": (
                "Early users are eligible for the airdrop."
            ),
        },
        "Retroactive",
    ),

    (
        "Early Activity + Speculation",
        {
            "name": "Protocol",
            "description": (
                "Early activity could become relevant for a future "
                "retroactive airdrop."
            ),
        },
        "Activity",
    ),

    (
        "Future Retroactive Alone",
        {
            "name": "Protocol",
            "description": (
                "The project may launch a future retroactive airdrop."
            ),
        },
        "Other",
    ),

    (
        "Historical Claim",
        {
            "name": "Airdrop",
            "description": (
                "Users who previously participated can claim rewards."
            ),
        },
        "Retroactive",
    ),

    (
        "Gaming Mining",
        {
            "name": "Kintara",
            "description": (
                "Play the game, mine resources, fish and fight "
                "to earn rewards."
            ),
        },
        "Activity",
    ),

    (
        "DePIN Client",
        {
            "name": "Aether",
            "description": (
                "Run the Core Client and contribute bandwidth."
            ),
        },
        "Activity",
    ),

    (
        "Upload Media",
        {
            "name": "Scout",
            "description": (
                "Upload original photos and videos."
            ),
        },
        "Activity",
    ),

    (
        "Points Lead To Rewards",
        {
            "name": "Points",
            "description": (
                "Points lead to token rewards."
            ),
        },
        "Points",
    ),

    (
        "Points Result In Allocation",
        {
            "name": "Points",
            "description": (
                "Points result in an allocation."
            ),
        },
        "Points",
    ),

    (
        "News Trading Mention",
        {
            "name": "Market News",
            "description": (
                "The market is reacting to increased trading activity."
            ),
        },
        "Other",
    ),
]


# ============================================================
# TEST RUNNER
# ============================================================

def run_test_suite(title, tests):
    print()
    print(title)
    print("=" * 60)

    passed = 0
    failed = 0

    for label, candidate, expected in tests:

        try:
            details = classify_with_details(
                candidate
            )

            actual = details["category"]

        except Exception as error:

            actual = "ERROR"

            print(
                f"❌ FAIL | {label} → ERROR"
            )

            print(
                f"   Exception: {error}"
            )

            failed += 1
            continue

        if actual == expected:

            print(
                f"✅ PASS | {label} → {actual}"
            )

            passed += 1

        else:

            print(
                f"❌ FAIL | {label} → {actual} "
                f"(expected {expected})"
            )

            print(
                f"   Evidence: {details.get('evidence')}"
            )

            print(
                f"   Scores: {details.get('scores')}"
            )

            failed += 1

    print()

    print(
        f"Tests passed: {passed}/{len(tests)}"
    )

    print(
        f"Tests failed: {failed}/{len(tests)}"
    )

    return passed, failed


def run_tests():
    total_passed = 0
    total_failed = 0
    total_tests = 0

    suites = [
        (
            "🧪 CATEGORY CLASSIFIER TESTS",
            REGRESSION_TESTS,
        ),
        (
            "🧪 CALIBRATION EDGE TESTS",
            CALIBRATION_EDGE_TESTS,
        ),
        (
            "🛡️ SEMANTIC GUARD TESTS",
            SEMANTIC_GUARD_TESTS,
        ),
    ]

    for title, tests in suites:

        passed, failed = run_test_suite(
            title,
            tests,
        )

        total_passed += passed
        total_failed += failed
        total_tests += len(tests)

    print()
    print("=" * 60)
    print("📊 INTERNAL CLASSIFIER TEST SUMMARY")
    print("=" * 60)

    print(
        f"Total tests:   {total_tests}"
    )

    print(
        f"Passed:        {total_passed}"
    )

    print(
        f"Failed:        {total_failed}"
    )

    if total_failed == 0:

        print(
            "✅ INTERNAL TEST GATE: PASS"
        )

    else:

        print(
            "❌ INTERNAL TEST GATE: FAIL"
        )

    return (
        total_passed,
        total_failed,
    )


# ============================================================
# LIVE CLASSIFICATION
# ============================================================

def run_live_classification():
    """
    Optional live scanner classification.

    This function does NOT modify the database.
    """

    print()
    print("=" * 60)
    print("📡 LIVE AIRDROP CLASSIFICATION")
    print("=" * 60)

    try:
        discovered = scan()

    except Exception as error:

        print(
            f"❌ Scanner failed: {error}"
        )

        return []

    if not isinstance(discovered, list):
        print(
            "❌ Scanner returned invalid data."
        )
        return []

    print(
        f"📡 Discovered: {len(discovered)}"
    )

    qualified = []

    for candidate in discovered:

        if not isinstance(candidate, dict):
            continue

        try:

            result = qualify_candidate(
                candidate
            )

            if result:
                qualified.append(
                    candidate
                )

        except Exception as error:

            print(
                f"⚠️ Qualification error for "
                f"{candidate.get('name', 'Unknown')}: "
                f"{error}"
            )

    print(
        f"🎯 Qualified: {len(qualified)}"
    )

    results = []

    for candidate in qualified:

        try:

            details = classify_with_details(
                candidate
            )

            results.append(
                {
                    "name": candidate.get(
                        "name",
                        "Unknown",
                    ),
                    "url": candidate.get(
                        "url",
                        "",
                    ),
                    "category": details[
                        "category"
                    ],
                    "confidence": details[
                        "confidence"
                    ],
                    "mechanism": details[
                        "mechanism"
                    ],
                    "evidence": details[
                        "evidence"
                    ],
                }
            )

        except Exception as error:

            print(
                f"⚠️ Classification error for "
                f"{candidate.get('name', 'Unknown')}: "
                f"{error}"
            )

    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("🚀 AirdropRadar Category Classifier")

    print(
        f"🧠 Classifier version: "
        f"{CLASSIFIER_VERSION}"
    )

    passed, failed = run_tests()

    print()

    if failed == 0:

        print(
            "✅ ALL INTERNAL CLASSIFIER TESTS PASSED."
        )

    else:

        print(
            "❌ INTERNAL CLASSIFIER TESTS FAILED."
        )

    print()
    print(
        "🛡️ DATABASE WAS NOT MODIFIED."
    )

    print(
        "🛡️ NO CATEGORY BACKFILL WAS PERFORMED."
    )

    print()

    # IMPORTANT:
    # Live classification is intentionally NOT started here.
    # Calibration remains isolated and deterministic.
