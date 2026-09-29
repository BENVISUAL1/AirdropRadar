"""
AirdropRadar Participation Intelligence
V1.1

Extracts actionable participation information from verified
airdrop opportunity data without inventing missing details.
"""

from asyncio import tasks
from email.mime import text
import re


# ============================================================
# PARTICIPATION PATTERNS
# ============================================================
TASK_PATTERNS = [
    ("Create account", [
        r"\bcreate\s+(?:an?\s+)?(?:your\s+)?account\b",
        r"\bcreate\s+(?:an?\s+)?account\b",
        r"\bsign\s*up\b",
        r"\bregister\s+(?:an?\s+)?account\b",
    ]),

    ("Connect wallet", [
        r"\bconnect(?:ing)?\s+(?:your\s+)?(?:evm\s+|ethereum[-\s]?compatible\s+|solana\s+|sui\s+)?wallet\b",
        r"\bconnect\s+(?:your\s+)?wallet\b",
        r"\bwallet\s+connection\b",
    ]),

   ("Connect X", [
    r"\bconnect\s+(?:your\s+)?x\s+account\b",
    r"\bconnect\s+(?:your\s+)?twitter\s+account\b",
    r"\blink\s+(?:your\s+)?x\s+account\b",
    r"\blink\s+(?:your\s+)?twitter\s+account\b",
    r"\bconnect\s+x\s+and\s+(?:solana\s+)?wallet\b",
    r"\bconnect\s+(?:your\s+)?x\b",
    r"\blink\s+(?:your\s+)?x\b",
]),

    ("Bind wallet", [
        r"\bbind\s+(?:your\s+)?(?:sui|evm|solana)\s+wallet\b",
        r"\bbind\s+(?:your\s+)?wallet\b",
    ]),

    ("Complete onboarding", [
        r"\bcomplete\s+(?:the\s+)?onboarding\b",
        r"\bcomplete\s+(?:your\s+)?onboarding\b",
        r"\bfinish\s+(?:the\s+)?onboarding\b",
    ]),

    ("Complete verification", [
        r"\bcomplete\s+(?:the\s+)?verificationverification\b",
        r"\bcomplete\s+(?:your\s+)?verification\b",
        r"\bverify\s+(?:your\s+)?account\b",
        r"\bcomplete\s+(?:the\s+)?account\s+verification\b",
    ]),

    ("Complete quests", [
        r"\bcomplete\s+(?:the\s+)?(?:campaign\s+)?quests?\b",
        r"\bcomplete\s+(?:daily|social|campaign)\s+quests?\b",
        r"\bcomplete\s+(?:the\s+)?(?:core|daily|fam|burst)\s+quests?\b",
        r"\bquests?\s+(?:and\s+)?earn\b",
    ]),

    ("Complete social tasks", [
        r"\bcomplete\s+(?:the\s+)?social\s+tasks?\b",
        r"\bcomplete\s+(?:your\s+)?social\s+tasks?\b",
        r"\bdo\s+(?:the\s+)?social\s+tasks?\b",
    ]),

    ("Submit content", [
        r"\bsubmit\s+(?:the\s+)?(?:link|post|content)\b",
        r"\bsubmit\s+(?:your\s+)?(?:x|twitter)\s+post\b",
        r"\bsubmit\s+(?:a|your)\s+post\b",
        r"\bpublish\s+(?:a|your)\s+(?:post|content)\s+on\s+(?:x|twitter)\b",
        r"\bcreate\s+(?:original\s+)?(?:content|posts?)\b",
    ]),

    ("Refer friends", [
        r"\binvite\s+(?:your\s+)?friends\b",
        r"\binvite\s+friends\b",
        r"\brefer\s+(?:your\s+)?friends\b",
        r"\brefer\s+friends\b",
        r"\breferral\s+program\b",
        r"\breferrals?\b",
    ]),

    ("Vote", [
        r"\bvote(?:d|s|ing)?\s+(?:on\s+)?(?:polls?|questions?)\b",
        r"\bdaily\s+voting\b",
        r"\bcast\s+(?:your\s+)?votes?\b",
        r"\bvote\s+through\b",
    ]),

    ("Complete swaps", [
        r"\bcomplete(?:ing)?\s+(?:the\s+)?(?:required\s+)?swaps?\b",
        r"\bmake(?:ing)?\s+(?:the\s+)?(?:required\s+)?swaps?\b",
        r"\bperform(?:ing)?\s+(?:the\s+)?(?:required\s+)?swaps?\b",
        r"\bswap(?:ping)?\s+(?:your\s+)?(?:tokens?|assets?)\b",
    ]),

    ("Complete transactions", [
        r"\bcomplete(?:ing)?\s+(?:the\s+)?(?:required\s+)?transactions?\b",
        r"\bmake(?:ing)?\s+(?:the\s+)?(?:required\s+)?transactions?\b",
        r"\bcomplete\s+(?:the\s+)?on.?chain\s+transactions?\b",
        r"\bperform\s+(?:the\s+)?on.?chain\s+transactions?\b",
    ]),

    ("Use the protocol", [
        r"\buse\s+(?:the\s+)?(?:protocol|platform|dapp)\b",
        r"\buse\s+(?:the\s+)?(?:protocol|platform|dapp)\s+and\b",
        r"\binteract\s+with\s+(?:the\s+)?(?:protocol|platform|dapp)\b",
    ]),

    ("Deposit funds", [
        r"\bdeposit\s+(?:funds|assets|tokens|stablecoins?|usdc|usdt|eth)\b",
        r"\bdeposit\s+(?:into|to)\s+(?:the\s+)?(?:vault|protocol|platform)\b",
        r"\bdeposit\s+(?:your\s+)?(?:stablecoins?|usdc|usdt)\b",
    ]),

    ("Mint assets", [
    r"\bmint\s+(?:an?\s+)?(?:nft|iusd|tokens?|assets?)\b",
    r"\bmint(?:ing)?\s+(?:an?\s+)?(?:nft|iusd)\b",
    r"\bmint\s+to\s+deposit\b",
]),

    ("Lock assets", [
        r"\block\s+(?:your\s+)?(?:iusd|tokens?|assets?)\b",
        r"\block\s+(?:the\s+)?(?:iusd|tokens?|assets?)\b",
    ]),

    ("Provide liquidity", [
        r"\bprovide\s+(?:the\s+)?liquidity\b",
        r"\bprovide\s+liquidity\b",
        r"\badd\s+(?:the\s+)?liquidity\b",
        r"\badd\s+liquidity\b",
    ]),

    ("Stake assets", [
        r"\bstake\s+(?:your\s+)?(?:tokens?|assets?|eth|usdc|usdt)\b",
        r"\bdeposit\s+.*?\s+and\s+stake\b",
        r"\bstake\s+your\b",
    ]),

    ("Bridge assets", [
        r"\bbridge\s+(?:your\s+)?(?:assets?|tokens?|funds?)\b",
        r"\bbridge\s+.*?\bto\b",
        r"\buse\s+(?:the\s+)?bridge\b",
    ]),

  ("Register agent", [
    r"\bregister\s+(?:your\s+)?agent(?:\s+id)?\b",
    r"\bregister\s+agent\s+id\b",
    r"\bregister\s+agent\b",
]),
    ("Activate account or role", [
        r"\bactivate\s+(?:your\s+)?(?:agent|account|profile)\b",
        r"\bactivate\s+(?:the\s+)?(?:client|provider)\b",
    ]),

    ("Post job or service", [
        r"\bpost\s+(?:a\s+)?job\b",
        r"\bpublish\s+(?:a\s+)?service\b",
        r"\bpost\s+(?:your\s+)?service\b",
    ]),
]


