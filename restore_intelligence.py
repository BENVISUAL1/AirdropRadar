import sqlite3
import json
import os
import shutil
import time
from datetime import datetime

from config import DATABASE_NAME

from database import (
    get_all_airdrops,
    update_airdrop_intelligence,
)

from api_sources import get_project_intelligence
from scorer import calculate_score, calculate_confidence


DB_PATH = DATABASE_NAME

# ---------------------------------------------------------
# RECOVERY SETTINGS
# ---------------------------------------------------------

# Wait between projects to reduce API rate limiting.
DELAY_BETWEEN_PROJECTS = 8

# Number of projects to process in one run.
# Start small for safety.
MAX_RECOVERY = 10


# ---------------------------------------------------------
# DATABASE BACKUP
# ---------------------------------------------------------

def create_database_backup():
    """
    Create a backup of the database before recovery.
    """

    if not os.path.exists(DB_PATH):

        print("❌ Database file not found.")

        return None

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        f"airdrops_backup_before_recovery_{timestamp}.db"
    )

    try:

        shutil.copy2(
            DB_PATH,
            backup_path
        )

        print(
            f"💾 Database backup created:"
        )

        print(
            f"   {backup_path}"
        )

        return backup_path

    except Exception as error:

        print(
            f"❌ Could not create database backup: {error}"
        )

        return None


# ---------------------------------------------------------
# GET EXISTING RECORD
# ---------------------------------------------------------

def get_existing_record(airdrop_id):
    """
    Read the current stored intelligence for one airdrop.
    """

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            url,
            description,
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
        (airdrop_id,),
    )

    row = cursor.fetchone()

    conn.close()

    if not row:

        return None

    return dict(row)


# ---------------------------------------------------------
# RELIABLE SIGNAL CHECK
# ---------------------------------------------------------

def is_reliable_signal(signal):
    """
    A signal is reliable only when the API actually
    found a matching project/protocol.
    """

    if not signal:

        return False

    return signal.get("found") is True


# ---------------------------------------------------------
# LOAD STORED JSON
# ---------------------------------------------------------

def load_json_signal(value):
    """
    Safely convert stored JSON into a dictionary.
    """

    if not value:

        return {}

    if isinstance(value, dict):

        return value

    try:

        return json.loads(value)

    except Exception:

        return {}


# ---------------------------------------------------------
# RESTORE ONE PROJECT
# ---------------------------------------------------------

