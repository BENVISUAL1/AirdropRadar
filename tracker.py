import json
from datetime import datetime, timedelta, timezone

import database
from verifier import verify_candidate
from scorer import calculate_score, calculate_confidence
from lifecycle import analyze_lifecycle
from risk_intelligence import analyze_risk


# -----------------------------------------
# TRACKING SETTINGS
# -----------------------------------------

TRACKING_BATCH_SIZE = 5

DEFAULT_CHECK_INTERVAL_MINUTES = 60

MEANINGFUL_SCORE_CHANGE = 5

SIGNIFICANT_TVL_CHANGE = 0.10

# Market rank must move by at least this many
# positions before it becomes a meaningful change.
MEANINGFUL_RANK_CHANGE = 100

# A market/DeFi match disappearance must be
# confirmed across two consecutive checks.
CONFIRM_DISAPPEARANCE = True


# -----------------------------------------
# SAFE JSON HELPERS
# -----------------------------------------

def load_json(value, default=None):
    """
    Safely convert JSON text from the database
    back into Python data.
    """

    if default is None:
        default = []

    if not value:
        return default

    if isinstance(value, (dict, list)):
        return value

    try:
        return json.loads(value)

    except (
        json.JSONDecodeError,
        TypeError
    ):
        return default


# -----------------------------------------
# NORMALIZE VALUE
# -----------------------------------------

def normalize_value(value):
    """
    Convert values into a stable representation
    for comparison.
    """

    if isinstance(value, dict):

        return {
            str(key): normalize_value(item)
            for key, item in sorted(
                value.items()
            )
        }

    if isinstance(value, list):

        return sorted(
            [
                normalize_value(item)
                for item in value
            ],
            key=str
        )

    return value


# -----------------------------------------
# FORMAT TVL
# -----------------------------------------

def format_tvl(value):
    """
    Format TVL for human-readable change
    messages.
    """

    if not isinstance(
        value,
        (int, float)
    ):
        return "Unknown"

    if value >= 1_000_000_000:

        return (
            f"${value / 1_000_000_000:.2f}B"
        )

    if value >= 1_000_000:

        return (
            f"${value / 1_000_000:.2f}M"
        )

    if value >= 1_000:

        return (
            f"${value / 1_000:.2f}K"
        )

    return f"${value:.2f}"


# -----------------------------------------
# GET PREVIOUS HISTORY SNAPSHOT
# -----------------------------------------

def get_previous_history_snapshot(
    airdrop_id
):
    """
    Get the snapshot immediately before
    the current database state.

    Used to confirm API/matching
    disappearances across consecutive checks.
    """

    try:

        history = database.get_airdrop_history(
            airdrop_id,
            3
        )

    except Exception:

        return None

    if not history:
        return None

    # History is returned newest first.
    #
    # The newest row represents the last
    # completed tracking check.
    #
    # If there are at least two rows,
    # the second row is the check before that.

    if len(history) < 2:
        return None

    snapshot = history[1]

    try:

        return {
            "score": snapshot[3],
            "confidence": snapshot[4],
            "verification_level": snapshot[5],
            "official_links": load_json(
                snapshot[6],
                []
            ),
            "warnings": load_json(
                snapshot[7],
                []
            ),
            "market_signal": load_json(
                snapshot[8],
                {}
            ),
            "defi_signal": load_json(
                snapshot[9],
                {}
            ),
        }

    except (
        IndexError,
        TypeError
    ):

        return None


# -----------------------------------------
# CONFIRM API DISAPPEARANCE
# -----------------------------------------

def confirmed_market_disappearance(
    airdrop_id,
    old_market_signal,
    new_market_signal
):
    """
    Confirm that a CoinGecko match has
    disappeared across consecutive checks.

    A temporary matching fluctuation should
    not immediately trigger a Telegram alert.
    """

    old_found = (
        old_market_signal.get("found")
        is True
    )

    new_found = (
        new_market_signal.get("found")
        is False
    )

    if not (
        old_found
        and new_found
    ):
        return False

    if not CONFIRM_DISAPPEARANCE:
        return True

    previous = get_previous_history_snapshot(
        airdrop_id
    )

    if not previous:
        return False

    previous_market = previous.get(
        "market_signal",
        {}
    )

    return (
        previous_market.get("found")
        is False
    )