REQUIREMENT_PATTERNS = [
    ("Wallet", [
        r"\bconnect\s+(?:your\s+)?(?:evm\s+|ethereum[-\s]?compatible\s+|solana\s+|sui\s+)?wallet\b",
        r"\bwallet\s+(?:is\s+)?required\b",
        r"\brequires?\s+(?:an?\s+)?wallet\b",
    ]),

    ("EVM wallet", [
        r"\bconnect\s+(?:your\s+)?evm\s+wallet\b",
        r"\bconnect\s+(?:your\s+)?ethereum[-\s]?compatible\s+wallet\b",
        r"\bevm\s+wallet\s+(?:is\s+)?required\b",
    ]),

    ("Solana wallet", [
        r"\bconnect\s+(?:your\s+)?solana\s+wallet\b",
        r"\bsolana\s+wallet\s+(?:is\s+)?required\b",
    ]),

    ("Sui wallet", [
        r"\bconnect\s+(?:your\s+)?sui\s+wallet\b",
        r"\bsui\s+wallet\s+(?:is\s+)?required\b",
    ]),

    ("X account", [
        r"\bconnect\s+(?:your\s+)?x\s+account\b",
        r"\bconnect\s+(?:your\s+)?𝕏\s+account\b",
        r"\bconnect\s+(?:your\s+)?twitter\s+account\b",
        r"\blink\s+(?:your\s+)?x\s+account\b",
        r"\blink\s+(?:your\s+)?twitter\s+account\b",
        r"\bx\s+account\s+(?:is\s+)?required\b",
    ]),

    ("Discord account", [
        r"\bconnect\s+(?:your\s+)?discord\s+account\b",
        r"\blink\s+(?:your\s+)?discord\s+account\b",
        r"\bdiscord\s+account\s+(?:is\s+)?required\b",
        r"\bjoin\s+(?:the\s+)?discord\s+(?:server\s+)?to\s+(?:participate|qualify|earn|claim)\b",
    ]),

    ("Solana wallet", [
        r"\bconnect\s+(?:your\s+)?solana\s+wallet\b",
        r"\bconnect\s+(?:your\s+)?(?:𝕏|x|twitter)\s+account\s+and\s+(?:your\s+)?solana\s+wallet\b",
        r"\bconnect\s+(?:your\s+)?solana\s+wallet\s+and\s+(?:your\s+)?(?:𝕏|x|twitter)\s+account\b",
        r"\bsolana\s+wallet\s+(?:is\s+)?required\b",
    ]),

    ("Funds", [
        r"\bminimum\s+(?:balance|deposit)\b",
        r"\bminimum\s+(?:amount|funds)\b",
        r"\bhold\s+(?:at\s+least\s+)?[\d,.]+\s+(?:tokens?|coins?)\b",
        r"\bmust\s+have\s+(?:funds|tokens?|assets?|balance)\b",
    ]),

    ("ETH for gas", [
        r"\bkeep\s+(?:some\s+)?eth\s+for\s+gas\b",
        r"\bhold\s+(?:some\s+)?eth\s+for\s+gas\b",
        r"\beth\s+(?:is\s+)?required\s+for\s+gas\b",
        r"\brequire[s]?\s+eth\s+for\s+gas\b",
    ]),

    ("USDC or stablecoins", [
        r"\brequires?\s+(?:usdc|usdt|stablecoins?)\b",
        r"\bmust\s+(?:have|hold|deposit)\s+(?:usdc|usdt|stablecoins?)\b",
        r"\b(?:usdc|usdt|stablecoins?)\s+(?:is|are)\s+required\b",
    ]),

    ("SBT pass", [
        r"\bsbt\s+pass\s+(?:is\s+)?required\b",
        r"\brequires?\s+(?:an?\s+)?sbt\s+pass\b",
        r"\bmust\s+have\s+(?:an?\s+)?sbt\s+pass\b",
        r"\b(?:eligible|upcoming)\s+sbt\s+pass\b",
        r"\bsbt\s+pass\s+minted\b",
    ]),

    ("U.S. bank account", [
        r"\bu\.?s\.?\s+bank\s+account\s+(?:is\s+)?required\b",
        r"\brequires?\s+(?:a\s+)?u\.?s\.?\s+bank\s+account\b",
        r"\bmust\s+have\s+(?:a\s+)?u\.?s\.?\s+bank\s+account\b",
    ]),

    ("Good credit", [
        r"\bgood\s+credit\s+(?:is\s+)?required\b",
        r"\brequires?\s+(?:a\s+)?good\s+credit\b",
        r"\bmust\s+have\s+(?:a\s+)?good\s+credit\b",
    ]),

    ("Credit score", [
        r"\bcredit\s+score\s+(?:of|above|over|at\s+least)\s+\d+\b",
        r"\brequires?\s+(?:a\s+)?credit\s+score\b",
        r"\bminimum\s+credit\s+score\b",
    ]),

    ("Ethos score", [
        r"\bethos\s+score\s+(?:of|above|over|at\s+least)\s+\d+\b",
        r"\brequires?\s+(?:an?\s+)?ethos\s+score\b",
        r"\bminimum\s+ethos\s+score\b",
    ]),
]

