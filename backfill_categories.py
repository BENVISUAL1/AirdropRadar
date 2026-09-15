import os
import shutil

from config import DATABASE_NAME

from database import (
    get_all_airdrops,
    update_airdrop_type,
    get_airdrop_type_counts,
    get_airdrop_type_emoji,
)

from filter import detect_airdrop_type


DATABASE_FILE = DATABASE_NAME
BACKUP_FILE = "airdrops_before_category_backfill.db"


# ============================================================
# BACKUP DATABASE
# ============================================================

def backup_database():

    if not os.path.exists(DATABASE_FILE):

        print(
            "❌ Database file not found:"
            f" {DATABASE_FILE}"
        )

        return False

    try:

        shutil.copy2(
            DATABASE_FILE,
            BACKUP_FILE
        )

        print(
            f"🛡️ Database backup created:"
            f" {BACKUP_FILE}"
        )

        return True

    except Exception as error:

        print(
            f"❌ Failed to create backup: {error}"
        )

        return False


# ============================================================
# BACKFILL CATEGORIES
# ============================================================

def backfill_categories():

    print(
        "\n🔄 Starting AirdropRadar "
        "category backfill...\n"
    )

    airdrops = get_all_airdrops()

    if not airdrops:

        print(
            "⚠️ No airdrops found."
        )

        return

    print(
        f"🪂 Found {len(airdrops)} "
        "existing airdrop(s).\n"
    )

    updated = 0
    other_count = 0
    failed = 0

    for row in airdrops:

        # database.get_all_airdrops() returns:
        #
        # id
        # name
        # url
        # description
        # source

        airdrop_id = row[0]
        name = row[1]
        url = row[2]
        description = row[3]
        source = row[4]

        airdrop = {

            "id": airdrop_id,

            "name": name,

            "url": url,

            "description": description,

            "source": source,
        }

        try:

            airdrop_type = detect_airdrop_type(
                airdrop
            )

            success = update_airdrop_type(
                airdrop_id,
                airdrop_type
            )

            if success:

                updated += 1

                emoji = get_airdrop_type_emoji(
                    airdrop_type
                )

                print(
                    f"{emoji} "
                    f"{name} → "
                    f"{airdrop_type}"
                )

                if airdrop_type == "Other":

                    other_count += 1

            else:

                failed += 1

                print(
                    f"❌ Failed to update: "
                    f"{name}"
                )

        except Exception as error:

            failed += 1

            print(
                f"❌ Classification failed "
                f"for {name}: {error}"
            )

    # ========================================================
    # FINAL RESULTS
    # ========================================================

    print(
        "\n========================================"
    )

    print(
        "🪂 CATEGORY BACKFILL COMPLETE"
    )

    print(
        "========================================"
    )

    print(
        f"📊 Total records: "
        f"{len(airdrops)}"
    )

    print(
        f"✅ Successfully updated: "
        f"{updated}"
    )

    print(
        f"📦 Classified as Other: "
        f"{other_count}"
    )

    print(
        f"❌ Failed: "
        f"{failed}"
    )

    # ========================================================
    # CATEGORY COUNTS
    # ========================================================

    print(
        "\n🪂 Airdrop categories:\n"
    )

    counts = get_airdrop_type_counts()

    for airdrop_type, count in counts.items():

        emoji = get_airdrop_type_emoji(
            airdrop_type
        )

        print(
            f"   {emoji} "
            f"{airdrop_type}: "
            f"{count}"
        )

    print(
        "\n🛡️ Original database was backed up."
    )

    print(
        "🔄 Tracking/history were not modified."
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "🪂 AirdropRadar "
        "Category Backfill Tool"
    )

    print(
        "========================================"
    )

    # --------------------------------------------------------
    # CREATE BACKUP FIRST
    # --------------------------------------------------------

    if not backup_database():

        print(
            "\n❌ Backfill cancelled."
        )

        raise SystemExit(1)

    # --------------------------------------------------------
    # RUN BACKFILL
    # --------------------------------------------------------

    backfill_categories()

    print(
        "\n✅ AirdropRadar category system "
        "is now synchronized."
    )