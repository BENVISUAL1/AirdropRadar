"""
AirdropRadar Qualification Engine

Purpose:
    Decide whether a discovered RSS item is a genuine actionable
    airdrop/reward opportunity or merely crypto/news content.

Design:
    - Specialized airdrop sources are handled more permissively.
    - General crypto/news sources require stronger evidence.
    - News-only articles are rejected.
    - Speculation/rumors are rejected.
    - Testnet mentions without a reward mechanism are rejected.
    - Protocol/product announcements without user rewards are rejected.
    - Funding, partnerships, market updates, and regulatory news are rejected.
    - AirdropAlert is treated as an opportunity-discovery source, so
      legitimate listings do not need to contain every action/reward keyword.
"""

import re


# ============================================================
# SOURCE RULES
# ============================================================

SPECIALIZED_OPPORTUNITY_SOURCES = [
    "airdropalert",
    "airdrop alert",
]


GENERAL_NEWS_SOURCES = [
    "cointelegraph",
    "coindesk",
    "decrypt",
    "theblock",
    "the block",
    "coinmarketcap",
    "coinmarketcap community",
]


# ============================================================
# STRONG AIRDROP / REWARD SIGNALS
# ============================================================

STRONG_AIRDROP_SIGNALS = [
    "airdrop",
    "token airdrop",
    "crypto airdrop",
    "claim tokens",
    "claim token",
    "claim rewards",
    "claim reward",
    "free tokens",
    "free token",
    "airdrop campaign",
    "airdrop program",
    "airdrop eligibility",
    "airdrop eligible",
    "eligible for airdrop",
    "eligible users",
    "reward campaign",
    "rewards campaign",
    "token rewards",
    "token reward",
    "points rewards",
    "points campaign",
    "points program",
    "points system",
    "earn points",
    "farm points",
    "retroactive rewards",
    "retroactive airdrop",
    "retroactive reward",
    "holder rewards",
    "holder reward",
    "community rewards",
    "user rewards",
    "trading rewards",
    "liquidity rewards",
    "testnet rewards",
    "testnet airdrop",
    "testnet reward",
]


# ============================================================
# ACTION SIGNALS
# ============================================================

ACTION_SIGNALS = [
    "participate",
    "participation",
    "join the campaign",
    "join campaign",
    "complete tasks",
    "complete task",
    "perform tasks",
    "perform task",
    "do tasks",
    "do task",
    "earn points",
    "farm points",
    "collect points",
    "claim rewards",
    "claim reward",
    "claim tokens",
    "claim token",
    "use the protocol",
    "use the app",
    "use the platform",
    "interact with",
    "interact on",
    "make transactions",
    "make a transaction",
    "complete transactions",
    "complete a transaction",
    "bridge",
    "bridge assets",
    "bridge tokens",
    "swap",
    "make swaps",
    "trade",
    "trade on",
    "provide liquidity",
    "provide liquidity to",
    "add liquidity",
    "stake",
    "stake tokens",
    "hold tokens",
    "hold token",
    "hold nft",
    "mint",
    "mint nft",
    "refer users",
    "referral",
    "invite friends",
    "invite users",
    "sign up",
    "register",
    "connect wallet",
    "connect your wallet",
    "complete quests",
    "complete a quest",
    "complete quests",
    "quests",
    "quest",
]


# ============================================================
# REWARD CONTEXT SIGNALS
# ============================================================

REWARD_CONTEXT_SIGNALS = [
    "reward",
    "rewards",
    "points",
    "points program",
    "points campaign",
    "xp",
    "xp points",
    "tokens",
    "token rewards",
    "token allocation",
    "allocation",
    "incentives",
    "incentive",
    "prizes",
    "prize",
    "earn",
    "earning",
    "eligible",
    "eligibility",
    "claim",
    "claiming",
    "distribution",
    "distribution event",
    "reward pool",
    "reward pool allocation",
]


# ============================================================
# CAMPAIGN SIGNALS
# ============================================================

CAMPAIGN_SIGNALS = [
    "campaign",
    "program",
    "rewards program",
    "reward program",
    "points program",
    "points campaign",
    "community campaign",
    "user campaign",
    "incentive program",
    "incentive campaign",
    "quest",
    "quests",
    "season",
    "season 1",
    "season 2",
    "season 3",
    "phase",
    "phase 1",
    "phase 2",
    "wave",
    "round",
]


# ============================================================
# TESTNET SIGNALS
# ============================================================

TESTNET_SIGNALS = [
    "testnet",
    "test net",
    "test network",
    "devnet",
    "developer network",
]


TESTNET_REWARD_SIGNALS = [
    "testnet airdrop",
    "testnet reward",
    "testnet rewards",
    "testnet campaign",
    "testnet incentive",
    "testnet incentives",
    "testnet points",
    "testnet points campaign",
    "testnet users",
    "testnet participants",
    "testnet participation",
    "testnet rewards program",
    "testnet token",
    "testnet tokens",
]


