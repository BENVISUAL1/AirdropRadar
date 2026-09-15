
"""
AirdropRadar
REAL DATABASE CATEGORY CALIBRATION — DIAGNOSTIC

This script:
1. Reads all airdrops from the database.
2. Converts database tuples into the dictionary format expected by filter.py.
3. Runs the REAL classifier.
4. Compares reviewed records against expected categories.
5. Shows proposed distribution for all records.
6. Shows FULL DATABASE CONTENT for mismatched reviewed records.
7. Shows a simple mismatch summary for easy copying.
8. DOES NOT modify the database.

IMPORTANT:
    This script is READ-ONLY.
    No category backfill is performed.
    No database records are changed.
"""

from database import get_all_airdrops
from filter import classify_with_details


# ============================================================
# CALIBRATED EXPECTED RESULTS
# ============================================================

EXPECTED_CATEGORIES = {

    # Previously reviewed records
    6: "Testnet",
    8: "Testnet",
    10: "Liquidity",
    33: "Testnet",
    43: "Points",
    46: "Holder",
    50: "Activity",
    58: "Points",
    64: "Activity",
    73: "Testnet",
    75: "Activity",
    79: "Activity",
    84: "Points",
    85: "Liquidity",
    87: "Liquidity",
    95: "Activity",
    96: "Activity",
    100: "Liquidity",
    101: "Testnet",
    103: "Points",
    106: "Activity",
    107: "Activity",
    108: "Activity",
    109: "Liquidity",
    110: "Points",
    116: "Testnet",
    117: "Activity",
    119: "Activity",
    120: "Points",
    122: "Activity",

    # Reviewed labels (primary mechanism, not keyword noise)
    34: "Points",
    104: "Other",
    124: "Other",
    125: "Other",
    126: "Other",
}


# ============================================================
# DATABASE RECORD → CLASSIFIER RECORD
# ============================================================

def database_record_to_result(record):
    """
    Convert database.get_all_airdrops() tuple:

        (id, name, url, description, source)

    into the dictionary structure expected by filter.py.
    """

    if not record:
        return {}

    airdrop_id, name, url, description, source = record

    return {
        "id": airdrop_id,
        "name": name or "",
        "title": name or "",
        "url": url or "",
        "description": description or "",
        "source": source or "",
    }


# ============================================================
# SAFE CLASSIFICATION
# ============================================================

def classify_record(record):
    """
    Run the REAL classifier using classify_with_details().

    Returns:
        category
        confidence
        mechanism
        evidence
    """

    candidate = database_record_to_result(record)

    if not candidate:
        return {
            "category": "Other",
            "confidence": "Low",
            "mechanism": "",
            "evidence": [],
            "error": "Empty database record",
        }

    try:

        details = classify_with_details(candidate)

        if not isinstance(details, dict):
            return {
                "category": "Other",
                "confidence": "Low",
                "mechanism": "",
                "evidence": [],
                "error": (
                    "classify_with_details() "
                    "did not return a dictionary"
                ),
            }

        return {
            "category": details.get(
                "category",
                "Other"
            ),

            "confidence": details.get(
                "confidence",
                "Low"
            ),

            "mechanism": details.get(
                "mechanism",
                ""
            ),

            "evidence": details.get(
                "evidence",
                []
            ),

            "error": None,
        }

    except Exception as error:

        return {
            "category": "Other",
            "confidence": "Low",
            "mechanism": "",
            "evidence": [],
            "error": str(error),
        }


# ============================================================
# MAIN CALIBRATION
# ============================================================