COST_PATTERNS = [
    (r"free", "Free"),
    (r"no cost", "Free"),
    (r"no fee", "Free"),
    (r"no fees", "Free"),
    (r"gas fee", "Gas fees may apply"),
    (r"gas fees", "Gas fees may apply"),
    (r"transaction fee", "Transaction fees may apply"),
    (r"transaction fees", "Transaction fees may apply"),
]


TIME_PATTERNS = [
    (r"(\d+)\s*[-–]\s*(\d+)\s*(?:minutes?|mins?)", "minutes"),
    (r"(\d+)\s*(?:minutes?|mins?)", "minutes"),
    (r"(\d+)\s*[-–]\s*(\d+)\s*(?:hours?|hrs?)", "hours"),
    (r"(\d+)\s*(?:hours?|hrs?)", "hours"),
]


# ============================================================
# HELPERS
# ============================================================

def normalize_text(value):
    """Convert input into clean lowercase text."""
    if value is None:
        return ""

    if not isinstance(value, str):
        value = str(value)

    return re.sub(r"\s+", " ", value).strip().lower()


def unique_list(items):
    """Remove duplicates while preserving order."""
    seen = set()
    result = []

    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


def extract_participation_section(text):
    """
    Extract the step-by-step participation guide when available.

    The guide contains the clearest evidence of what a user
    actually needs to do. If no guide is found, use the full text.
    """
    guide_markers = [
        r"step by step guide",
        r"step-by-step guide",
        r"how to participate",
        r"how to earn",
    ]

    start = None

    for marker in guide_markers:
        match = re.search(marker, text, re.IGNORECASE)

        if match:
            start = match.start()
            break

    if start is None:
        return text

    section = text[start:]

    stop_markers = [
        r"stay tuned with",
        r"use the airdropalert eligibility checker",
    ]

    stop_positions = []

    for marker in stop_markers:
        match = re.search(marker, section, re.IGNORECASE)

        if match:
            stop_positions.append(match.start())

    if stop_positions:
        section = section[:min(stop_positions)]

    return section.strip()