# ============================================================
# RETROACTIVE SIGNALS
# ============================================================

RETROACTIVE_SIGNALS = [
    "retroactive",
    "retroactive airdrop",
    "retroactive rewards",
    "retroactive reward",
    "past users",
    "early users",
    "early adopters",
    "historical users",
    "previous users",
    "users who interacted",
    "interaction history",
    "activity history",
    "past activity",
    "historical activity",
]


# ============================================================
# BOUNTY SIGNALS
# ============================================================

BOUNTY_SIGNALS = [
    "bounty",
    "bug bounty",
    "social bounty",
    "content bounty",
    "referral bounty",
    "translation bounty",
    "community bounty",
    "task bounty",
    "bug rewards",
]


# ============================================================
# HOLDER SIGNALS
# ============================================================

HOLDER_SIGNALS = [
    "holder reward",
    "holder rewards",
    "holder airdrop",
    "holders eligible",
    "eligible holders",
    "token holders",
    "nft holders",
    "snapshot",
    "snapshot date",
    "holding requirement",
    "hold tokens",
    "hold token",
    "hold nft",
    "hold an nft",
]


# ============================================================
# LIQUIDITY SIGNALS
# ============================================================

LIQUIDITY_SIGNALS = [
    "liquidity rewards",
    "liquidity reward",
    "liquidity mining",
    "liquidity incentive",
    "liquidity incentives",
    "liquidity provider rewards",
    "liquidity providers",
    "provide liquidity",
    "provide liquidity to",
    "add liquidity",
    "liquidity pool rewards",
    "yield farming rewards",
    "yield farming",
]


# ============================================================
# ACTIVITY SIGNALS
# ============================================================

ACTIVITY_SIGNALS = [
    "on-chain activity rewards",
    "onchain activity rewards",
    "user activity rewards",
    "transaction rewards",
    "transaction reward",
    "interaction rewards",
    "activity rewards",
    "bridge and earn",
    "swap and earn",
    "trade and earn",
    "deposit and earn",
    "volume requirement",
    "trading rewards",
]


# ============================================================
# NEWS / NON-OPPORTUNITY SIGNALS
# ============================================================

NEWS_SIGNALS = [
    "price",
    "prices",
    "bitcoin",
    "btc",
    "ethereum",
    "eth",
    "market",
    "markets",
    "trading",
    "traders",
    "rally",
    "surge",
    "surges",
    "jumps",
    "jumped",
    "falls",
    "fell",
    "drops",
    "dropped",
    "inflows",
    "outflows",
    "etf",
    "etfs",
    "regulation",
    "regulatory",
    "regulators",
    "lawsuit",
    "lawsuits",
    "court",
    "supreme court",
    "sec",
    "cftc",
    "fincen",
    "imf",
    "bank",
    "banks",
    "funding",
    "funded",
    "raises",
    "raised",
    "investment",
    "investor",
    "investors",
    "partnership",
    "partnerships",
    "partners",
    "integrates",
    "integration",
    "launches",
    "launched",
    "launch",
    "announces",
    "announced",
    "announcement",
    "approval",
    "approved",
    "acquisition",
    "acquires",
    "acquired",
    "ipo",
    "stocks",
    "stock",
    "shares",
    "stablecoin",
    "stablecoins",
    "tokenized",
    "tokenization",
    "roadmap",
    "study",
    "report",
    "reports",
    "analysis",
    "interview",
]


# ============================================================
# SPECULATION SIGNALS
# ============================================================

SPECULATION_SIGNALS = [
    "speculation",
    "speculative",
    "rumor",
    "rumors",
    "rumoured",
    "rumored",
    "may airdrop",
    "might airdrop",
    "could airdrop",
    "possible airdrop",
    "potential airdrop",
    "airdrop speculation",
    "airdrop rumors",
    "airdrop rumor",
    "likely airdrop",
    "expected airdrop",
    "possibly",
    "could launch",
    "might launch",
    "may launch",
]


# ============================================================
# NEWS ROUNDUP SIGNALS
# ============================================================

NEWS_ROUNDUP_SIGNALS = [
    "here's what happened",
    "heres what happened",
    "what happened in crypto",
    "crypto today",
    "morning minute",
    "daily crypto",
    "weekly crypto",
    "crypto roundup",
    "market roundup",
    "weekly roundup",
    "daily roundup",
    "this week in crypto",
    "today in crypto",
    "under exposed",
    "market update",
    "market updates",
]


# ============================================================
# ANNOUNCEMENT SIGNALS
# ============================================================

