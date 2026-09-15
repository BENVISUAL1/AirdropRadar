from category_calibration import EXPECTED_CATEGORIES
from database import get_all_airdrops

wanted = set(EXPECTED_CATEGORIES.keys())

for row in get_all_airdrops():
    if row[0] not in wanted:
        continue

    result = __import__("filter").classify_with_details(row)

    if result["category"] != EXPECTED_CATEGORIES[row[0]]:
        print("\n" + "=" * 100)
        print(f"ID: {row[0]}")
        print(f"NAME: {row[1]}")
        print(f"EXPECTED: {EXPECTED_CATEGORIES[row[0]]}")
        print(f"CLASSIFIER: {result['category']}")
        print(f"EVIDENCE: {result.get('evidence', {})}")
        print(f"SCORES: {result.get('scores', {})}")
        print("FULL RECORD:")
        print(row)
