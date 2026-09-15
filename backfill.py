import sqlite3

from config import DATABASE_NAME

from database import (
    create_database,
    get_all_airdrops,
    update_airdrop_intelligence,
)

from verifier import verify_candidate

from scorer import (
    calculate_score,
    calculate_confidence,
)

from intelligence import (
    analyze_intelligence,
    intelligence_summary,
)


# -----------------------------------------
# SETTINGS
# -----------------------------------------

MAX_BACKFILL = 1000


# -----------------------------------------
# GET EXISTING DATABASE DATA
# -----------------------------------------

def get_existing_record(
    airdrop_id
):

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            score,
            confidence,
            verification_level,
            official_links,
            warnings,
            market_signal,
            defi_signal
        FROM airdrops
        WHERE id = ?
        """,
        (
            airdrop_id,
        )
    )

    row = cursor.fetchone()

    connection.close()

    if not row:

        return {

            "score": None,

            "confidence": None,

            "verification_level": "",

            "official_links": [],

            "warnings": [],

            "market_signal": {},

            "defi_signal": {}

        }


    (
        score,
        confidence,
        verification_level,
        official_links,
        warnings,
        market_signal,
        defi_signal,
    ) = row


    # -------------------------------------
    # JSON DATA
    # -------------------------------------

    import json


    try:

        existing_links = (
            json.loads(
                official_links
            )
            if official_links
            else []
        )

    except Exception:

        existing_links = []


    try:

        existing_warnings = (
            json.loads(
                warnings
            )
            if warnings
            else []
        )

    except Exception:

        existing_warnings = []


    try:

        existing_market = (
            json.loads(
                market_signal
            )
            if market_signal
            else {}
        )

    except Exception:

        existing_market = {}


    try:

        existing_defi = (
            json.loads(
                defi_signal
            )
            if defi_signal
            else {}
        )

    except Exception:

        existing_defi = {}


    return {

        "score":
            score,

        "confidence":
            confidence,

        "verification_level":
            verification_level or "",

        "official_links":
            existing_links,

        "warnings":
            existing_warnings,

        "market_signal":
            existing_market,

        "defi_signal":
            existing_defi

    }


# -----------------------------------------
# CHECK WHETHER INTELLIGENCE IS USEFUL
# -----------------------------------------

def has_reliable_intelligence(
    result
):

    market = result.get(
        "market_signal",
        {}
    )

    defi = result.get(
        "defi_signal",
        {}
    )


    if not isinstance(
        market,
        dict
    ):

        market = {}


    if not isinstance(
        defi,
        dict
    ):

        defi = {}


    market_found = bool(
        market.get(
            "found",
            False
        )
    )


    defi_found = bool(
        defi.get(
            "found",
            False
        )
    )


    return (
        market_found
        or defi_found
    )


# -----------------------------------------
# CHECK WHETHER RESULT IS SOURCE-UNAVAILABLE
# -----------------------------------------

def source_is_unavailable(
    result
):

    return (
        result.get(
            "verification_level",
            ""
        )
        == "source_unavailable"
    )


# -----------------------------------------
# MERGE EXISTING AND NEW DATA
# -----------------------------------------

def merge_data(
    existing,
    result
):

    merged = {}


    # -------------------------------------
    # MARKET INTELLIGENCE
    # -------------------------------------

    new_market = result.get(
        "market_signal",
        {}
    )


    old_market = existing.get(
        "market_signal",
        {}
    )


    if (
        isinstance(
            new_market,
            dict
        )
        and new_market.get(
            "found",
            False
        )
    ):

        merged[
            "market_signal"
        ] = new_market

    else:

        merged[
            "market_signal"
        ] = old_market


    # -------------------------------------
    # DEFI INTELLIGENCE
    # -------------------------------------

    new_defi = result.get(
        "defi_signal",
        {}
    )


    old_defi = existing.get(
        "defi_signal",
        {}
    )


    if (
        isinstance(
            new_defi,
            dict
        )
        and new_defi.get(
            "found",
            False
        )
    ):

        merged[
            "defi_signal"
        ] = new_defi

    else:

        merged[
            "defi_signal"
        ] = old_defi


    # -------------------------------------
    # OFFICIAL LINKS
    # -------------------------------------

    new_links = result.get(
        "official_links",
        []
    )


    old_links = existing.get(
        "official_links",
        []
    )


    if new_links:

        merged[
            "official_links"
        ] = new_links

    else:

        merged[
            "official_links"
        ] = old_links


    # -------------------------------------
    # WARNINGS
    # -------------------------------------

    new_warnings = result.get(
        "warnings",
        []
    )


    # Do NOT treat source access
    # problems as scam warnings.

    real_warnings = [

        warning

        for warning in new_warnings

        if warning
        != "candidate page unreachable"

    ]


    if real_warnings:

        merged[
            "warnings"
        ] = real_warnings

    else:

        merged[
            "warnings"
        ] = []


    # -------------------------------------
    # VERIFICATION
    # -------------------------------------

    new_verification = result.get(
        "verification_level",
        ""
    )


    old_verification = existing.get(
        "verification_level",
        ""
    )


    if (
        new_verification
        == "source_unavailable"
    ):

        # Preserve previous verification
        # instead of downgrading the project
        # simply because the source website
        # could not be reached.

        merged[
            "verification_level"
        ] = old_verification

    else:

        merged[
            "verification_level"
        ] = new_verification


    return merged


# -----------------------------------------
# PROCESS ONE EXISTING AIRDROP
# -----------------------------------------

def process_existing_airdrop(
    row
):

    (
        airdrop_id,
        name,
        url,
        description,
        source,
    ) = row


    print(
        "\n" + "=" * 60
    )


    print(
        f"🪂 {name}"
    )


    print(
        f"🔗 {url}"
    )


    candidate = {

        "name":
            name,

        "url":
            url,

        "description":
            description or "",

        "source":
            source or "",

    }


    # -------------------------------------
    # LOAD EXISTING DATA
    # -------------------------------------

    existing = get_existing_record(
        airdrop_id
    )


    # -------------------------------------
    # VERIFICATION
    # -------------------------------------

    print(
        "🔎 Running verification..."
    )


    result = verify_candidate(
        candidate
    )


    # -------------------------------------
    # CHECK SOURCE STATUS
    # -------------------------------------

    unavailable = source_is_unavailable(
        result
    )


    if unavailable:

        print(
            "⚠️ Source page unavailable."
        )

        print(
            "➡️ Existing verification "
            "data will be preserved."
        )


    # -------------------------------------
    # INTELLIGENCE
    # -------------------------------------

    intelligence = analyze_intelligence(
        result
    )


    result[
        "intelligence"
    ] = intelligence


    print(
        "\n🧠 Intelligence:"
    )


    print(
        intelligence_summary(
            result
        )
    )


    # -------------------------------------
    # INTELLIGENCE SAFETY CHECK
    # -------------------------------------

    reliable_intelligence = (
        has_reliable_intelligence(
            result
        )
    )


    if reliable_intelligence:

        print(
            "\n✅ Reliable project "
            "intelligence detected."
        )

    else:

        print(
            "\n⚠️ No positive market/"
            "DeFi intelligence detected."
        )

        print(
            "➡️ Existing intelligence "
            "will be preserved."
        )


    # -------------------------------------
    # MERGE DATA
    # -------------------------------------

    merged = merge_data(
        existing,
        result
    )


    # -------------------------------------
    # BUILD SCORING RESULT
    # -------------------------------------

    scoring_result = {

        "name":
            name,

        "url":
            url,

        "description":
            description or "",

        "source":
            source or "",

        "market_signal":
            merged[
                "market_signal"
            ],

        "defi_signal":
            merged[
                "defi_signal"
            ],

        "official_links":
            merged[
                "official_links"
            ],

        "warnings":
            merged[
                "warnings"
            ],

        "verification_level":
            merged[
                "verification_level"
            ]

    }


    # -------------------------------------
    # SCORE
    # -------------------------------------

    score = calculate_score(
        scoring_result
    )


    # -------------------------------------
    # CONFIDENCE
    # -------------------------------------

    confidence = calculate_confidence(
        scoring_result
    )


    # -------------------------------------
    # SAFETY CHECK
    # -------------------------------------

    if (
        not reliable_intelligence
        and unavailable
    ):

        old_score = existing.get(
            "score"
        )

        old_confidence = existing.get(
            "confidence"
        )


        if old_score is not None:

            print(
                "\n🛡️ Safety protection:"
            )

            print(
                f"➡️ Keeping existing "
                f"score: {old_score}/75"
            )

            score = old_score


        if old_confidence:

            confidence = old_confidence


    # -------------------------------------
    # SAVE UPDATED DATA
    # -------------------------------------

    update_airdrop_intelligence(

        airdrop_id,

        merged[
            "market_signal"
        ],

        merged[
            "defi_signal"
        ],

        score,

        confidence,

        merged[
            "verification_level"
        ],

        merged[
            "official_links"
        ],

        merged[
            "warnings"
        ],

    )


    # -------------------------------------
    # OUTPUT
    # -------------------------------------

    print(
        "\n💾 Database updated safely."
    )


    print(
        f"🎯 Score: "
        f"{score}/75"
    )


    print(
        f"🛡️ Confidence: "
        f"{confidence}"
    )


# -----------------------------------------
# BACKFILL
# -----------------------------------------

def run_backfill():

    create_database()


    print(
        "\n🧠 AIRDROPRADAR "
        "SAFE INTELLIGENCE BACKFILL"
    )


    print(
        "=" * 60
    )


    rows = get_all_airdrops()


    print(
        f"📦 Existing records: "
        f"{len(rows)}"
    )


    processed = 0

    failed = 0


    for row in rows:

        if processed >= MAX_BACKFILL:

            print(
                "\n🛑 Backfill limit reached."
            )

            break


        try:

            process_existing_airdrop(
                row
            )

            processed += 1


        except Exception as error:

            failed += 1


            print(
                f"\n⚠️ Failed: "
                f"{row[1]}"
            )


            print(
                f"   Error: {error}"
            )


    print(
        "\n" + "=" * 60
    )


    print(
        "✅ SAFE BACKFILL COMPLETE"
    )


    print(
        f"📊 Successfully processed: "
        f"{processed}"
    )


    print(
        f"⚠️ Failed: "
        f"{failed}"
    )


# -----------------------------------------
# START
# -----------------------------------------

if __name__ == "__main__":

    run_backfill()