
import asyncio
import json
import html
import re
import threading


# ============================================================
# SCAN LOCK
# ============================================================

scan_lock = threading.Lock()


def run_scan_once():
    """
    Prevent automatic scans and /check from running together.
    """
    if not scan_lock.acquire(blocking=False):
        return None

    try:
        return run_scan()
    finally:
        scan_lock.release()


# ============================================================
# TELEGRAM IMPORTS
# ============================================================

from telegram import (
    Update,
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)


# ============================================================
# CONFIG
# ============================================================

import config

from config import (
    ALERT_THRESHOLD,
    SCAN_INTERVAL,
)


# ============================================================
# DATABASE
# ============================================================

from database import (
    create_database,
    save_airdrop,
    add_subscriber,
    remove_subscriber,
    get_subscribers,
    get_latest_airdrops,
    get_total_airdrops,
    get_high_confidence_count,
    get_medium_confidence_count,
    get_low_confidence_count,
    alert_exists,
    record_alert,
    get_airdrop_types,
    get_airdrop_type_emoji,
    get_airdrops_by_type,
    get_airdrop_by_id,
    get_airdrop_type_counts,

    # Monitoring alerts
    monitoring_alert_exists,
    record_monitoring_alert,
    get_airdrop_history,
)


# ============================================================
# SCANNER + TRACKER
# ============================================================

from filter import run_scan
from tracker import run_tracking_cycle


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_json(value):
    """
    Safely convert JSON strings into Python objects.
    """

    if not value:
        return []

    if isinstance(value, (list, dict)):
        return value

    try:
        return json.loads(value)
    except Exception:
        return []


def clean_display_text(text):
    """
    Clean text before displaying it in Telegram.
    """

    if not text:
        return ""

    text = str(text)

    # Decode HTML entities.
    text = html.unescape(text)

    # Convert Markdown links to visible text.
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text,
    )

    # Remove HTML tags.
    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    # Remove leftover HTML entities.
    text = re.sub(
        r"&[a-zA-Z0-9#]+;",
        " ",
        text,
    )

    # Remove excessive whitespace.
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    # Clean spaces before punctuation.
    text = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        text,
    )

    return text.strip()


def format_tvl(tvl):
    """
    Format TVL values into readable units.
    """

    try:
        tvl = float(tvl or 0)
    except Exception:
        return "N/A"

    if tvl >= 1_000_000_000:
        return f"${tvl / 1_000_000_000:.2f}B"

    if tvl >= 1_000_000:
        return f"${tvl / 1_000_000:.2f}M"

    if tvl >= 1_000:
        return f"${tvl / 1_000:.2f}K"

    if tvl > 0:
        return f"${tvl:.0f}"

    return "N/A"


def safe_score(value):
    """
    Safely convert a score into an integer from 0 to 100.
    """

    try:
        if value is None:
            return 0

        if isinstance(value, bool):
            return 0

        score = int(float(value))

    except (TypeError, ValueError):
        return 0

    return max(0, min(100, score))


def format_confidence(value):
    """
    Convert internal confidence values into
    user-friendly confidence labels.
    """

    if value is None:
        return "🔴 Low"

    text = str(value).strip().lower()

    # Already a label.
    if text == "high":
        return "🟢 High"

    if text == "medium":
        return "🟡 Medium"

    if text == "low":
        return "🔴 Low"

    # Numeric confidence.
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return "🔴 Low"

    if confidence >= 80:
        return "🟢 High"

    if confidence >= 50:
        return "🟡 Medium"

    return "🔴 Low"


# ============================================================
# STORE SCAN RESULTS
# ============================================================

def store_scan_results(results):
    """
    Save all enriched scan results into the database.

    Pipeline:

    SCAN
    → QUALIFY
    → CLASSIFY
    → VERIFY
    → SCORE
    → STORE
    """

    stored_count = 0

    for result in results:

        if not isinstance(result, dict):
            print(
                "⚠️ Skipping invalid scan result."
            )
            continue

        try:
            save_airdrop(result)
            stored_count += 1

        except Exception as error:
            print(
                f"⚠️ Failed to store "
                f"{result.get('name', 'Unknown')}: "
                f"{error}"
            )

    print(
        f"💾 Stored: {stored_count} result(s)."
    )

    return stored_count


# ============================================================
# AIRDROP DATABASE RECORD HELPERS
# ============================================================

