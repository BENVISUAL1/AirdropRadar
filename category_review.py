from database import get_all_airdrops
from filter import detect_airdrop_type


def main():
    print("🔍 CATEGORY REVIEW")
    print("=" * 60)

    airdrops = get_all_airdrops()

    suspicious_categories = {
        "Other",
        "Activity",
        "Liquidity",
        "Holder",
        "Retroactive",
    }

    review_items = []

    for row in airdrops:
        airdrop_id, name, url, description, source = row

        result = {
            "name": name or "",
            "url": url or "",
            "description": description or "",
            "source": source or "",
        }

        category = detect_airdrop_type(result)

        # Focus on categories where mistakes are more likely.
        if category in suspicious_categories:
            review_items.append({
                "id": airdrop_id,
                "name": name,
                "category": category,
                "description": description,
                "source": source,
                "url": url,
            })

    print(f"\n📦 Total database records: {len(airdrops)}")
    print(f"🔎 Records selected for review: {len(review_items)}")
    print("\n⚠️ DATABASE WILL NOT BE MODIFIED.\n")

    print("=" * 60)
    print("⚠️ RECORDS NEEDING REVIEW")
    print("=" * 60)

    for item in review_items:
        print(f"\nID: {item['id']}")
        print(f"Name: {item['name']}")
        print(f"Proposed category: {item['category']}")
        print(f"Source: {item['source']}")
        print(f"URL: {item['url']}")
        print(f"Description: {item['description']}")
        print("-" * 60)

    print("\n✅ Review extraction complete.")
    print("🛡️ Database was NOT modified.")


if __name__ == "__main__":
    main()