# ============================================================
# TASK EXTRACTION
# ============================================================
def extract_tasks(text):
    """Extract participation tasks from the strongest available evidence."""
    tasks = []
    evidence = []

    task_text = extract_participation_section(text)

    for task_name, patterns in TASK_PATTERNS:
        for pattern in patterns:
            match = re.search(pattern, task_text, re.IGNORECASE)

            if match:
                tasks.append(task_name)
                evidence.append(match.group(0))
                break

    return unique_list(tasks), unique_list(evidence)


# ============================================================
# REQUIREMENT EXTRACTION
# ============================================================

def extract_requirements(text):
    """Extract requirements using specific evidence before generic requirements."""
    requirements = []
    evidence = []

    # Specific requirements take priority over generic ones.
    specific_requirements = [
        "EVM wallet",
        "Solana wallet",
        "Sui wallet",
        "X account",
        "Discord account",
        "Telegram account",
        "ETH for gas",
        "USDC or stablecoins",
        "SBT pass",
        "U.S. bank account",
        "Good credit",
        "Credit score",
        "Ethos score",
    ]

    matched_names = set()

    for requirement_name, patterns in REQUIREMENT_PATTERNS:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)

            if not match:
                continue

            # Skip generic Wallet if a specific wallet type was detected.
            if requirement_name == "Wallet":
                specific_wallets = {
                    "EVM wallet",
                    "Solana wallet",
                    "Sui wallet",
                }

                if specific_wallets.intersection(matched_names):
                    continue

            requirements.append(requirement_name)
            matched_names.add(requirement_name)
            evidence.append(match.group(0))
            break

    # Keep only the most specific wallet requirement.
    wallet_types = {"EVM wallet", "Solana wallet", "Sui wallet"}

    if wallet_types.intersection(matched_names):
        requirements = [
            item for item in requirements
            if item != "Wallet"
        ]

    return unique_list(requirements), unique_list(evidence)

# ============================================================
# COST ANALYSIS
# ============================================================