def extract_airdrop_record(airdrop):
    """
    Convert a database tuple or dictionary into
    one consistent dictionary.

    Database v9 tuple order:

        0  id
        1  name
        2  url
        3  description
        4  source
        5  score
        6  confidence
        7  verified
        8  verification_level
        9  official_links
        10 warnings
        11 market_signal
        12 defi_signal
        13 created_at
        14 last_checked_at
        15 previous_score
        16 previous_confidence
        17 last_change_at
        18 next_check_at
        19 airdrop_type
    """

    # --------------------------------------------------------
    # DICTIONARY RECORD
    # --------------------------------------------------------

    if isinstance(airdrop, dict):

        return {
            "id": airdrop.get("id"),

            "name": airdrop.get(
                "name",
                "",
            ),

            "url": airdrop.get(
                "url",
                "",
            ),

            "description": airdrop.get(
                "description",
                "",
            ),

            "source": airdrop.get(
                "source",
                "",
            ),

            "score": airdrop.get(
                "score",
                0,
            ),

            "confidence": airdrop.get(
                "confidence",
                "",
            ),

            "verified": airdrop.get(
                "verified",
                False,
            ),

            "verification_level": airdrop.get(
                "verification_level",
                "",
            ),

            "official_links": airdrop.get(
                "official_links",
                [],
            ),

            "warnings": airdrop.get(
                "warnings",
                [],
            ),

            "market_signal": airdrop.get(
                "market_signal",
                {},
            ),

            "defi_signal": airdrop.get(
                "defi_signal",
                {},
            ),

            "created_at": airdrop.get(
                "created_at",
                "",
            ),

            "last_checked_at": airdrop.get(
                "last_checked_at",
                "",
            ),

            "previous_score": airdrop.get(
                "previous_score",
                None,
            ),

            "previous_confidence": airdrop.get(
                "previous_confidence",
                "",
            ),

            "last_change_at": airdrop.get(
                "last_change_at",
                "",
            ),

            "next_check_at": airdrop.get(
                "next_check_at",
                "",
            ),

            "airdrop_type": airdrop.get(
                "airdrop_type",
                "Other",
            ),
        }

    # --------------------------------------------------------
    # DATABASE TUPLE
    # --------------------------------------------------------

    values = list(airdrop)

    def get_value(index, default=None):

        if index < len(values):
            return values[index]

        return default

    return {
        "id": get_value(0),

        "name": get_value(
            1,
            "",
        ),

        "url": get_value(
            2,
            "",
        ),

        "description": get_value(
            3,
            "",
        ),

        "source": get_value(
            4,
            "",
        ),

        "score": get_value(
            5,
            0,
        ),

        "confidence": get_value(
            6,
            "",
        ),

        "verified": get_value(
            7,
            False,
        ),

        "verification_level": get_value(
            8,
            "",
        ),

        "official_links": get_value(
            9,
            [],
        ),

        "warnings": get_value(
            10,
            [],
        ),

        "market_signal": get_value(
            11,
            {},
        ),

        "defi_signal": get_value(
            12,
            {},
        ),

        "created_at": get_value(
            13,
            "",
        ),

        "last_checked_at": get_value(
            14,
            "",
        ),

        "previous_score": get_value(
            15,
            None,
        ),

        "previous_confidence": get_value(
            16,
            "",
        ),

        "last_change_at": get_value(
            17,
            "",
        ),

        "next_check_at": get_value(
            18,
            "",
        ),

        "airdrop_type": get_value(
            19,
            "Other",
        ),
    }


# ============================================================
# FORMAT AIRDROP
# ============================================================

def format_airdrop(
    airdrop,
    display_type=None,
):
    """
    Convert an airdrop record into a Telegram HTML message.
    """

    data = extract_airdrop_record(airdrop)

    name = clean_display_text(
        data.get(
            "name",
            "",
        )
    )

    description = clean_display_text(
        data.get(
            "description",
            "",
        )
    )

    url = str(
        data.get(
            "url",
            "",
        ) or ""
    ).strip()

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = safe_score(
        data.get(
            "score",
            0,
        )
    )

    # --------------------------------------------------------
    # OTHER DATA
    # --------------------------------------------------------

    confidence = data.get(
        "confidence",
        "",
    )

    verification_level = data.get(
        "verification_level",
        "",
    )

    official_links = safe_json(
        data.get(
            "official_links",
            [],
        )
    )

    warnings = safe_json(
        data.get(
            "warnings",
            [],
        )
    )

    market_signal = safe_json(
        data.get(
            "market_signal",
            {},
        )
    )

    defi_signal = safe_json(
        data.get(
            "defi_signal",
            {},
        )
    )

    if not isinstance(
        market_signal,
        dict,
    ):
        market_signal = {}

    if not isinstance(
        defi_signal,
        dict,
    ):
        defi_signal = {}

    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    if display_type:
        airdrop_type = display_type
    else:
        airdrop_type = data.get(
            "airdrop_type",
            "Other",
        )

    if not airdrop_type:
        airdrop_type = "Other"

    type_emoji = get_airdrop_type_emoji(
        airdrop_type
    )

    # --------------------------------------------------------
    # CLEAN AND ESCAPE TEXT
    # --------------------------------------------------------

    name = html.escape(
        name or "Unknown Airdrop"
    )

    description = html.escape(
        description or "No description available."
    )

    url = html.escape(
        url,
        quote=True,
    )

    confidence = format_confidence(
        confidence
    )

    verification_level = html.escape(
        str(
            verification_level or "Unknown"
        )
    )

    airdrop_type = html.escape(
        str(
            airdrop_type or "Other"
        )
    )

    if len(description) > 500:
        description = (
            description[:500]
            + "..."
        )

    # --------------------------------------------------------
    # MARKET INTELLIGENCE
    # --------------------------------------------------------

    market_found = market_signal.get(
        "found",
        False,
    )

    market_status = market_signal.get(
        "status",
        "",
    )

    if market_found:

        market_name = clean_display_text(
            market_signal.get(
                "name",
                "Recognized",
            )
        )

        market_name = html.escape(
            market_name
        )

        symbol = str(
            market_signal.get(
                "symbol",
                "",
            ) or ""
        )

        rank = market_signal.get(
            "market_rank"
        )

        match = market_signal.get(
            "match_score",
            0,
        )

        market_text = (
            "🪙 <b>Market:</b> "
            f"✅ {market_name}"
        )

        if symbol:
            market_text += (
                f" ({html.escape(symbol.upper())})"
            )

        if rank:
            market_text += (
                f" • Rank #{rank}"
            )

        market_text += (
            f" • Match {match}%"
        )

    elif market_status == "api_unavailable":

        market_text = (
            "🪙 <b>Market:</b> "
            "⚠️ Unavailable"
        )

    else:

        market_text = (
            "🪙 <b>Market:</b> "
            "❌ Not found"
        )

    # --------------------------------------------------------
    # DEFI INTELLIGENCE
    # --------------------------------------------------------

    defi_found = defi_signal.get(
        "found",
        False,
    )

    defi_status = defi_signal.get(
        "status",
        "",
    )

    if defi_found:

        protocol = clean_display_text(
            defi_signal.get(
                "protocol",
                "Recognized",
            )
        )

        protocol = html.escape(
            protocol
        )

        tvl = defi_signal.get(
            "tvl",
            0,
        )

        defi_match = defi_signal.get(
            "match_score",
            0,
        )

        defi_text = (
            "🧩 <b>DeFi:</b> "
            f"✅ {protocol}"
            f" • TVL {format_tvl(tvl)}"
            f" • Match {defi_match}%"
        )

    elif defi_status == "api_unavailable":

        defi_text = (
            "🧩 <b>DeFi:</b> "
            "⚠️ Unavailable"
        )

    else:

        defi_text = (
            "🧩 <b>DeFi:</b> "
            "❌ Not found"
        )

    # --------------------------------------------------------
    # WARNINGS
    # --------------------------------------------------------

    if warnings:

        warning_text = (
            "\n⚠️ <b>Warnings:</b>\n"
        )

        for warning in warnings[:5]:

            warning_text += (
                "• "
                f"{html.escape(str(warning))}\n"
            )

    else:

        warning_text = (
            "\n⚠️ <b>Warnings:</b> "
            "None detected\n"
        )

    # --------------------------------------------------------
    # PROJECT LINKS
    # --------------------------------------------------------

    links_text = ""

    if official_links:

        links_text = (
            "\n🔗 <b>Project links:</b>\n"
        )

        for link in official_links[:3]:

            safe_link = html.escape(
                str(link),
                quote=True,
            )

            links_text += (
                f"• {safe_link}\n"
            )

    # --------------------------------------------------------
    # FINAL MESSAGE
    # --------------------------------------------------------

    message = (
        f"{type_emoji} <b>{name}</b>\n\n"

        f"🏷️ <b>Type:</b> "
        f"{type_emoji} {airdrop_type}\n\n"

        f"📝 {description}\n\n"

        f"🎯 <b>Score:</b> "
        f"{score}/100\n"

        f"🛡️ <b>Confidence:</b> "
        f"{confidence}\n"

        f"🔎 <b>Verification:</b> "
        f"{verification_level}\n\n"

        f"{market_text}\n"

        f"{defi_text}\n"

        f"{warning_text}"

        f"{links_text}\n"

        f"🌐 <b>Source:</b>\n"
        f"{url}\n\n"

        "⚠️ <i>AirdropRadar does not "
        "guarantee legitimacy, eligibility, "
        "or payment. Always verify through "
        "official project channels.</i>"
    )

    return message