def restore_project(record):

    airdrop_id = record["id"]

    name = record["name"]

    print("\n" + "=" * 60)

    print(
        f"🪂 {name}"
    )

    print("=" * 60)

    print(
        "🧠 Checking CoinGecko + DeFiLlama..."
    )

    # -----------------------------------------------------
    # GET NEW INTELLIGENCE
    # -----------------------------------------------------

    try:

        intelligence = get_project_intelligence(
            name
        )

    except Exception as error:

        print(
            f"⚠️ Intelligence check failed: {error}"
        )

        print(
            "🛡️ Existing intelligence preserved."
        )

        return False

    # IMPORTANT:
    # api_sources.py returns:
    #
    # market_signal
    # defi_signal

    new_market = intelligence.get(
        "market_signal",
        {}
    )

    new_defi = intelligence.get(
        "defi_signal",
        {}
    )

    # -----------------------------------------------------
    # LOAD OLD INTELLIGENCE
    # -----------------------------------------------------

    old_market = load_json_signal(
        record.get("market_signal")
    )

    old_defi = load_json_signal(
        record.get("defi_signal")
    )

    # -----------------------------------------------------
    # MARKET
    # -----------------------------------------------------

    if is_reliable_signal(new_market):

        market_signal = new_market

        print("\n🪙 CoinGecko:")

        print(
            f"   ✅ Match: "
            f"{new_market.get('name', 'Unknown')}"
        )

        print(
            f"   🔤 Symbol: "
            f"{new_market.get('symbol', '')}"
        )

        print(
            f"   🎯 Match: "
            f"{new_market.get('match_score', 0)}%"
        )

        print(
            f"   📊 Rank: "
            f"{new_market.get('market_rank', 'N/A')}"
        )

    else:

        market_signal = old_market

        print("\n🪙 CoinGecko:")

        if old_market:

            print(
                "   ↩️ No reliable new match."
            )

            print(
                "   ➡️ Existing market intelligence preserved."
            )

        else:

            print(
                "   ℹ️ No reliable match."
            )

    # -----------------------------------------------------
    # DEFI
    # -----------------------------------------------------

    if is_reliable_signal(new_defi):

        defi_signal = new_defi

        print("\n🧩 DeFiLlama:")

        print(
            f"   ✅ Protocol: "
            f"{new_defi.get('protocol', 'Unknown')}"
        )

        print(
            f"   🎯 Match: "
            f"{new_defi.get('match_score', 0)}%"
        )

        print(
            f"   💰 TVL: "
            f"{new_defi.get('tvl', 0)}"
        )

    else:

        defi_signal = old_defi

        print("\n🧩 DeFiLlama:")

        if old_defi:

            print(
                "   ↩️ No reliable new match."
            )

            print(
                "   ➡️ Existing DeFi intelligence preserved."
            )

        else:

            print(
                "   ℹ️ No reliable match."
            )

    # -----------------------------------------------------
    # CHECK WHETHER ANYTHING WAS RECOVERED
    # -----------------------------------------------------

    recovered_market = is_reliable_signal(
        new_market
    )

    recovered_defi = is_reliable_signal(
        new_defi
    )

    if not recovered_market and not recovered_defi:

        print(
            "\n⚠️ No new reliable intelligence recovered."
        )

        print(
            "🛡️ Nothing changed in the database."
        )

        return False

    # -----------------------------------------------------
    # BUILD SCORING DATA
    # -----------------------------------------------------

    merged = dict(record)

    merged["market_signal"] = market_signal

    merged["defi_signal"] = defi_signal

    # Preserve verification data.

    merged["verification_level"] = record.get(
        "verification_level"
    )

    merged["official_links"] = record.get(
        "official_links"
    )

    merged["warnings"] = record.get(
        "warnings"
    )

    # -----------------------------------------------------
    # SCORE
    # -----------------------------------------------------

    try:

        score = calculate_score(
            merged
        )

    except Exception as error:

        print(
            f"⚠️ Score calculation failed: {error}"
        )

        print(
            "🛡️ Intelligence will not be written."
        )

        return False

    # -----------------------------------------------------
    # CONFIDENCE
    # -----------------------------------------------------

    try:

        confidence = calculate_confidence(
            merged
        )

    except Exception as error:

        print(
            f"⚠️ Confidence calculation failed: {error}"
        )

        print(
            "🛡️ Intelligence will not be written."
        )

        return False

    print("\n📊 RECOVERED RESULT")

    print(
        f"   Score: {score}/75"
    )

    print(
        f"   Confidence: {confidence}"
    )

    # -----------------------------------------------------
    # DATABASE UPDATE
    # -----------------------------------------------------

    try:

        update_airdrop_intelligence(
            airdrop_id=airdrop_id,
            market_signal=market_signal,
            defi_signal=defi_signal,
            score=score,
            confidence=confidence,
            verification_level=record.get(
                "verification_level"
            ),
            official_links=record.get(
                "official_links"
            ),
            warnings=record.get(
                "warnings"
            ),
        )

    except Exception as error:

        print(
            f"❌ Database update failed: {error}"
        )

        print(
            "🛡️ Recovery was not confirmed."
        )

        return False

    print(
        "💾 Intelligence restored successfully."
    )

    return True


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print(
        "🧠 AirdropRadar Intelligence Recovery"
    )

    print("=" * 60)

    print(
        "🛡️ SAFETY MODE ENABLED"
    )

    print(
        "Only reliable API matches can replace stored intelligence."
    )

    print(
        "Existing verification, links and warnings are preserved."
    )

    print(
        f"⏱️ Delay between projects: "
        f"{DELAY_BETWEEN_PROJECTS} seconds"
    )

    print(
        f"📦 Maximum projects this run: "
        f"{MAX_RECOVERY}"
    )

    print("=" * 60)

    # -----------------------------------------------------
    # BACKUP
    # -----------------------------------------------------

    backup = create_database_backup()

    if not backup:

        print(
            "\n🛑 Recovery cancelled."
        )

        print(
            "A database backup could not be created."
        )

        return

    print(
        "\n✅ Backup verified."
    )

    # -----------------------------------------------------
    # LOAD DATABASE
    # -----------------------------------------------------

    records = get_all_airdrops()

    print(
        f"\n📦 Found {len(records)} stored airdrop(s)."
    )

    recovered = 0

    skipped = 0

    failed = 0

    processed = 0

    # -----------------------------------------------------
    # PROCESS LIMITED BATCH
    # -----------------------------------------------------

    for record in records:

        if processed >= MAX_RECOVERY:

            print(
                "\n⏸️ Batch limit reached."
            )

            print(
                f"➡️ Processed {processed} project(s)."
            )

            break

        try:

            # get_all_airdrops() returns tuples.
            #
            # First value = ID.

            airdrop_id = record[0]

            record_name = (
                record[1]
                if len(record) > 1
                else "Unknown"
            )

            # -------------------------------------------------
            # LOAD COMPLETE RECORD
            # -------------------------------------------------

            existing = get_existing_record(
                airdrop_id
            )

            if not existing:

                print(
                    f"\n⚠️ Could not load record:"
                    f" {record_name}"
                )

                failed += 1

                processed += 1

                continue

            # -------------------------------------------------
            # RECOVER
            # -------------------------------------------------

            success = restore_project(
                existing
            )

            if success:

                recovered += 1

            else:

                skipped += 1

            processed += 1

            # -------------------------------------------------
            # DELAY
            # -------------------------------------------------

            if processed < MAX_RECOVERY:

                print(
                    f"\n⏳ Waiting "
                    f"{DELAY_BETWEEN_PROJECTS}s "
                    f"before next project..."
                )

                time.sleep(
                    DELAY_BETWEEN_PROJECTS
                )

        # -----------------------------------------------------
        # USER INTERRUPT
        # -----------------------------------------------------

        except KeyboardInterrupt:

            print(
                "\n\n🛑 Recovery stopped by user."
            )

            break

        # -----------------------------------------------------
        # UNEXPECTED ERROR
        # -----------------------------------------------------

        except Exception as error:

            record_name = (
                record[1]
                if isinstance(record, tuple)
                and len(record) > 1
                else "Unknown"
            )

            print(
                f"\n❌ Error processing "
                f"{record_name}: {error}"
            )

            failed += 1

            processed += 1

    # ---------------------------------------------------------
    # FINAL REPORT
    # ---------------------------------------------------------

    print("\n" + "=" * 60)

    print(
        "🏁 RECOVERY BATCH COMPLETE"
    )

    print("=" * 60)

    print(
        f"📦 Processed: {processed}"
    )

    print(
        f"🟢 Recovered: {recovered}"
    )

    print(
        f"🟡 Skipped/preserved: {skipped}"
    )

    print(
        f"🔴 Failed: {failed}"
    )

    print(
        f"💾 Backup: {backup}"
    )

    print(
        "\n🛡️ Existing verification, links and warnings were protected."
    )

    if processed < len(records):

        print(
            "\n➡️ More projects remain."
        )

        print(
            "Run the script again for the next batch."
        )


if __name__ == "__main__":

    main()