def estimate_cost(text):
    """
    Estimate cost only when the source text provides evidence.

    We never assume that an opportunity is free simply because
    no cost information was found.
    """

    for pattern, cost in COST_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return {
                "value": cost,
                "confidence": "supported",
                "evidence": pattern,
            }

    if re.search(r"\b(?:swap|bridge|stake|liquidity|transaction)\b", text):
        return {
            "value": "Transaction fees may apply",
            "confidence": "inferred",
            "evidence": "On-chain activity detected",
        }

    return {
        "value": "Unknown",
        "confidence": "unknown",
        "evidence": None,
    }


# ============================================================
# TIME ANALYSIS
# ============================================================

def estimate_time(text):
    """Extract explicit time estimates when available."""

    for pattern, unit in TIME_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)

        if not match:
            continue

        groups = match.groups()

        if len(groups) >= 2 and groups[1]:
            return {
                "value": f"{groups[0]}–{groups[1]} {unit}",
                "confidence": "supported",
                "evidence": match.group(0),
            }

        return {
            "value": f"{groups[0]} {unit}",
            "confidence": "supported",
            "evidence": match.group(0),
        }

    return {
        "value": "Unknown",
        "confidence": "unknown",
        "evidence": None,
    }


# ============================================================
# DIFFICULTY ANALYSIS
# ============================================================

def estimate_difficulty(tasks, requirements):
    """
    Estimate difficulty from detected participation complexity.

    This is explicitly an inference, not a fact from the source.
    """

    task_count = len(tasks)
    requirement_count = len(requirements)

    complex_tasks = {
        "Provide liquidity",
        "Stake assets",
        "Bridge assets",
        "Complete transactions",
    }

    complex_count = len(
        [task for task in tasks if task in complex_tasks]
    )

    if complex_count >= 2 or task_count >= 5:
        return {
            "value": "Hard",
            "confidence": "inferred",
        }

    if complex_count >= 1 or task_count >= 3 or requirement_count >= 3:
        return {
            "value": "Medium",
            "confidence": "inferred",
        }

    if task_count >= 1:
        return {
            "value": "Easy",
            "confidence": "inferred",
        }

    return {
        "value": "Unknown",
        "confidence": "unknown",
    }

# ============================================================
# EVIDENCE INTELLIGENCE
# ============================================================

def build_evidence_item(category, value, evidence, status="supported"):
    """
    Build a structured evidence record.

    status:
        supported = directly found in source text
        inferred  = derived from available evidence
        unknown   = no reliable evidence found
    """
    return {
        "category": category,
        "value": value,
        "evidence": evidence,
        "status": status,
    }


def build_evidence(
    tasks,
    task_evidence,
    requirements,
    requirement_evidence,
    time,
    cost,
    difficulty,
):
    """
    Build structured evidence for participation intelligence.
    """

    evidence_items = []

    # Tasks
    for task, evidence in zip(tasks, task_evidence):
        evidence_items.append(
            build_evidence_item(
                "task",
                task,
                evidence,
                "supported",
            )
        )

    # Requirements
    for requirement, evidence in zip(
        requirements,
        requirement_evidence,
    ):
        evidence_items.append(
            build_evidence_item(
                "requirement",
                requirement,
                evidence,
                "supported",
            )
        )

    # Time
    if time["value"] != "Unknown":
        evidence_items.append(
            build_evidence_item(
                "time",
                time["value"],
                time["evidence"],
                time["confidence"],
            )
        )

    # Cost
    if cost["value"] != "Unknown":
        evidence_items.append(
            build_evidence_item(
                "cost",
                cost["value"],
                cost["evidence"],
                cost["confidence"],
            )
        )

    # Difficulty
    if difficulty["value"] != "Unknown":
        evidence_items.append(
            build_evidence_item(
                "difficulty",
                difficulty["value"],
                "Derived from detected tasks and requirements.",
                difficulty["confidence"],
            )
        )

    return evidence_items


# ============================================================
# MAIN ANALYZER
# ============================================================