def confirmed_defi_disappearance(
    airdrop_id,
    old_defi_signal,
    new_defi_signal
):
    """
    Confirm that a DeFiLlama match has
    disappeared across consecutive checks.
    """

    old_found = (
        old_defi_signal.get("found")
        is True
    )

    new_found = (
        new_defi_signal.get("found")
        is False
    )

    if not (
        old_found
        and new_found
    ):
        return False

    if not CONFIRM_DISAPPEARANCE:
        return True

    previous = get_previous_history_snapshot(
        airdrop_id
    )

    if not previous:
        return False

    previous_defi = previous.get(
        "defi_signal",
        {}
    )

    return (
        previous_defi.get("found")
        is False
    )


# -----------------------------------------
# CHANGE DETECTION
# -----------------------------------------

def detect_changes(
    old_score,
    old_confidence,
    old_verification_level,
    old_official_links,
    old_warnings,
    old_market_signal,
    old_defi_signal,
    new_score,
    new_confidence,
    new_verification_level,
    new_official_links,
    new_warnings,
    new_market_signal,
    new_defi_signal,
    airdrop_id=None
):
    """
    Compare previous and current airdrop
    intelligence.

    Returns:

        change_detected
        change_summary
    """

    changes = []

    # -------------------------------------
    # SCORE CHANGE
    # -------------------------------------

    if old_score is not None:

        try:

            score_difference = (
                new_score - old_score
            )

            if (
                abs(score_difference)
                >= MEANINGFUL_SCORE_CHANGE
            ):

                if score_difference > 0:

                    changes.append(
                        f"Score increased "
                        f"{old_score} → {new_score}"
                    )

                else:

                    changes.append(
                        f"Score decreased "
                        f"{old_score} → {new_score}"
                    )

        except (
            TypeError,
            ValueError
        ):

            pass

    # -------------------------------------
    # CONFIDENCE CHANGE
    # -------------------------------------

    if (
        old_confidence != new_confidence
        and (
            old_confidence
            or new_confidence
        )
    ):

        changes.append(
            f"Confidence changed "
            f"{old_confidence or 'None'} → "
            f"{new_confidence or 'None'}"
        )

    # -------------------------------------
    # VERIFICATION CHANGE
    # -------------------------------------

    if (
        old_verification_level
        != new_verification_level
    ):

        changes.append(
            "Verification level changed "
            f"{old_verification_level or 'None'} → "
            f"{new_verification_level or 'None'}"
        )

    # -------------------------------------
    # OFFICIAL LINKS CHANGE
    # -------------------------------------

    old_links = normalize_value(
        old_official_links
    )

    new_links = normalize_value(
        new_official_links
    )

    if old_links != new_links:

        changes.append(
            "Official project links changed"
        )

    # -------------------------------------
    # WARNINGS CHANGE
    # -------------------------------------

    old_warning_list = normalize_value(
        old_warnings
    )

    new_warning_list = normalize_value(
        new_warnings
    )

    if (
        old_warning_list
        != new_warning_list
    ):

        changes.append(
            "Risk warnings changed"
        )

    # -------------------------------------
    # MARKET STATUS CHANGE
    # -------------------------------------

    old_market_found = (
        old_market_signal.get(
            "found"
        )
    )

    new_market_found = (
        new_market_signal.get(
            "found"
        )
    )

    # New market match appeared.
    if (
        old_market_found is False
        and new_market_found is True
    ):

        changes.append(
            "CoinGecko market match detected"
        )

    # Existing market match disappeared.
    elif (
        old_market_found is True
        and new_market_found is False
    ):

        if confirmed_market_disappearance(
            airdrop_id,
            old_market_signal,
            new_market_signal
        ):

            changes.append(
                "CoinGecko market match disappeared"
            )

    # -------------------------------------
    # MARKET MATCH SCORE CHANGE
    # -------------------------------------

    old_market_match = (
        old_market_signal.get(
            "match_score"
        )
    )

    new_market_match = (
        new_market_signal.get(
            "match_score"
        )
    )

    if (
        old_market_found is True
        and new_market_found is True
        and old_market_match is not None
        and new_market_match is not None
        and old_market_match
        != new_market_match
    ):

        changes.append(
            "CoinGecko match score changed "
            f"{old_market_match}% → "
            f"{new_market_match}%"
        )

    # -------------------------------------
    # MARKET RANK CHANGE
    # -------------------------------------

    old_market_rank = (
        old_market_signal.get(
            "market_rank"
        )
    )

    new_market_rank = (
        new_market_signal.get(
            "market_rank"
        )
    )

    if (
        old_market_found is True
        and new_market_found is True
        and isinstance(
            old_market_rank,
            (int, float)
        )
        and isinstance(
            new_market_rank,
            (int, float)
        )
        and old_market_rank
        != new_market_rank
    ):

        rank_difference = abs(
            new_market_rank
            - old_market_rank
        )

        if (
            rank_difference
            >= MEANINGFUL_RANK_CHANGE
        ):

            changes.append(
                "CoinGecko market rank changed "
                f"{old_market_rank} → "
                f"{new_market_rank}"
            )

    # -------------------------------------
    # DEFI MATCH CHANGE
    # -------------------------------------

    old_defi_found = (
        old_defi_signal.get(
            "found"
        )
    )

    new_defi_found = (
        new_defi_signal.get(
            "found"
        )
    )

    # New DeFi match appeared.
    if (
        old_defi_found is False
        and new_defi_found is True
    ):

        changes.append(
            "DeFiLlama protocol match detected"
        )

    # Existing DeFi match disappeared.
    elif (
        old_defi_found is True
        and new_defi_found is False
    ):

        if confirmed_defi_disappearance(
            airdrop_id,
            old_defi_signal,
            new_defi_signal
        ):

            changes.append(
                "DeFiLlama protocol match disappeared"
            )

    # -------------------------------------
    # DEFI MATCH SCORE CHANGE
    # -------------------------------------

    old_defi_match = (
        old_defi_signal.get(
            "match_score"
        )
    )

    new_defi_match = (
        new_defi_signal.get(
            "match_score"
        )
    )

    if (
        old_defi_found is True
        and new_defi_found is True
        and old_defi_match is not None
        and new_defi_match is not None
        and old_defi_match
        != new_defi_match
    ):

        changes.append(
            "DeFiLlama match score changed "
            f"{old_defi_match}% → "
            f"{new_defi_match}%"
        )

    # -------------------------------------
    # DEFI TVL CHANGE
    # -------------------------------------

    old_tvl = old_defi_signal.get(
        "tvl"
    )

    new_tvl = new_defi_signal.get(
        "tvl"
    )

    if (
        old_defi_found is True
        and new_defi_found is True
        and isinstance(
            old_tvl,
            (int, float)
        )
        and isinstance(
            new_tvl,
            (int, float)
        )
        and old_tvl != new_tvl
    ):

        if old_tvl == 0:

            if new_tvl > 0:

                changes.append(
                    "DeFi TVL increased from 0"
                )

        else:

            tvl_difference = (
                abs(new_tvl - old_tvl)
                / abs(old_tvl)
            )

            if (
                tvl_difference
                >= SIGNIFICANT_TVL_CHANGE
            ):

                changes.append(
                    "DeFi TVL changed significantly "
                    f"{format_tvl(old_tvl)} → "
                    f"{format_tvl(new_tvl)}"
                )

    # -------------------------------------
    # RESULT
    # -------------------------------------

    change_detected = (
        len(changes) > 0
    )

    change_summary = "; ".join(
        changes
    )

    return (
        change_detected,
        change_summary
    )