# ============================================================
# MONITORING HELPERS
# ============================================================

def get_latest_monitoring_history_id(
    airdrop_id,
):
    """
    Get the newest history record ID for
    a monitored airdrop.

    This is used by the monitoring alert system
    to prevent duplicate alerts.
    """

    try:

        history = get_airdrop_history(
            airdrop_id,
            1,
        )

        if not history:
            return None

        return history[0][0]

    except Exception as error:

        print(
            f"⚠️ Could not get monitoring "
            f"history for {airdrop_id}: {error}"
        )

        return None


# ============================================================
# MONITORING ALERT FORMATTER
# ============================================================

def format_monitoring_alert(
    name,
    url,
    old_score,
    new_score,
    old_confidence,
    new_confidence,
    change_summary,
):
    """
    Format a meaningful monitoring change
    into a Telegram alert.
    """

    safe_name = html.escape(
        str(
            name or "Unknown Airdrop"
        )
    )

    safe_url = html.escape(
        str(
            url or ""
        ),
        quote=True,
    )

    old_score_value = safe_score(
        old_score
    )

    new_score_value = safe_score(
        new_score
    )

    score_difference = (
        new_score_value
        - old_score_value
    )

    # --------------------------------------------------------
    # SCORE CHANGE
    # --------------------------------------------------------

    if score_difference > 0:

        score_text = (
            f"📈 <b>Score:</b> "
            f"{old_score_value} → "
            f"{new_score_value} "
            f"(+{score_difference})"
        )

    elif score_difference < 0:

        score_text = (
            f"📉 <b>Score:</b> "
            f"{old_score_value} → "
            f"{new_score_value} "
            f"({score_difference})"
        )

    else:

        score_text = (
            f"🎯 <b>Score:</b> "
            f"{new_score_value}/100"
        )

    # --------------------------------------------------------
    # CONFIDENCE CHANGE
    # --------------------------------------------------------

    old_confidence_text = format_confidence(
        old_confidence
    )

    new_confidence_text = format_confidence(
        new_confidence
    )

    if old_confidence != new_confidence:

        confidence_text = (
            f"🧠 <b>Confidence:</b> "
            f"{old_confidence_text} → "
            f"{new_confidence_text}"
        )

    else:

        confidence_text = (
            f"🧠 <b>Confidence:</b> "
            f"{new_confidence_text}"
        )

    # --------------------------------------------------------
    # CHANGE SUMMARY
    # --------------------------------------------------------

    if isinstance(
        change_summary,
        (list, tuple),
    ):

        summary_lines = [
            f"• {html.escape(str(item))}"
            for item in change_summary
        ]

        summary_text = "\n".join(
            summary_lines
        )

    else:

        summary_text = html.escape(
            str(
                change_summary
                or "A meaningful change was detected."
            )
        )

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    message = (
        "🚨 <b>AirdropRadar Monitoring Alert</b>\n\n"

        f"🪂 <b>{safe_name}</b>\n\n"

        f"{score_text}\n"

        f"{confidence_text}\n\n"

        "📊 <b>What changed:</b>\n"

        f"{summary_text}\n\n"
    )

    if safe_url:

        message += (
            f'<a href="{safe_url}">'
            "🔗 View Airdrop"
            "</a>\n\n"
        )

    message += (
        "🔄 AirdropRadar will continue "
        "monitoring this opportunity."
    )

    return message


# ============================================================
# TELEGRAM COMMAND MENU
# ============================================================