def run_calibration():

    print()
    print("REAL DATABASE CATEGORY CALIBRATION - DIAGNOSTIC")
    print("=" * 70)
    print()

    records = get_all_airdrops()

    print(
        f"Records found: {len(records)}"
    )

    print(
        "Database will NOT be modified."
    )

    print()

    reviewed = 0
    correct = 0
    mismatched = 0
    unreviewed = 0
    errors = 0

    proposed_distribution = {
        "Points": 0,
        "Testnet": 0,
        "Retroactive": 0,
        "Holder": 0,
        "Bounty": 0,
        "Liquidity": 0,
        "Activity": 0,
        "Other": 0,
    }

    mismatched_results = []
    correct_results = []
    unreviewed_results = []

    # ========================================================
    # CLASSIFY EVERY DATABASE RECORD
    # ========================================================

    for record in records:

        airdrop_id = record[0]
        name = record[1]

        classification = classify_record(record)

        category = classification["category"]
        confidence = classification["confidence"]
        mechanism = classification["mechanism"]
        evidence = classification["evidence"]
        error = classification.get("error")

        # ----------------------------------------------------
        # ERROR COUNT
        # ----------------------------------------------------

        if error:
            errors += 1

        # ----------------------------------------------------
        # SAFETY CHECK
        # ----------------------------------------------------

        if category not in proposed_distribution:

            print()
            print(
                f"Unknown category returned "
                f"for ID {airdrop_id}: {category}"
            )

            category = "Other"

        proposed_distribution[category] += 1

        # ====================================================
        # REVIEWED RECORD
        # ====================================================

        if airdrop_id in EXPECTED_CATEGORIES:

            expected = EXPECTED_CATEGORIES[airdrop_id]

            reviewed += 1

            result = {
                "id": airdrop_id,
                "name": name,
                "classifier": category,
                "expected": expected,
                "confidence": confidence,
                "mechanism": mechanism,
                "evidence": evidence,
                "error": error,

                # FULL DATABASE RECORD
                "url": record[2] or "",
                "description": record[3] or "",
                "source": record[4] or "",
            }

            if category == expected:

                correct += 1
                correct_results.append(result)

            else:

                mismatched += 1
                mismatched_results.append(result)

        # ====================================================
        # UNREVIEWED RECORD
        # ====================================================

        else:

            unreviewed += 1

            unreviewed_results.append({
                "id": airdrop_id,
                "name": name,
                "proposed": category,
                "confidence": confidence,
                "mechanism": mechanism,
                "evidence": evidence,
                "error": error,
            })

    # ========================================================
    # ACCURACY
    # ========================================================

    accuracy = 0

    if reviewed:
        accuracy = (
            correct / reviewed
        ) * 100

    # ========================================================
    # CALIBRATION SUMMARY
    # ========================================================

    print()
    print("CALIBRATION SUMMARY")
    print("-" * 70)

    print(
        f"Reviewed records:       {reviewed}"
    )

    print(
        f"Correct:                {correct}"
    )

    print(
        f"Mismatched:             {mismatched}"
    )

    print(
        f"Unreviewed:             {unreviewed}"
    )

    print(
        f"Classifier errors:      {errors}"
    )

    print(
        f"Calibration accuracy:   {accuracy:.1f}%"
    )

    # ========================================================
    # MISMATCH IDS ONLY — EASY TO COPY
    # ========================================================

    print()
    print("MISMATCHED REVIEWED IDS")
    print("=" * 70)

    if not mismatched_results:

        print("None")

    else:

        for item in mismatched_results:

            print(
                f"{item['id']}: "
                f"{item['name']} | "
                f"Expected={item['expected']} | "
                f"Classifier={item['classifier']}"
            )

    # ========================================================
    # FULL MISMATCH DIAGNOSTICS
    # ========================================================

    print()
    print("FULL MISMATCH DIAGNOSTICS")
    print("=" * 70)

    if not mismatched_results:

        print("None")

    else:

        for item in mismatched_results:

            print()
            print("=" * 70)

            print(
                f"ID:         {item['id']}"
            )

            print(
                f"NAME:       {item['name']}"
            )

            print(
                f"EXPECTED:   {item['expected']}"
            )

            print(
                f"CLASSIFIER: {item['classifier']}"
            )

            print(
                f"CONFIDENCE: {item['confidence']}"
            )

            print(
                f"MECHANISM:  {item['mechanism']}"
            )

            print()
            print("URL:")
            print(
                item["url"]
            )

            print()
            print("SOURCE:")
            print(
                item["source"]
            )

            print()
            print("DESCRIPTION:")
            print(
                item["description"]
            )

            print()
            print("CLASSIFIER EVIDENCE:")
            print(
                item["evidence"]
            )

            if item["error"]:

                print()
                print("CLASSIFIER ERROR:")
                print(
                    item["error"]
                )

            print()
            print("-" * 70)

    # ========================================================
    # CORRECT RECORDS
    # ========================================================

    print()
    print("CORRECTLY CLASSIFIED CALIBRATED RECORDS")
    print("=" * 70)

    if not correct_results:

        print("None")

    else:

        for item in correct_results:

            print(
                f"{item['id']:>3}. "
                f"{item['name']} -> "
                f"{item['classifier']}"
            )

    # ========================================================
    # UNREVIEWED RECORDS
    # ========================================================

    print()
    print("UNREVIEWED RECORDS")
    print("=" * 70)

    if not unreviewed_results:

        print("None")

    else:

        for item in unreviewed_results:

            print()

            print(
                f"{item['id']:>3}. "
                f"{item['name']}"
            )

            print(
                f"     Proposed:   "
                f"{item['proposed']}"
            )

            print(
                f"     Confidence: "
                f"{item['confidence']}"
            )

            print(
                f"     Mechanism:  "
                f"{item['mechanism']}"
            )

            print(
                f"     Evidence:   "
                f"{item['evidence']}"
            )

            if item["error"]:

                print(
                    f"     ERROR: "
                    f"{item['error']}"
                )

    # ========================================================
    # PROPOSED DISTRIBUTION
    # ========================================================

    print()
    print("PROPOSED CATEGORY DISTRIBUTION")
    print("=" * 70)

    for category, count in proposed_distribution.items():

        print(
            f"   {category:<12}: {count}"
        )

    # ========================================================
    # REVIEWED EXPECTED DISTRIBUTION
    # ========================================================

    expected_distribution = {
        "Points": 0,
        "Testnet": 0,
        "Retroactive": 0,
        "Holder": 0,
        "Bounty": 0,
        "Liquidity": 0,
        "Activity": 0,
        "Other": 0,
    }

    for expected in EXPECTED_CATEGORIES.values():

        expected_distribution[expected] += 1

    print()
    print("REVIEWED EXPECTED DISTRIBUTION")
    print("=" * 70)

    for category, count in expected_distribution.items():

        print(
            f"   {category:<12}: {count}"
        )

    # ========================================================
    # CORRECT IDS
    # ========================================================

    print()
    print("CORRECTLY CLASSIFIED IDS")
    print("=" * 70)

    correct_ids = [
        str(item["id"])
        for item in correct_results
    ]

    if correct_ids:

        print(
            ", ".join(correct_ids)
        )

    else:

        print("None")

    # ========================================================
    # FINAL STATUS
    # ========================================================

    print()
    print("=" * 70)

    print("CALIBRATION ONLY")
    print("DATABASE WAS NOT MODIFIED.")
    print("NO CATEGORY BACKFILL WAS PERFORMED.")
    print("=" * 70)
    print()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_calibration()