ANNOUNCEMENT_SIGNALS = [
    "launches",
    "launched",
    "launch",
    "announces",
    "announced",
    "announcement",
    "introduces",
    "introduced",
    "unveils",
    "unveiled",
    "partners with",
    "partnered with",
    "integrates",
    "integrated",
    "integration",
    "adds support",
    "supports",
    "secures",
    "secured",
    "raises",
    "raised",
    "funding",
    "funded",
]


# ============================================================
# WEAK SIGNALS
# ============================================================

WEAK_SIGNALS = [
    "crypto",
    "blockchain",
    "web3",
    "token",
    "tokens",
    "protocol",
    "network",
    "community",
    "users",
    "platform",
    "ecosystem",
]


# ============================================================
# TEXT HELPERS
# ============================================================

def _normalize_text(text):
    """
    Normalize text for reliable keyword matching.
    """

    if text is None:
        return ""

    text = str(text).lower()

    text = text.replace("’", "'")
    text = text.replace("“", '"')
    text = text.replace("”", '"')
    text = text.replace("–", "-")
    text = text.replace("—", "-")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _get_candidate_text(airdrop):
    """
    Build the text used by the qualification engine.
    """

    if not isinstance(airdrop, dict):
        return ""

    name = airdrop.get("name", "")
    title = airdrop.get("title", "")
    description = airdrop.get("description", "")
    source = airdrop.get("source", "")
    url = airdrop.get("url", "")

    combined = " ".join(
        [
            str(name),
            str(title),
            str(description),
            str(source),
            str(url),
        ]
    )

    return _normalize_text(combined)


def _get_title(airdrop):
    """
    Extract and normalize the strongest title field.
    """

    if not isinstance(airdrop, dict):
        return ""

    title = airdrop.get("title", "")

    if not title:
        title = airdrop.get("name", "")

    return _normalize_text(title)


def _get_source(airdrop):
    """
    Extract normalized source.
    """

    if not isinstance(airdrop, dict):
        return ""

    return _normalize_text(airdrop.get("source", ""))


def _count_matches(text, signals):
    """
    Count keyword/phrase matches.

    Longer phrases receive more weight.
    """

    score = 0

    for signal in signals:

        signal = _normalize_text(signal)

        if not signal:
            continue

        if signal in text:

            words = signal.split()

            if len(words) >= 3:
                score += 3

            elif len(words) == 2:
                score += 2

            else:
                score += 1

    return score


def _has_any(text, signals):
    """
    Return True when any signal exists.
    """

    for signal in signals:

        signal = _normalize_text(signal)

        if signal and signal in text:
            return True

    return False


def _is_specialized_source(source):
    """
    Determine whether an item comes from a specialized
    airdrop/opportunity source.
    """

    source = _normalize_text(source)

    return any(
        specialized in source
        for specialized in SPECIALIZED_OPPORTUNITY_SOURCES
    )


def _title_has_opportunity_language(title):
    """
    Determine whether the title itself strongly suggests
    an airdrop/reward opportunity.
    """

    strong_title_signals = [
        "airdrop",
        "reward",
        "rewards",
        "points",
        "points campaign",
        "points program",
        "testnet airdrop",
        "testnet rewards",
        "holder rewards",
        "holder reward",
        "liquidity rewards",
        "bounty",
        "retroactive",
        "earn",
        "claim",
        "quest",
        "incentive",
        "incentives",
        "free tokens",
        "token rewards",
        "token reward",
        "campaign",
        "program",
        "season",
        "snapshot",
        "hold-to-earn",
        "hold to earn",
        "trade-to-earn",
        "trade to earn",
        "play-to-earn",
        "play to earn",
        "task",
        "tasks",
    ]

    return _has_any(title, strong_title_signals)


def _has_clear_action(text):
    """
    Determine whether users have an actual action they can perform.
    """

    return _has_any(text, ACTION_SIGNALS)


def _has_clear_reward(text):
    """
    Determine whether the content contains a meaningful reward mechanism.
    """

    return _has_any(text, REWARD_CONTEXT_SIGNALS)


def _has_strong_airdrop_signal(text):
    """
    Determine whether there is explicit airdrop/reward language.
    """

    return _has_any(text, STRONG_AIRDROP_SIGNALS)


def _is_speculative(text):
    """
    Reject airdrop speculation and rumors.
    """

    return _has_any(text, SPECULATION_SIGNALS)


# ============================================================
# NEWS DETECTION
# ============================================================

