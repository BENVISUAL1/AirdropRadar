# -----------------------------------------
# AIRDROP INTELLIGENCE ENGINE
# -----------------------------------------


def analyze_intelligence(result):

    # -------------------------------------
    # PRESERVE ORIGINAL RESULT
    # -------------------------------------

    if not isinstance(result, dict):
        result = {}

    # Create a copy so we don't accidentally
    # destroy the verifier result.
    enriched = dict(result)

    market = result.get(
        "market_signal",
        {}
    )

    defi = result.get(
        "defi_signal",
        {}
    )

    if not isinstance(market, dict):
        market = {}

    if not isinstance(defi, dict):
        defi = {}

    intelligence = {

        "market_status": "Unknown",

        "market_name": "",

        "market_symbol": "",

        "market_rank": None,

        "market_match": 0,

        "defi_status": "Unknown",

        "defi_protocol": "",

        "defi_tvl": 0,

        "defi_match": 0,

        "signals": [],

        "warnings": [],

        "strength": "Weak",

    }

    # -------------------------------------
    # COINGECKO
    # -------------------------------------

    market_signal = market.get(
        "signal",
        ""
    )

    if market.get("found"):

        intelligence["market_status"] = (
            "Recognized"
        )

        intelligence["market_name"] = (
            market.get(
                "name",
                ""
            )
        )

        intelligence["market_symbol"] = (
            market.get(
                "symbol",
                ""
            )
        )

        intelligence["market_rank"] = (
            market.get(
                "market_rank"
            )
        )

        intelligence["market_match"] = (
            market.get(
                "match_score",
                0
            )
        )

        intelligence["signals"].append(
            "CoinGecko recognition"
        )

    elif market_signal == "api_unavailable":

        intelligence["market_status"] = (
            "Unavailable"
        )

    else:

        intelligence["market_status"] = (
            "Not found"
        )

    # -------------------------------------
    # DEFILLAMA
    # -------------------------------------

    defi_signal = defi.get(
        "signal",
        ""
    )

    if defi.get("found"):

        intelligence["defi_status"] = (
            "Recognized"
        )

        intelligence["defi_protocol"] = (
            defi.get(
                "protocol",
                ""
            )
        )

        intelligence["defi_tvl"] = (
            defi.get(
                "tvl",
                0
            ) or 0
        )

        intelligence["defi_match"] = (
            defi.get(
                "match_score",
                0
            )
        )

        intelligence["signals"].append(
            "DeFiLlama recognition"
        )

        # ---------------------------------
        # TVL SIGNAL
        # ---------------------------------

        tvl = intelligence[
            "defi_tvl"
        ]

        if tvl >= 100_000_000:

            intelligence["signals"].append(
                "Strong TVL"
            )

        elif tvl >= 10_000_000:

            intelligence["signals"].append(
                "Established TVL"
            )

        elif tvl >= 1_000_000:

            intelligence["signals"].append(
                "Measurable TVL"
            )

    elif defi_signal == "api_unavailable":

        intelligence["defi_status"] = (
            "Unavailable"
        )

    else:

        intelligence["defi_status"] = (
            "Not found"
        )

    # -------------------------------------
    # INTELLIGENCE WARNINGS
    # -------------------------------------

    if (
        intelligence["market_status"]
        == "Not found"
        and
        intelligence["defi_status"]
        == "Not found"
    ):

        intelligence["warnings"].append(
            "No market or DeFi intelligence found"
        )

    # -------------------------------------
    # INTELLIGENCE STRENGTH
    # -------------------------------------

    signal_count = len(
        intelligence["signals"]
    )

    if signal_count >= 3:

        intelligence["strength"] = (
            "Strong"
        )

    elif signal_count >= 1:

        intelligence["strength"] = (
            "Moderate"
        )

    else:

        intelligence["strength"] = (
            "Weak"
        )

    # -------------------------------------
    # MERGE INTELLIGENCE INTO ORIGINAL
    # -------------------------------------

    enriched["intelligence"] = intelligence

    # Preserve existing warnings from
    # verification and add intelligence
    # warnings without destroying them.

    existing_warnings = enriched.get(
        "warnings",
        []
    )

    if not isinstance(
        existing_warnings,
        list
    ):
        existing_warnings = []

    combined_warnings = list(
        existing_warnings
    )

    for warning in intelligence[
        "warnings"
    ]:

        if warning not in combined_warnings:

            combined_warnings.append(
                warning
            )

    enriched["warnings"] = (
        combined_warnings
    )

    return enriched


# -----------------------------------------
# HUMAN-READABLE SUMMARY
# -----------------------------------------