async def setup_bot(
    application: Application,
):
    """
    Configure Telegram's command menu.
    """

    commands = [
        BotCommand(
            "start",
            "Start AirdropRadar",
        ),

        BotCommand(
            "airdrop",
            "Browse airdrops by type",
        ),

        BotCommand(
            "latest",
            "View latest airdrops",
        ),

        BotCommand(
            "subscribe",
            "Subscribe to airdrop alerts",
        ),

        BotCommand(
            "unsubscribe",
            "Stop airdrop alerts",
        ),

        BotCommand(
            "status",
            "View bot statistics",
        ),

        BotCommand(
            "check",
            "Run a manual scan",
        ),

        BotCommand(
            "help",
            "Show help",
        ),
    ]

    await application.bot.set_my_commands(
        commands
    )

    print(
        "📋 Telegram command menu configured."
    )


# ============================================================
# /AIRDROP
# ============================================================

async def airdrop_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Show the main airdrop category menu.
    """

    counts = get_airdrop_type_counts()

    keyboard = []

    # --------------------------------------------------------
    # ALL AIRDROPS
    # --------------------------------------------------------

    total = get_total_airdrops()

    keyboard.append(
        [
            InlineKeyboardButton(
                f"🪂 All Airdrops ({total})",
                callback_data="airdrop:all",
            )
        ]
    )

    # --------------------------------------------------------
    # CATEGORY BUTTONS
    # --------------------------------------------------------

    types = get_airdrop_types()

    row = []

    for airdrop_type in types:

        emoji = get_airdrop_type_emoji(
            airdrop_type
        )

        count = counts.get(
            airdrop_type,
            0,
        )

        button = InlineKeyboardButton(
            f"{emoji} {airdrop_type} ({count})",
            callback_data=(
                f"airdrop:type:{airdrop_type}"
            ),
        )

        row.append(button)

        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard_markup = InlineKeyboardMarkup(
        keyboard
    )

    message = (
        "🪂 <b>AirdropRadar</b>\n\n"

        "Choose an airdrop type to explore:\n\n"

        "🎯 Points — Earn through points systems\n"
        "🧪 Testnet — Testnet participation\n"
        "🔄 Retroactive — Past activity rewards\n"
        "🏆 Bounty — Tasks and bounty campaigns\n"
        "👑 Holder — Holder-based eligibility\n"
        "💧 Liquidity — Liquidity participation\n"
        "🔗 Activity — Protocol/user activity\n"
        "📦 Other — Other opportunities"
    )

    await update.message.reply_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard_markup,
    )


# ============================================================
# CATEGORY LIST
# ============================================================

async def show_airdrop_category(
    query,
    airdrop_type,
    page=1,
):
    """
    Display a paginated list of airdrops
    belonging to one category.
    """

    emoji = get_airdrop_type_emoji(
        airdrop_type
    )

    per_page = 10

    # --------------------------------------------------------
    # GET ALL AIRDROPS IN CATEGORY
    # --------------------------------------------------------

    all_airdrops = get_airdrops_by_type(
        airdrop_type,
        1000,
    )

    # --------------------------------------------------------
    # EMPTY CATEGORY
    # --------------------------------------------------------

    if not all_airdrops:

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Back to categories",
                    callback_data="airdrop:menu",
                )
            ]
        ]

        await query.edit_message_text(
            (
                f"{emoji} "
                f"<b>{html.escape(airdrop_type)}</b>\n\n"
                "📭 No airdrops found in this "
                "category yet."
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return

    # --------------------------------------------------------
    # PAGINATION CALCULATION
    # --------------------------------------------------------

    total_airdrops = len(all_airdrops)

    total_pages = (
        total_airdrops + per_page - 1
    ) // per_page

    # Make sure page stays valid

    if page < 1:
        page = 1

    if page > total_pages:
        page = total_pages

    start_index = (
        (page - 1) * per_page
    )

    end_index = (
        start_index + per_page
    )

    airdrops = all_airdrops[
        start_index:end_index
    ]

    # --------------------------------------------------------
    # AIRDROP BUTTONS
    # --------------------------------------------------------

    keyboard = []

    for airdrop in airdrops:

        data = extract_airdrop_record(
            airdrop
        )

        airdrop_id = data["id"]

        name = clean_display_text(
            data["name"]
        )

        score = safe_score(
            data.get(
                "score",
                0,
            )
        )

        confidence = format_confidence(
            data.get(
                "confidence"
            )
        )

        button_text = (
            f"🪂 {name[:35]}"
        )

        button_text += (
            f" • {score}"
        )

        button_text += (
            f" • {confidence}"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    button_text,
                    callback_data=(
                        f"airdrop:view:"
                        f"{airdrop_id}:"
                        f"{airdrop_type}"
                    ),
                )
            ]
        )

    # --------------------------------------------------------
    # PAGINATION BUTTONS
    # --------------------------------------------------------

    pagination_row = []

    if page > 1:

        pagination_row.append(
            InlineKeyboardButton(
                "◀️ Previous",
                callback_data=(
                    f"airdrop:page:"
                    f"{airdrop_type}:"
                    f"{page - 1}"
                ),
            )
        )

    pagination_row.append(
        InlineKeyboardButton(
            f"Page {page}/{total_pages}",
            callback_data="airdrop:noop",
        )
    )

    if page < total_pages:

        pagination_row.append(
            InlineKeyboardButton(
                "Next ▶️",
                callback_data=(
                    f"airdrop:page:"
                    f"{airdrop_type}:"
                    f"{page + 1}"
                ),
            )
        )

    keyboard.append(
        pagination_row
    )

    # --------------------------------------------------------
    # BACK BUTTON
    # --------------------------------------------------------

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Back to categories",
                callback_data="airdrop:menu",
            )
        ]
    )

    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    message = (
        f"{emoji} "
        f"<b>{html.escape(airdrop_type)} "
        "Airdrops</b>\n\n"

        f"Showing {start_index + 1}-"
        f"{min(end_index, total_airdrops)} "
        f"of {total_airdrops} available "
        "airdrops.\n\n"

        "Tap an airdrop to view its full analysis."
    )

    await query.edit_message_text(
        message,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


# ============================================================
# ALL AIRDROPS
# ============================================================

async def show_all_airdrops(
    query,
):
    """
    Display the latest airdrops across
    all categories.
    """

    airdrops = get_latest_airdrops(
        10
    )

    if not airdrops:

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Back to categories",
                    callback_data="airdrop:menu",
                )
            ]
        ]

        await query.edit_message_text(
            (
                "🪂 <b>All Airdrops</b>\n\n"
                "📭 No airdrops found yet."
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return

    keyboard = []

    for airdrop in airdrops:

        data = extract_airdrop_record(
            airdrop
        )

        airdrop_id = data["id"]

        name = clean_display_text(
            data["name"]
        )

        score = safe_score(
            data.get(
                "score",
                0,
            )
        )

        airdrop_type = data.get(
            "airdrop_type",
            "Other",
        )

        if not airdrop_type:
            airdrop_type = "Other"

        emoji = get_airdrop_type_emoji(
            airdrop_type
        )

        button_text = (
            f"{emoji} {name[:35]}"
            f" • {score}"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    button_text,
                    callback_data=(
                        f"airdrop:view:"
                        f"{airdrop_id}:"
                        f"{airdrop_type}"
                    ),
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Back to categories",
                callback_data="airdrop:menu",
            )
        ]
    )

    await query.edit_message_text(
        (
            "🪂 <b>All Airdrops</b>\n\n"
            "Here are the latest discoveries.\n\n"
            "Tap one to view the full analysis."
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


# ============================================================
# AIRDROP DETAILS
# ============================================================

async def show_airdrop_details(
    query,
    airdrop_id,
    category=None,
):
    """
    Display the full details of one airdrop.
    """

    # --------------------------------------------------------
    # VALIDATE ID
    # --------------------------------------------------------

    try:

        airdrop_id = int(
            airdrop_id
        )

    except (TypeError, ValueError):

        await query.answer(
            "Invalid airdrop.",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # LOAD AIRDROP
    # --------------------------------------------------------

    airdrop = get_airdrop_by_id(
        airdrop_id
    )

    if not airdrop:

        await query.answer(
            "Airdrop no longer exists.",
            show_alert=True,
        )

        return

    data = extract_airdrop_record(
        airdrop
    )

    # --------------------------------------------------------
    # DETERMINE DISPLAY CATEGORY
    # --------------------------------------------------------

    if category:
        display_type = category
    else:
        display_type = data.get(
            "airdrop_type",
            "Other",
        )

    if not display_type:
        display_type = "Other"

    # --------------------------------------------------------
    # FORMAT MESSAGE
    # --------------------------------------------------------

    message = format_airdrop(
        airdrop,
        display_type=display_type,
    )

    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

    source_url = str(
        data.get(
            "url",
            "",
        ) or ""
    ).strip()

    keyboard = []

    if source_url:

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🌐 Open source",
                    url=source_url,
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Back to category",
                callback_data=(
                    f"airdrop:type:{display_type}"
                ),
            ),

            InlineKeyboardButton(
                "🪂 Categories",
                callback_data="airdrop:menu",
            ),
        ]
    )

    await query.edit_message_text(
        message,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


# ============================================================
# AIRDROP CALLBACK HANDLER
# ============================================================

async def airdrop_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Handle all inline-button interactions
    for the AirdropRadar category browser.
    """

    query = update.callback_query

    await query.answer()

    data = query.data or ""

    # --------------------------------------------------------
    # MAIN CATEGORY MENU
    # --------------------------------------------------------

    if data == "airdrop:menu":

        counts = get_airdrop_type_counts()

        keyboard = []

        total = get_total_airdrops()

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🪂 All Airdrops ({total})",
                    callback_data="airdrop:all",
                )
            ]
        )

        types = get_airdrop_types()

        row = []

        for airdrop_type in types:

            emoji = get_airdrop_type_emoji(
                airdrop_type
            )

            count = counts.get(
                airdrop_type,
                0,
            )

            row.append(
                InlineKeyboardButton(
                    f"{emoji} {airdrop_type} ({count})",
                    callback_data=(
                        f"airdrop:type:{airdrop_type}"
                    ),
                )
            )

            if len(row) == 2:

                keyboard.append(row)
                row = []

        if row:
            keyboard.append(row)

        await query.edit_message_text(
            (
                "🪂 <b>AirdropRadar</b>\n\n"
                "Choose an airdrop type to explore."
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return

    # --------------------------------------------------------
    # ALL AIRDROPS
    # --------------------------------------------------------

    if data == "airdrop:all":

        await show_all_airdrops(
            query
        )

        return

    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:type:"
    ):

        airdrop_type = data[
            len("airdrop:type:"):
        ]

        await show_airdrop_category(
            query,
            airdrop_type,
        )

        return

    # --------------------------------------------------------
    # CATEGORY PAGINATION
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:page:"
    ):

        page_data = data[
            len("airdrop:page:"):
        ]

        parts = page_data.rsplit(
            ":",
            1,
        )

        if len(parts) != 2:

            await query.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        airdrop_type = parts[0]

        try:
            page = int(parts[1])

        except ValueError:

            await query.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        await show_airdrop_category(
            query,
            airdrop_type,
            page,
        )

        return

    # --------------------------------------------------------
    # PAGINATION PAGE INDICATOR
    # --------------------------------------------------------

    if data == "airdrop:noop":

        return

    # --------------------------------------------------------
    # AIRDROP DETAILS
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:view:"
    ):

        view_data = data[
            len("airdrop:view:"):
        ]

        parts = view_data.split(
            ":",
            1,
        )

        airdrop_id = parts[0]

        if len(parts) > 1:
            category = parts[1]
        else:
            category = None

        await show_airdrop_details(
            query,
            airdrop_id,
            category,
        )

        return

    await query.answer(
        "Unknown action.",
        show_alert=True,
    )


