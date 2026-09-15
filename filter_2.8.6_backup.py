
# ============================================================
# AIRDROP RADAR — CATEGORY CLASSIFIER
# VERSION 2.8.6
# ============================================================

import re
from collections import Counter


CLASSIFIER_VERSION = "2.8.6"


# ============================================================
# CATEGORIES
# ============================================================

CATEGORIES = [
    "Retroactive",
    "Holder",
    "Bounty",
    "Testnet",
    "Points",
    "Liquidity",
    "Activity",
    "Other",
]


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(text):
    """
    Convert any input into normalized lowercase text.
    """

    if text is None:
        return ""

    if isinstance(text, (list, tuple, set)):
        text = " ".join(str(x) for x in text)

    text = str(text).lower()

    text = text.replace("_", " ")
    text = text.replace("-", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def contains_any(text, signals):
    """
    Return True if any signal exists in text.

    Single-word signals use word boundaries to reduce
    accidental substring matches.
    """

    text = normalize_text(text)

    for signal in signals:

        signal = normalize_text(signal)

        if not signal:
            continue

        if " " not in signal:
            if re.search(rf"\b{re.escape(signal)}\b", text):
                return True

        else:
            if signal in text:
                return True

    return False


def keyword_matches(text, signals):
    """
    Return all matching signals.
    """

    text = normalize_text(text)

    matches = []

    for signal in signals:

        signal = normalize_text(signal)

        if not signal:
            continue

        if " " not in signal:

            found = re.search(
                rf"\b{re.escape(signal)}\b",
                text,
            )

        else:

            found = signal in text

        if found:
            matches.append(signal)

    return matches


# ============================================================
# CANDIDATE TEXT
# ============================================================

SEARCH_FIELDS = [
    "title",
    "name",
    "description",
    "summary",
    "content",
    "text",
    "details",
    "requirements",
    "eligibility",
    "reward",
    "rewards",
    "instructions",
    "url",
    "source",
]


def get_candidate_text(candidate):
    """
    Extract searchable text from:

        - string
        - dictionary
        - object with attributes
    """

    if candidate is None:
        return ""

    if isinstance(candidate, str):
        return normalize_text(candidate)

    if isinstance(candidate, dict):

        values = []

        for field in SEARCH_FIELDS:

            value = candidate.get(field)

            if value is not None:
                values.append(str(value))

        # Fallback for simple dictionary values.
        if not values:

            for value in candidate.values():

                if isinstance(value, (str, int, float)):
                    values.append(str(value))

        return normalize_text(" ".join(values))

    values = []

    for field in SEARCH_FIELDS:

        try:
            value = getattr(candidate, field, None)

        except Exception:
            value = None

        if value is not None:
            values.append(str(value))

    return normalize_text(" ".join(values))


# ============================================================
# RETROACTIVE
# ============================================================

RETROACTIVE_EXPLICIT_SIGNALS = [

    "retroactive airdrop",
    "retroactive distribution",
    "retroactive allocation",
    "retroactive rewards",
    "retroactive reward",
    "retroactive eligibility",
    "retroactive claim",

    "historical airdrop",
    "historical distribution",
    "historical allocation",
    "historical rewards",
    "historical reward",
    "historical eligibility",

    "past users qualify",
    "past users are eligible",
    "past users eligible",
    "past users received",
    "past users will receive",
    "past users can claim",

    "previous users qualify",
    "previous users are eligible",
    "previous users eligible",
    "previous users received",
    "previous users will receive",
    "previous users can claim",

    "historical users are eligible",
    "historical users qualify",
    "historical users will receive",

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

    "historical participation qualifies",
    "previous participation qualifies",
    "past participation qualifies",
    "historical activity qualifies",
    "previous activity qualifies",
    "past activity qualifies",

    "historical snapshot",
    "snapshot of past users",
    "snapshot of historical users",
    "snapshot of previous users",

    "early users are eligible",
    "early users were eligible",
    "early users qualify",
    "early users received",
    "early users will receive",
    "early users can claim",
    "early users can receive",

    "early adopters are eligible",
    "early adopters qualify",
    "early adopters received",
    "early adopters will receive",
    "early adopters can claim",

    "early participants are eligible",
    "early participants qualify",
    "early participants received",
    "early participants will receive",
    "early participants can claim",
]


# Kept for analysis/documentation.
# These are intentionally NOT enough to classify something
# as Retroactive.
WEAK_HISTORICAL_SIGNALS = [

    "early users",
    "early user",
    "early adopters",
    "early adopter",

    "early participants",
    "early participant",

    "historical users",
    "historical user",

    "past users",
    "past user",

    "previous users",
    "previous user",

    "former users",
    "former user",

    "retroactive",
]


def has_retroactive_requirement(text):
    """
    Historical wording alone is NOT enough.

    Examples:

        early users can trade
            -> Activity

        early users earn points
            -> Points

        early users provide liquidity
            -> Liquidity

        early users join testnet
            -> Testnet

        early users are eligible
            -> Retroactive

        past users can claim
            -> Retroactive

        retroactive airdrop
            -> Retroactive

        retroactive program
            -> NOT Retroactive
    """

    text = normalize_text(text)

    return contains_any(
        text,
        RETROACTIVE_EXPLICIT_SIGNALS,
    )


# ============================================================
# HOLDER
# ============================================================

STRONG_HOLDER_SIGNALS = [

    "holder snapshot",

    "eligible holders",
    "eligible holder",
    "holders eligible",

    "holder eligibility",

    "holding requirement",

    "minimum balance",
    "minimum token balance",

    "minimum holding",
    "minimum holdings",

    "must hold",
    "must be holding",

    "hold at least",
    "holding at least",

    "wallet balance",
    "balance requirement",
]


def has_holder_requirement(text):
    """
    Holder requires actual ownership/balance eligibility.

    Generic mentions such as:

        token holders
        many holders
        token snapshot

    do NOT automatically qualify as Holder.
    """

    text = normalize_text(text)

    if contains_any(
        text,
        STRONG_HOLDER_SIGNALS,
    ):
        return True

    if contains_any(text, ["snapshot"]):

        holder_context = [

            "holder",
            "holders",
            "holding",
            "hold",

            "balance",

            "eligible",
            "eligibility",
        ]

        if contains_any(
            text,
            holder_context,
        ):
            return True

    return False


# ============================================================
# BOUNTY
# ============================================================

BOUNTY_SIGNALS = [

    "bug bounty",
    "bug bounties",

    "content bounty",
    "translation bounty",
    "community bounty",

    "developer bounty",
    "development bounty",

    "security bounty",
    "audit bounty",

    "referral bounty",
    "social bounty",
    "task bounty",

    "complete bounty",
    "bounty campaign",

    "bounties",
    "bounty",

    "earn rewards for bugs",
    "report bugs for rewards",
    "report bugs and earn",
]


def has_bounty_requirement(text):
    """
    Bounty requires a genuine work-for-reward mechanism.
    """

    return contains_any(
        text,
        BOUNTY_SIGNALS,
    )


# ============================================================
# TESTNET
# ============================================================

TESTNET_STRONG_SIGNALS = [

    "public testnet",
    "public testnet is live",

    "private testnet",

    "testnet is live",
    "testnet campaign",

    "join the testnet",
    "join testnet",

    "use the testnet",
    "use testnet",

    "on testnet",

    "testnet participation",

    "testnet rewards",
    "testnet reward",

    "test tokens",
    "test token",

    "claim test tokens",
    "claim test token",

    "test funds",
    "test fund",

    "faucet",
]


def has_testnet_requirement(text):
    """
    Testnet must represent actual participation.
    """

    text = normalize_text(text)

    if contains_any(
        text,
        TESTNET_STRONG_SIGNALS,
    ):
        return True

    if contains_any(text, ["testnet"]):

        participation_context = [

            "join",
            "use",

            "trade",
            "trading",

            "swap",
            "swapping",

            "bridge",
            "bridging",

            "quest",
            "quests",

            "task",
            "tasks",

            "activity",
            "activities",

            "participate",
            "participation",

            "reward",
            "rewards",

            "points",
            "xp",

            "transactions",
            "transaction",

            "deploy",

            "faucet",

            "test token",
            "test tokens",

            "test fund",
            "test funds",
        ]

        return contains_any(
            text,
            participation_context,
        )

    return False


# ============================================================
# POINTS
# ============================================================

STRONG_POINTS_ALLOCATION_SIGNALS = [

    "points determine allocation",
    "points determine eligibility",

    "points used to determine allocation",
    "points used to determine eligibility",

    "points used for allocation",

    "points based rewards",
    "points based reward",

    "points based allocation",
    "points based eligibility",

    "xp determines rewards",
    "xp determine rewards",

    "xp determines eligibility",
    "xp determine eligibility",

    "xp converts into",
    "xp will convert into",
]


STRONG_POINTS_PROGRAM_SIGNALS = [

    "points campaign",
    "points program",

    "points rewards",
    "points reward",

    "reward points",

    "points system",
    "point system",

    "collect points",
    "earn points",
    "earning points",
    "accumulate points",

    "xp rewards",
    "xp reward",

    "xp system",

    "earn xp",
    "earning xp",
    "collect xp",
    "accumulate xp",
]


def has_points_requirement(text):
    """
    Detect a real points/XP reward mechanism.
    """

    text = normalize_text(text)

    if contains_any(
        text,
        STRONG_POINTS_ALLOCATION_SIGNALS
        + STRONG_POINTS_PROGRAM_SIGNALS,
    ):
        return True

    if contains_any(
        text,
        ["points", "xp"],
    ):

        reward_context = [

            "airdrop",

            "allocation",
            "allocated",

            "eligible",
            "eligibility",

            "reward",
            "rewards",

            "token reward",
            "token rewards",

            "token allocation",

            "campaign",
            "season",

            "leaderboard",

            "distribution",
            "distributed",

            "claim",

            "qualify",
            "qualified",
        ]

        if contains_any(
            text,
            reward_context,
        ):
            return True

    return False


# ============================================================
# LIQUIDITY
# ============================================================

STRONG_LIQUIDITY_SIGNALS = [

    "provide liquidity",
    "providing liquidity",

    "liquidity provider",
    "liquidity providers",

    "liquidity pool",
    "liquidity pools",

    "liquidity position",
    "liquidity positions",

    "provide lp",
    "provide an lp",

    "provide liquidity to",

    "deposit liquidity",

    "add liquidity",
    "adding liquidity",

    "earn yield",
    "earn yield from",

    "yield farming",
    "yield farm",
    "yield farms",

    "yield strategy",
    "yield strategies",

    "yield vault",
    "yield vaults",

    "liquidity vault",
    "liquidity vaults",

    "staking rewards",
    "staking reward",

    "stake tokens",
    "stake to earn",
    "stake and earn",

    "liquidity mining",
    "liquidity mining rewards",

    "farm liquidity",
    "farm lp",
]


def has_real_liquidity_requirement(text):
    """
    Detect actual liquidity/yield/staking participation.
    """

    text = normalize_text(text)

    if contains_any(
        text,
        STRONG_LIQUIDITY_SIGNALS,
    ):
        return True

    if contains_any(
        text,
        ["staking"],
    ):

        staking_context = [

            "reward",
            "rewards",

            "earn",
            "yield",

            "apy",
            "apr",

            "stake",
        ]

        if contains_any(
            text,
            staking_context,
        ):
            return True

    if contains_any(
        text,
        ["liquidity"],
    ):

        liquidity_context = [

            "provide",
            "providing",

            "add",
            "adding",

            "deposit",
            "depositing",

            "position",
            "positions",

            "pool",
            "pools",

            "earn",
            "yield",

            "farm",
            "farming",

            "stake",
            "staking",
        ]

        if contains_any(
            text,
            liquidity_context,
        ):
            return True

    return False


# ============================================================
# ACTIVITY
# ============================================================

ACTIVITY_SIGNALS = [

    "trade",
    "trading",
    "traded",

    "swap",
    "swapping",
    "swapped",

    "mint",
    "minting",
    "minted",

    "burn",
    "burning",
    "burned",

    "bridge",
    "bridging",
    "bridged",

    "deposit",
    "depositing",
    "deposited",

    "withdraw",
    "withdrawal",
    "withdrawing",
    "withdrawn",

    "transfer",
    "transfers",

    "send tokens",

    "buy",
    "buying",
    "bought",

    "sell",
    "selling",
    "sold",

    "complete quests",
    "complete quest",

    "quests",
    "quest",

    "tasks",
    "task",

    "missions",
    "mission",

    "referral",
    "referrals",

    "refer friends",

    "invite friends",
    "invite your friends",

    "wallet connect",

    "connect your wallet",
    "connect wallet",

    "daily tasks",
    "daily task",

    "daily activity",
    "daily activities",

    "activities",
    "activity",

    "play the game",
    "playing the game",

    "gaming",
    "game",
    "games",
    "gameplay",

    "run the app",
    "run app",

    "use the app",
    "using the app",

    "use the platform",
    "using the platform",

    "use the protocol",
    "using the protocol",

    "use the product",
    "using the product",

    "download the app",
    "install the app",

    "create an account",

    "sign up",
    "signup",

    "register",

    "login",
    "log in",

    "complete activities",
    "complete activity",

    "daily check in",
    "check in daily",

    "mine",
    "mining",
    "mine tokens",

    "run a node",
    "run node",
    "run the node",
    "operate a node",

    "contribute bandwidth",

    "upload photos",
    "upload videos",
    "upload content",
]


def has_current_activity_requirement(text):
    """
    Detect normal current participation.
    """

    return contains_any(
        text,
        ACTIVITY_SIGNALS,
    )


# ============================================================
# NEWS / NON-OPPORTUNITY
# ============================================================

NEWS_SIGNALS = [

    "announced",
    "announcement",

    "breaking",

    "news",

    "reported",
    "reports",

    "funding",
    "raised",

    "investors",
    "investment",

    "partnership",
    "partnerships",

    "price",

    "market",
    "markets",

    "etf",
    "etfs",

    "btc price",

    "crypto market",

    "market update",
    "market roundup",

    "funding round",
    "investment round",
    "capital raise",
]


def is_news_like(text):
    """
    Detect obvious news/market/funding content.
    """

    return contains_any(
        text,
        NEWS_SIGNALS,
    )


# ============================================================
# LIQUIDITY / POINTS PRIORITY HELPERS
# ============================================================

LIQUIDITY_ACTION_SIGNALS = [

    "provide liquidity",
    "providing liquidity",

    "liquidity provider",
    "liquidity providers",

    "liquidity pool",
    "liquidity pools",

    "liquidity position",
    "liquidity positions",

    "provide lp",
    "provide an lp",

    "deposit liquidity",

    "add liquidity",
    "adding liquidity",

    "yield farming",
    "yield farm",

    "yield strategy",
    "yield strategies",

    "yield vault",
    "yield vaults",

    "liquidity vault",
    "liquidity vaults",

    "staking rewards",
    "staking reward",

    "stake tokens",
    "stake to earn",
    "stake and earn",

    "liquidity mining",
]


def has_explicit_points_allocation(text):
    """
    Strong evidence that points themselves determine
    the reward or allocation.
    """

    return contains_any(
        text,
        STRONG_POINTS_ALLOCATION_SIGNALS,
    )


# ============================================================
# PRIMARY CLASSIFIER
# ============================================================

def classify_airdrop(candidate):
    """
    Classify by PRIMARY participation/reward mechanism.

    Priority:

        1. Explicit Retroactive
        2. Holder
        3. Bounty
        4. Testnet / Points / Liquidity
        5. News / Other
        6. Activity
        7. Other

    Important:

        Generic "early users" does NOT automatically mean
        Retroactive.

    Examples:

        early users can trade
            -> Activity

        early users earn points
            -> Points

        early users provide liquidity
            -> Liquidity

        early users join testnet
            -> Testnet

        early users are eligible for the airdrop
            -> Retroactive
    """

    text = get_candidate_text(candidate)

    if not text:
        return "Other"

    # --------------------------------------------------------
    # 1. RETROACTIVE
    # --------------------------------------------------------

    if has_retroactive_requirement(text):
        return "Retroactive"

    # --------------------------------------------------------
    # 2. HOLDER
    # --------------------------------------------------------

    if has_holder_requirement(text):
        return "Holder"

    # --------------------------------------------------------
    # 3. BOUNTY
    # --------------------------------------------------------

    if has_bounty_requirement(text):
        return "Bounty"

    # --------------------------------------------------------
    # CURRENT MECHANISMS
    # --------------------------------------------------------

    testnet = has_testnet_requirement(text)

    points = has_points_requirement(text)

    liquidity = has_real_liquidity_requirement(text)

    # --------------------------------------------------------
    # TESTNET + POINTS
    # --------------------------------------------------------

    if testnet and points:

        if has_explicit_points_allocation(text):
            return "Points"

        return "Testnet"

    # --------------------------------------------------------
    # TESTNET + LIQUIDITY + POINTS
    # --------------------------------------------------------

    if testnet and liquidity:

        if (
            points
            and has_explicit_points_allocation(text)
        ):
            return "Points"

        return "Testnet"

    # --------------------------------------------------------
    # LIQUIDITY + POINTS
    # --------------------------------------------------------

    if liquidity and points:

        if has_explicit_points_allocation(text):
            return "Points"

        if contains_any(
            text,
            LIQUIDITY_ACTION_SIGNALS,
        ):
            return "Liquidity"

        return "Points"

    # --------------------------------------------------------
    # INDIVIDUAL MECHANISMS
    # --------------------------------------------------------

    if liquidity:
        return "Liquidity"

    if points:
        return "Points"

    if testnet:
        return "Testnet"

    # --------------------------------------------------------
    # NEWS / NON-OPPORTUNITY
    # --------------------------------------------------------
    #
    # Check news before generic Activity.
    #
    # This prevents something like:
    #
    # "News: the company raised funding and users can
    # use the app..."
    #
    # from being classified as an airdrop Activity.
    # --------------------------------------------------------

    if is_news_like(text):
        return "Other"

    # --------------------------------------------------------
    # ACTIVITY
    # --------------------------------------------------------

    if has_current_activity_requirement(text):
        return "Activity"

    # --------------------------------------------------------
    # OTHER
    # --------------------------------------------------------

    return "Other"


# ============================================================
# EVIDENCE
# ============================================================

def get_classification_evidence(candidate):
    """
    Return matching evidence for every category.
    """

    text = get_candidate_text(candidate)

    evidence = {

        "Retroactive": keyword_matches(
            text,
            RETROACTIVE_EXPLICIT_SIGNALS,
        ),

        "Holder": keyword_matches(
            text,
            STRONG_HOLDER_SIGNALS,
        ),

        "Bounty": keyword_matches(
            text,
            BOUNTY_SIGNALS,
        ),

        "Testnet": keyword_matches(
            text,
            TESTNET_STRONG_SIGNALS,
        ),

        "Points": keyword_matches(
            text,
            STRONG_POINTS_ALLOCATION_SIGNALS
            + STRONG_POINTS_PROGRAM_SIGNALS,
        ),

        "Liquidity": keyword_matches(
            text,
            STRONG_LIQUIDITY_SIGNALS,
        ),

        "Activity": keyword_matches(
            text,
            ACTIVITY_SIGNALS,
        ),

        "Other": keyword_matches(
            text,
            NEWS_SIGNALS,
        ),
    }

    # Contextual testnet evidence.

    if (
        "testnet" in text
        and not evidence["Testnet"]
        and has_testnet_requirement(text)
    ):

        evidence["Testnet"].append(
            "testnet + participation context"
        )

    # Contextual liquidity evidence.

    if (
        "liquidity" in text
        and not evidence["Liquidity"]
        and has_real_liquidity_requirement(text)
    ):

        evidence["Liquidity"].append(
            "liquidity + participation context"
        )

    # Generic points evidence.

    if (
        contains_any(
            text,
            ["points", "xp"],
        )
        and not evidence["Points"]
        and has_points_requirement(text)
    ):

        evidence["Points"].append(
            "points/xp + reward context"
        )

    return evidence


# ============================================================
# CONFIDENCE
# ============================================================

def calculate_confidence(candidate, category=None):
    """
    Calculate deterministic informational confidence.

    This function does NOT modify the database.
    """

    if category is None:
        category = classify_airdrop(candidate)

    text = get_candidate_text(candidate)

    if not text:
        return 0.0

    evidence = get_classification_evidence(
        candidate
    )

    matches = evidence.get(
        category,
        [],
    )

    if not matches:
        return 35.0

    strong_counts = {

        "Retroactive": 4,
        "Holder": 4,
        "Bounty": 4,

        "Testnet": 3,
        "Points": 3,
        "Liquidity": 3,

        "Activity": 2,
        "Other": 2,
    }

    base = {

        "Retroactive": 55.0,
        "Holder": 55.0,
        "Bounty": 60.0,

        "Testnet": 55.0,
        "Points": 55.0,
        "Liquidity": 55.0,

        "Activity": 50.0,
        "Other": 50.0,

    }.get(
        category,
        50.0,
    )

    bonus = min(
        len(matches)
        * strong_counts.get(
            category,
            2,
        ),
        35,
    )

    return min(
        95.0,
        base + bonus,
    )


# ============================================================
# CLASSIFICATION DETAILS
# ============================================================

def classify_with_details(candidate):
    """
    Return complete classification information.
    """

    category = classify_airdrop(
        candidate
    )

    evidence = get_classification_evidence(
        candidate
    )

    confidence = calculate_confidence(
        candidate,
        category,
    )

    return {

        "category": category,

        "confidence": round(
            confidence,
            1,
        ),

        "evidence": evidence,

        "classifier_version":
            CLASSIFIER_VERSION,
    }


# ============================================================
# CATEGORY DISTRIBUTION
# ============================================================

def category_distribution(candidates):
    """
    Calculate category distribution.

    Does not modify anything.
    """

    counts = Counter(
        classify_airdrop(candidate)
        for candidate in candidates
    )

    return {
        category:
            counts.get(category, 0)
        for category in CATEGORIES
    }


# ============================================================
# REGRESSION TESTS
# ============================================================

TEST_CASES = [

    # --------------------------------------------------------
    # RETROACTIVE
    # --------------------------------------------------------

    (
        "Historical Users",
        "Historical users are eligible for the airdrop.",
        "Retroactive",
    ),

    (
        "Early Users Alone",
        "Early users can trade on the platform.",
        "Activity",
    ),

    (
        "Retroactive Word Alone",
        "The project discusses a possible retroactive program.",
        "Other",
    ),

    (
        "Retroactive Airdrop",
        "The protocol announced a retroactive airdrop.",
        "Retroactive",
    ),

    # --------------------------------------------------------
    # HOLDER
    # --------------------------------------------------------

    (
        "Holder Snapshot",
        "Eligible holders were selected using a holder snapshot.",
        "Holder",
    ),

    (
        "Minimum Balance",
        "Users must maintain a minimum token balance.",
        "Holder",
    ),

    (
        "Generic Holder",
        "The protocol has many token holders.",
        "Other",
    ),

    (
        "Snapshot Alone",
        "A snapshot will be taken on Friday.",
        "Other",
    ),

    (
        "Token Snapshot Alone",
        "The protocol will publish a token snapshot.",
        "Other",
    ),

    # --------------------------------------------------------
    # BOUNTY
    # --------------------------------------------------------

    (
        "Bug Bounty",
        "Report security bugs and earn rewards through the bug bounty.",
        "Bounty",
    ),

    (
        "Content Bounty",
        "Complete the content bounty campaign for rewards.",
        "Bounty",
    ),

    # --------------------------------------------------------
    # TESTNET
    # --------------------------------------------------------

    (
        "Testnet Campaign",
        "Join the public testnet campaign and complete transactions.",
        "Testnet",
    ),

    (
        "Testnet",
        "Users can join the testnet and earn rewards.",
        "Testnet",
    ),

    (
        "Test Tokens",
        "Claim test tokens from the faucet and use the network.",
        "Testnet",
    ),

    (
        "Testnet Points",
        "Use the testnet to earn points through transactions.",
        "Testnet",
    ),

    (
        "Testnet Liquidity Points",
        "On testnet, provide liquidity and earn points.",
        "Testnet",
    ),

    # --------------------------------------------------------
    # POINTS
    # --------------------------------------------------------

    (
        "Points Allocation",
        "Points determine allocation of the token airdrop.",
        "Points",
    ),

    (
        "Points Program",
        "Join the points program and earn points.",
        "Points",
    ),

    (
        "Earn Points",
        "Users earn points for qualifying activities.",
        "Points",
    ),

    (
        "Checkpoint XP Reward",
        "XP determines rewards in the campaign.",
        "Points",
    ),

    (
        "Limitless Points",
        "The points system determines future rewards.",
        "Points",
    ),

    (
        "Points Campaign",
        "Complete the points campaign to earn allocation.",
        "Points",
    ),

    # --------------------------------------------------------
    # LIQUIDITY
    # --------------------------------------------------------

    (
        "Liquidity",
        "Provide liquidity to earn rewards.",
        "Liquidity",
    ),

    (
        "Liquidity Provider",
        "Liquidity providers receive rewards.",
        "Liquidity",
    ),

    (
        "Liquidity Vault",
        "Deposit into the liquidity vault and earn yield.",
        "Liquidity",
    ),

    (
        "Staking Rewards",
        "Stake tokens to earn staking rewards.",
        "Liquidity",
    ),

    (
        "Yield Farming",
        "Use the yield farming strategy to earn yield.",
        "Liquidity",
    ),

    # --------------------------------------------------------
    # ACTIVITY
    # --------------------------------------------------------

    (
        "Trading",
        "Trade on the protocol to qualify.",
        "Activity",
    ),

    (
        "Swapping",
        "Swap tokens and complete quests.",
        "Activity",
    ),

    (
        "Quest",
        "Complete quests and daily tasks.",
        "Activity",
    ),

    (
        "Referral",
        "Invite friends and complete referral activities.",
        "Activity",
    ),

    (
        "Gaming",
        "Play the game and complete missions.",
        "Activity",
    ),

    (
        "Wallet",
        "Connect your wallet and use the application.",
        "Activity",
    ),

    # --------------------------------------------------------
    # OTHER
    # --------------------------------------------------------

    (
        "News Article",
        "Breaking news: the protocol announced a major update.",
        "Other",
    ),

    (
        "Funding News",
        "The company raised funding from major investors.",
        "Other",
    ),

    (
        "Market Update",
        "Bitcoin price falls as the crypto market reacts.",
        "Other",
    ),
]


# ============================================================
# TEST RUNNER
# ============================================================

def run_tests():
    """
    Run all classifier regression tests.
    """

    print()

    print("🧪 CATEGORY CLASSIFIER TESTS")

    print("=" * 60)

    passed = 0
    failed = 0

    failures = []

    for name, text, expected in TEST_CASES:

        actual = classify_airdrop(
            text
        )

        if actual == expected:

            passed += 1

            print(
                f"✅ PASS | "
                f"{name} → {actual}"
            )

        else:

            failed += 1

            failures.append({

                "name": name,
                "text": text,
                "expected": expected,
                "actual": actual,

            })

            print(
                f"❌ FAIL | "
                f"{name} → "
                f"{actual} "
                f"(expected {expected})"
            )

    print("=" * 60)

    print(
        f"Tests passed: "
        f"{passed}/{len(TEST_CASES)}"
    )

    print(
        f"Tests failed: "
        f"{failed}/{len(TEST_CASES)}"
    )

    if failures:

        print()

        print("❌ FAILURES")

        print("-" * 60)

        for failure in failures:

            print(
                f"• {failure['name']}: "
                f"expected={failure['expected']}, "
                f"actual={failure['actual']}"
            )

    return (
        passed,
        failed,
        failures,
    )


# ============================================================
# SIMPLE LIVE CLASSIFICATION
# ============================================================

def classify_text(text):
    """
    Convenience wrapper for raw text.
    """

    return classify_airdrop(text)


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        "🚀 AirdropRadar Category Classifier"
    )

    print(
        f"🧠 Classifier version: "
        f"{CLASSIFIER_VERSION}"
    )

    print()

    passed, failed, failures = run_tests()

    print()

    if failed == 0:

        print(
            "✅ Classifier tests passed."
        )

        print(
            "🛡️ Database was NOT modified."
        )

        print()

        print(
            "ℹ️ Run category_calibration.py "
            "separately to inspect the "
            "real database records."
        )

    else:

        print(
            "⚠️ Classifier tests failed."
        )

        print(
            "🛡️ Database was NOT modified."
        )

        print()

        print(
            "❌ Do NOT backfill the database "
            "until the regression tests pass."
        )

    return 0 if failed == 0 else 1


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    raise SystemExit(main())