# -----------------------------------------
# BUILD CHANGE DETAILS
# -----------------------------------------

def build_change_details(
    old_score,
    old_confidence,
    old_verification_level,
    old_official_links,
    old_warnings,
    old_market_signal,
    old_defi_signal,
    new_score,
    new_confidence,
    new_verification_level,
    new_official_links,
    new_warnings,
    new_market_signal,
    new_defi_signal
):
    """
    Build a structured old/new comparison.

    This is used later by the Telegram
    alert system.
    """

    return {

        "score": {
            "old": old_score,
            "new": new_score
        },

        "confidence": {
            "old": old_confidence,
            "new": new_confidence
        },

        "verification_level": {
            "old": old_verification_level,
            "new": new_verification_level
        },

        "official_links": {
            "old": old_official_links,
            "new": new_official_links
        },

        "warnings": {
            "old": old_warnings,
            "new": new_warnings
        },

        "market_signal": {
            "old": old_market_signal,
            "new": new_market_signal
        },

        "defi_signal": {
            "old": old_defi_signal,
            "new": new_defi_signal
        }
    }

# -----------------------------------------
# TRACK ONE AIRDROP
# -----------------------------------------

def track_airdrop(airdrop):
    """
    Re-check one existing airdrop.

    Also calculates:
        - lifecycle intelligence
        - risk intelligence
        - score changes
        - monitoring changes
    """

    airdrop_id = airdrop[0]
    name = airdrop[1]
    url = airdrop[2]
    description = airdrop[3]
    source = airdrop[4]

    old_score = airdrop[5]
    old_confidence = airdrop[6]

    old_verification_level = (
        airdrop[8]
    )

    old_official_links = load_json(
        airdrop[9],
        []
    )

    old_warnings = load_json(
        airdrop[10],
        []
    )

    old_market_signal = load_json(
        airdrop[11],
        {}
    )

    old_defi_signal = load_json(
        airdrop[12],
        {}
    )

    print(
        f"\n🔄 Tracking: {name}"
    )

    # -------------------------------------
    # BUILD AIRDROP OBJECT
    # -------------------------------------

    airdrop_data = {

        "name": name,

        "url": url,

        "description": description,

        "source": source
    }

    # -------------------------------------
    # LIFECYCLE INTELLIGENCE
    # -------------------------------------

    try:

        lifecycle = analyze_lifecycle(
            airdrop_data
        )

    except Exception as error:

        print(
            f"⚠️ Lifecycle analysis failed: "
            f"{error}"
        )

        lifecycle = {
            "status": "unknown",
            "start_date": None,
            "end_date": None,
            "dates_detected": [],
            "evidence": []
        }

    # -------------------------------------
    # RISK INTELLIGENCE
    # -------------------------------------

    try:

        risk_intelligence = analyze_risk(
            airdrop_data
        )

    except Exception as error:

        print(
            f"⚠️ Risk analysis failed: "
            f"{error}"
        )

        risk_intelligence = {
            "risk_level": "unknown",
            "signals": [],
            "summary": "Risk analysis unavailable."
        }

    # -------------------------------------
    # RE-VERIFY
    # -------------------------------------

    try:

        result = verify_candidate(
            airdrop_data
        )

    except Exception as error:

        print(
            f"⚠️ Verification failed: {error}"
        )

        return {

            "success": False,

            "change_detected": False,

            "error": str(error),

            "lifecycle": lifecycle,

            "risk_intelligence":
                risk_intelligence
        }

    # -------------------------------------
    # VERIFY RESULT
    # -------------------------------------

    if not isinstance(
        result,
        dict
    ):

        print(
            "⚠️ Verifier returned invalid data."
        )

        return {

            "success": False,

            "change_detected": False,

            "error":
                "Invalid verifier result",

            "lifecycle": lifecycle,

            "risk_intelligence":
                risk_intelligence
        }

    # -------------------------------------
    # GET NEW DATA
    # -------------------------------------

    new_verification_level = (
        result.get(
            "verification_level",
            old_verification_level
        )
    )

    new_official_links = (
        result.get(
            "official_links",
            old_official_links
        )
    )

    new_warnings = (
        result.get(
            "warnings",
            old_warnings
        )
    )

    new_market_signal = (
        result.get(
            "market_signal",
            old_market_signal
        )
    )

    new_defi_signal = (
        result.get(
            "defi_signal",
            old_defi_signal
        )
    )

    # -------------------------------------
    # DATA TYPE SAFETY
    # -------------------------------------

    if not isinstance(
        new_official_links,
        list
    ):

        new_official_links = (
            old_official_links
        )

    if not isinstance(
        new_warnings,
        list
    ):

        new_warnings = (
            old_warnings
        )

    if not isinstance(
        new_market_signal,
        dict
    ):

        new_market_signal = (
            old_market_signal
        )

    if not isinstance(
        new_defi_signal,
        dict
    ):

        new_defi_signal = (
            old_defi_signal
        )

    # -------------------------------------
    # API FAILURE SAFETY
    # -------------------------------------

    market_unavailable = (
        new_market_signal.get(
            "status"
        )
        == "api_unavailable"
    )

    defi_unavailable = (
        new_defi_signal.get(
            "status"
        )
        == "api_unavailable"
    )

    if market_unavailable:

        print(
            "⚠️ CoinGecko unavailable — "
            "preserving previous market data."
        )

        new_market_signal = (
            old_market_signal
        )

    if defi_unavailable:

        print(
            "⚠️ DeFiLlama unavailable — "
            "preserving previous DeFi data."
        )

        new_defi_signal = (
            old_defi_signal
        )

    # -------------------------------------
    # BUILD SCORING RESULT
    # -------------------------------------

    result["name"] = name
    result["url"] = url
    result["description"] = description
    result["source"] = source

    result["verification_level"] = (
        new_verification_level
    )

    result["official_links"] = (
        new_official_links
    )

    result["warnings"] = (
        new_warnings
    )

    result["market_signal"] = (
        new_market_signal
    )

    result["defi_signal"] = (
        new_defi_signal
    )

    # -------------------------------------
    # CALCULATE SCORE
    # -------------------------------------

    try:

        score_result = calculate_score(
            result
        )

        if isinstance(
            score_result,
            dict
        ):

            new_score = score_result.get(
                "score",
                0
            )

        else:

            new_score = score_result

        new_confidence = calculate_confidence(
            result
        )

    except Exception as error:

        print(
            f"⚠️ Scoring failed: {error}"
        )

        return {

            "success": False,

            "change_detected": False,

            "error": str(error),

            "lifecycle": lifecycle,

            "risk_intelligence":
                risk_intelligence
        }

    # -------------------------------------
    # DETECT CHANGES
    # -------------------------------------

    (
        change_detected,
        change_summary
    ) = detect_changes(

        old_score,

        old_confidence,

        old_verification_level,

        old_official_links,

        old_warnings,

        old_market_signal,

        old_defi_signal,

        new_score,

        new_confidence,

        new_verification_level,

        new_official_links,

        new_warnings,

        new_market_signal,

        new_defi_signal,

        airdrop_id
    )

    # -------------------------------------
    # BUILD EXACT CHANGE DETAILS
    # -------------------------------------

    change_details = build_change_details(

        old_score,

        old_confidence,

        old_verification_level,

        old_official_links,

        old_warnings,

        old_market_signal,

        old_defi_signal,

        new_score,

        new_confidence,

        new_verification_level,

        new_official_links,

        new_warnings,

        new_market_signal,

        new_defi_signal
    )

    # -------------------------------------
    # NEXT CHECK TIME
    # -------------------------------------

    next_check = (
        datetime.now(
            timezone.utc
        )
        + timedelta(
            minutes=
            DEFAULT_CHECK_INTERVAL_MINUTES
        )
    )

    next_check_at = (
        next_check.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    # -------------------------------------
    # SAVE TRACKING RESULT
    # -------------------------------------

    saved = database.update_airdrop_tracking(

        airdrop_id,

        new_score,

        new_confidence,

        new_verification_level,

        new_official_links,

        new_warnings,

        new_market_signal,

        new_defi_signal,

        change_detected,

        change_summary,

        next_check_at
    )

    if not saved:

        print(
            "❌ Failed to save tracking result"
        )

        return {

            "success": False,

            "change_detected": False,

            "error":
                "Database update failed",

            "lifecycle": lifecycle,

            "risk_intelligence":
                risk_intelligence
        }

    # -------------------------------------
    # OUTPUT
    # -------------------------------------

    if change_detected:

        print(
            f"📈 Change detected: "
            f"{change_summary}"
        )

    else:

        print(
            "✅ No meaningful change"
        )

    print(
        f"📊 Score: {new_score}"
    )

    print(
        f"🎯 Confidence: {new_confidence}"
    )

    print(
        f"🔄 Lifecycle: "
        f"{lifecycle.get('status', 'unknown')}"
    )

    print(
        f"🛡️ Risk: "
        f"{risk_intelligence.get('risk_level', 'unknown')}"
    )

    # -------------------------------------
    # RETURN RESULT
    # -------------------------------------

    return {

        "success": True,

        "airdrop_id": airdrop_id,

        "name": name,

        "url": url,

        "old_score": old_score,

        "new_score": new_score,

        "old_confidence":
            old_confidence,

        "new_confidence":
            new_confidence,

        "change_detected":
            change_detected,

        "change_summary":
            change_summary,

        "change_details":
            change_details,

        "lifecycle":
            lifecycle,

        "risk_intelligence":
            risk_intelligence,

        "next_check_at":
            next_check_at
    }

    

# -----------------------------------------
# RUN TRACKING CYCLE
# -----------------------------------------

def run_tracking_cycle(
    limit=TRACKING_BATCH_SIZE
):
    """
    Run one tracking cycle.

    Only a small number of existing
    airdrops are checked at a time.
    """

    print(
        "\n🔄 AirdropRadar tracking cycle started..."
    )

    airdrops = (
        database.get_airdrops_for_tracking(
            limit
        )
    )

    if not airdrops:

        print(
            "📭 No airdrops are due for tracking."
        )

        return []

    print(
        f"🔎 Checking {len(airdrops)} "
        f"existing airdrop(s)..."
    )

    results = []

    for airdrop in airdrops:

        try:

            result = track_airdrop(
                airdrop
            )

            results.append(
                result
            )

        except Exception as error:

            print(
                f"❌ Tracking error: {error}"
            )

            results.append({

                "success": False,

                "change_detected": False,

                "error": str(error)
            })

    changed = sum(

        1

        for result in results

        if result.get(
            "change_detected",
            False
        )
    )

    successful = sum(

        1

        for result in results

        if result.get(
            "success",
            False
        )
    )

    print(
        "\n📊 Tracking cycle complete."
    )

    print(
        f"✅ Successfully checked: "
        f"{successful}"
    )

    print(
        f"📈 Meaningful changes: "
        f"{changed}"
    )

    return results


# -----------------------------------------
# TEST
# -----------------------------------------

if __name__ == "__main__":

    print(
        "🔄 AirdropRadar Tracker v4"
    )

    database.create_database()

    ready = (
        database.get_airdrops_for_tracking(
            5
        )
    )

    print(
        f"🪂 Airdrops ready for tracking: "
        f"{len(ready)}"
    )

    print(
        f"📊 Already tracked: "
        f"{database.get_tracking_count()}"
    )

    print(
        f"📈 Recorded changes: "
        f"{database.get_change_count()}"
    )

    print(
        "\n🚀 Running test tracking cycle..."
    )

    results = run_tracking_cycle(
        limit=TRACKING_BATCH_SIZE
    )

    # -------------------------------------
    # CHANGE SUMMARY
    # -------------------------------------

    changed_results = [

        result

        for result in results

        if result.get(
            "change_detected",
            False
        )
    ]

    if changed_results:

        print(
            "\n📋 Change details:"
        )

        for result in changed_results:

            print(
                f"\n🪂 {result.get('name', 'Unknown')}"
            )

            print(
                f"   📊 Score: "
                f"{result.get('old_score')} → "
                f"{result.get('new_score')}"
            )

            print(
                f"   🎯 Confidence: "
                f"{result.get('old_confidence')} → "
                f"{result.get('new_confidence')}"
            )

            print(
                f"   📈 Changes: "
                f"{result.get('change_summary', '')}"
            )