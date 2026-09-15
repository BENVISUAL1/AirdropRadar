import re
import html
import feedparser

import config


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

    print(
        f"📦 Total unique discoveries: "
        f"{len(unique_items)}"
    )

    return unique_items


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