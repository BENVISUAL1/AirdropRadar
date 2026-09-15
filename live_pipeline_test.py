from collections import Counter

from scanner import scan
from qualifier import qualify_candidate
from filter import detect_airdrop_type
from verifier import verify_candidate
from intelligence import analyze_intelligence
from scorer import calculate_score


def main():

    print("🚀 AirdropRadar Full Scoring Calibration")
    print("=" * 60)

    # ---------------------------------------------------------
    # STEP 1 — DISCOVERY
    # ---------------------------------------------------------

    print("\n📡 STEP 1: Discovering airdrop candidates...")

    discovered = scan()

    print(f"📥 Discovered: {len(discovered)}")

    if not discovered:
        print("❌ No discoveries found.")
        return

    # ---------------------------------------------------------
    # STEP 2 — QUALIFICATION
    # ---------------------------------------------------------

    print("\n🧠 STEP 2: Qualifying candidates...")

    qualified = []
    rejected = 0

    for candidate in discovered:

        result = qualify_candidate(candidate)

        if result.get("qualified"):
            qualified.append(candidate)
        else:
            rejected += 1

    print(f"✅ Qualified: {len(qualified)}")
    print(f"❌ Rejected: {rejected}")

    if not qualified:
        print("\n⚠️ No candidates survived qualification.")
        return

    # ---------------------------------------------------------
    # STEP 3 — CATEGORY CLASSIFICATION
    # ---------------------------------------------------------

    print("\n🏷️ STEP 3: Classifying qualified candidates...")

    categorized = []

    for candidate in qualified:

        candidate = dict(candidate)

        airdrop_type = detect_airdrop_type(candidate)

        candidate["airdrop_type"] = airdrop_type

        categorized.append(candidate)

    print(f"🏷️ Categorized: {len(categorized)}")

    # ---------------------------------------------------------
    # CATEGORY DISTRIBUTION
    # ---------------------------------------------------------

    category_counts = Counter(
        candidate.get("airdrop_type", "Other")
        for candidate in categorized
    )

    print("\n📊 Category distribution:")

    for category, count in sorted(category_counts.items()):

        print(f"   {category}: {count}")

    # ---------------------------------------------------------
    # STEP 4 — VERIFICATION
    # ---------------------------------------------------------

    print("\n🛡️ STEP 4: Verifying ALL qualified candidates...")

    verified_results = []

    verification_failures = 0

    for index, candidate in enumerate(
        categorized,
        start=1
    ):

        name = candidate.get(
            "name",
            "Unknown"
        )

        print(
            f"\n🔎 [{index}/{len(categorized)}] "
            f"Verifying: {name}"
        )

        try:

            verification = verify_candidate(candidate)

            if not verification:

                print(
                    "   ⚠️ Verification returned no result."
                )

                verification_failures += 1
                continue

            result = dict(candidate)

            result.update(verification)

            result["airdrop_type"] = candidate.get(
                "airdrop_type",
                "Other"
            )

            verified_results.append(result)

            print(
                f"   Category: "
                f"{result.get('airdrop_type', 'Other')}"
            )

            print(
                f"   Verification: "
                f"{result.get('verification_level', 'unknown')}"
            )

            print(
                f"   Verified: "
                f"{result.get('verified', False)}"
            )

        except Exception as error:

            verification_failures += 1

            print(
                f"   ❌ Verification error: "
                f"{error}"
            )

    # ---------------------------------------------------------
    # STEP 5 — INTELLIGENCE
    # ---------------------------------------------------------

    print("\n🧠 STEP 5: Running intelligence analysis...")

    intelligence_results = []

    intelligence_failures = 0

    for index, result in enumerate(
        verified_results,
        start=1
    ):

        try:

            analyzed = analyze_intelligence(result)

            if analyzed:

                intelligence_results.append(analyzed)

                print(
                    f"   🧠 [{index}/{len(verified_results)}] "
                    f"{analyzed.get('name', 'Unknown')}: "
                    f"analysis complete"
                )

            else:

                intelligence_failures += 1

                print(
                    f"   ⚠️ Intelligence returned no result "
                    f"for {result.get('name', 'Unknown')}"
                )

        except Exception as error:

            intelligence_failures += 1

            print(
                f"   ❌ Intelligence error for "
                f"{result.get('name', 'Unknown')}: "
                f"{error}"
            )

    # ---------------------------------------------------------
    # STEP 6 — SCORING
    # ---------------------------------------------------------

    print("\n📊 STEP 6: Calculating scores...")

    scored_results = []

    scoring_failures = 0

    for index, result in enumerate(
        intelligence_results,
        start=1
    ):

        try:

            # Run the actual scoring engine.
            scored = calculate_score(result)

            if not scored:

                scoring_failures += 1

                print(
                    f"   ⚠️ Scoring returned no result "
                    f"for {result.get('name', 'Unknown')}"
                )

                continue

            # -------------------------------------------------
            # v2.3 uses these exact score_breakdown keys:
            #
            # category_opportunity
            # actions
            # rewards
            # effort_value
            # verification
            # links
            # evidence_quality
            # market
            # defi
            # positive_signals
            # warnings
            # risk
            # -------------------------------------------------

            breakdown = scored.get(
                "score_breakdown",
                {}
            )

            scored_results.append(
                {
                    "name": scored.get(
                        "name",
                        "Unknown"
                    ),

                    "airdrop_type": scored.get(
                        "airdrop_type",
                        "Other"
                    ),

                    "score": scored.get(
                        "score",
                        0
                    ),

                    "confidence": scored.get(
                        "confidence",
                        "Low"
                    ),

                    "score_level": scored.get(
                        "score_level",
                        "Low"
                    ),

                    "risk_level": scored.get(
                        "risk_level",
                        "Low"
                    ),

                    "recommendation": scored.get(
                        "recommendation",
                        "⚪ Low priority"
                    ),

                    "verification_level": scored.get(
                        "verification_level",
                        "unknown"
                    ),

                    "verification_status": scored.get(
                        "verification_status",
                        "unknown"
                    ),

                    "verified": scored.get(
                        "verified",
                        False
                    ),

                    # IMPORTANT:
                    # These keys match Scorer v2.3 exactly.

                    "category_opportunity": breakdown.get(
                        "category_opportunity",
                        0
                    ),

                    "action_score": breakdown.get(
                        "actions",
                        0
                    ),

                    "reward_score": breakdown.get(
                        "rewards",
                        0
                    ),

                    "effort_value": breakdown.get(
                        "effort_value",
                        0
                    ),

                    "verification_score": breakdown.get(
                        "verification",
                        0
                    ),

                    "links_score": breakdown.get(
                        "links",
                        0
                    ),

                    "evidence_quality": breakdown.get(
                        "evidence_quality",
                        0
                    ),

                    "market_score": breakdown.get(
                        "market",
                        0
                    ),

                    "defi_score": breakdown.get(
                        "defi",
                        0
                    ),

                    "positive_signal_score": breakdown.get(
                        "positive_signals",
                        0
                    ),

                    "warning_score": breakdown.get(
                        "warnings",
                        0
                    ),

                    "risk_score": breakdown.get(
                        "risk",
                        0
                    ),

                    "reasons": scored.get(
                        "score_reasons",
                        []
                    ),
                }
            )

            print(
                f"   📊 [{index}/{len(intelligence_results)}] "
                f"{scored.get('name', 'Unknown')}: "
                f"{scored.get('score', 0)}/100"
            )

        except Exception as error:

            scoring_failures += 1

            print(
                f"   ❌ Scoring error for "
                f"{result.get('name', 'Unknown')}: "
                f"{error}"
            )

    # ---------------------------------------------------------
    # FINAL REPORT
    # ---------------------------------------------------------

    print("\n" + "=" * 60)

    print("📋 FULL PIPELINE CALIBRATION REPORT")

    print("=" * 60)

    print(
        f"\n📥 Discovered:            "
        f"{len(discovered)}"
    )

    print(
        f"🧠 Qualified:             "
        f"{len(qualified)}"
    )

    print(
        f"🏷️ Categorized:           "
        f"{len(categorized)}"
    )

    print(
        f"🛡️ Verified:              "
        f"{len(verified_results)}"
    )

    print(
        f"🧠 Intelligence:          "
        f"{len(intelligence_results)}"
    )

    print(
        f"📊 Scored:                "
        f"{len(scored_results)}"
    )

    print(
        f"⚠️ Verification failures: "
        f"{verification_failures}"
    )

    print(
        f"⚠️ Intelligence failures: "
        f"{intelligence_failures}"
    )

    print(
        f"⚠️ Scoring failures:       "
        f"{scoring_failures}"
    )

    # ---------------------------------------------------------
    # SCORE DISTRIBUTION
    # ---------------------------------------------------------

    if scored_results:

        scores = [
            item["score"]
            for item in scored_results
        ]

        average_score = (
            sum(scores) /
            len(scores)
        )

        highest_score = max(scores)

        lowest_score = min(scores)

        print("\n📈 SCORE DISTRIBUTION")

        print("-" * 60)

        print(
            f"   Average score: "
            f"{average_score:.1f}/100"
        )

        print(
            f"   Highest score: "
            f"{highest_score}/100"
        )

        print(
            f"   Lowest score: "
            f"{lowest_score}/100"
        )

        # -----------------------------------------------------
        # SCORE BANDS
        # -----------------------------------------------------

        high_scores = [
            item
            for item in scored_results
            if item["score"] >= 75
        ]

        medium_scores = [
            item
            for item in scored_results
            if 50 <= item["score"] < 75
        ]

        low_scores = [
            item
            for item in scored_results
            if item["score"] < 50
        ]

        print(
            f"\n   🔥 High (75-100): "
            f"{len(high_scores)}"
        )

        print(
            f"   🟡 Medium (50-74): "
            f"{len(medium_scores)}"
        )

        print(
            f"   ⚪ Low (0-49): "
            f"{len(low_scores)}"
        )

        # -----------------------------------------------------
        # CATEGORY SCORE AVERAGES
        # -----------------------------------------------------

        print("\n🏷️ AVERAGE SCORE BY CATEGORY")

        print("-" * 60)

        categories = sorted(
            set(
                item["airdrop_type"]
                for item in scored_results
            )
        )

        for category in categories:

            category_items = [
                item
                for item in scored_results
                if item["airdrop_type"] == category
            ]

            category_scores = [
                item["score"]
                for item in category_items
            ]

            average = (
                sum(category_scores) /
                len(category_scores)
            )

            print(
                f"   {category}: "
                f"{average:.1f}/100 "
                f"({len(category_items)} opportunities)"
            )

        # -----------------------------------------------------
        # TOP OPPORTUNITIES
        # -----------------------------------------------------

        top_results = sorted(
            scored_results,
            key=lambda item: item["score"],
            reverse=True
        )

        print("\n🏆 TOP 15 OPPORTUNITIES")

        print("-" * 60)

        for position, item in enumerate(
            top_results[:15],
            start=1
        ):

            print(
                f"\n{position}. 🪂 "
                f"{item['name']}"
            )

            print(
                f"   Category: "
                f"{item['airdrop_type']}"
            )

            print(
                f"   Score: "
                f"{item['score']}/100"
            )

            print(
                f"   Confidence: "
                f"{item['confidence']}"
            )

            print(
                f"   Risk: "
                f"{item['risk_level']}"
            )

            print(
                f"   Recommendation: "
                f"{item['recommendation']}"
            )

        # -----------------------------------------------------
        # LOWEST OPPORTUNITIES
        # -----------------------------------------------------

        bottom_results = sorted(
            scored_results,
            key=lambda item: item["score"]
        )

        print("\n📉 LOWEST 10 OPPORTUNITIES")

        print("-" * 60)

        for position, item in enumerate(
            bottom_results[:10],
            start=1
        ):

            print(
                f"\n{position}. 🪂 "
                f"{item['name']}"
            )

            print(
                f"   Category: "
                f"{item['airdrop_type']}"
            )

            print(
                f"   Score: "
                f"{item['score']}/100"
            )

            print(
                f"   Confidence: "
                f"{item['confidence']}"
            )

            print(
                f"   Risk: "
                f"{item['risk_level']}"
            )

        # -----------------------------------------------------
        # RECOMMENDATION DISTRIBUTION
        # -----------------------------------------------------

        recommendation_counts = Counter(
            item["recommendation"]
            for item in scored_results
        )

        print("\n🎯 RECOMMENDATION DISTRIBUTION")

        print("-" * 60)

        for recommendation, count in (
            recommendation_counts.most_common()
        ):

            print(
                f"   {recommendation}: "
                f"{count}"
            )

        # -----------------------------------------------------
        # SCORE COMPONENT AVERAGES
        # -----------------------------------------------------

        print("\n🧮 AVERAGE SCORE COMPONENTS")

        print("-" * 60)

        components = {

            "Category opportunity":
                "category_opportunity",

            "Action":
                "action_score",

            "Reward":
                "reward_score",

            "Effort/value":
                "effort_value",

            "Verification":
                "verification_score",

            "Links":
                "links_score",

            "Evidence quality":
                "evidence_quality",

            "Market":
                "market_score",

            "DeFi":
                "defi_score",

            "Positive signals":
                "positive_signal_score",

            "Warnings":
                "warning_score",

            "Risk":
                "risk_score",
        }

        for label, key in components.items():

            values = [
                item[key]
                for item in scored_results
            ]

            average = (
                sum(values) /
                len(values)
            )

            print(
                f"   {label}: "
                f"{average:.1f}"
            )

        # -----------------------------------------------------
        # DETAILED TOP 5
        # -----------------------------------------------------

        print("\n🔬 TOP 5 DETAILED BREAKDOWNS")

        print("-" * 60)

        for position, item in enumerate(
            top_results[:5],
            start=1
        ):

            print(
                f"\n{position}. 🪂 "
                f"{item['name']}"
            )

            print(
                f"   Category: "
                f"{item['airdrop_type']}"
            )

            print(
                f"   Score: "
                f"{item['score']}/100"
            )

            print(
                f"   Recommendation: "
                f"{item['recommendation']}"
            )

            print(
                f"   Category opportunity: "
                f"{item['category_opportunity']}"
            )

            print(
                f"   Action: "
                f"{item['action_score']}"
            )

            print(
                f"   Reward: "
                f"{item['reward_score']}"
            )

            print(
                f"   Effort/value: "
                f"{item['effort_value']}"
            )

            print(
                f"   Verification: "
                f"{item['verification_score']}"
            )

            print(
                f"   Links: "
                f"{item['links_score']}"
            )

            print(
                f"   Evidence quality: "
                f"{item['evidence_quality']}"
            )

            print(
                f"   Market: "
                f"{item['market_score']}"
            )

            print(
                f"   DeFi: "
                f"{item['defi_score']}"
            )

            print(
                f"   Positive signals: "
                f"{item['positive_signal_score']}"
            )

            print(
                f"   Warnings: "
                f"{item['warning_score']}"
            )

            print(
                f"   Risk: "
                f"{item['risk_score']}"
            )

            if item["reasons"]:

                print("   Reasons:")

                for reason in item["reasons"]:

                    print(
                        f"      + {reason}"
                    )

    # ---------------------------------------------------------
    # COMPLETION
    # ---------------------------------------------------------

    print("\n" + "=" * 60)

    print("✅ Full scoring calibration complete!")

    print("=" * 60)


if __name__ == "__main__":
    main()