def is_news_only(airdrop):
    """
    Detect content that is primarily ordinary crypto/news reporting.

    Important:
        This function is mainly used as a hard filter for general
        news sources. Specialized opportunity sources are handled
        separately by qualify_candidate().
    """

    text = _get_candidate_text(airdrop)
    title = _get_title(airdrop)

    if not text:
        return True

    # Roundups are news unless the title itself clearly identifies
    # an actionable reward opportunity.
    if _has_any(title, NEWS_ROUNDUP_SIGNALS):

        if not _title_has_opportunity_language(title):
            return True

    # Speculation is never a real opportunity.
    if _is_speculative(text):
        return True

    has_reward = _has_clear_reward(text)
    has_action = _has_clear_action(text)
    has_strong = _has_strong_airdrop_signal(text)

    news_score = _count_matches(text, NEWS_SIGNALS)
    announcement_score = _count_matches(text, ANNOUNCEMENT_SIGNALS)

    # Pure news without action/reward evidence.
    if news_score >= 4 and not (
        has_reward and has_action
    ):
        return True

    # Product/protocol announcements without user rewards.
    if announcement_score >= 2 and not (
        has_reward and has_action
    ):
        return True

    # General news article with a weak incidental airdrop mention.
    if news_score >= 3 and not has_strong:
        return True

    return False


# ============================================================
# SPECIALIZED SOURCE QUALIFICATION
# ============================================================