# ============================================================
# /START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Welcome the user using their Telegram first name.
    """

    user = update.effective_user

    user_name = (
        user.first_name
        if user and user.first_name
        else "there"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🪂 Browse Airdrops",
                    callback_data="airdrop:menu",
                )
            ],

            [
                InlineKeyboardButton(
                    "📊 Status",
                    callback_data="bot:status",
                ),

                InlineKeyboardButton(
                    "❓ Help",
                    callback_data="bot:help",
                ),
            ],
        ]
    )

    message = (
        f"👋 Hey {html.escape(user_name)}!\n\n"

        "🚀 <b>Welcome to AirdropRadar!</b>\n\n"

        "I'm being built to discover, verify, "
        "and track legitimate crypto airdrop "
        "opportunities.\n\n"

        "Use the button below or the command menu "
        "to explore available airdrops."
    )

    await update.message.reply_text(
        message,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ============================================================
# /HELP
# ============================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = (
        "🪂 <b>AirdropRadar Help</b>\n\n"

        "/airdrop — Browse airdrops by type\n"
        "/latest — View latest airdrops\n"
        "/subscribe — Subscribe to alerts\n"
        "/unsubscribe — Unsubscribe\n"
        "/status — Database statistics\n"
        "/check — Run a manual scan\n"
        "/help — Show this help message\n\n"

        "Airdrops are scored using multiple "
        "signals including verification, "
        "market data, DeFi data and risk indicators."
    )

    await update.message.reply_text(
        message,
        parse_mode="HTML",
    )


# ============================================================
# /SUBSCRIBE
# ============================================================

async def subscribe(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    chat_id = update.effective_chat.id

    add_subscriber(
        chat_id
    )

    await update.message.reply_text(
        "🔔 <b>Subscribed!</b>\n\n"
        "You'll receive alert-worthy "
        "airdrops automatically.",
        parse_mode="HTML",
    )


# ============================================================
# /UNSUBSCRIBE
# ============================================================

async def unsubscribe(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    chat_id = update.effective_chat.id

    remove_subscriber(
        chat_id
    )

    await update.message.reply_text(
        "🔕 <b>Unsubscribed.</b>\n\n"
        "You will no longer receive automatic alerts.",
        parse_mode="HTML",
    )


# ============================================================
# /LATEST
# ============================================================

async def latest(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    try:

        results = get_latest_airdrops(
            5
        )

        if not results:

            await update.message.reply_text(
                "📭 No airdrops found yet."
            )

            return

        await update.message.reply_text(
            "🪂 <b>Latest AirdropRadar Discoveries</b>",
            parse_mode="HTML",
        )

        for index, airdrop in enumerate(
            results,
            start=1,
        ):

            try:

                message = format_airdrop(
                    airdrop
                )

                await update.message.reply_text(
                    message,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )

            except Exception as error:

                print(
                    f"⚠️ Failed formatting "
                    f"result #{index}: {error}"
                )

    except Exception as error:

        print(
            f"❌ /latest error: {error}"
        )

        await update.message.reply_text(
            "❌ Could not load the latest discoveries.\n"
            "Check the PowerShell console."
        )


# ============================================================
# /STATUS
# ============================================================

async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    total = get_total_airdrops()

    high = get_high_confidence_count()

    medium = get_medium_confidence_count()

    low = get_low_confidence_count()

    subscribers = len(
        get_subscribers()
    )

    message = (
        "📊 <b>AirdropRadar Status</b>\n\n"

        f"🪂 Total discoveries: "
        f"<b>{total}</b>\n\n"

        f"🟢 High confidence: "
        f"<b>{high}</b>\n"

        f"🟡 Medium confidence: "
        f"<b>{medium}</b>\n"

        f"🔴 Low confidence: "
        f"<b>{low}</b>\n\n"

        f"👥 Subscribers: "
        f"<b>{subscribers}</b>\n\n"

        "🟢 System: <b>Online</b>"
    )

    await update.message.reply_text(
        message,
        parse_mode="HTML",
    )


# ============================================================
# /CHECK
# ============================================================

async def check(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        "🔎 Running AirdropRadar scan...\n\n"
        "Please wait."
    )

    try:

        results = await asyncio.to_thread(
            run_scan_once
        )

        if results is None:

            await update.message.reply_text(
                "⏳ A scan is already running.\n"
                "Please wait for it to finish."
            )

            return

        if not results:

            await update.message.reply_text(
                "📭 Scan complete.\n\n"
                "No new airdrops were found."
            )

            return

        stored_count = store_scan_results(
            results
        )

        alert_count = 0

        for result in results:

            if not isinstance(
                result,
                dict,
            ):
                continue

            score = safe_score(
                result.get(
                    "score",
                    0,
                )
            )

            if score >= ALERT_THRESHOLD:
                alert_count += 1

        message = (
            "✅ <b>Scan complete.</b>\n\n"

            f"🪂 Processed results: "
            f"<b>{len(results)}</b>\n"

            f"💾 Stored: "
            f"<b>{stored_count}</b>\n"

            f"🚨 Alert-worthy: "
            f"<b>{alert_count}</b>\n\n"

            "Use /airdrop to browse by category "
            "or /latest to view the newest results."
        )

        await update.message.reply_text(
            message,
            parse_mode="HTML",
        )

    except Exception as error:

        print(
            f"❌ Scan error: {error}"
        )

        await update.message.reply_text(
            "❌ Scan failed.\n"
            "Check the PowerShell console for details."
        )


# ============================================================
# GENERAL BOT CALLBACK
# ============================================================

async def general_callback(
    update,
    context,
):

    query = update.callback_query

    await query.answer()

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if query.data == "bot:status":

        total = get_total_airdrops()

        high = get_high_confidence_count()

        medium = get_medium_confidence_count()

        low = get_low_confidence_count()

        subscribers = len(
            get_subscribers()
        )

        message = (
            "📊 <b>AirdropRadar Status</b>\n\n"

            f"🪂 Total discoveries: "
            f"<b>{total}</b>\n\n"

            f"🟢 High confidence: "
            f"<b>{high}</b>\n"

            f"🟡 Medium confidence: "
            f"<b>{medium}</b>\n"

            f"🔴 Low confidence: "
            f"<b>{low}</b>\n\n"

            f"👥 Subscribers: "
            f"<b>{subscribers}</b>\n\n"

            "🟢 System: <b>Online</b>"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🪂 Browse Airdrops",
                    callback_data="airdrop:menu",
                )
            ]
        ]

        await query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if query.data == "bot:help":

        message = (
            "❓ <b>AirdropRadar Help</b>\n\n"

            "🪂 <b>/airdrop</b>\n"
            "Browse opportunities by type.\n\n"

            "📋 <b>/latest</b>\n"
            "View the latest discoveries.\n\n"

            "🔔 <b>/subscribe</b>\n"
            "Receive alert-worthy discoveries.\n\n"

            "🔎 <b>/check</b>\n"
            "Run a manual scan.\n\n"

            "📊 <b>/status</b>\n"
            "View system statistics."
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🪂 Browse Airdrops",
                    callback_data="airdrop:menu",
                )
            ]
        ]

        await query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return


# ============================================================
# AUTOMATIC SCAN + TELEGRAM ALERTS
# ============================================================

async def automatic_scan(
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Automatically scan for new airdrops and send
    alert-worthy discoveries to subscribers.
    """

    print(
        "\n⏰ Automatic AirdropRadar scan started..."
    )

    try:

        # ----------------------------------------------------
        # RUN LOCKED SCAN
        # ----------------------------------------------------

        results = await asyncio.to_thread(
            run_scan_once
        )

        if results is None:

            print(
                "⏳ Automatic scan skipped "
                "because another scan is already running."
            )

            return

        # ----------------------------------------------------
        # HANDLE EMPTY RESULTS
        # ----------------------------------------------------

        if not results:

            print(
                "📭 No new airdrops found."
            )

            return

        # ----------------------------------------------------
        # STORE RESULTS
        # ----------------------------------------------------

        stored_count = store_scan_results(
            results
        )

        print(
            f"💾 Automatic scan stored: "
            f"{stored_count}"
        )

        # ----------------------------------------------------
        # GET SUBSCRIBERS
        # ----------------------------------------------------

        subscribers = get_subscribers()

        if not subscribers:

            print(
                "👥 No subscribers. "
                "Skipping Telegram alerts."
            )

            return

        print(
            f"👥 Subscribers available: "
            f"{len(subscribers)}"
        )

        # ----------------------------------------------------
        # PROCESS EACH RESULT
        # ----------------------------------------------------

        alert_candidates = 0
        alerts_sent = 0

        for result in results:

            if not isinstance(
                result,
                dict,
            ):
                continue

            score = safe_score(
                result.get(
                    "score",
                    0,
                )
            )

            if score < ALERT_THRESHOLD:

                print(
                    f"⏭️ Below alert threshold: "
                    f"{result.get('name', 'Unknown')} "
                    f"({score}/{ALERT_THRESHOLD})"
                )

                continue

            alert_candidates += 1

            airdrop_url = str(
                result.get(
                    "url",
                    "",
                ) or ""
            ).strip()

            if not airdrop_url:

                print(
                    f"⚠️ Skipping alert for "
                    f"{result.get('name', 'Unknown')} "
                    f"because it has no URL."
                )

                continue

            airdrop = {
                "id": result.get("id"),

                "name": result.get(
                    "name",
                    "",
                ),

                "url": airdrop_url,

                "description": result.get(
                    "description",
                    "",
                ),

                "source": result.get(
                    "source",
                    "",
                ),

                "score": score,

                "confidence": result.get(
                    "confidence",
                    "",
                ),

                "verified": result.get(
                    "verified",
                    False,
                ),

                "verification_level": result.get(
                    "verification_level",
                    "",
                ),

                "official_links": result.get(
                    "official_links",
                    [],
                ),

                "warnings": result.get(
                    "warnings",
                    [],
                ),

                "market_signal": result.get(
                    "market_signal",
                    {},
                ),

                "defi_signal": result.get(
                    "defi_signal",
                    {},
                ),

                "created_at": result.get(
                    "created_at",
                    "",
                ),

                "last_checked_at": result.get(
                    "last_checked_at",
                    "",
                ),

                "previous_score": result.get(
                    "previous_score",
                    None,
                ),

                "previous_confidence": result.get(
                    "previous_confidence",
                    "",
                ),

                "last_change_at": result.get(
                    "last_change_at",
                    "",
                ),

                "next_check_at": result.get(
                    "next_check_at",
                    "",
                ),

                "airdrop_type": result.get(
                    "airdrop_type",
                    "Other",
                ),
            }

            # ------------------------------------------------
            # FORMAT TELEGRAM ALERT
            # ------------------------------------------------

            message = format_airdrop(
                airdrop
            )

            # ------------------------------------------------
            # SEND TO EACH SUBSCRIBER
            # ------------------------------------------------

            for chat_id in subscribers:

                try:

                    if alert_exists(
                        chat_id,
                        airdrop_url,
                    ):

                        print(
                            f"🔁 Alert already sent "
                            f"to {chat_id}: "
                            f"{result.get('name', 'Unknown')}"
                        )

                        continue

                    print(
                        f"📨 Sending alert to "
                        f"{chat_id}: "
                        f"{result.get('name', 'Unknown')} "
                        f"(score {score})"
                    )

                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )

                    record_alert(
                        chat_id,
                        airdrop_url,
                    )

                    alerts_sent += 1

                    print(
                        f"✅ Alert sent to "
                        f"{chat_id}: "
                        f"{result.get('name', 'Unknown')}"
                    )

                except Exception as error:

                    print(
                        f"⚠️ Failed alert to "
                        f"{chat_id}: "
                        f"{error}"
                    )

        # ----------------------------------------------------
        # FINAL SUMMARY
        # ----------------------------------------------------

        print(
            f"🚨 Alert-worthy discoveries: "
            f"{alert_candidates}"
        )

        print(
            f"📨 Telegram alerts sent: "
            f"{alerts_sent}"
        )

    except Exception as error:

        print(
            f"❌ Automatic scan error: "
            f"{error}"
        )


