"""
AirdropRadar — Category Classifier
Version: 2.12.6

Purpose:
    Classify airdrop opportunities by their PRIMARY participation mechanism.

    Context rules (global, not per-project):
    - Early user language != Retroactive unless eligibility is confirmed
    - Testnet as environment != Testnet when XP/points is the reward framework
    - Another project's points program != Points for this project
    - Vault/liquidity mentioned in passing != Liquidity
    - Product capabilities like swap != Activity
    - Points used only to score LP/activity != automatically Points

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

CLASSIFIER_VERSION = "2.12.6"


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
]

# Bare "early users" is NOT historical by itself.
# Only confirmed early-user eligibility phrases count.
EARLY_USER_RETROACTIVE_SIGNALS = [
    "early users are eligible",
    "early users qualify",
    "early users will receive",
    "early users can claim",
    "early users can receive",
    "early user are eligible",
    "early adopters are eligible",
    "early adopters qualify",
    "early adopters will receive",
    "early adopters can claim",
    "early participants are eligible",
    "early participants qualify",
    "early participants will receive",
    "early participants can claim",
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

    "nft holders",
    "nft holder",
    "sbt holders",
    "sbt holder",
    "hold nfts",
    "hold nft",
    "collect sbts",
    "collect sbt",
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
    "testnet portal",
    "hertzflow testnet",
    "bnb smart chain testnet",
    "ekiden testnet",
    "canton testnet",
    "testnet trading",
    "trade on the testnet",
    "trade on testnet",
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
    "points reward",
    "points rewards",
    "xp reward",
    "xp rewards",

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
    "snapshot",
    "snapshot date",

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

        signal = normalize_text(
            raw_signal
        ).strip()

        if not signal:
            continue

        if (
            " " in signal
            or "-" in signal
            or "'" in signal
        ):
            if signal in text:
                matches.append(signal)

        else:
            pattern = (
                r"\b"
                + re.escape(signal)
                + r"\b"
            )

            if re.search(
                pattern,
                text,
            ):
                matches.append(signal)

    return matches


def contains_any(text, signals):
    return bool(
        keyword_matches(
            text,
            signals,
        )
    )


def contains_all(text, signals):
    text = normalize_text(text)

    for signal in signals:

        signal = normalize_text(
            signal
        )

        if signal and signal not in text:
            return False

    return True


def split_sentences(text):
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
    if contains_any(
        text,
        EARLY_USER_RETROACTIVE_SIGNALS,
    ):
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

        if not sentence_is_speculative(sentence):
            return True

        if sentence_is_confirmed_retroactive(sentence):
            return True

    return False


def has_historical_distribution_only(text):
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
    text = normalize_text(text)

    if contains_any(
        text,
        EARLY_USER_RETROACTIVE_SIGNALS,
    ):
        return True

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

    if contains_any(
        text,
        HOLDER_SIGNALS,
    ):
        return True

    real_holder_signals = [
        "must hold",
        "must be holding",
        "hold at least",
        "minimum balance",
        "minimum token balance",
        "holding requirement",
        "eligible holders",
        "token holders are eligible",
        "token holders will receive",
        "holders are eligible",
        "holders will receive",
        "holders qualify",
        "nft holders",
        "sbt holders",
        "hold nfts",
        "collect sbts",
    ]

    return contains_any(
        text,
        real_holder_signals,
    )


# ============================================================
# BOUNTY
# ============================================================

def has_real_bounty_requirement(text):
    text = normalize_text(text)

    if contains_any(
        text,
        BOUNTY_SIGNALS,
    ):
        return True

    if contains_any(
        text,
        BOUNTY_WORK_SIGNALS,
    ):
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


def has_strong_testnet_participation(text):
    text = normalize_text(text)

    strong_signals = [
        "join the testnet",
        "join testnet",
        "participate in the testnet",
        "participate in testnet",
        "use the testnet",
        "use testnet",
        "trade on the testnet",
        "trade on testnet",
        "testnet campaign",
        "testnet participation",
        "testnet participants",
        "testnet users",
        "public testnet",
        "testnet is live",
        "testnet live",
        "testnet rewards",
        "testnet reward",
        "test tokens",
        "test token",
        "claim test tokens",
        "claim testnet tokens",
    ]

    if contains_any(
        text,
        strong_signals,
    ):
        return True

    for sentence in split_sentences(text):

        has_testnet = contains_any(
            sentence,
            ["testnet", "test net"],
        )

        if not has_testnet:
            continue

        participation = contains_any(
            sentence,
            [
                "join",
                "participate",
                "use",
                "trade",
                "complete",
                "claim",
                "earn",
                "play",
                "interact",
                "activity",
                "transaction",
                "transactions",
            ],
        )

        if participation:
            return True

    return False


# ============================================================
# POINTS
# ============================================================

def has_points_allocation(text):
    text = normalize_text(text)

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
        "pear points",
        "pear rewards",
        "pear.trade rewards campaign",
        "rewards campaign",
        "multi-season points",
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
        "experience points",
        "xp system",
        "participation tracked via xp",
        "xp earned by",
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
        "points from trading",
        "points from activity",
        "points from referrals",
        "points from quests",
        "xp from trading",
        "xp from activity",
        "xp from quests",
        "points convert into token allocation",
        "points convert into",
        "points converted into",
        "points translate into",
        "points lead to",
        "points result in",
    ]

    return contains_any(
        text,
        action_context,
    )


def has_strong_points_mechanism(text):
    text = normalize_text(text)

    return contains_any(
        text,
        [
            "xp system",
            "participation tracked via xp",
            "xp earned by",
            "earn xp",
            "earning xp",
            "collect xp",
            "accumulate xp",
            "xp earned",
            "points campaign",
            "points program",
            "points season",
            "multi-season points",
            "points convert into token allocation",
            "points convert into tokens",
            "points determine your allocation",
            "points determine allocation",
        ],
    )


# ============================================================
# LIQUIDITY
# ============================================================

def has_real_liquidity_requirement(text):
    text = normalize_text(text)

    direct_liquidity_signals = [
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
        "liquidity rewards",
        "liquidity incentives",
        "liquidity incentive",
        "liquidity for trading fees",
        "liquidity for market activity",
    ]

    if contains_any(
        text,
        direct_liquidity_signals,
    ):
        return True

    if contains_any(
        text,
        STAKING_CONTEXT_SIGNALS,
    ):
        return True

    staking_requirement_patterns = [
        "stake tokens for rewards",
        "stake token for rewards",
        "stake to earn rewards",
        "stake to earn",
        "staking rewards",
        "staking incentive",
        "staking incentives",
        "stake for points",
        "stake to receive",
        "stake to qualify",
        "staking qualifies",
        "staking eligibility",
        "must stake",
        "need to stake",
        "users must stake",
        "users need to stake",
        "stake tokens to qualify",
        "stake tokens to earn",
        "stake assets to earn",
    ]

    if contains_any(
        text,
        staking_requirement_patterns,
    ):
        return True

    # Incidental vault mentions are not liquidity participation.
    # Require an explicit deposit/LP vault action.
    vault_participation = contains_any(
        text,
        [
            "deposit into the vault",
            "deposit into vault",
            "deposit into a vault",
            "deposit to the vault",
            "deposit to vault",
            "enter the vault",
            "liquidity vault",
            "liquidity vaults",
            "yield vault",
            "yield vaults",
            "strategy vaults for curated yield",
            "provide liquidity",
            "providing liquidity",
            "liquidity provider",
            "liquidity providers",
        ],
    )

    if vault_participation:
        return True

    # "Vault shares" as an eligibility/holding route is not LP.
    if contains_any(
        text,
        [
            "vault shares",
            "maintain vault shares",
            "hold vault shares",
        ],
    ):
        return False

    # Aggregator / routing language is not liquidity participation.
    if contains_any(
        text,
        [
            "fragmented liquidity",
            "liquidity sources",
            "across liquidity",
            "route trades",
            "routing across",
            "aggregated from",
            "liquidity aggregated",
        ],
    ) and not contains_any(
        text,
        [
            "provide liquidity",
            "providing liquidity",
            "liquidity provider",
            "liquidity pool",
            "liquidity pools",
        ],
    ):
        return False

    vault = contains_any(
        text,
        ["vault", "vaults"],
    )

    # Require yield/LP context, not generic "strategy" (trading agents).
    vault_context = contains_any(
        text,
        [
            "yield",
            "liquidity provider",
            "liquidity pool",
            "deposit assets",
            "deposit into",
            "earn yield",
            "apy",
            "apr",
            "farm",
            "farming",
            "rate-market yield",
            "rewards hub",
        ],
    )

    return bool(
        vault
        and vault_context
    )


def has_strong_liquidity_mechanism(text):
    text = normalize_text(text)

    return contains_any(
        text,
        [
            "provide liquidity",
            "providing liquidity",
            "liquidity provider",
            "liquidity pool",
            "liquidity pools",
            "liquidity vault",
            "liquidity vaults",
            "liquidity for trading fees",
            "liquidity for market activity",
            "yield platform",
            "rate-market yield",
            "liquidity mining",
            "yield farming",
            "rewards hub",
            "keep liquidity in range",
            "keeping liquidity in range",
            "concentrated liquidity",
            "curated yield",
            "yield strategies",
        ],
    )


# ============================================================
# ACTIVITY
# ============================================================

def is_product_capability_only(text):
    text = normalize_text(text)

    # Only clear hardware/wallet-product marketing — not airdrop guides
    # that merely say "connect your wallet".
    product_context = contains_any(
        text,
        [
            "hardware wallet",
            "wallet device",
            "cold wallet",
            "hardware device",
            "smartcard",
            "card-based wallet",
            "wallet company",
            "hardware wallets",
            "wallet manufacturers",
            "manufactures smartcard",
        ],
    )

    if not product_context:
        return False

    capability_signals = [
        "store",
        "send",
        "receive",
        "buy",
        "swap",
        "swapping",
        "stake",
        "staking",
        "manage tokens",
        "token management",
        "hold tokens",
    ]

    if len(
        keyword_matches(
            text,
            capability_signals,
        )
    ) < 2:
        return False

    # Real airdrop participation mechanisms — not wallet promos.
    genuine_campaign_context = contains_any(
        text,
        [
            "earn points",
            "earn xp",
            "points campaign",
            "points program",
            "quest",
            "quests",
            "mission",
            "missions",
            "join the testnet",
            "provide liquidity",
            "liquidity mining",
            "claim airdrop",
            "retroactive airdrop",
            "snapshot date",
            "users must",
            "you must complete",
        ],
    )

    if genuine_campaign_context:
        return False

    return True


def has_media_participation(text):
    return contains_any(
        normalize_text(text),
        [
            "upload photos",
            "upload photo",
            "upload videos",
            "upload video",
            "upload media",
            "upload original photos",
            "upload original photo",
            "upload original videos",
            "upload original video",
            "upload original media",
            "submit media",
            "submit original media",
            "submit a batch",
            "submit batch",
        ],
    )


def has_wallet_activity(text):
    return contains_any(
        normalize_text(text),
        [
            "connect wallet",
            "connect your wallet",
            "connect wallet and",
            "connect your wallet and",
            "wallet connect",
        ],
    )


def has_hold_to_earn_activity(text):
    text = normalize_text(text)

    if not contains_any(
        text,
        [
            "hold-to-earn",
            "hold to earn",
        ],
    ):
        return False

    if has_real_holder_requirement(text):
        return False

    return contains_any(
        text,
        [
            "campaign",
            "program",
            "participate",
            "participation",
            "activities",
            "activity",
            "complete",
            "earn",
            "join",
            "users",
            "user",
        ],
    )


def has_current_activity_requirement(text):
    text = normalize_text(text)

    if (
        has_media_participation(text)
        or has_wallet_activity(text)
        or has_hold_to_earn_activity(text)
    ):
        return True

    return contains_any(
        text,
        ACTIVITY_SIGNALS,
    )


def has_concrete_activity(text):
    text = normalize_text(text)

    if (
        has_media_participation(text)
        or has_wallet_activity(text)
        or has_hold_to_earn_activity(text)
    ):
        return True

    return bool(
        keyword_matches(
            text,
            CONCRETE_ACTIVITY_SIGNALS,
        )
    )


def has_real_activity_participation(text):
    text = normalize_text(text)

    if (
        has_media_participation(text)
        or has_wallet_activity(text)
        or has_hold_to_earn_activity(text)
    ):
        return True

    participation_patterns = [
        "users can",
        "users may",
        "users must",
        "users need",
        "you can",
        "you may",
        "you must",
        "you need",
        "complete",
        "participate",
        "use the",
        "use ",
        "earn",
        "claim",
        "join",
        "trade on",
        "trade assets",
        "swap tokens",
        "swap assets",
        "bridge tokens",
        "bridge assets",
        "deposit",
        "withdraw",
        "play",
        "upload",
        "submit",
        "run",
        "contribute",
        "invite",
        "referral",
        "quest",
        "mission",
        "task",
        "open a",
        "open long",
        "open short",
        "place",
        "monitor",
        "fund",
        "copy trade",
        "go long",
        "go short",
        "buy yes",
        "buy no",
        "trade 24/7",
        "deposit usdc",
    ]

    for sentence in split_sentences(text):

        if (
            contains_any(
                sentence,
                CONCRETE_ACTIVITY_SIGNALS,
            )
            and contains_any(
                sentence,
                participation_patterns,
            )
        ):
            return True

    return False


def activity_match_count(text):
    return len(
        unique(
            keyword_matches(
                text,
                ACTIVITY_SIGNALS,
            )
        )
    )


def has_primary_swap_activity(text):
    text = normalize_text(text)

    return contains_any(
        text,
        [
            "main product is akka swap",
            "main product is",
            "primary product",
            "swap aggregator",
            "routes trades across liquidity sources",
            "trading assistant",
            "ai-native trading assistant",
            "go long",
            "go short",
            "buy yes",
            "buy no",
            "copy trades",
            "monitor markets",
            "trade 24/7",
        ],
    )


# ============================================================
# NEWS
# ============================================================

def is_incidental_news_activity(text):
    text = normalize_text(text)

    news_context = contains_any(
        text,
        NEWS_SIGNALS,
    )

    if not news_context:
        return False

    if has_real_activity_participation(text):
        return False

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

    return not contains_any(
        text,
        opportunity_signals,
    )


def has_news_activity_sentence(text):
    for sentence in split_sentences(text):

        if not contains_any(
            sentence,
            CONCRETE_ACTIVITY_SIGNALS,
        ):
            continue

        participation_patterns = [
            "users can",
            "users may",
            "users must",
            "users need",
            "you can",
            "you may",
            "you must",
            "you need",
            "complete",
            "participate",
            "use the",
            "use ",
            "earn",
            "claim",
            "join",
            "trade on",
            "trade assets",
            "swap tokens",
            "swap assets",
            "bridge tokens",
            "bridge assets",
            "provide liquidity",
            "deposit",
            "withdraw",
            "play",
            "upload",
            "run the",
            "run a node",
            "contribute",
            "invite",
            "referral",
            "quest",
            "mission",
            "task",
        ]

        if contains_any(
            sentence,
            participation_patterns,
        ):
            return True

    return False


def is_news_only(text):
    text = normalize_text(text)

    if not text:
        return False

    if not contains_any(
        text,
        NEWS_SIGNALS,
    ):
        return False

    # ------------------------------------------------------------
    # SNAPSHOT IS ACTIVITY CONTEXT
    # (checked BEFORE the incidental-news early return, so a bare
    # "snapshot ... announced" sentence isn't short-circuited into
    # Other before this exception has a chance to fire)
    # ------------------------------------------------------------

    if contains_any(
        text,
        [
            "snapshot",
            "snapshot date",
            "snapshot scheduled",
            "snapshot was announced",
        ],
    ):
        return False

    if is_incidental_news_activity(text):
        return True

    if has_real_activity_participation(text):
        return False

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

    if has_news_activity_sentence(text):
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
        + keyword_matches(
            text,
            EARLY_USER_RETROACTIVE_SIGNALS,
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

    retroactive = has_real_retroactive_requirement(
        text
    )

    holder_requirement = has_real_holder_requirement(
        text
    )

    bounty_requirement = has_real_bounty_requirement(
        text
    )

    testnet_context = has_explicit_testnet_context(
        text
    )

    points_allocation = has_points_allocation(
        text
    )

    points_campaign = has_points_campaign(
        text
    )

    liquidity_requirement = has_real_liquidity_requirement(
        text
    )

    activity_requirement = has_current_activity_requirement(
        text
    )

    strong_testnet_participation = (
        has_strong_testnet_participation(text)
    )

    strong_points_mechanism = (
        has_strong_points_mechanism(text)
    )

    strong_liquidity_mechanism = (
        has_strong_liquidity_mechanism(text)
    )

    real_activity_participation = (
        has_real_activity_participation(text)
    )

    product_capability_only = (
        is_product_capability_only(text)
    )

    primary_swap_activity = (
        has_primary_swap_activity(text)
    )

    evidence["Retroactive"] = (
        retro
        if retroactive
        else []
    )

    evidence["Holder"] = (
        holder
        if holder_requirement
        else []
    )

    evidence["Bounty"] = (
        bounty
        if bounty_requirement
        else []
    )

    evidence["Testnet"] = (
        testnet
        if testnet_context
        else []
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

    if strong_testnet_participation:
        evidence["Testnet"].append(
            "testnet participation"
        )

    if strong_points_mechanism:
        evidence["Points"].append(
            "points campaign mechanism"
        )

    if strong_liquidity_mechanism:
        evidence["Liquidity"].append(
            "liquidity mechanism"
        )

    if real_activity_participation:
        evidence["Activity"].append(
            "real activity participation"
        )

    if primary_swap_activity:
        evidence["Activity"].append(
            "primary swap/trading activity"
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

        "strong_testnet_participation":
            strong_testnet_participation,

        "strong_points_mechanism":
            strong_points_mechanism,

        "strong_liquidity_mechanism":
            strong_liquidity_mechanism,

        "real_activity_participation":
            real_activity_participation,

        "product_capability_only":
            product_capability_only,

        "primary_swap_activity":
            primary_swap_activity,

        "concrete_activity":
            has_concrete_activity(text),

        "activity_count":
            activity_match_count(text),

        "news_only":
            is_news_only(text),

        "historical_distribution_only":
            has_historical_distribution_only(text),
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
                "testnet portal",
                "hertzflow testnet",
                "bnb smart chain testnet",
                "ekiden testnet",
                "canton testnet",
                "testnet trading",
                "trade on the testnet",
                "trade on testnet",
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


def calculate_confidence(analysis, category):

    scores = calculate_scores_from_analysis(
        analysis
    )

    score = scores.get(
        category,
        0,
    )

    if score >= 100:
        return 0.95

    if score >= 80:
        return 0.85

    if score >= 60:
        return 0.70

    if score >= 40:
        return 0.55

    if score >= 20:
        return 0.45

    return 0.35


# ============================================================
# CATEGORY RESOLUTION
# ============================================================

def resolve_category(analysis):
    """
    Resolve the PRIMARY airdrop participation mechanism.

    Priority philosophy:

    1. News/product-only content is Other.
    2. Explicit bounty/work mechanisms beat generic XP/points.
    3. Explicit liquidity participation can override testnet when
       testnet is only the environment.
    4. Explicit testnet participation beats generic signals.
    5. Genuine retroactive eligibility requires historical context.
    6. Holder requires an actual holding/snapshot mechanism.
    7. Points requires points/XP to be the reward mechanism.
    8. Liquidity requires actual liquidity/staking/yield participation.
    9. Concrete current user activity falls to Activity.
    10. Context-only snapshot/retroactive language falls to Activity.
    11. Future/speculative retroactive language falls to Other.
    """

    text = analysis.get(
        "text",
        "",
    ).lower()

    # ------------------------------------------------------------
    # 1. NON-AIRDROP / NEWS / PRODUCT CONTENT
    # ------------------------------------------------------------

    if analysis.get("news_only"):
        return "Other"

    if analysis.get("product_capability_only"):
        return "Other"

    # ------------------------------------------------------------
    # 2. BOUNTY / WORK MECHANISM
    # ------------------------------------------------------------

    if analysis.get("bounty"):
        return "Bounty"

    bounty_override_signals = (
        "bug bounty",
        "bug bounties",
        "bounty program",
        "bounty campaign",
        "content bounty",
        "bounties",
        "submit a bug",
        "report a bug",
        "security researcher",
        "find vulnerabilities",
        "complete tasks for rewards",
    )

    if any(
        signal in text
        for signal in bounty_override_signals
    ):
        return "Bounty"

    # ------------------------------------------------------------
    # 3. TESTNET ENVIRONMENT + LIQUIDITY
    # ------------------------------------------------------------

    # Testnet can describe the environment rather than the
    # actual participation mechanism.
    #
    # If users MUST provide liquidity to participate, the
    # primary mechanism is Liquidity.

    testnet_liquidity_signals = (
        "must provide liquidity",
        "provide liquidity to participate",
        "provide liquidity to join",
        "provide liquidity in order to participate",
        "provide liquidity in order to join",
    )

    if (
        "testnet" in text
        and any(
            signal in text
            for signal in testnet_liquidity_signals
        )
    ):
        return "Liquidity"

    # ------------------------------------------------------------
    # 4. STRONG TESTNET PARTICIPATION
    # ------------------------------------------------------------

    # Testnet can be only the environment. If XP/points is clearly
    # the reward framework for this project, prefer Points later.

    points_is_reward_framework = contains_any(
        text,
        [
            "xp system",
            "participation tracked via xp",
            "points program",
            "points campaign",
            "earn xp",
            "earning xp",
            "accumulate xp",
            "points convert into",
            "points determine",
        ],
    )

    if analysis.get(
        "strong_testnet_participation"
    ):
        if not (
            points_is_reward_framework
            and (
                analysis.get("strong_points_mechanism")
                or analysis.get("points_campaign")
                or analysis.get("points_allocation")
            )
        ):
            return "Testnet"

    explicit_testnet_campaign = (
        "testnet campaign",
        "testnet rewards",
        "testnet airdrop",
        "testnet program",
        "testnet participation",
        "join the testnet",
        "participate in the testnet",
        "use the testnet",
        "testnet users",
        "testnet user",
        "public testnet",
        "testnet is live",
        "testnet is now live",
        "testnet phase",
        "testnet network",
        "test tokens",
        "test token",
        "faucet on the testnet",
        "faucet for the testnet",
    )

    if any(
        signal in text
        for signal in explicit_testnet_campaign
    ):
        if not (
            points_is_reward_framework
            and (
                analysis.get("strong_points_mechanism")
                or analysis.get("points_campaign")
                or analysis.get("points_allocation")
            )
        ):
            return "Testnet"

    # ------------------------------------------------------------
    # 5. HOLD-TO-EARN / CURRENT ACTIVITY
    # ------------------------------------------------------------

    hold_to_earn_activity = (
        "hold-to-earn",
        "hold to earn",
        "earn by holding",
        "earn rewards by using",
        "earn rewards through activity",
    )

    if any(
        signal in text
        for signal in hold_to_earn_activity
    ):
        return "Activity"

    # ------------------------------------------------------------
    # 6. REAL RETROACTIVE
    # ------------------------------------------------------------

    if analysis.get("retroactive"):
        return "Retroactive"

    confirmed_retroactive = (
        "past users are eligible",
        "past users qualify",
        "previous users are eligible",
        "previous users qualify",
        "historical users are eligible",
        "historical users qualify",
        "past participants are eligible",
        "past participants qualify",
        "previous participants are eligible",
        "previous participants qualify",
        "users who previously participated are eligible",
        "users who previously used the protocol are eligible",
        "users who previously used the platform are eligible",
        "previous users can claim",
        "past users can claim",
        "historical users can claim",
        "users who previously interacted can claim",
    )

    if any(
        signal in text
        for signal in confirmed_retroactive
    ):
        return "Retroactive"

    # ------------------------------------------------------------
    # 7. HOLDER
    # ------------------------------------------------------------

    real_holder_signals = (
        "token holders are eligible",
        "token holders receive",
        "token holders qualify",
        "holders are eligible",
        "holders will receive",
        "holders qualify",
        "must hold",
        "minimum balance",
        "minimum token balance",
        "hold at least",
        "holding requirement",
        "eligible holder",
        "eligible holders",
        "holder snapshot",
        "nft holders",
        "sbt holders",
        "hold nfts",
        "collect sbts",
    )

    # Avoid product-access phrases like "holders receive early access".
    weak_holder_access = contains_any(
        text,
        [
            "holders receive early access",
            "holders receive access",
            "holders get early access",
            "holders get access",
        ],
    )

    if (
        any(
            signal in text
            for signal in real_holder_signals
        )
        and not weak_holder_access
    ):
        return "Holder"

    if (
        analysis.get("holder")
        and not analysis.get("liquidity")
        and not weak_holder_access
    ):
        return "Holder"

    # NFT/SBT holding as eligibility even when vault shares are mentioned.
    if (
        analysis.get("holder")
        and contains_any(
            text,
            [
                "nft",
                "nfts",
                "sbt",
                "sbts",
                "holders",
            ],
        )
        and contains_any(
            text,
            [
                "vault shares",
                "maintain vault shares",
            ],
        )
    ):
        return "Holder"

    # ------------------------------------------------------------
    # 8. POINTS
    # ------------------------------------------------------------

    points_mechanism_signals = (
        "points program",
        "points campaign",
        "points system",
        "points season",
        "points leaderboard",
        "earn points",
        "earn xp",
        "accumulate points",
        "accumulate xp",
        "points determine",
        "points determine allocation",
        "points convert into",
        "points will convert into",
        "points translate into",
        "points result in",
        "points lead to rewards",
        "xp determines",
        "xp determine",
        "xp converts into",
        "xp convert into",
        "xp system",
        "participation tracked via xp",
    )

    has_points_mechanism = any(
        signal in text
        for signal in points_mechanism_signals
    )

    # ------------------------------------------------------------
    # LIQUIDITY IS PRIMARY; POINTS MAY ONLY SCORE IT
    # ------------------------------------------------------------

    # Generic points campaigns that merely list LP as one earn action
    # remain Points ("trade and provide liquidity to earn points").
    generic_points_via_lp = contains_any(
        text,
        [
            "provide liquidity to earn points",
            "providing liquidity to earn points",
            "provide liquidity and trade to earn points",
            "trade and provide liquidity to earn points",
            "trade and provide liquidity to earn",
            "provide liquidity and earn points",
        ],
    )

    # Strong LP product framing: vaults / in-range LP / yield products.
    # Avoid bare "deposit into vault" — trading venues often have vaults.
    lp_product_primary = contains_any(
        text,
        [
            "liquidity vault",
            "liquidity vaults",
            "mlp vault",
            "keep liquidity in range",
            "keeping liquidity in range",
            "concentrated liquidity",
            "liquidity providers can",
            "curated yield",
            "yield strategies",
            "yield vault",
            "yield vaults",
            "rate-market",
            "must provide liquidity",
            "provide liquidity to participate",
            "deposit into the mlp",
            "liquidity provider (mlp)",
            "meridian liquidity provider",
        ],
    )

    if (
        lp_product_primary
        and not generic_points_via_lp
        and (
            analysis.get("points_allocation")
            or analysis.get("points_campaign")
            or has_points_mechanism
            or analysis.get("liquidity")
            or analysis.get("strong_liquidity_mechanism")
        )
    ):
        return "Liquidity"

    if (
        analysis.get("liquidity")
        and analysis.get("strong_liquidity_mechanism")
        and not generic_points_via_lp
        and not (
            analysis.get("points_allocation")
            or analysis.get("points_campaign")
            or has_points_mechanism
        )
    ):
        return "Liquidity"

    # ------------------------------------------------------------
    # POINTS ALLOCATION OVERRIDE
    # ------------------------------------------------------------

    # If points determine the actual token/reward allocation,
    # and liquidity is NOT the primary action, Points wins.

    if analysis.get("points_allocation"):
        return "Points"

    points_allocation_signals = (
        "points determine",
        "points determine allocation",
        "points determine your token allocation",
        "points convert into",
        "points will convert into",
        "points translate into",
        "points result in",
        "points lead to rewards",
        "xp determines",
        "xp determine",
        "xp converts into",
        "xp convert into",
    )

    if any(
        signal in text
        for signal in points_allocation_signals
    ):
        return "Points"

    # ------------------------------------------------------------
    # ACTIVITY + POINTS
    # ------------------------------------------------------------

    # Points earned as a SECONDARY / SIDE reward for performing
    # a normal activity remain Activity.
    #
    # Example:
    #   "Trade assets and earn points as a side reward."
    #
    # PRIMARY mechanism = trading
    # SECONDARY reward = points
    #
    # Therefore:
    #   Activity > Points
    #
    # But:
    #   "Earn points by completing tasks during the points campaign."
    #
    # has Points as the actual reward mechanism and should remain
    # Points.

    side_reward_points_context = (
        "as a side reward",
        "as side rewards",
        "side reward",
        "side rewards",
        "secondary reward",
        "secondary rewards",
        "bonus points",
        "bonus xp",
        "points as a side",
        "xp as a side",
        "points as an additional",
        "xp as an additional",
    )

    if (
        (
            analysis.get("primary_swap_activity")
            or analysis.get("real_activity_participation")
            or analysis.get("concrete_activity")
        )
        and contains_any(
            text,
            [
                "points",
                "xp",
            ],
        )
        and contains_any(
            text,
            side_reward_points_context,
        )
    ):
        return "Activity"

    # ------------------------------------------------------------
    # NORMAL ACTIVITY + POINTS
    # ------------------------------------------------------------

    if (
        analysis.get("primary_swap_activity")
        or analysis.get("real_activity_participation")
        or analysis.get("concrete_activity")
    ):

        activity_points_context = contains_any(
            text,
            [
                "trade and earn points",
                "trade to earn points",
                "trading and earn points",
                "trading to earn points",
                "trade assets and earn points",
                "trade assets to earn points",
                "trading assets and earn points",
                "trading assets to earn points",

                "swap and earn points",
                "swap to earn points",
                "swapping and earn points",
                "swapping to earn points",

                "earn points by trading",
                "earn points through trading",
                "earn points from trading",

                "earn points by swapping",
                "earn points through swapping",
                "earn points from swapping",

                "points for trading",
                "points from trading",

                "points for swaps",
                "points from swaps",

                "bridge and earn points",
                "bridge to earn points",
                "bridging and earn points",

                "quest and earn points",
                "quests and earn points",

                "complete tasks and earn points",
                "complete tasks to earn points",
            ],
        )

        if activity_points_context:
            return "Activity"

    if has_points_mechanism:

        activity_with_points = (
            "trade and earn points",
            "trade to earn points",
            "trade assets and earn points",
            "trade assets to earn points",

            "trading and earn points",
            "trading to earn points",
            "trading assets and earn points",

            "swap and earn points",
            "swap to earn points",
            "swapping and earn points",

            "bridge and earn points",
            "bridge to earn points",

            "quest and earn points",
            "quests and earn points",

            "complete tasks and earn points",
            "complete tasks to earn points",

            "provide liquidity and earn points",
        )

        if any(
            signal in text
            for signal in activity_with_points
        ):
            return "Activity"

        return "Points"

    if analysis.get("points_campaign"):
        return "Points"

    # ------------------------------------------------------------
    # 9. LIQUIDITY
    # ------------------------------------------------------------

    liquidity_mechanism_signals = (
        "provide liquidity",
        "providing liquidity",
        "liquidity provider",
        "liquidity providers",
        "liquidity pool",
        "liquidity pools",
        "liquidity mining",
        "yield farming",
        "earn yield",
        "earning yield",
        "deposit into a vault",
        "deposit into vault",
        "deposit into the vault",
        "liquidity vault",
        "provide lp",
        "lp position",
        "lp rewards",
        "staking rewards",
        "stake tokens",
        "staking pool",
    )

    # Swap aggregators mentioning liquidity routes are Activity.
    if (
        analysis.get("primary_swap_activity")
        and not analysis.get("strong_liquidity_mechanism")
    ):
        pass
    elif any(
        signal in text
        for signal in liquidity_mechanism_signals
    ):
        return "Liquidity"

    if analysis.get("liquidity") and not (
        analysis.get("primary_swap_activity")
        and not analysis.get("strong_liquidity_mechanism")
    ):
        return "Liquidity"

    # ------------------------------------------------------------
    # 10. CONCRETE CURRENT ACTIVITY
    # ------------------------------------------------------------

    if analysis.get("concrete_activity"):
        return "Activity"

    if analysis.get("activity"):
        return "Activity"

    if analysis.get("real_activity_participation"):
        return "Activity"

    # ------------------------------------------------------------
    # 11. GENERIC TESTNET FALLBACK
    # ------------------------------------------------------------

    if analysis.get("testnet"):
        return "Testnet"

    # ------------------------------------------------------------
    # 12. SPECULATIVE / FUTURE RETROACTIVE
    # ------------------------------------------------------------

    # Future/speculative retroactive language does not prove
    # a real retroactive mechanism.

    speculative_retroactive_signals = (
        "future retroactive",
        "future retroactive airdrop",
        "may launch a future retroactive",
        "could become relevant for a future retroactive",
        "might launch a future retroactive",
        "possible future retroactive",
        "potential future retroactive",
    )

    if contains_any(
        text,
        speculative_retroactive_signals,
    ):
        return "Other"

    # ------------------------------------------------------------
    # 13. CONTEXTUAL ACTIVITY FALLBACK
    # ------------------------------------------------------------

    # Words such as snapshot, retroactive, and early users
    # alone do not prove Holder or Retroactive.
    #
    # If no stronger mechanism exists, classify them as Activity.

    contextual_activity_signals = (
        "early users",
        "early user",
        "early adopters",
        "early adopter",
        "early participants",
        "early participant",
        "retroactive",
        "snapshot",
        "snapshot date",
        "snapshot scheduled",
        "snapshot was announced",
    )

    if contains_any(
        text,
        contextual_activity_signals,
    ):
        return "Activity"

    # ------------------------------------------------------------
    # 14. FINAL FALLBACK
    # ------------------------------------------------------------

    return "Other"


# ============================================================
# CLASSIFICATION ENTRY POINT
# ============================================================

def classify_with_details(
    candidate_or_name,
    description="",
):
    """
    Primary entry point used by calibration,
    process_results and tests.

    Accepts either:
        - a full candidate dict, or
        - (name, description) for backwards compatibility.
    """

    if isinstance(
        candidate_or_name,
        dict,
    ):
        candidate = candidate_or_name

    else:
        candidate = {
            "name": candidate_or_name,
            "description": description,
        }

    analysis = analyze_candidate(
        candidate
    )

    category = resolve_category(
        analysis
    )

    scores = calculate_scores_from_analysis(
        analysis
    )

    confidence = calculate_confidence(
        analysis,
        category,
    )

    mechanism_map = {
        "Retroactive": "Historical participation",
        "Holder": "Token/asset holding",
        "Bounty": "Work/bounty participation",
        "Testnet": "Testnet participation",
        "Points": "Points/XP reward mechanism",
        "Liquidity": "Liquidity/staking/yield participation",
        "Activity": "Current product activity",
        "Other": "No qualifying participation mechanism",
    }

    return {
        "category": category,
        "airdrop_type": category,
        "confidence": confidence,
        "mechanism": mechanism_map.get(
            category,
            "Unknown",
        ),
        "evidence": analysis["evidence"],
        "scores": scores,
        "analysis": analysis,
    }


# ============================================================
# RESULT PROCESSING
# ============================================================

def process_results(results):

    processed = []

    if not isinstance(
        results,
        list,
    ):
        return processed

    for candidate in results:

        if not isinstance(
            candidate,
            dict,
        ):
            continue

        try:
            details = classify_with_details(
                candidate
            )

            item = dict(candidate)

            item["airdrop_type"] = details[
                "category"
            ]

            item["category"] = details[
                "category"
            ]

            item["category_confidence"] = (
                details["confidence"]
            )

            item["category_mechanism"] = (
                details["mechanism"]
            )

            item["category_evidence"] = (
                details["evidence"]
            )

            processed.append(item)

        except Exception as error:
            print(
                f"⚠️ Classification error for "
                f"{candidate.get('name', 'Unknown')}: "
                f"{error}"
            )

    return processed


def get_category_distribution(results):

    distribution = {
        category: 0
        for category in AIRDROP_TYPE_PRIORITY
    }

    for result in results:

        if not isinstance(
            result,
            dict,
        ):
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
                "Historical users are eligible "
                "for the airdrop."
            ),
        },
        "Retroactive",
    ),

    (
        "Early Users Alone",
        {
            "name": "Early Users",
            "description": (
                "Early users can participate "
                "in the program."
            ),
        },
        "Activity",
    ),

    (
        "Retroactive Word Alone",
        {
            "name": "Retroactive",
            "description": (
                "The project mentions a "
                "retroactive mechanism."
            ),
        },
        "Activity",
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
                "A snapshot will determine "
                "eligible token holders."
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
        "Activity",
    ),

    (
        "Token Snapshot Alone",
        {
            "name": "Snapshot",
            "description": (
                "The token snapshot is scheduled."
            ),
        },
        "Activity",
    ),

    (
        "Holder Can Claim",
        {
            "name": "Holder Airdrop",
            "description": (
                "Eligible holders can claim "
                "their allocation."
            ),
        },
        "Holder",
    ),

    (
        "Bug Bounty",
        {
            "name": "Bug Bounty",
            "description": (
                "Join the bug bounty program "
                "and earn rewards."
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
                "Join the public testnet "
                "and complete transactions."
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
                "Join the testnet, provide liquidity "
                "and earn points for participation."
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
                "Claim faucet tokens and "
                "complete transactions."
            ),
        },
        "Activity",
    ),

    (
        "Points Allocation",
        {
            "name": "Points",
            "description": (
                "Earn points. Your points determine "
                "your token allocation."
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
                "Deposit assets into the vault "
                "to earn yield."
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
                "Bitcoin rises as investors discuss ETF "
                "flows and market conditions."
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
                "Early users may receive a future "
                "retroactive airdrop."
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
                "Future users could potentially benefit "
                "from another one."
            ),
        },
        "Other",
    ),

    (
        "Gaming Activity",
        {
            "name": "Game",
            "description": (
                "Play games, complete daily quests, "
                "maintain streaks and earn rewards."
            ),
        },
        "Activity",
    ),

    (
        "DePIN Activity",
        {
            "name": "DePIN",
            "description": (
                "Run the Core Client and contribute "
                "internet bandwidth to earn rewards."
            ),
        },
        "Activity",
    ),

    (
        "Media Activity",
        {
            "name": "Scout",
            "description": (
                "Upload original photos and videos, "
                "submit them and enter your payout wallet."
            ),
        },
        "Activity",
    ),

    (
        "Points Conversion",
        {
            "name": "Points",
            "description": (
                "Users earn points. Points convert "
                "into token allocation."
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
                "The application is on testnet and users "
                "must provide liquidity to participate."
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
                "Our new product launches with a beautiful "
                "platform for users."
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
                "Early activity could become relevant "
                "for a future retroactive airdrop."
            ),
        },
        "Activity",
    ),

    (
        "Future Retroactive Alone",
        {
            "name": "Protocol",
            "description": (
                "The project may launch a future "
                "retroactive airdrop."
            ),
        },
        "Other",
    ),

    (
        "Historical Claim",
        {
            "name": "Airdrop",
            "description": (
                "Users who previously participated "
                "can claim rewards."
            ),
        },
        "Retroactive",
    ),

    (
        "Gaming Mining",
        {
            "name": "Kintara",
            "description": (
                "Play the game, mine resources, fish "
                "and fight to earn rewards."
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
                "The market is reacting to increased "
                "trading activity."
            ),
        },
        "Other",
    ),

    (
        "Early Users Earn Points Is Not Retroactive",
        {
            "name": "Campaign",
            "description": (
                "Early users earn points through quests "
                "and platform activity during season one."
            ),
        },
        "Points",
    ),

    (
        "Other Project Points Program",
        {
            "name": "The Index",
            "description": (
                "Users can trade tokenized stocks on the protocol. "
                "Lighter also runs a Points Airdrop Program "
                "for its own users."
            ),
        },
        "Activity",
    ),

    (
        "Vault Mention In Passing",
        {
            "name": "Aggregator",
            "description": (
                "Users can swap tokens through the aggregator. "
                "The product also mentions a strategy vault."
            ),
        },
        "Activity",
    ),

    (
        "Hardware Wallet Promo Is Other",
        {
            "name": "Tangem",
            "description": (
                "Tangem is a hardware wallet company. "
                "The wallet lets users store, send, receive "
                "and swap crypto. Get 20% off and join the giveaway."
            ),
        },
        "Other",
    ),

    (
        "Testnet XP Framework Is Points",
        {
            "name": "Checkpoint",
            "description": (
                "The testnet campaign is live. Participation "
                "is tracked via an XP system. Earn XP by trading "
                "on the orderbook and completing quests."
            ),
        },
        "Points",
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
                f"❌ FAIL | {label} → "
                f"{actual} (expected {expected})"
            )

            print(
                f"   Evidence: "
                f"{details.get('evidence')}"
            )

            print(
                f"   Scores: "
                f"{details.get('scores')}"
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

    return total_passed, total_failed


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

    if not isinstance(
        discovered,
        list,
    ):

        print(
            "❌ Scanner returned invalid data."
        )

        return []

    print(
        f"📡 Discovered: {len(discovered)}"
    )

    qualified = []

    for candidate in discovered:

        if not isinstance(
            candidate,
            dict,
        ):
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
    print(
        "🚀 AirdropRadar Category Classifier"
    )

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


    # Compatibility function for category backfill

def detect_airdrop_type(airdrop):
    details = classify_with_details(airdrop)
    return details["category"]

# ============================================================
# LIVE SCAN COMPATIBILITY WRAPPER
# ============================================================

def run_scan():
    """
    Run the full AirdropRadar pipeline:

    SCAN → QUALIFY → CLASSIFY → VERIFY → SCORE
    """

    from scanner import scan
    from verifier import verify_candidate
    from scorer import calculate_score

    print("🪂 Starting full AirdropRadar scan...")

    # 1. DISCOVER
    raw_results = scan()

    print(f"🔎 Discovered: {len(raw_results)} candidate(s).")

    # 2. QUALIFY
    qualified_results = []

    for candidate in raw_results:
        try:
            qualification = qualify_candidate(candidate)

            if not isinstance(qualification, dict):
                print(
                    f"⚠️ Invalid qualification result for "
                    f"{candidate.get('name', 'Unknown')}"
                )
                continue

            if not qualification.get("qualified"):
                continue

            qualified_results.append(candidate)

        except Exception as error:
            print(
                f"⚠️ Qualification error for "
                f"{candidate.get('name', 'Unknown')}: {error}"
            )

    print(
        f"✅ Qualified: {len(qualified_results)} candidate(s)."
    )

    # 3. CLASSIFY
    processed_results = process_results(qualified_results)

    print(
        f"🏷️ Classified: {len(processed_results)} candidate(s)."
    )

    # 4. VERIFY
    verified_results = []

    for result in processed_results:
        try:
            verification = verify_candidate(result)

            if isinstance(verification, dict):
                result.update(verification)

            verified_results.append(result)

        except Exception as error:
            print(
                f"⚠️ Verification error for "
                f"{result.get('name', 'Unknown')}: {error}"
            )

            # Keep the result.
            # The scorer treats missing verification as unavailable.
            verified_results.append(result)

    print(
        f"🔐 Verified/enriched: {len(verified_results)} candidate(s)."
    )

    # 5. SCORE
    scored_results = []

    for result in verified_results:
        try:
            scored = calculate_score(result)

            if isinstance(scored, dict):
                result.update(scored)

            scored_results.append(result)

        except Exception as error:
            print(
                f"⚠️ Scoring error for "
                f"{result.get('name', 'Unknown')}: {error}"
            )

            # Keep the result even if scoring fails.
            result.setdefault("score", 0)

            scored_results.append(result)

    print(
        f"✅ Full scan complete: "
        f"{len(scored_results)} result(s)."
    )

    return scored_results