def _qualify_specialized_source(
    text,
    title,
):
    """
    Qualification logic for specialized opportunity sources.

    AirdropAlert is itself an opportunity-discovery source.

    Therefore:
        - Explicit airdrop titles are strongly trusted.
        - Named airdrop listings can qualify without action words.
        - Reward/points/testnet/etc. listings receive specialized handling.
        - Obvious speculation/news remains rejected.
        - Completely unrelated content is rejected.
    """

    strong_score = _count_matches(
        text,
        STRONG_AIRDROP_SIGNALS
    )

    reward_score = _count_matches(
        text,
        REWARD_CONTEXT_SIGNALS
    )

    action_score = _count_matches(
        text,
        ACTION_SIGNALS
    )

    campaign_score = _count_matches(
        text,
        CAMPAIGN_SIGNALS
    )

    testnet_score = _count_matches(
        text,
        TESTNET_SIGNALS
    )

    testnet_reward_score = _count_matches(
        text,
        TESTNET_REWARD_SIGNALS
    )

    retroactive_score = _count_matches(
        text,
        RETROACTIVE_SIGNALS
    )

    bounty_score = _count_matches(
        text,
        BOUNTY_SIGNALS
    )

    holder_score = _count_matches(
        text,
        HOLDER_SIGNALS
    )

    liquidity_score = _count_matches(
        text,
        LIQUIDITY_SIGNALS
    )

    activity_score = _count_matches(
        text,
        ACTIVITY_SIGNALS
    )

    news_score = _count_matches(
        text,
        NEWS_SIGNALS
    )

    announcement_score = _count_matches(
        text,
        ANNOUNCEMENT_SIGNALS
    )

    title_opportunity = _title_has_opportunity_language(
        title
    )

    # --------------------------------------------------------
    # HARD NEWS ROUNDUP REJECTION
    # --------------------------------------------------------

    if _has_any(title, NEWS_ROUNDUP_SIGNALS):

        if not title_opportunity:
            return {
                "qualified": False,
                "score": 0,
                "reason": (
                    "News roundup without a clear opportunity detected"
                ),
            }

    # --------------------------------------------------------
    # EXPLICIT AIRDROP TITLE
    # --------------------------------------------------------

    if _has_any(
        title,
        [
            "airdrop",
            "airdrop campaign",
            "airdrop program",
            "airdrop rewards",
            "airdrop reward",
            "testnet airdrop",
            "holder airdrop",
            "retroactive airdrop",
        ]
    ):

        score = (
            20
            + strong_score * 3
            + reward_score * 2
            + action_score * 2
            + campaign_score
        )

        return {
            "qualified": True,
            "score": score,
            "reason": (
                "Specialized airdrop source with explicit "
                "airdrop opportunity detected"
            ),
        }

    # --------------------------------------------------------
    # EXPLICIT REWARD / POINTS TITLE
    # --------------------------------------------------------

    if title_opportunity:

        opportunity_title_signals = [
            "reward",
            "rewards",
            "points",
            "points campaign",
            "points program",
            "bounty",
            "retroactive",
            "holder",
            "liquidity",
            "earn",
            "claim",
            "quest",
            "incentive",
            "incentives",
            "free tokens",
            "token rewards",
            "snapshot",
            "hold-to-earn",
            "hold to earn",
            "trade-to-earn",
            "trade to earn",
            "play-to-earn",
            "play to earn",
        ]

        if _has_any(title, opportunity_title_signals):

            # Specialized source + opportunity title is strong
            # enough even when the description is sparse.
            score = (
                12
                + strong_score * 2
                + reward_score * 2
                + action_score * 2
                + campaign_score
            )

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Specialized opportunity source with "
                    "opportunity-focused title detected"
                ),
            }

    # --------------------------------------------------------
    # STRONG AIRDROP / REWARD EVIDENCE
    # --------------------------------------------------------

    if strong_score >= 2:

        score = (
            strong_score * 3
            + reward_score * 2
            + action_score * 2
            + campaign_score
        )

        return {
            "qualified": True,
            "score": score,
            "reason": (
                "Strong airdrop or reward opportunity evidence detected"
            ),
        }

    # --------------------------------------------------------
    # REWARD + ACTION
    # --------------------------------------------------------

    if (
        reward_score >= 2
        and action_score >= 1
    ):

        score = (
            reward_score * 2
            + action_score * 2
            + campaign_score
        )

        return {
            "qualified": True,
            "score": score,
            "reason": (
                "Reward campaign with qualifying user activity detected"
            ),
        }

    # --------------------------------------------------------
    # TESTNET OPPORTUNITY
    # --------------------------------------------------------

    if testnet_score >= 1:

        if testnet_reward_score >= 1:

            score = (
                testnet_reward_score * 3
                + action_score * 2
                + reward_score
                + campaign_score
            )

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Testnet reward opportunity detected"
                ),
            }

        # AirdropAlert testnet listings are still useful discoveries
        # when the title itself clearly presents the project as an
        # opportunity rather than merely reporting a testnet launch.
        if title_opportunity:

            score = (
                10
                + testnet_score * 2
                + strong_score * 2
                + action_score
            )

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Specialized testnet opportunity detected"
                ),
            }

    # --------------------------------------------------------
    # RETROACTIVE
    # --------------------------------------------------------

    if retroactive_score >= 1:

        if (
            reward_score >= 1
            or strong_score >= 1
            or title_opportunity
        ):

            score = (
                retroactive_score * 3
                + reward_score * 2
                + action_score
                + strong_score * 2
            )

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Retroactive reward opportunity evidence detected"
                ),
            }

    # --------------------------------------------------------
    # BOUNTY
    # --------------------------------------------------------

    if bounty_score >= 1:

        if (
            action_score >= 1
            or reward_score >= 1
            or title_opportunity
        ):

            score = (
                bounty_score * 3
                + action_score * 2
                + reward_score * 2
            )

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Bounty opportunity detected"
                ),
            }

    # --------------------------------------------------------
    # HOLDER
    # --------------------------------------------------------

    if holder_score >= 1:

        if (
            reward_score >= 1
            or strong_score >= 1
            or title_opportunity
        ):

            score = (
                holder_score * 3
                + reward_score * 2
                + action_score
            )

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Holder reward opportunity detected"
                ),
            }

    # --------------------------------------------------------
    # LIQUIDITY
    # --------------------------------------------------------

    if liquidity_score >= 1:

        if (
            reward_score >= 1
            or action_score >= 1
            or title_opportunity
        ):

            score = (
                liquidity_score * 3
                + reward_score * 2
                + action_score * 2
            )

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Liquidity reward opportunity detected"
                ),
            }

    # --------------------------------------------------------
    # ACTIVITY
    # --------------------------------------------------------

    if activity_score >= 1:

        if (
            reward_score >= 1
            or strong_score >= 1
            or title_opportunity
        ):

            score = (
                activity_score * 3
                + reward_score * 2
                + action_score * 2
            )

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Actionable activity reward opportunity detected"
                ),
            }

    # --------------------------------------------------------
    # SPECIALIZED SOURCE + CLEAR OPPORTUNITY LANGUAGE
    # --------------------------------------------------------

    # This is the important recovery layer.
    #
    # AirdropAlert may publish concise listings where the RSS
    # description does not contain enough traditional keywords.
    #
    # If the title clearly looks like an opportunity and the
    # content contains at least one supporting signal, accept it.

    if title_opportunity:

        supporting_signal = (
            strong_score
            + reward_score
            + action_score
            + campaign_score
            + retroactive_score
            + bounty_score
            + holder_score
            + liquidity_score
            + activity_score
        )

        if supporting_signal >= 1:

            score = (
                8
                + strong_score * 2
                + reward_score * 2
                + action_score * 2
                + campaign_score
            )

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Specialized opportunity source with "
                    "supporting reward evidence detected"
                ),
            }

    # --------------------------------------------------------
    # SPARSE SPECIALIZED LISTING
    # --------------------------------------------------------

    # AirdropAlert sometimes provides a very short project listing.
    # If it does not look like news, speculation, funding, regulation,
    # or a normal announcement, allow a low-confidence discovery.
    #
    # This is intentionally conservative: the candidate will still
    # go through verification and scoring later.

    dangerous_news_score = (
        _count_matches(
            text,
            [
                "funding",
                "funded",
                "raises",
                "raised",
                "investment",
                "investor",
                "investors",
                "partnership",
                "partners",
                "lawsuit",
                "regulation",
                "regulatory",
                "regulators",
                "price",
                "market update",
                "market updates",
                "etf",
                "approval",
                "approved",
            ]
        )
    )

    obvious_announcement_score = (
        _count_matches(
            text,
            [
                "launches",
                "launched",
                "announces",
                "announced",
                "announcement",
                "partners with",
                "integrates",
                "integration",
                "raises",
                "raised",
                "funding",
            ]
        )
    )

    if (
        not title_opportunity
        and dangerous_news_score == 0
        and obvious_announcement_score == 0
        and news_score <= 2
        and (
            reward_score >= 1
            or strong_score >= 1
            or campaign_score >= 1
            or action_score >= 1
        )
    ):

        score = (
            5
            + strong_score * 2
            + reward_score * 2
            + action_score
            + campaign_score
        )

        return {
            "qualified": True,
            "score": score,
            "reason": (
                "Specialized opportunity listing with "
                "supporting signals detected"
            ),
        }

    # --------------------------------------------------------
    # REJECT
    # --------------------------------------------------------

    return {
        "qualified": False,
        "score": 0,
        "reason": (
            "Insufficient evidence of an actual airdrop or "
            "reward opportunity"
        ),
    }


