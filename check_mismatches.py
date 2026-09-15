from category_calibration import EXPECTED_CATEGORIES, classify_record
from database import get_all_airdrops


rows = get_all_airdrops()

mismatches = []


for row in rows:

    if row[0] not in EXPECTED_CATEGORIES:
        continue

    result = classify_record(row)

    actual = result["category"]
    expected = EXPECTED_CATEGORIES[row[0]]

    if actual != expected:

        mismatches.append(
            {
                "id": row[0],
                "name": row[1],
                "expected": expected,
                "actual": actual,
                "confidence": result.get(
                    "confidence",
                    ""
                ),
                "mechanism": result.get(
                    "mechanism",
                    ""
                ),
                "evidence": result.get(
                    "evidence",
                    []
                ),
                "url": row[2] or "",
                "description": row[3] or "",
                "source": row[4] or "",
                "error": result.get(
                    "error"
                ),
            }
        )


# ============================================================
# SUMMARY
# ============================================================

print(
    "REVIEWED:",
    len(EXPECTED_CATEGORIES)
)

print(
    "MISMATCHES:",
    len(mismatches)
)

print()


# ============================================================
# MISMATCH LIST
# ============================================================

print("=" * 70)
print("MISMATCHED REVIEWED IDS")
print("=" * 70)

for item in mismatches:

    print(
        f"{item['id']} | "
        f"{item['name']} | "
        f"Expected={item['expected']} | "
        f"Classifier={item['actual']}"
    )


# ============================================================
# FULL DIAGNOSTICS
# ============================================================

print()
print("=" * 70)
print("FULL MISMATCH DIAGNOSTICS")
print("=" * 70)


for item in mismatches:

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
        f"CLASSIFIER: {item['actual']}"
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


print()
print("=" * 70)
print("DATABASE WAS NOT MODIFIED.")
print("NO CATEGORY BACKFILL WAS PERFORMED.")
print("=" * 70)