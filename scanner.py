import re
import html
import feedparser
import config

from cross_source_matching import (
    analyze_cross_source_match,
    normalize_project_name,
)

# -----------------------------------------
# CLEAN DESCRIPTION
# -----------------------------------------

def clean_description(text):

    if not text:
        return ""

    text = str(text)

    # Decode HTML entities
    text = html.unescape(text)

    # Remove HTML tags
    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    # Remove Telegram-style links
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    # Remove markdown-style links
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    # Remove leftover HTML entities
    text = re.sub(
        r"&[a-zA-Z0-9#]+;",
        " ",
        text
    )

    # Remove excessive whitespace
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    # Clean spaces around punctuation
    text = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        text
    )

    return text.strip()


# -----------------------------------------
# CLEAN TITLE
# -----------------------------------------

def clean_title(text):

    if not text:
        return "Unknown Airdrop"

    text = html.unescape(str(text))

    text = re.sub(
        r"<[^>]+>",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# -----------------------------------------
# RSS SCANNER
# -----------------------------------------

def scan_rss():

    print("📡 Starting RSS discovery...")

    results = []

    for source_url in config.SOURCES:

        print(f"📡 Reading: {source_url}")

        try:

            feed = feedparser.parse(
                source_url
            )

            for entry in feed.entries:

                title = clean_title(
                    entry.get(
                        "title",
                        "Unknown Airdrop"
                    )
                )

                url = entry.get(
                    "link",
                    ""
                )

                description = entry.get(
                    "summary",
                    ""
                )

                if not description:

                    description = entry.get(
                        "description",
                        ""
                    )

                description = clean_description(
                    description
                )

                results.append({

                    "name": title,

                    "url": url,

                    "description": description,

                    "source": source_url

                })

        except Exception as error:

            print(
                f"⚠️ RSS error for "
                f"{source_url}: {error}"
            )

    print(
        f"📥 RSS discovery found "
        f"{len(results)} item(s)."
    )

    return results


# -----------------------------------------
# REMOVE DUPLICATES
# -----------------------------------------

def remove_duplicates(items):

    unique = []

    seen_urls = set()

    for item in items:

        url = item.get(
            "url",
            ""
        )

        if not url:
            continue

        if url in seen_urls:
            continue

        seen_urls.add(url)

        unique.append(item)

    return unique

# -----------------------------------------
# CROSS-SOURCE MATCHING
# -----------------------------------------

def match_cross_sources(items):

    if not items:
        return items

    matched_items = [
        dict(item)
        for item in items
    ]

    # Prepare storage for match information
    for item in matched_items:

        item["cross_source_matches"] = []

        item["matched_sources"] = []

        item["cross_source_match_count"] = 0

    # --------------------------------------------------------
    # BUILD CANDIDATE GROUPS
    # --------------------------------------------------------
    #
    # Only compare opportunities that have a similar
    # normalized project-name starting point.
    #

    candidate_groups = {}

    for index, item in enumerate(matched_items):
        project_name = normalize_project_name(
            item.get("name", "")
        )

        if not project_name:
            continue

        words = project_name.split()

        if not words:
            continue

        for word in set(words):
            if len(word) < 3:
                continue

            candidate_groups.setdefault(
                word,
                []
            ).append(index)

            
    # --------------------------------------------------------
    # COMPARE CANDIDATES
    # --------------------------------------------------------

    for indexes in candidate_groups.values():

        if len(indexes) < 2:
            continue

        for position in range(
            len(indexes)
        ):

            first_index = indexes[position]

            first_item = matched_items[
                first_index
            ]

            first_source = first_item.get(
                "source",
                ""
            )

            for next_position in range(
                position + 1,
                len(indexes)
            ):

                second_index = indexes[
                    next_position
                ]

                second_item = matched_items[
                    second_index
                ]

                second_source = second_item.get(
                    "source",
                    ""
                )

                # Same-source discoveries are not
                # cross-source matches.
                if first_source == second_source:
                    continue

                result = analyze_cross_source_match(
                    first_item,
                    second_item,
                )

                if result["match_status"] not in (
                    "possible_match",
                    "strong_match",
                ):
                    continue

                # ------------------------------------------------
                # STORE MATCH ON FIRST ITEM
                # ------------------------------------------------

                first_match = {
                    "source": second_source,
                    "match_status": result[
                        "match_status"
                    ],
                    "match_score": result[
                        "match_score"
                    ],
                    "confidence": result[
                        "confidence"
                    ],
                }

                matched_items[
                    first_index
                ]["cross_source_matches"].append(
                    first_match
                )

                if (
                    second_source
                    and second_source
                    not in matched_items[
                        first_index
                    ]["matched_sources"]
                ):
                    matched_items[
                        first_index
                    ]["matched_sources"].append(
                        second_source
                    )

                # ------------------------------------------------
                # STORE MATCH ON SECOND ITEM
                # ------------------------------------------------

                second_match = {
                    "source": first_source,
                    "match_status": result[
                        "match_status"
                    ],
                    "match_score": result[
                        "match_score"
                    ],
                    "confidence": result[
                        "confidence"
                    ],
                }

                matched_items[
                    second_index
                ]["cross_source_matches"].append(
                    second_match
                )

                if (
                    first_source
                    and first_source
                    not in matched_items[
                        second_index
                    ]["matched_sources"]
                ):
                    matched_items[
                        second_index
                    ]["matched_sources"].append(
                        first_source
                    )

    # --------------------------------------------------------
    # FINAL COUNTS
    # --------------------------------------------------------

    for item in matched_items:

        item[
            "cross_source_match_count"
        ] = len(
            item.get(
                "matched_sources",
                []
            )
        )

    return matched_items


# -----------------------------------------
# MAIN SCANNER
# -----------------------------------------

def scan():

    print(
        "🔍 AirdropRadar scanner is running..."
    )

    items = scan_rss()

    unique_items = remove_duplicates(
        items
    )

    matched_items = match_cross_sources(
    unique_items
    )

    print(
        f"📦 Total unique discoveries: "
        f"{len(matched_items)}"
    )

    return matched_items


# -----------------------------------------
# TEST
# -----------------------------------------

if __name__ == "__main__":

    results = scan()

    print(
        "\n🧪 Sample cleaned discoveries:\n"
    )

    for item in results[:3]:

        print(
            f"🪂 {item['name']}"
        )

        print(
            f"🔗 {item['url']}"
        )

        print(
            f"📝 {item['description'][:300]}"
        )

        print(
            "-" * 50
        )