# ============================================================
# AUTOMATIC MONITORING ALERTS
# ============================================================

async def automatic_monitoring(
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Run the monitoring engine automatically
    and send alerts when meaningful changes
    are detected.
    """

    print(
        "\n🔄 Automatic AirdropRadar monitoring started..."
    )

    try:

        # ----------------------------------------------------
        # RUN TRACKING ENGINE
        # ----------------------------------------------------

        results = await asyncio.to_thread(
            run_tracking_cycle
        )

        if not results:

            print(
                "📭 No airdrops were due for monitoring."
            )

            return

        # ----------------------------------------------------
        # GET SUBSCRIBERS
        # ----------------------------------------------------

        subscribers = get_subscribers()

        if not subscribers:

            print(
                "👥 No subscribers for monitoring alerts."
            )

            return

        alerts_sent = 0
        changes_found = 0

        # ----------------------------------------------------
        # PROCESS TRACKING RESULTS
        # ----------------------------------------------------

        for result in results:

            if not isinstance(
                result,
                dict,
            ):
                continue

            if not result.get(
                "success",
                False,
            ):
                continue

            if not result.get(
                "change_detected",
                False,
            ):
                continue

            changes_found += 1

            airdrop_id = result.get(
                "airdrop_id"
            )

            if not airdrop_id:

                print(
                    "⚠️ Monitoring result "
                    "has no airdrop ID."
                )

                continue

            name = result.get(
                "name",
                "Unknown Airdrop",
            )

            url = result.get(
                "url",
                "",
            )

            old_score = result.get(
                "old_score",
                0,
            )

            new_score = result.get(
                "new_score",
                0,
            )

            old_confidence = result.get(
                "old_confidence",
                "",
            )

            new_confidence = result.get(
                "new_confidence",
                "",
            )

            change_summary = result.get(
                "change_summary",
                "A meaningful change was detected.",
            )

            # ------------------------------------------------
            # GET LATEST HISTORY ID
            # ------------------------------------------------

            history_id = (
                get_latest_monitoring_history_id(
                    airdrop_id
                )
            )

            if history_id is None:

                print(
                    f"⚠️ No history record found "
                    f"for {name}."
                )

                continue

            # ------------------------------------------------
            # FORMAT MONITORING ALERT
            # ------------------------------------------------

            message = format_monitoring_alert(
                name,
                url,
                old_score,
                new_score,
                old_confidence,
                new_confidence,
                change_summary,
            )

            # ------------------------------------------------
            # SEND TO SUBSCRIBERS
            # ------------------------------------------------

            for chat_id in subscribers:

                try:

                    if monitoring_alert_exists(
                        chat_id,
                        history_id,
                    ):

                        print(
                            f"🔁 Monitoring alert "
                            f"already sent to "
                            f"{chat_id}: {name}"
                        )

                        continue

                    print(
                        f"📨 Sending monitoring alert "
                        f"to {chat_id}: {name}"
                    )

                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )

                    record_monitoring_alert(
                        chat_id,
                        airdrop_id,
                        history_id,
                    )

                    alerts_sent += 1

                    print(
                        f"📢 Monitoring alert sent "
                        f"to {chat_id}: {name}"
                    )

                except Exception as error:

                    print(
                        f"⚠️ Failed monitoring alert "
                        f"to {chat_id}: {error}"
                    )

        # ----------------------------------------------------
        # FINAL SUMMARY
        # ----------------------------------------------------

        print(
            f"📈 Meaningful changes found: "
            f"{changes_found}"
        )

        print(
            f"🔔 Monitoring alerts sent: "
            f"{alerts_sent}"
        )

    except Exception as error:

        print(
            f"❌ Automatic monitoring error: "
            f"{error}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    create_database()

    print(
        "\n🤖 Starting AirdropRadar bot..."
    )

    application = (
        Application.builder()
        .token(
            config.require_bot_token()
        )
        .post_init(
            setup_bot
        )
        .build()
    )

    # --------------------------------------------------------
    # COMMAND HANDLERS
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "airdrop",
            airdrop_menu,
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "subscribe",
            subscribe,
        )
    )

    application.add_handler(
        CommandHandler(
            "unsubscribe",
            unsubscribe,
        )
    )

    application.add_handler(
        CommandHandler(
            "latest",
            latest,
        )
    )

    application.add_handler(
        CommandHandler(
            "status",
            status,
        )
    )

    application.add_handler(
        CommandHandler(
            "check",
            check,
        )
    )

    # --------------------------------------------------------
    # AIRDROP INLINE BUTTONS
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            airdrop_callback,
            pattern=r"^airdrop:",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            general_callback,
            pattern=r"^bot:",
        )
    )

    # --------------------------------------------------------
    # AUTOMATIC DISCOVERY SCANNING
    # --------------------------------------------------------

    application.job_queue.run_repeating(
        automatic_scan,
        interval=SCAN_INTERVAL,
        first=30,
    )

    print(
        "⏰ Automatic scanning enabled."
    )

    # --------------------------------------------------------
    # AUTOMATIC MONITORING
    # --------------------------------------------------------

    application.job_queue.run_repeating(
        automatic_monitoring,
        interval=3600,
        first=120,
    )

    print(
        "🔄 Automatic monitoring enabled."
    )

    # --------------------------------------------------------
    # STARTUP
    # --------------------------------------------------------

    print(
        "🪂 Airdrop category browser enabled."
    )

    print(
        "🚀 AirdropRadar is online!"
    )

    application.run_polling()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()