# ============================================================
# MAIN QUALIFICATION ENGINE
# ============================================================

def qualify_candidate(airdrop):
    """
    Qualify one discovered candidate.

    Returns:
        {
            "qualified": bool,
            "score": int,
            "reason": str
        }
    """

    if not isinstance(airdrop, dict):

        return {
            "qualified": False,
            "score": 0,
            "reason": "Invalid candidate format",
        }

    text = _get_candidate_text(airdrop)
    title = _get_title(airdrop)
    source = _get_source(airdrop)

    if not text:

        return {
            "qualified": False,
            "score": 0,
            "reason": "Empty candidate content",
        }

    # --------------------------------------------------------
    # HARD REJECTION: SPECULATION
    # --------------------------------------------------------

    if _is_speculative(text):

        return {
            "qualified": False,
            "score": 0,
            "reason": "Airdrop speculation or rumor detected",
        }

    # --------------------------------------------------------
    # SPECIALIZED OPPORTUNITY SOURCES
    # --------------------------------------------------------

    if _is_specialized_source(source):

        return _qualify_specialized_source(
            text,
            title,
        )

    # --------------------------------------------------------
    # GENERAL CRYPTO / NEWS SOURCES
    # --------------------------------------------------------

    strong_score = _count_matches(
        text,
        STRONG_AIRDROP_SIGNALS
    )

    reward_score = _count_matches(
        text,
        REWARD_CONTEXT_SIGNALS
    )

    action_score = _count_matches(
        text,
        ACTION_SIGNALS
    )

    campaign_score = _count_matches(
        text,
        CAMPAIGN_SIGNALS
    )

    news_score = _count_matches(
        text,
        NEWS_SIGNALS
    )

    announcement_score = _count_matches(
        text,
        ANNOUNCEMENT_SIGNALS
    )

    testnet_score = _count_matches(
        text,
        TESTNET_SIGNALS
    )

    testnet_reward_score = _count_matches(
        text,
        TESTNET_REWARD_SIGNALS
    )

    # --------------------------------------------------------
    # HARD NEWS REJECTION
    # --------------------------------------------------------

    if is_news_only(airdrop):

        return {
            "qualified": False,
            "score": 0,
            "reason": (
                "News-only content with no meaningful airdrop "
                "campaign evidence"
            ),
        }

    # --------------------------------------------------------
    # TESTNET WITHOUT REWARDS
    # --------------------------------------------------------

    if testnet_score >= 1:

        if testnet_reward_score == 0:

            return {
                "qualified": False,
                "score": 0,
                "reason": (
                    "Testnet mention without a qualifying reward "
                    "or airdrop mechanism"
                ),
            }

        if action_score == 0:

            return {
                "qualified": False,
                "score": 0,
                "reason": (
                    "Testnet reward mentioned without clear "
                    "user participation action"
                ),
            }

    # --------------------------------------------------------
    # GENERAL SOURCE: EXPLICIT AIRDROP
    # --------------------------------------------------------

    title_opportunity = _title_has_opportunity_language(
        title
    )

    if strong_score >= 2:

        if (
            title_opportunity
            and reward_score >= 1
            and action_score >= 1
        ):

            score = (
                strong_score * 3
                + reward_score * 3
                + action_score * 3
                + campaign_score
                - news_score
            )

            if score >= 8:

                return {
                    "qualified": True,
                    "score": score,
                    "reason": (
                        "Actionable airdrop opportunity with clear "
                        "reward and participation evidence detected"
                    ),
                }

        if (
            strong_score >= 3
            and reward_score >= 2
            and action_score >= 1
            and news_score <= 4
        ):

            score = (
                strong_score * 3
                + reward_score * 2
                + action_score * 2
                + campaign_score
                - news_score
            )

            if score >= 9:

                return {
                    "qualified": True,
                    "score": score,
                    "reason": (
                        "Strong actionable airdrop evidence detected"
                    ),
                }

    # --------------------------------------------------------
    # GENERAL SOURCE: REWARD CAMPAIGN
    # --------------------------------------------------------

    if (
        reward_score >= 3
        and action_score >= 2
        and (
            campaign_score >= 1
            or title_opportunity
        )
        and news_score <= 3
    ):

        score = (
            reward_score * 3
            + action_score * 3
            + campaign_score * 2
            - news_score
        )

        if score >= 10:

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Reward campaign with clear qualifying user "
                    "activity detected"
                ),
            }

    # --------------------------------------------------------
    # GENERAL SOURCE: TESTNET REWARD
    # --------------------------------------------------------

    if (
        testnet_reward_score >= 1
        and reward_score >= 1
        and action_score >= 1
        and news_score <= 3
    ):

        score = (
            testnet_reward_score * 4
            + reward_score * 2
            + action_score * 2
            - news_score
        )

        if score >= 8:

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Testnet reward campaign with clear "
                    "participation evidence detected"
                ),
            }

    # --------------------------------------------------------
    # GENERAL SOURCE: RETROACTIVE
    # --------------------------------------------------------

    retroactive_score = _count_matches(
        text,
        RETROACTIVE_SIGNALS
    )

    if (
        retroactive_score >= 1
        and reward_score >= 1
        and (
            action_score >= 1
            or strong_score >= 1
        )
        and news_score <= 3
    ):

        score = (
            retroactive_score * 4
            + reward_score * 2
            + action_score * 2
            + strong_score * 2
            - news_score
        )

        if score >= 8:

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Retroactive reward opportunity evidence detected"
                ),
            }

    # --------------------------------------------------------
    # GENERAL SOURCE: BOUNTY
    # --------------------------------------------------------

    bounty_score = _count_matches(
        text,
        BOUNTY_SIGNALS
    )

    if (
        bounty_score >= 1
        and action_score >= 1
        and reward_score >= 1
        and news_score <= 3
    ):

        score = (
            bounty_score * 4
            + action_score * 2
            + reward_score * 2
            - news_score
        )

        if score >= 7:

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Bounty campaign with qualifying user "
                    "activity detected"
                ),
            }

    # --------------------------------------------------------
    # GENERAL SOURCE: HOLDER
    # --------------------------------------------------------

    holder_score = _count_matches(
        text,
        HOLDER_SIGNALS
    )

    if (
        holder_score >= 1
        and reward_score >= 1
        and news_score <= 3
    ):

        score = (
            holder_score * 4
            + reward_score * 2
            + action_score
            - news_score
        )

        if score >= 7:

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Holder reward opportunity detected"
                ),
            }

    # --------------------------------------------------------
    # GENERAL SOURCE: LIQUIDITY
    # --------------------------------------------------------

    liquidity_score = _count_matches(
        text,
        LIQUIDITY_SIGNALS
    )

    if (
        liquidity_score >= 1
        and reward_score >= 1
        and action_score >= 1
        and news_score <= 3
    ):

        score = (
            liquidity_score * 4
            + reward_score * 2
            + action_score * 2
            - news_score
        )

        if score >= 7:

            return {
                "qualified": True,
                "score": score,
                "reason": (
                    "Liquidity reward opportunity detected"
                ),
            }

    # --------------------------------------------------------
    # FINAL GENERAL-SOURCE REJECTION
    # --------------------------------------------------------

    weak_score = _count_matches(
        text,
        WEAK_SIGNALS
    )

    fallback_score = (
        strong_score * 2
        + reward_score
        + action_score
        + campaign_score
        + weak_score
        - news_score
        - announcement_score
    )

    return {
        "qualified": False,
        "score": max(0, fallback_score),
        "reason": (
            "Insufficient evidence of an actual airdrop or "
            "reward opportunity"
        ),
    }


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print("🧠 AirdropRadar Qualification Engine Test")
    print()

    test_cases = [

        # ----------------------------------------------------
        # VALID AIRDROPALERT CASES
        # ----------------------------------------------------

        {
            "name": "Example Airdrop",
            "title": "Example Airdrop",
            "description": (
                "Users can complete tasks and claim token rewards "
                "through the official airdrop campaign."
            ),
            "source": "airdropalert",
        },

        {
            "name": "Example Points Campaign",
            "title": "Example Points Campaign",
            "description": (
                "Users can participate in the points program, "
                "earn points and receive rewards."
            ),
            "source": "airdropalert",
        },

        {
            "name": "Example Testnet",
            "title": "Example Testnet Airdrop",
            "description": (
                "Join the testnet, complete transactions and "
                "earn testnet rewards."
            ),
            "source": "airdropalert",
        },

        {
            "name": "Example Holder Reward",
            "title": "Example Holder Reward",
            "description": (
                "Eligible token holders can claim rewards "
                "after the snapshot."
            ),
            "source": "airdropalert",
        },

        {
            "name": "Example Liquidity Campaign",
            "title": "Example Liquidity Campaign",
            "description": (
                "Provide liquidity to earn liquidity rewards "
                "during the campaign."
            ),
            "source": "airdropalert",
        },

        {
            "name": "Example Bounty",
            "title": "Example Bounty",
            "description": (
                "Complete community tasks and earn bounty rewards."
            ),
            "source": "airdropalert",
        },

        {
            "name": "Example Retroactive",
            "title": "Example Retroactive Airdrop",
            "description": (
                "Past users who interacted with the protocol "
                "can claim retroactive rewards."
            ),
            "source": "airdropalert",
        },

        # Sparse but legitimate-style listings.
        {
            "name": "Entropy",
            "title": "Entropy",
            "description": (
                "Entropy is a new Web3 opportunity for users "
                "to participate and earn rewards."
            ),
            "source": "airdropalert",
        },

        {
            "name": "Dow Protocol",
            "title": "Dow Protocol",
            "description": (
                "Users can participate in the protocol campaign."
            ),
            "source": "airdropalert",
        },

        {
            "name": "MetaMask Money Account Rewards",
            "title": "MetaMask Money Account Rewards",
            "description": (
                "Users can earn rewards through the program."
            ),
            "source": "airdropalert",
        },

        {
            "name": "LitVMSwap",
            "title": "LitVMSwap",
            "description": (
                "Use LitVMSwap and participate in the ecosystem."
            ),
            "source": "airdropalert",
        },

        # ----------------------------------------------------
        # FALSE POSITIVE TESTS
        # ----------------------------------------------------

        {
            "name": "Bitcoin Price Update",
            "title": "Bitcoin Price Update",
            "description": (
                "Bitcoin price rises as traders react to market "
                "conditions and ETF inflows."
            ),
            "source": "cointelegraph",
        },

        {
            "name": "Trump Discusses Crypto",
            "title": "Trump Discusses Crypto",
            "description": (
                "Trump discussed cryptocurrency regulation and "
                "the future of the crypto market."
            ),
            "source": "cointelegraph",
        },

        {
            "name": "Protocol Funding Announcement",
            "title": "Protocol Funding Announcement",
            "description": (
                "The protocol raises $20 million from investors "
                "to expand its blockchain ecosystem."
            ),
            "source": "cointelegraph",
        },

        {
            "name": "AMC CEO Criticizes Robinhood",
            "title": "AMC CEO Criticizes Robinhood",
            "description": (
                "The AMC CEO criticized Robinhood's tokenized "
                "stock plans."
            ),
            "source": "cointelegraph",
        },

        {
            "name": "QuFi launches post-quantum verification platform",
            "title": (
                "QuFi launches post-quantum verification "
                "platform with Bitcoin testnet proof"
            ),
            "description": (
                "QuFi launches a new verification platform "
                "using a Bitcoin testnet proof."
            ),
            "source": "cointelegraph",
        },

        {
            "name": "Mantle adds USDG stablecoin",
            "title": (
                "Mantle adds Paxos USDG stablecoin, "
                "joins Global Dollar Network"
            ),
            "description": (
                "Mantle has added the USDG stablecoin and "
                "joined the Global Dollar Network."
            ),
            "source": "cointelegraph",
        },

        {
            "name": "Airdrop Speculation",
            "title": "Hyperliquid Airdrop Speculation",
            "description": (
                "Users speculate that Hyperliquid could launch "
                "another airdrop."
            ),
            "source": "decrypt",
        },

        {
            "name": "Crypto News Roundup",
            "title": (
                "Crypto rebounds after tariffs, IPO and "
                "Solana token surge"
            ),
            "description": (
                "Bitcoin rebounds as crypto markets rally. "
                "Several projects and tokens gain value."
            ),
            "source": "decrypt",
        },

        {
            "name": "Ordinary Testnet",
            "title": "Project launches Bitcoin testnet",
            "description": (
                "The project launches a new Bitcoin testnet "
                "for developers to test its technology."
            ),
            "source": "cointelegraph",
        },

        {
            "name": "Generic Crypto Article",
            "title": "Crypto Technology Update",
            "description": (
                "A blockchain project announces a new protocol "
                "update and partnership."
            ),
            "source": "coindesk",
        },
    ]

    for test in test_cases:

        result = qualify_candidate(test)

        status = (
            "✅ QUALIFIED"
            if result["qualified"]
            else "❌ REJECTED"
        )

        print(
            f"{status} | {test['name']}"
        )

        print(
            f"   Score: {result['score']}"
        )

        print(
            f"   Reason: {result['reason']}"
        )

        print()

    print("✅ Qualification engine ready!")