def intelligence_summary(result):

    intelligence = analyze_intelligence(
        result
    )

    lines = []

    # -------------------------------------
    # MARKET
    # -------------------------------------

    if (
        intelligence["intelligence"][
            "market_status"
        ]
        == "Recognized"
    ):

        market_intelligence = (
            intelligence[
                "intelligence"
            ]
        )

        name = market_intelligence[
            "market_name"
        ]

        symbol = market_intelligence[
            "market_symbol"
        ]

        rank = market_intelligence[
            "market_rank"
        ]

        match = market_intelligence[
            "market_match"
        ]

        market_line = (
            f"🪙 CoinGecko: "
            f"✅ {name}"
        )

        if symbol:

            market_line += (
                f" ({symbol.upper()})"
            )

        if rank:

            market_line += (
                f" | Rank #{rank}"
            )

        market_line += (
            f" | Match {match}%"
        )

        lines.append(
            market_line
        )

    elif (
        intelligence["intelligence"][
            "market_status"
        ]
        == "Unavailable"
    ):

        lines.append(
            "🪙 CoinGecko: ⚠️ Unavailable"
        )

    else:

        lines.append(
            "🪙 CoinGecko: ❌ Not found"
        )

    # -------------------------------------
    # DEFI
    # -------------------------------------

    intelligence_data = (
        intelligence[
            "intelligence"
        ]
    )

    if (
        intelligence_data[
            "defi_status"
        ]
        == "Recognized"
    ):

        protocol = intelligence_data[
            "defi_protocol"
        ]

        tvl = intelligence_data[
            "defi_tvl"
        ]

        match = intelligence_data[
            "defi_match"
        ]

        if tvl:

            if tvl >= 1_000_000_000:

                tvl_text = (
                    f"${tvl / 1_000_000_000:.2f}B"
                )

            elif tvl >= 1_000_000:

                tvl_text = (
                    f"${tvl / 1_000_000:.2f}M"
                )

            elif tvl >= 1_000:

                tvl_text = (
                    f"${tvl / 1_000:.2f}K"
                )

            else:

                tvl_text = (
                    f"${tvl:.0f}"
                )

        else:

            tvl_text = "N/A"

        lines.append(
            f"🧩 DeFiLlama: ✅ "
            f"{protocol or 'Recognized'}"
            f" | TVL {tvl_text}"
            f" | Match {match}%"
        )

    elif (
        intelligence_data[
            "defi_status"
        ]
        == "Unavailable"
    ):

        lines.append(
            "🧩 DeFiLlama: ⚠️ Unavailable"
        )

    else:

        lines.append(
            "🧩 DeFiLlama: ❌ Not found"
        )

    # -------------------------------------
    # STRENGTH
    # -------------------------------------

    lines.append(
        f"🧠 Intelligence strength: "
        f"{intelligence_data['strength']}"
    )

    # -------------------------------------
    # WARNINGS
    # -------------------------------------

    for warning in intelligence.get(
        "warnings",
        []
    ):

        lines.append(
            f"⚠️ {warning}"
        )

    return "\n".join(lines)


# -----------------------------------------
# TEST
# -----------------------------------------


if __name__ == "__main__":

    from api_sources import (
        get_project_intelligence
    )

    print(
        "🧠 Testing AirdropRadar "
        "Intelligence Engine...\n"
    )

    # -------------------------------------
    # GET REAL API INTELLIGENCE
    # -------------------------------------

    result = get_project_intelligence(
        "Bitcoin"
    )

    # -------------------------------------
    # ANALYZE RESULT
    # -------------------------------------

    analyzed = analyze_intelligence(
        result
    )

    intelligence = analyzed[
        "intelligence"
    ]

    print(
        "\n📊 Intelligence Analysis\n"
    )

    print(
        f"🪙 Market status: "
        f"{intelligence['market_status']}"
    )

    print(
        f"🔤 Market name: "
        f"{intelligence['market_name']}"
    )

    print(
        f"🎯 Market match: "
        f"{intelligence['market_match']}%"
    )

    print(
        f"📊 Market rank: "
        f"{intelligence['market_rank']}"
    )

    print(
        f"🧩 DeFi status: "
        f"{intelligence['defi_status']}"
    )

    print(
        f"💰 DeFi TVL: "
        f"{intelligence['defi_tvl']}"
    )

    print(
        f"🎯 DeFi match: "
        f"{intelligence['defi_match']}%"
    )

    print(
        f"💪 Intelligence strength: "
        f"{intelligence['strength']}"
    )

    # -------------------------------------
    # SUMMARY
    # -------------------------------------

    print(
        "\n📋 Human-readable summary:\n"
    )

    print(
        intelligence_summary(
            analyzed
        )
    )