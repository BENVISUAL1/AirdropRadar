from scanner import scan
from qualifier import qualify_candidate


results = scan()

qualified = []
rejected = []

for r in results:
    q = qualify_candidate(r)

    if q["qualified"]:
        qualified.append((r, q))
    else:
        rejected.append((r, q))


print(f"Discovered: {len(results)}")
print(f"Qualified: {len(qualified)}")
print(f"Rejected: {len(rejected)}")

print("\n=== QUALIFIED ===")

for r, q in qualified:
    print(
        f"✅ {r.get('name', '')} "
        f"| Score: {q['score']} "
        f"| {r.get('source', '')}"
    )

print("\n=== REJECTED ===")

for r, q in rejected:
    print(
        f"❌ {r.get('name', '')} "
        f"| Score: {q['score']} "
        f"| {r.get('source', '')}"
    )