def analyze_participation(airdrop):
    """
    Analyze participation requirements for an airdrop.

    Expected input:
        {
            "name": ...,
            "description": ...,
            "url": ...,
            "official_links": ...,
            ...
        }
    """

    if not isinstance(airdrop, dict):
        raise TypeError("airdrop must be a dictionary")

    name = airdrop.get("name", "")
    description = airdrop.get("description", "")
    url = airdrop.get("url", "")

    source_text = " ".join([
        str(name or ""),
        str(description or ""),
        str(url or ""),
    ])

    text = normalize_text(source_text)

    tasks, task_evidence = extract_tasks(text)
    requirements, requirement_evidence = extract_requirements(text)

    cost = estimate_cost(text)
    time = estimate_time(text)
    difficulty = estimate_difficulty(tasks, requirements)

    evidence = unique_list(
        task_evidence
        + requirement_evidence
        + [
            cost["evidence"]
            for cost in [cost]
            if cost["evidence"]
        ]
        + [
            time["evidence"]
            for time in [time]
            if time["evidence"]
        ]
    )

    if tasks:
        overall_confidence = "medium"
    else:
        overall_confidence = "low"

    evidence_details = build_evidence(
        tasks,
        task_evidence,
        requirements,
        requirement_evidence,
        time,
        cost,
        difficulty,
    )

    return {
        "tasks": {
            "items": tasks,
            "confidence": "supported" if tasks else "unknown",
            "evidence": task_evidence,
        },

        "requirements": {
            "items": requirements,
            "confidence": "supported" if requirements else "unknown",
            "evidence": requirement_evidence,
        },

        "estimated_time": {
            "value": time["value"],
            "confidence": time["confidence"],
        },

        "estimated_cost": {
            "value": cost["value"],
            "confidence": cost["confidence"],
        },

        "difficulty": {
            "value": difficulty["value"],
            "confidence": difficulty["confidence"],
        },

        "evidence": evidence,
        "evidence_details": evidence_details,
        "confidence": overall_confidence,
    }


# ============================================================
# TESTS
# ============================================================

if __name__ == "__main__":

    test_cases = [
        {
            "name": "Points Campaign",
            "description": (
                "Connect your wallet and complete daily swaps "
                "to earn points. Gas fees may apply."
            ),
            "url": "https://example.com",
        },
        {
            "name": "Liquidity Campaign",
            "description": (
                "Provide liquidity to the protocol and stake "
                "your LP tokens to earn rewards."
            ),
            "url": "https://example.com",
        },
        {
            "name": "Testnet",
            "description": (
                "Join the testnet, connect your wallet, "
                "complete transactions and use the protocol."
            ),
            "url": "https://example.com",
        },
        {
            "name": "Social Campaign",
            "description": (
                "Follow us on X, join our Discord and "
                "complete the campaign quests."
            ),
            "url": "https://example.com",
        },
        {
            "name": "Bridge Campaign",
            "description": (
                "Bridge assets to the network and complete "
                "on-chain activity."
            ),
            "url": "https://example.com",
        },
        {
            "name": "NFT Campaign",
            "description": (
                "Connect your wallet and mint an NFT."
            ),
            "url": "https://example.com",
        },

                {
            "name": "Explicit Time and Free Cost",
            "description": (
                "Connect your wallet and complete the campaign. "
                "The task takes approximately 15 minutes and is free "
                "with no fees required."
            ),
            "url": "https://example.com",
        },
        {
            "name": "Explicit Time Range and Gas",
            "description": (
                "Complete the required swaps. "
                "This usually takes 15–30 minutes. "
                "Gas fees may apply."
            ),
            "url": "https://example.com",
        },

        
        {
            "name": "Unknown Opportunity",
            "description": (
                "A new protocol has announced an upcoming "
                "community campaign."
            ),
            "url": "https://example.com",
        },
    ]

    print("\n🎯 AIRDROPRADAR PARTICIPATION INTELLIGENCE")
    print("=" * 70)

    for index, test_case in enumerate(test_cases, start=1):

        result = analyze_participation(test_case)

        print(f"\nTEST {index}: {test_case['name']}")
        print("-" * 70)

        print(
             f"Tasks:        {result['tasks']['items']} "
             f"({result['tasks']['confidence']})"
        )

        print(
            f"Requirements: {result['requirements']['items']} "
            f"({result['requirements']['confidence']})"
        )
        print(
            f"Time:         {result['estimated_time']['value']} "
            f"({result['estimated_time']['confidence']})"
        )

        print(
            f"Cost:         {result['estimated_cost']['value']} "
            f"({result['estimated_cost']['confidence']})"
        )

        print(
            f"Difficulty:   {result['difficulty']['value']} "
            f"({result['difficulty']['confidence']})"
        )

        print(f"Confidence:   {result['confidence']}")
        print(f"Evidence:     {result['evidence']}")