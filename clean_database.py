import sqlite3
import re
import html

from config import DATABASE_NAME


# -----------------------------------------
# CLEAN DESCRIPTION
# -----------------------------------------

def clean_description(text):

    if not text:
        return ""

    text = str(text)

    # Decode HTML entities
    text = html.unescape(text)

    # Convert Telegram/Markdown links to visible text
    # Example:
    # [$KINS](tg://search_hashtag?hashtag=%24KINS)
    # becomes:
    # $KINS
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    # Remove HTML tags
    text = re.sub(
        r"<[^>]+>",
        " ",
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

    # Clean spaces before punctuation
    text = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        text
    )

    return text.strip()


# -----------------------------------------
# CLEAN DATABASE
# -----------------------------------------

def clean_database():

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, description FROM airdrops"
    )

    rows = cursor.fetchall()

    updated = 0

    for row_id, description in rows:

        cleaned = clean_description(
            description
        )

        if cleaned != description:

            cursor.execute(
                """
                UPDATE airdrops
                SET description = ?
                WHERE id = ?
                """,
                (
                    cleaned,
                    row_id
                )
            )

            updated += 1

    connection.commit()
    connection.close()

    print(
        "✅ Database cleaning complete."
    )

    print(
        f"🧹 Records cleaned: {updated}"
    )

    print(
        f"📊 Total records checked: {len(rows)}"
    )


# -----------------------------------------
# START
# -----------------------------------------

if __name__ == "__main__":

    clean_database()