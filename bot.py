import asyncio
import json
import html
import re
import threading
from datetime import datetime

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
    get_alert_preferences,
    set_alert_preference,
    get_airdrops_for_lifecycle,
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
    monitoring_alert_exists,
    record_monitoring_alert,
    get_airdrop_history,
    track_airdrop,
    untrack_airdrop,
    is_airdrop_tracked,
    get_tracked_airdrops,
)


# ============================================================
# SCANNER + TRACKER
# ============================================================

from filter import run_scan
from tracker import run_tracking_cycle
from telegram.error import BadRequest
from participation import analyze_participation
from lifecycle import analyze_lifecycle
from database import get_latest_monitoring_history_id


# ============================================================
# GENERAL HELPERS
# ============================================================

def safe_json(value):
    if not value:
        return []

    if isinstance(value, (list, dict)):
        return value

    try:
        return json.loads(value)
    except Exception:
        return []


def clean_display_text(text):
    if not text:
        return ""

    text = str(text)
    text = html.unescape(text)

    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text,
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = re.sub(
        r"&[a-zA-Z0-9#]+;",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    text = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        text,
    )

    return text.strip()


def format_tvl(tvl):
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
    if value is None:
        return "🔴 Low"

    text = str(value).strip().lower()

    if text == "high":
        return "🟢 High"

    if text == "medium":
        return "🟡 Medium"

    if text == "low":
        return "🔴 Low"

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
    stored_count = 0

    for result in results:

        if not isinstance(result, dict):
            print("⚠️ Skipping invalid scan result.")
            continue

        try:
            save_airdrop(result)
            stored_count += 1

        except Exception as error:
            print(
                f"⚠️ Failed to store "
                f"{result.get('name', 'Unknown')}: {error}"
            )

    print(f"💾 Stored: {stored_count} result(s).")

    return stored_count


# ============================================================
# DATABASE RECORD NORMALIZER
# ============================================================

def extract_airdrop_record(airdrop):

    if isinstance(airdrop, dict):

        return {
            "id": airdrop.get("id"),
            "name": airdrop.get("name", ""),
            "url": airdrop.get("url", ""),
            "description": airdrop.get("description", ""),
            "source": airdrop.get("source", ""),
            "score": airdrop.get("score", 0),
            "confidence": airdrop.get("confidence", ""),
            "verified": airdrop.get("verified", False),
            "verification_level": airdrop.get(
                "verification_level",
                "",
            ),
            "official_links": airdrop.get(
                "official_links",
                [],
            ),
            "warnings": airdrop.get("warnings", []),
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

            "lifecycle": airdrop.get(
                "lifecycle", 
                {}
            ),

            "risk_signals": airdrop.get(
                "risk_signals",
                [],
            ),

            "intelligence_risk_level": airdrop.get(
                "intelligence_risk_level",
                "",
            ),
            "risk_summary": airdrop.get(
                "risk_summary",
                "",
            ),
            "cross_source_matches": airdrop.get(
                "cross_source_matches",
                [],
            ),
            "matched_sources": airdrop.get(
                "matched_sources",
                [],
            ),
            "cross_source_match_count": airdrop.get(
                "cross_source_match_count",
                0,
            ),
        }

    values = list(airdrop)

    def get_value(index, default=None):
        if index < len(values):
            return values[index]
        return default

    return {
        "id": get_value(0),
        "name": get_value(1, ""),
        "url": get_value(2, ""),
        "description": get_value(3, ""),
        "source": get_value(4, ""),
        "score": get_value(5, 0),
        "confidence": get_value(6, ""),
        "verified": get_value(7, False),
        "verification_level": get_value(8, ""),
        "official_links": get_value(9, []),
        "warnings": get_value(10, []),
        "market_signal": get_value(11, {}),
        "defi_signal": get_value(12, {}),
        "created_at": get_value(13, ""),
        "last_checked_at": get_value(14, ""),
        "previous_score": get_value(15, None),
        "previous_confidence": get_value(16, ""),
        "last_change_at": get_value(17, ""),
        "next_check_at": get_value(18, ""),
        "airdrop_type": get_value(19, "Other"),
        "risk_signals": get_value(20, []),
        "intelligence_risk_level": get_value(21, ""),
        "risk_summary": get_value(22, ""),
        "cross_source_matches": get_value(23, []),
        "matched_sources": get_value(24, []),
        "cross_source_match_count": get_value(25, 0),
    }

# ============================================================
# OPPORTUNITY CARD
# ============================================================
def format_airdrop(airdrop, display_type=None):

    data = extract_airdrop_record(airdrop)

    # --------------------------------------------------------
    # LIFECYCLE
    # --------------------------------------------------------

    lifecycle = data.get(
        "lifecycle",
        {},
    )

    if not isinstance(lifecycle, dict) or not lifecycle:
        try:
            lifecycle = analyze_lifecycle(data)
        except Exception as error:
            print(
                f"⚠️ Lifecycle analysis error: {error}"
            )
            lifecycle = {}

    lifecycle_status = lifecycle.get(
        "status"
    )

    lifecycle_start = lifecycle.get(
        "start_date"
    )

    lifecycle_end = lifecycle.get(
        "end_date"
    )

    if lifecycle_status == "upcoming":
        lifecycle_status_text = "🟡 Upcoming"
    elif lifecycle_status == "active":
        lifecycle_status_text = "🟢 Active"
    elif lifecycle_status == "ending_soon":
        lifecycle_status_text = "🟠 Ending Soon"
    elif lifecycle_status == "ended":
        lifecycle_status_text = "🔴 Ended"
    else:
        lifecycle_status_text = "⚪ Unknown"

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    name = clean_display_text(
        data.get("name", "")
    ) or "Unknown Opportunity"

    description = clean_display_text(
        data.get("description", "")
    )

    if len(description) > 700:
        description = (
            description[:700]
            .rsplit(" ", 1)[0]
            + "..."
        )

    url = str(
        data.get("url", "") or ""
    ).strip()

    score = safe_score(
        data.get("score", 0)
    )

    confidence = format_confidence(
        data.get("confidence")
    )

    verification_level = clean_display_text(
        data.get("verification_level", "")
    ) or "Unknown"

    airdrop_type = clean_display_text(
        display_type
        or data.get("airdrop_type", "Other")
    ) or "Other"

    emoji = get_airdrop_type_emoji(
        airdrop_type
    )

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    risk_level = clean_display_text(
        data.get(
            "intelligence_risk_level",
            "",
        )
    ).lower()

    risk_summary = clean_display_text(
        data.get(
            "risk_summary",
            "",
        )
    )

    risk_signals = safe_json(
        data.get(
            "risk_signals",
            [],
        )
    )

    if risk_level == "critical":
        risk_text = "🔴 Critical"
    elif risk_level == "high":
        risk_text = "🔴 High"
    elif risk_level == "medium":
        risk_text = "🟠 Medium"
    elif risk_level == "low":
        risk_text = "🟢 Low"
    else:
        risk_text = "⚪ Unknown"

    # --------------------------------------------------------
    # CROSS SOURCE
    # --------------------------------------------------------

    matched_sources = safe_json(
        data.get(
            "matched_sources",
            [],
        )
    )

    cross_source_matches = safe_json(
        data.get(
            "cross_source_matches",
            [],
        )
    )

    try:
        cross_source_count = int(
            data.get(
                "cross_source_match_count",
                0,
            ) or 0
        )
    except (TypeError, ValueError):
        cross_source_count = 0

    # --------------------------------------------------------
    # WARNINGS
    # --------------------------------------------------------

    warnings = safe_json(
        data.get(
            "warnings",
            [],
        )
    )

    warning_lines = []

    if isinstance(warnings, list):

        for warning in warnings[:5]:

            if isinstance(warning, dict):

                warning_text = (
                    warning.get("message")
                    or warning.get("warning")
                    or warning.get("text")
                    or ""
                )

            else:
                warning_text = warning

            warning_text = clean_display_text(
                warning_text
            )

            if warning_text:
                warning_lines.append(
                    "• "
                    + html.escape(
                        str(warning_text)
                    )
                )

    if warning_lines:

        warning_text = (
            "⚠️ <b>Warnings</b>\n"
            + "\n".join(warning_lines)
        )

    else:

        warning_text = (
            "⚠️ <b>Warnings:</b> "
            "None detected"
        )

    # --------------------------------------------------------
    # RISK SIGNALS
    # --------------------------------------------------------

    risk_lines = []

    ignored_risk_values = {
        "unavailable",
        "unknown",
        "none",
        "null",
        "n/a",
        "project_domains=[]",
        "official_links=[]",
    }

    if isinstance(risk_signals, list):

        for signal in risk_signals[:10]:

            if isinstance(signal, dict):

                signal_text = (
                    signal.get("evidence")
                    or signal.get("value")
                    or signal.get("message")
                    or ""
                )

            else:

                signal_text = signal

            signal_text = clean_display_text(
                signal_text
            )

            if not signal_text:
                continue

            normalized_signal = (
                str(signal_text)
                .strip()
                .lower()
            )

            if normalized_signal in ignored_risk_values:
                continue

            if normalized_signal.startswith(
                "project_domains="
            ):
                continue

            if normalized_signal.startswith(
                "official_links="
            ):
                continue

            risk_lines.append(
                "• "
                + html.escape(
                    str(signal_text)
                )
            )

    if risk_lines:

        risk_signal_text = (
            "🚨 <b>Risk Signals</b>\n"
            + "\n".join(
                risk_lines[:5]
            )
        )

    else:

        risk_signal_text = ""

    # --------------------------------------------------------
    # RISK SUMMARY
    # --------------------------------------------------------

    if risk_summary:

        risk_summary_text = (
            "🧠 <b>Risk Analysis:</b> "
            + html.escape(
                risk_summary
            )
        )

    else:

        risk_summary_text = ""

    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    market = data.get(
        "market_signal",
        {},
    )

    if isinstance(market, str):
        market = safe_json(market)

    market_text = ""

    if isinstance(market, dict):

        found = market.get(
            "found",
            market.get(
                "available",
                False,
            ),
        )

        if found:

            symbol = clean_display_text(
                market.get("symbol", "")
            )

            price = market.get("price")
            market_cap = market.get("market_cap")

            parts = []

            if symbol:
                parts.append(
                    html.escape(symbol)
                )

            if price is not None:

                try:
                    parts.append(
                        f"${float(price):,.4f}"
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            if market_cap is not None:

                parts.append(
                    f"MC {format_tvl(market_cap)}"
                )

            if parts:

                market_text = (
                    "🪙 <b>Market:</b> "
                    + " • ".join(parts)
                )

            else:

                market_text = (
                    "🪙 <b>Market:</b> "
                    "🟢 Data found"
                )

        else:

            market_text = (
                "🪙 <b>Market:</b> "
                "❌ Not found"
            )

    # --------------------------------------------------------
    # DEFI
    # --------------------------------------------------------

    defi = data.get(
        "defi_signal",
        {},
    )

    if isinstance(defi, str):
        defi = safe_json(defi)

    defi_text = ""

    if isinstance(defi, dict):

        found = defi.get(
            "found",
            defi.get(
                "available",
                False,
            ),
        )

        if found:

            tvl = defi.get("tvl")
            protocols = defi.get("protocols")

            parts = []

            if tvl is not None:
                parts.append(
                    f"TVL {format_tvl(tvl)}"
                )

            if protocols:

                try:
                    parts.append(
                        f"{int(protocols)} protocol(s)"
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            if parts:

                defi_text = (
                    "🧩 <b>DeFi:</b> "
                    + " • ".join(parts)
                )

            else:

                defi_text = (
                    "🧩 <b>DeFi:</b> "
                    "🟢 Data found"
                )

        else:

            defi_text = (
                "🧩 <b>DeFi:</b> "
                "❌ Not found"
            )

    # --------------------------------------------------------
    # CROSS SOURCE TEXT
    # --------------------------------------------------------

    cross_source_text = ""

    if (
        cross_source_count > 0
        or matched_sources
        or cross_source_matches
    ):

        source_count = max(
            cross_source_count,
            len(matched_sources)
            if isinstance(
                matched_sources,
                list,
            )
            else 0,
        )

        cross_source_text = (
            "🔗 <b>Cross-Source Match:</b> "
            f"{source_count} additional source(s)"
        )

    # --------------------------------------------------------
    # SMART ALERT REASONS
    # --------------------------------------------------------

    smart_alert_text = ""

    if isinstance(airdrop, dict):

        smart_alert_reasons = airdrop.get(
            "smart_alert_reasons",
            [],
        )

        if (
            isinstance(
                smart_alert_reasons,
                list,
            )
            and smart_alert_reasons
        ):

            reason_lines = []

            for reason in smart_alert_reasons[:6]:

                reason = clean_display_text(
                    reason
                )

                if reason:
                    reason_lines.append(
                        "• "
                        + html.escape(
                            str(reason)
                        )
                    )

            if reason_lines:

                smart_alert_text = (
                    "🚨 <b>Why this alert?</b>\n"
                    + "\n".join(
                        reason_lines
                    )
                )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    if description:

        description_text = (
            "📝 "
            + html.escape(
                description
            )
        )

    else:

        description_text = (
            "📝 No description available."
        )

    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    source_text = clean_display_text(
        data.get(
            "source",
            "",
        )
    )

    if source_text:

        source_section = (
            "📡 <b>Source:</b> "
            + html.escape(
                source_text
            )
        )

    else:

        source_section = ""

    # --------------------------------------------------------
    # FINAL CARD
    # --------------------------------------------------------

    message_parts = [

        (
            f"{emoji} <b>"
            f"{html.escape(name)}"
            f"</b>"
        ),

        "",

        (
            "🏷️ <b>Type:</b> "
            f"{emoji} "
            f"{html.escape(airdrop_type)}"
        ),

        (
            "🎯 <b>Score:</b> "
            f"{score}/100"
        ),

        (
            "🛡️ <b>Confidence:</b> "
            f"{confidence}"
        ),

        (
            "🔎 <b>Verification:</b> "
            f"{html.escape(verification_level)}"
        ),

        (
            "🛡️ <b>Risk:</b> "
            f"{risk_text}"
        ),

        (
            "📅 <b>Start Date:</b> "
            + html.escape(
                str(lifecycle_start)
                if lifecycle_start
                else "Unknown"
            )
        ),

        (
            "⏳ <b>End Date:</b> "
            + html.escape(
                str(lifecycle_end)
                if lifecycle_end
                else "Unknown"
            )
        ),

        (
            "🔄 <b>Lifecycle:</b> "
            f"{lifecycle_status_text}"
        ),

        "",

        description_text,

        "",
    ]

    if market_text:
        message_parts.append(
            market_text
        )

    if defi_text:
        message_parts.append(
            defi_text
        )

    if cross_source_text:
        message_parts.append(
            cross_source_text
        )

    message_parts.extend(
        [
            "",
            warning_text,
        ]
    )

    if risk_signal_text:

        message_parts.extend(
            [
                "",
                risk_signal_text,
            ]
        )

    if risk_summary_text:

        message_parts.extend(
            [
                "",
                risk_summary_text,
            ]
        )

    if smart_alert_text:

        message_parts.extend(
            [
                "",
                smart_alert_text,
            ]
        )

    if source_section:

        message_parts.extend(
            [
                "",
                source_section,
            ]
        )

    if url:

        safe_url = html.escape(
            url,
            quote=True,
        )

        message_parts.extend(
            [
                "",
                (
                    f'<a href="{safe_url}">'
                    "🌐 Open Opportunity"
                    "</a>"
                ),
            ]
        )

    message_parts.extend(
        [
            "",
            (
                "⚠️ <i>AirdropRadar does not "
                "guarantee legitimacy, eligibility, "
                "or payment. Always verify through "
                "official project channels.</i>"
            ),
        ]
    )

    return "\n".join(
        message_parts
    )



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

    if score_difference > 0:

        score_text = (
            "📈 <b>Score:</b> "
            f"{old_score_value} → "
            f"{new_score_value} "
            f"(+{score_difference})"
        )

    elif score_difference < 0:

        score_text = (
            "📉 <b>Score:</b> "
            f"{old_score_value} → "
            f"{new_score_value} "
            f"({score_difference})"
        )

    else:

        score_text = (
            "🎯 <b>Score:</b> "
            f"{new_score_value}/100"
        )

    old_confidence_text = format_confidence(
        old_confidence
    )

    new_confidence_text = format_confidence(
        new_confidence
    )

    if old_confidence != new_confidence:

        confidence_text = (
            "🧠 <b>Confidence:</b> "
            f"{old_confidence_text} → "
            f"{new_confidence_text}"
        )

    else:

        confidence_text = (
            "🧠 <b>Confidence:</b> "
            f"{new_confidence_text}"
        )

    if isinstance(
        change_summary,
        (list, tuple),
    ):

        summary_text = "\n".join(
            "• "
            + html.escape(
                str(item)
            )
            for item in change_summary
        )

    else:

        summary_text = html.escape(
            str(
                change_summary
                or "A meaningful change was detected."
            )
        )

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

async def setup_bot(application):

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
    update,
    context,
):

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

    keyboard.append(
        [
            InlineKeyboardButton(
                "📡 My Radar",
                callback_data="airdrop:my_radar",
            )
        ]
    )

    ending_soon = get_ending_soon_airdrops()

    keyboard.append(
        [
            InlineKeyboardButton(
                f"⏳ Ending Soon ({len(ending_soon)})",
                callback_data="airdrop:ending_soon",
            )
        ]
    )


    keyboard.append(
        [
            InlineKeyboardButton(
               "🔔 Alert Controls",
                callback_data="airdrop:alerts",
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
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )


# ============================================================
# CATEGORY LIST
# ============================================================

async def show_airdrop_category(
    query,
    airdrop_type,
    page=1,
):

    emoji = get_airdrop_type_emoji(
        airdrop_type
    )

    per_page = 10

    all_airdrops = get_airdrops_by_type(
        airdrop_type,
        1000,
    )

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

    total_airdrops = len(
        all_airdrops
    )

    total_pages = (
        total_airdrops
        + per_page
        - 1
    ) // per_page

    page = max(
        1,
        min(
            page,
            total_pages,
        ),
    )

    start_index = (
        (page - 1)
        * per_page
    )

    end_index = (
        start_index
        + per_page
    )

    airdrops = all_airdrops[
        start_index:end_index
    ]

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
            f" • {score}"
            f" • {confidence}"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    button_text,
                    callback_data=(
                        "airdrop:view:"
                        f"{airdrop_id}:"
                        f"{airdrop_type}"
                    ),
                )
            ]
        )

    pagination_row = []

    if page > 1:

        pagination_row.append(
            InlineKeyboardButton(
                "◀️ Previous",
                callback_data=(
                    "airdrop:page:"
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
                    "airdrop:page:"
                    f"{airdrop_type}:"
                    f"{page + 1}"
                ),
            )
        )

    keyboard.append(
        pagination_row
    )

    keyboard.append(
        [
            InlineKeyboardButton(
                "⬅️ Back to categories",
                callback_data="airdrop:menu",
            )
        ]
    )

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


def get_ending_soon_airdrops(limit=1000):

    airdrops = get_airdrops_for_lifecycle(limit)

    ending_soon = []

    for airdrop in airdrops:

        data = extract_airdrop_record(
            airdrop
        )

        lifecycle = analyze_lifecycle(
            data
        )

        if lifecycle.get(
            "status"
        ) == "ending_soon":

            ending_soon.append(
                (
                    data,
                    lifecycle
                )
            )

    return ending_soon


# ============================================================
# ALL AIRDROPS
# ============================================================

async def show_all_airdrops(query):

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

        airdrop_type = (
            data.get(
                "airdrop_type",
                "Other",
            )
            or "Other"
        )

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
                        "airdrop:view:"
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


async def show_ending_soon_airdrops(query):

    ending_soon = get_ending_soon_airdrops()

    if not ending_soon:

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
                "⏳ <b>Ending Soon</b>\n\n"
                "📭 No airdrops are ending soon."
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return

    keyboard = []

    for data, lifecycle in ending_soon[:10]:

        airdrop_id = data["id"]

        name = clean_display_text(
            data.get("name", "Unknown Airdrop")
        )

        score = safe_score(
            data.get("score", 0)
        )

        emoji = get_airdrop_type_emoji(
            data.get("airdrop_type", "Other")
        )

        end_date = lifecycle.get(
            "end_date"
        )
        
        if end_date:
            try:
                parsed_end_date = datetime.strptime(
                    str(end_date),
                    "%Y-%m-%d",
                )
                end_date_text = parsed_end_date.strftime(
                    "%b %d"
                ).replace(" 0", " ")
            except ValueError:
                end_date_text = str(end_date)
        else:
            end_date_text = "Unknown"

        button_text = (
            f"⏳ {name[:30]} • "
            f"Ends {end_date_text}"
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    button_text,
                    callback_data=(
                        "airdrop:view:"
                        f"{airdrop_id}:"
                        f"{data.get('airdrop_type', 'Other')}"
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
            "⏳ <b>Ending Soon</b>\n\n"
            "These opportunities are approaching "
            "their detected end date.\n\n"
            "🟠 Ending within 3 days."
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )

async def show_alert_controls(query):

    chat_id = query.message.chat_id

    preferences = get_alert_preferences(chat_id)

    def status(enabled):
        return "🟢 ON" if enabled else "🔴 OFF"

    keyboard = [
        [
            InlineKeyboardButton(
                f"📊 New Opportunity Alerts {status(preferences['new_opportunity'])}",
                callback_data="alert:toggle:new_opportunity",
            )
        ],
        [
            InlineKeyboardButton(
                f"📈 Monitoring/Change Alerts {status(preferences['monitoring_changes'])}",
                callback_data="alert:toggle:monitoring_changes",
            )
        ],
        [
            InlineKeyboardButton(
                f"⏳ Ending Soon Alerts {status(preferences['ending_soon'])}",
                callback_data="alert:toggle:ending_soon",
            )
        ],
        [
            InlineKeyboardButton(
                f"🛡️ Risk Alerts {status(preferences['risk_alerts'])}",
                callback_data="alert:toggle:risk_alerts",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back to categories",
                callback_data="airdrop:menu",
            )
        ],
    ]

    await query.edit_message_text(
        (
            "🔔 <b>Alert Controls</b>\n\n"
            "Choose which alerts you want to receive.\n\n"
            "🟢 ON = alerts enabled\n"
            "🔴 OFF = alerts disabled"
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_my_radar(query):

    chat_id = query.message.chat_id

    tracked = get_tracked_airdrops(
        chat_id
    )

    if not tracked:

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
                "📡 <b>My Radar</b>\n\n"
                "📭 You are not tracking any "
                "airdrops yet.\n\n"
                "Open an airdrop and tap "
                "🔖 Track to add it here."
            ),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
        )

        return

    keyboard = []

    for airdrop in tracked[:10]:

        airdrop_id = airdrop[0]

        name = clean_display_text(
            airdrop[1]
        )

        airdrop_type = (
            airdrop[5]
            or "Other"
        )

        score = safe_score(
            airdrop[6]
        )

        emoji = get_airdrop_type_emoji(
            airdrop_type
        )

        confidence = format_confidence(
            airdrop[7]
        )

        display_name = (
            name[:32] + "..."
            if len(name) > 35
            else name
        )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"📡 {display_name} • "
                    f"{score} • {confidence}",
                    callback_data=(
                        "airdrop:view:"
                        f"{airdrop_id}:"
                        f"{airdrop_type}"
                    )
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
            "📡 <b>My Radar</b>\n\n"
            "🔖 You are tracking "
            f"<b>{len(tracked)}</b> "
            "opportunit"
            + ("y" if len(tracked) == 1 else "ies")
            + ".\n\n"
            "Tap an opportunity to view its "
            "latest analysis."
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
    )

    
# ============================================================
# OPPORTUNITY DETAILS
# ============================================================
def build_detail_keyboard(
    airdrop_id,
    display_type,
    chat_id=None,
):

    airdrop = get_airdrop_by_id(
        airdrop_id
    )

    official_url = None
    participate_url = None

    if airdrop:

        participate_url = airdrop[2]

        official_links = safe_json(
            airdrop[9]
        )

        if official_links:

            if isinstance(
                official_links,
                list
            ):

                for link in official_links:

                    if isinstance(
                        link,
                        str
                    ):

                        official_url = link
                        break

                    if isinstance(
                        link,
                        dict
                    ):

                        candidate = link.get(
                            "url"
                        )

                        if candidate:
                            official_url = candidate
                            break

    tracked = False

    if chat_id is not None:

        tracked = is_airdrop_tracked(
            chat_id,
            airdrop_id,
        )

    if tracked:

        tracking_button = InlineKeyboardButton(
            "✅ Tracked • Untrack",
            callback_data=(
                f"airdrop:untrack:{airdrop_id}"
            ),
        )

    else:

        tracking_button = InlineKeyboardButton(
            "🔖 Track",
            callback_data=(
                f"airdrop:track:{airdrop_id}"
            ),
        )

    action_buttons = []

    if official_url:

        action_buttons.append(
            InlineKeyboardButton(
                "🌐 Official",
                url=official_url,
            )
        )

    if participate_url:

        action_buttons.append(
            InlineKeyboardButton(
                "🎯 Participate",
                url=participate_url,
            )
        )

    keyboard = [

        [
            InlineKeyboardButton(
                "📊 Overview",
                callback_data=(
                    f"airdrop:overview:{airdrop_id}"
                ),
            )
        ],

        [
            InlineKeyboardButton(
                "🧩 Tasks",
                callback_data=(
                    f"airdrop:tasks:{airdrop_id}"
                ),
            ),

            InlineKeyboardButton(
                "🔎 Evidence",
                callback_data=(
                    f"airdrop:evidence:{airdrop_id}"
                ),
            ),
        ],

        [
            InlineKeyboardButton(
                "🛡️ Risk",
                callback_data=(
                    f"airdrop:risk:{airdrop_id}"
                ),
            ),

            InlineKeyboardButton(
                "📈 Score",
                callback_data=(
                    f"airdrop:score:{airdrop_id}"
                ),
            ),
        ],
    ]

    if action_buttons:

        keyboard.append(
            action_buttons
        )

    keyboard.extend(
        [

            [
                tracking_button
            ],

            [
                InlineKeyboardButton(
                    "↩️ Back",
                    callback_data=(
                        f"airdrop:type:{display_type}"
                    ),
                ),

                InlineKeyboardButton(
                    "🗂️ Categories",
                    callback_data="airdrop:menu",
                ),
            ],

        ]
    )

    return InlineKeyboardMarkup(
        keyboard
    )


async def show_airdrop_details(
    query,
    airdrop_id,
    category=None,
):

    try:
        airdrop_id = int(airdrop_id)

    except (TypeError, ValueError):

        await query.answer(
            "Invalid opportunity.",
            show_alert=True,
        )

        return

    airdrop = get_airdrop_by_id(
        airdrop_id
    )

    if not airdrop:

        await query.answer(
            "Opportunity no longer exists.",
            show_alert=True,
        )

        return

    data = extract_airdrop_record(
        airdrop
    )

    display_type = (
        category
        or data.get(
            "airdrop_type",
            "Other",
        )
        or "Other"
    )

    message = format_airdrop(
        airdrop,
        display_type=display_type,
    )

    await query.edit_message_text(
        message,
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=build_detail_keyboard(
            airdrop_id,
            display_type,
            query.message.chat_id,
        ),
    )


# ============================================================
# V1.1 — TASKS VIEW
# ============================================================

async def show_airdrop_tasks(
    query,
    airdrop_id,
):

    try:
        airdrop_id = int(airdrop_id)
    except (TypeError, ValueError):
        await query.answer(
            "Invalid opportunity.",
            show_alert=True,
        )
        return

    airdrop = get_airdrop_by_id(
        airdrop_id
    )

    if not airdrop:
        await query.answer(
            "Opportunity no longer exists.",
            show_alert=True,
        )
        return

    data = extract_airdrop_record(
        airdrop
    )

    try:
        participation = analyze_participation(
            data
        )
    except Exception as error:
        print(
            f"⚠️ Participation analysis error: {error}"
        )
        participation = {}

    tasks_data = (
        participation.get(
            "tasks",
            {},
        )
        if isinstance(
            participation,
            dict,
        )
        else {}
    )

    requirements_data = (
        participation.get(
            "requirements",
            {},
        )
        if isinstance(
            participation,
            dict,
        )
        else {}
    )

    tasks = tasks_data.get(
        "items",
        [],
    )

    requirements = requirements_data.get(
        "items",
        [],
    )

    estimated_time = participation.get(
        "estimated_time",
        {},
    )

    estimated_cost = participation.get(
        "estimated_cost",
        {},
    )

    difficulty = participation.get(
        "difficulty",
        {},
    )

    lines = [
        "🧩 <b>Tasks & Participation</b>",
        "",
        (
            "🪂 <b>"
            + html.escape(
                clean_display_text(
                    data.get(
                        "name",
                        "",
                    )
                )
            )
            + "</b>"
        ),
        "",
    ]

    if tasks:

        lines.append(
            "📋 <b>Tasks</b>"
        )

        for task in tasks[:10]:

            if isinstance(task, dict):

                task_text = (
                    task.get("task")
                    or task.get("name")
                    or task.get("description")
                    or task.get("value")
                    or ""
                )

            else:

                task_text = task

            task_text = clean_display_text(
                task_text
            )

            if task_text:
                lines.append(
                    "• "
                    + html.escape(
                        task_text
                    )
                )

    else:

        lines.append(
            "📋 <b>Tasks:</b> "
            "No specific tasks confidently detected."
        )

    lines.append("")

    if requirements:

        lines.append(
            "📋 <b>Requirements</b>"
        )

        for requirement in requirements[:10]:

            if isinstance(
                requirement,
                dict,
            ):

                requirement_text = (
                    requirement.get("requirement")
                    or requirement.get("name")
                    or requirement.get("description")
                    or requirement.get("value")
                    or ""
                )

            else:

                requirement_text = requirement

            requirement_text = clean_display_text(
                requirement_text
            )

            if requirement_text:
                lines.append(
                    "• "
                    + html.escape(
                        requirement_text
                    )
                )

    else:

        lines.append(
            "📋 <b>Requirements:</b> "
            "No specific requirements confidently detected."
        )

    lines.append("")

    time_value = (
        estimated_time.get(
            "value",
            "Unknown",
        )
        if isinstance(
            estimated_time,
            dict,
        )
        else "Unknown"
    )

    cost_value = (
        estimated_cost.get(
            "value",
            "Unknown",
        )
        if isinstance(
            estimated_cost,
            dict,
        )
        else "Unknown"
    )

    difficulty_value = (
        difficulty.get(
            "value",
            "Unknown",
        )
        if isinstance(
            difficulty,
            dict,
        )
        else "Unknown"
    )

    lines.extend(
        [
            "⏱️ <b>Estimated Time:</b> "
            + html.escape(
                str(time_value)
            ),
            "💰 <b>Estimated Cost:</b> "
            + html.escape(
                str(cost_value)
            ),
            "🎚️ <b>Difficulty:</b> "
            + html.escape(
                str(difficulty_value)
            ),
        ]
    )

    lines.extend(
        [
            "",
            "⚠️ Estimates are intelligence signals, "
            "not guarantees.",
        ]
    )

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📊 Overview",
                        callback_data=(
                            f"airdrop:overview:{airdrop_id}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔎 Evidence",
                        callback_data=(
                            f"airdrop:evidence:{airdrop_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        "🛡️ Risk",
                        callback_data=(
                            f"airdrop:risk:{airdrop_id}"
                        ),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "📈 Score",
                        callback_data=(
                            f"airdrop:score:{airdrop_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        "↩️ Back",
                        callback_data=(
                            f"airdrop:view:{airdrop_id}:"
                            f"{data.get('airdrop_type', 'Other')}"
                        ),
                    ),
                ],
            ]
        ),
    )


# ============================================================
# V1.1 — EVIDENCE VIEW
# ============================================================

async def show_airdrop_evidence(
    query,
    airdrop_id,
):

    try:
        airdrop_id = int(airdrop_id)
    except (TypeError, ValueError):
        await query.answer(
            "Invalid opportunity.",
            show_alert=True,
        )
        return

    airdrop = get_airdrop_by_id(
        airdrop_id
    )

    if not airdrop:
        await query.answer(
            "Opportunity no longer exists.",
            show_alert=True,
        )
        return

    data = extract_airdrop_record(
        airdrop
    )

    lines = [
        "🔎 <b>Evidence & Verification</b>",
        "",
        (
            "🪂 <b>"
            + html.escape(
                clean_display_text(
                    data.get(
                        "name",
                        "",
                    )
                )
            )
            + "</b>"
        ),
        "",
        (
            "🔎 <b>Verification:</b> "
            + html.escape(
                clean_display_text(
                    data.get(
                        "verification_level",
                        "",
                    )
                )
                or "Unknown"
            )
        ),
        (
            "📡 <b>Discovery Source:</b> "
            + html.escape(
                clean_display_text(
                    data.get(
                        "source",
                        "",
                    )
                )
                or "Unknown"
            )
        ),
    ]

    official_links = safe_json(
        data.get(
            "official_links",
            [],
        )
    )

    if official_links:

        lines.extend(
            [
                "",
                "🌐 <b>Official Links</b>",
            ]
        )

        for link in official_links[:8]:

            if isinstance(
                link,
                dict,
            ):

                link_value = (
                    link.get("url")
                    or link.get("link")
                    or ""
                )

            else:

                link_value = link

            link_value = str(
                link_value or ""
            ).strip()

            if link_value:

                safe_link = html.escape(
                    link_value,
                    quote=True,
                )

                lines.append(
                    f'• <a href="{safe_link}">'
                    f"{html.escape(link_value[:80])}"
                    "</a>"
                )

    else:

        lines.extend(
            [
                "",
                "🌐 <b>Official Links:</b> "
                "None detected.",
            ]
        )

    matched_sources = safe_json(
        data.get(
            "matched_sources",
            [],
        )
    )

    cross_matches = safe_json(
        data.get(
            "cross_source_matches",
            [],
        )
    )

    if matched_sources:

        lines.extend(
            [
                "",
                "🔗 <b>Additional Sources</b>",
            ]
        )

        for source in matched_sources[:8]:

            source_text = clean_display_text(
                source
            )

            if source_text:
                lines.append(
                    "• "
                    + html.escape(
                        source_text
                    )
                )

    elif cross_matches:

        lines.extend(
            [
                "",
                "🔗 <b>Cross-Source Evidence</b>",
            ]
        )

        for match in cross_matches[:8]:

            if isinstance(
                match,
                dict,
            ):

                source = (
                    match.get("source")
                    or ""
                )

                status = (
                    match.get("match_status")
                    or ""
                )

                score = (
                    match.get("match_score")
                    or ""
                )

                text = (
                    f"{source} "
                    f"({status}, {score})"
                )

            else:

                text = str(match)

            lines.append(
                "• "
                + html.escape(
                    clean_display_text(text)
                )
            )

    description = clean_display_text(
        data.get(
            "description",
            "",
        )
    )

    if description:

        lines.extend(
            [
                "",
                "📝 <b>Source Description</b>",
                html.escape(
                    description[:1200]
                ),
            ]
        )

    lines.extend(
        [
            "",
            "⚠️ Evidence indicates what AirdropRadar "
            "could verify or detect; it does not "
            "guarantee legitimacy.",
        ]
    )

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📊 Overview",
                        callback_data=(
                            f"airdrop:overview:{airdrop_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        "🧩 Tasks",
                        callback_data=(
                            f"airdrop:tasks:{airdrop_id}"
                        ),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🛡️ Risk",
                        callback_data=(
                            f"airdrop:risk:{airdrop_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        "📈 Score",
                        callback_data=(
                            f"airdrop:score:{airdrop_id}"
                        ),
                    ),
                ],
            ]
        ),
    )


# ============================================================
# V1.1 — RISK VIEW
# ============================================================

async def show_airdrop_risk(
    query,
    airdrop_id,
):

    try:
        airdrop_id = int(airdrop_id)
    except (TypeError, ValueError):
        await query.answer(
            "Invalid opportunity.",
            show_alert=True,
        )
        return

    airdrop = get_airdrop_by_id(
        airdrop_id
    )

    if not airdrop:
        await query.answer(
            "Opportunity no longer exists.",
            show_alert=True,
        )
        return

    data = extract_airdrop_record(
        airdrop
    )

    risk_level = clean_display_text(
        data.get(
            "intelligence_risk_level",
            "",
        )
    ).lower()

    if risk_level == "critical":
        risk_display = "🔴 Critical"
    elif risk_level == "high":
        risk_display = "🔴 High"
    elif risk_level == "medium":
        risk_display = "🟠 Medium"
    elif risk_level == "low":
        risk_display = "🟢 Low"
    else:
        risk_display = "⚪ Unknown"

    lines = [
        "🛡️ <b>Risk Intelligence</b>",
        "",
        (
            "🪂 <b>"
            + html.escape(
                clean_display_text(
                    data.get(
                        "name",
                        "",
                    )
                )
            )
            + "</b>"
        ),
        "",
        (
            "🛡️ <b>Risk Level:</b> "
            + risk_display
        ),
    ]

    risk_summary = clean_display_text(
        data.get(
            "risk_summary",
            "",
        )
    )

    if risk_summary:

        lines.extend(
            [
                "",
                "🧠 <b>Analysis</b>",
                html.escape(
                    risk_summary
                ),
            ]
        )

    risk_signals = safe_json(
        data.get(
            "risk_signals",
            [],
        )
    )

    if risk_signals:

        lines.extend(
            [
                "",
                "🚨 <b>Risk Signals</b>",
            ]
        )

        shown = 0

        for signal in risk_signals[:10]:

            if isinstance(
                signal,
                dict,
            ):

                category = clean_display_text(
                    signal.get(
                        "category",
                        "",
                    )
                )

                value = clean_display_text(
                    signal.get(
                        "value",
                        "",
                    )
                )

                severity = clean_display_text(
                    signal.get(
                        "severity",
                        "",
                    )
                )

                evidence = clean_display_text(
                    signal.get(
                        "evidence",
                        "",
                    )
                )

                text_parts = []

                if category:
                    text_parts.append(
                        category
                    )

                if value:
                    text_parts.append(
                        value
                    )

                text = ": ".join(
                    text_parts
                )

                if severity:
                    text += (
                        f" [{severity}]"
                    )

                if evidence and evidence not in {
                    "unavailable",
                    "unknown",
                    "project_domains=[]",
                    "official_links=[]",
                }:
                    text += (
                        f"\n  Evidence: {evidence}"
                    )

            else:

                text = clean_display_text(
                    signal
                )

            if not text:
                continue

            lines.append(
                "• "
                + html.escape(
                    text
                )
            )

            shown += 1

            if shown >= 7:
                break

    else:

        lines.extend(
            [
                "",
                "✅ No specific risk signals "
                "were stored for this opportunity.",
            ]
        )

    lines.extend(
        [
            "",
            "⚠️ Risk intelligence is evidence-based "
            "and is not a definitive scam verdict.",
        ]
    )

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📊 Overview",
                        callback_data=(
                            f"airdrop:overview:{airdrop_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        "🧩 Tasks",
                        callback_data=(
                            f"airdrop:tasks:{airdrop_id}"
                        ),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔎 Evidence",
                        callback_data=(
                            f"airdrop:evidence:{airdrop_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        "📈 Score",
                        callback_data=(
                            f"airdrop:score:{airdrop_id}"
                        ),
                    ),
                ],
            ]
        ),
    )


# ============================================================
# V1.1 — SCORE VIEW
# ============================================================

async def show_airdrop_score(
    query,
    airdrop_id,
):

    try:
        airdrop_id = int(airdrop_id)
    except (TypeError, ValueError):
        await query.answer(
            "Invalid opportunity.",
            show_alert=True,
        )
        return

    airdrop = get_airdrop_by_id(
        airdrop_id
    )

    if not airdrop:
        await query.answer(
            "Opportunity no longer exists.",
            show_alert=True,
        )
        return

    data = extract_airdrop_record(
        airdrop
    )

    score = safe_score(
        data.get(
            "score",
            0,
        )
    )

    confidence = format_confidence(
        data.get(
            "confidence",
            "",
        )
    )

    verification = clean_display_text(
        data.get(
            "verification_level",
            "",
        )
    ) or "Unknown"

    market = data.get(
        "market_signal",
        {},
    )

    if isinstance(
        market,
        str,
    ):
        market = safe_json(
            market
        )

    defi = data.get(
        "defi_signal",
        {},
    )

    if isinstance(
        defi,
        str,
    ):
        defi = safe_json(
            defi
        )

    market_found = (
        isinstance(market, dict)
        and bool(
            market.get(
                "found",
                market.get(
                    "available",
                    False,
                ),
            )
        )
    )

    defi_found = (
        isinstance(defi, dict)
        and bool(
            defi.get(
                "found",
                defi.get(
                    "available",
                    False,
                ),
            )
        )
    )

    if score >= 80:
        score_band = "🔥 Strong"
    elif score >= ALERT_THRESHOLD:
        score_band = "🟢 Alert-level"
    elif score >= 50:
        score_band = "🟡 Moderate"
    else:
        score_band = "⚪ Low"

    lines = [
        "📈 <b>Score Intelligence</b>",
        "",
        (
            "🪂 <b>"
            + html.escape(
                clean_display_text(
                    data.get(
                        "name",
                        "",
                    )
                )
            )
            + "</b>"
        ),
        "",
        (
            "🎯 <b>Score:</b> "
            f"{score}/100"
        ),
        (
            "📊 <b>Score Band:</b> "
            + score_band
        ),
        (
            "🧠 <b>Confidence:</b> "
            + confidence
        ),
        (
            "🔎 <b>Verification:</b> "
            + html.escape(
                verification
            )
        ),
        "",
        (
            "🪙 <b>Market Signal:</b> "
            + (
                "🟢 Detected"
                if market_found
                else "⚪ Not detected"
            )
        ),
        (
            "🧩 <b>DeFi Signal:</b> "
            + (
                "🟢 Detected"
                if defi_found
                else "⚪ Not detected"
            )
        ),
    ]

    risk_level = clean_display_text(
        data.get(
            "intelligence_risk_level",
            "",
        )
    ).lower()

    if risk_level:

        lines.extend(
            [
                "",
                (
                    "🛡️ <b>Risk Factor:</b> "
                    + html.escape(
                        risk_level.title()
                    )
                ),
            ]
        )

    lines.extend(
        [
            "",
            "ℹ️ The score combines AirdropRadar's "
            "available verification, market, DeFi, "
            "warning, evidence and risk signals.",
        ]
    )

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📊 Overview",
                        callback_data=(
                            f"airdrop:overview:{airdrop_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        "🧩 Tasks",
                        callback_data=(
                            f"airdrop:tasks:{airdrop_id}"
                        ),
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "🔎 Evidence",
                        callback_data=(
                            f"airdrop:evidence:{airdrop_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        "🛡️ Risk",
                        callback_data=(
                            f"airdrop:risk:{airdrop_id}"
                        ),
                    ),
                ],
            ]
        ),
    )


# ============================================================
# AIRDROP CALLBACK HANDLER
# ============================================================

async def airdrop_callback(
    update,
    context,
):

    query = update.callback_query

    data = query.data or ""

    # Answer exactly once for normal callbacks.
    await query.answer()

    # --------------------------------------------------------
    # CATEGORY MENU
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

        keyboard.append(
            [
                InlineKeyboardButton(
                    "📡 My Radar",
                    callback_data="airdrop:my_radar",
                ),
                InlineKeyboardButton(
                    "🔔 Alert Controls",
                    callback_data="airdrop:alerts",
                ),
            ]
        )

        ending_soon = get_ending_soon_airdrops()

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"⏳ Ending Soon ({len(ending_soon)})",
                    callback_data="airdrop:ending_soon",
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

        message = (
            "🪂 <b>AirdropRadar</b>\n\n"
            "🔎 <b>Browse Airdrops</b>\n"
            "Explore verified opportunities by category "
            "or view all available opportunities.\n\n"
            "📊 Each opportunity includes its latest "
            "score and confidence level.\n\n"
            "Choose an option below:"
        )

        await query.edit_message_text(
            message,
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
    if data == "airdrop:ending_soon":

         await show_ending_soon_airdrops(
             query
        )

         return


    if data == "airdrop:my_radar":

        await show_my_radar(
            query
        )

        return

    if data == "airdrop:alerts":

        await show_alert_controls(
            query
        )

        return

    # --------------------------------------------------------
    # ALERT TOGGLES
    # --------------------------------------------------------

    if data.startswith("alert:toggle:"):

        preference = data.split(
            ":",
            2,
        )[2]

        preferences = get_alert_preferences(
            query.message.chat_id
        )

        current = preferences.get(
            preference,
            True,
        )

        set_alert_preference(
            query.message.chat_id,
            preference,
            not current,
        )

        await show_alert_controls(
            query
        )

        return

    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:type:"
    ):

        # IMPORTANT:
        # [:] keeps the complete category name.
        airdrop_type = data[
            len("airdrop:type:"):
        :]

        await show_airdrop_category(
            query,
            airdrop_type,
        )

        return

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:page:"
    ):

        # IMPORTANT:
        # [:] keeps the entire suffix.
        page_data = data[
            len("airdrop:page:"):
        :]

        parts = page_data.rsplit(
            ":",
            1,
        )

        if len(parts) != 2:

            await query.edit_message_text(
                "❌ Invalid page.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Back",
                                callback_data="airdrop:menu",
                            )
                        ]
                    ]
                ),
            )

            return

        airdrop_type = parts[0]

        try:
            page = int(parts[1])
        except ValueError:

            await query.edit_message_text(
                "❌ Invalid page.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Back",
                                callback_data="airdrop:menu",
                            )
                        ]
                    ]
                ),
            )

            return

        await show_airdrop_category(
            query,
            airdrop_type,
            page,
        )

        return

    # --------------------------------------------------------
    # PAGE INDICATOR
    # --------------------------------------------------------

    if data == "airdrop:noop":
        return



        # --------------------------------------------------------
    # TRACK
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:track:"
    ):

        airdrop_id = data[
            len("airdrop:track:"):
        :]

        try:
            airdrop_id = int(
                airdrop_id
            )
        except ValueError:
            return

        airdrop = get_airdrop_by_id(
            airdrop_id
        )

        if not airdrop:
            return

        chat_id = query.message.chat_id

        track_airdrop(
            chat_id,
            airdrop_id,
        )

        await show_airdrop_details(
            query,
            airdrop_id,
        )

        return

    # --------------------------------------------------------
    # UNTRACK
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:untrack:"
    ):

        airdrop_id = data[
            len("airdrop:untrack:"):
        :]

        try:
            airdrop_id = int(
                airdrop_id
            )
        except ValueError:
            return

        airdrop = get_airdrop_by_id(
            airdrop_id
        )

        if not airdrop:
            return

        chat_id = query.message.chat_id

        untrack_airdrop(
            chat_id,
            airdrop_id,
        )

        await show_airdrop_details(
            query,
            airdrop_id,
        )

        return

    # --------------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:overview:"
    ):

        airdrop_id = data[
            len("airdrop:overview:"):
        :]

        await show_airdrop_details(
            query,
            airdrop_id,
        )

        return

    # --------------------------------------------------------
    # TASKS
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:tasks:"
    ):

        airdrop_id = data[
            len("airdrop:tasks:"):
        :]

        await show_airdrop_tasks(
            query,
            airdrop_id,
        )

        return

    # --------------------------------------------------------
    # EVIDENCE
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:evidence:"
    ):

        airdrop_id = data[
            len("airdrop:evidence:"):
        :]

        await show_airdrop_evidence(
            query,
            airdrop_id,
        )

        return

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:risk:"
    ):

        airdrop_id = data[
            len("airdrop:risk:"):
        :]

        await show_airdrop_risk(
            query,
            airdrop_id,
        )

        return

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:score:"
    ):

        airdrop_id = data[
            len("airdrop:score:"):
        :]

        await show_airdrop_score(
            query,
            airdrop_id,
        )

        return

    # --------------------------------------------------------
    # AIRDROP DETAILS
    # --------------------------------------------------------

    if data.startswith(
        "airdrop:view:"
    ):

        view_data = data[
            len("airdrop:view:"):
        :]

        parts = view_data.split(
            ":",
            1,
        )

        airdrop_id = parts[0]

        category = (
            parts[1]
            if len(parts) > 1
            else None
        )

        await show_airdrop_details(
            query,
            airdrop_id,
            category,
        )

        return

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    await query.edit_message_text(
        "❌ Unknown action.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🗂️ Categories",
                        callback_data="airdrop:menu",
                    )
                ]
            ]
        ),
    )


# ============================================================
# /START
# ============================================================

async def start(
    update,
    context,
):

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
                    "📡 My Radar",
                    callback_data="airdrop:my_radar",
                ),
                InlineKeyboardButton(
                    "🔔 Alert Controls",
                    callback_data="airdrop:alerts",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⏳ Ending Soon",
                    callback_data="airdrop:ending_soon",
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
        "🚀 <b>Welcome to AirdropRadar V1!</b>\n\n"
        "Discover, verify, understand, and track "
        "airdrop opportunities from one place.\n\n"
        "🪂 Browse opportunities\n"
        "📡 Track opportunities with My Radar\n"
        "⏳ Find opportunities ending soon\n"
        "🔔 Control the alerts you receive\n\n"
        "Choose an option below to get started."
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
    update,
    context,
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
    update,
    context,
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
    update,
    context,
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
    update,
    context,
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

                airdrop_id = airdrop[0]
                airdrop_type = (
                    airdrop[19]
                    or "Other"
                )

                keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📊 Overview",
                                callback_data=(
                                    "airdrop:view:"
                                    f"{airdrop_id}:"
                                    f"{airdrop_type}"
                                ),
                            )
                        ]
                    ]
                )

                await update.message.reply_text(
                    message,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                    reply_markup=keyboard,
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
    update,
    context,
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
# SMART ALERT INTELLIGENCE
# ============================================================

def get_smart_alert_reasons(result):

    if not isinstance(
        result,
        dict,
    ):
        return []

    reasons = []

    score = safe_score(
        result.get(
            "score",
            0,
        )
    )

    if score >= 80:

        reasons.append(
            "🔥 Strong opportunity score"
        )

    elif score >= ALERT_THRESHOLD:

        reasons.append(
            "📊 Alert-level opportunity score"
        )

    lifecycle = result.get(
        "lifecycle",
        {},
    )

    if isinstance(
        lifecycle,
        dict,
    ):

        lifecycle_status = str(
            lifecycle.get(
                "status",
                "",
            )
            or ""
        ).lower()

        if lifecycle_status == "ending_soon":

            reasons.append(
                "⏳ Ending soon"
            )

        elif lifecycle_status == "upcoming":

            reasons.append(
                "🗓️ Upcoming opportunity"
            )

    risk = result.get(
        "risk_intelligence",
        {},
    )

    if isinstance(
        risk,
        dict,
    ):

        risk_level = str(
            risk.get(
                "risk_level",
                "",
            )
            or ""
        ).lower()

        try:

            signal_count = int(
                risk.get(
                    "signal_count",
                    0,
                )
                or 0
            )

        except (
            TypeError,
            ValueError,
        ):

            signal_count = 0

        if risk_level in {
            "high",
            "critical",
        }:

            reasons.append(
                "⚠️ High-risk signals detected"
            )

        elif signal_count > 0:

            reasons.append(
                "⚠️ Risk signals detected"
            )

    participation = result.get(
        "participation",
        {},
    )

    if isinstance(
        participation,
        dict,
    ):

        tasks = participation.get(
            "tasks",
            {},
        )

        requirements = participation.get(
            "requirements",
            {},
        )

        if isinstance(
            tasks,
            dict,
        ):

            task_items = tasks.get(
                "items",
                [],
            )

            if (
                isinstance(
                    task_items,
                    list,
                )
                and task_items
            ):

                reasons.append(
                    f"🧩 {len(task_items)} "
                    "task(s) identified"
                )

        if isinstance(
            requirements,
            dict,
        ):

            requirement_items = requirements.get(
                "items",
                [],
            )

            if (
                isinstance(
                    requirement_items,
                    list,
                )
                and requirement_items
            ):

                reasons.append(
                    f"📋 {len(requirement_items)} "
                    "requirement(s) identified"
                )

    score_reasons = result.get(
        "score_reasons",
        [],
    )

    if isinstance(
        score_reasons,
        list,
    ):

        if any(
            "evidence" in str(reason).lower()
            for reason in score_reasons
        ):

            reasons.append(
                "🔎 Supporting evidence detected"
            )

    return reasons


def should_send_smart_alert(result):

    if not isinstance(
        result,
        dict,
    ):
        return False

    score = safe_score(
        result.get(
            "score",
            0,
        )
    )

    if score >= ALERT_THRESHOLD:
        return True

    lifecycle = result.get(
        "lifecycle",
        {},
    )

    if isinstance(
        lifecycle,
        dict,
    ):

        lifecycle_status = str(
            lifecycle.get(
                "status",
                "",
            )
            or ""
        ).lower()

        if (
            lifecycle_status == "ending_soon"
            and score >= 60
        ):
            return True

    risk = result.get(
        "risk_intelligence",
        {},
    )

    if isinstance(
        risk,
        dict,
    ):

        risk_level = str(
            risk.get(
                "risk_level",
                "",
            )
            or ""
        ).lower()

        if (
            risk_level in {
                "high",
                "critical",
            }
            and score >= 50
        ):
            return True

    return False


# ============================================================

def get_enabled_smart_alert_reasons(
    result,
    preferences,
):

    if not isinstance(result, dict):
        return []

    if not isinstance(preferences, dict):
        preferences = {}

    reasons = []

    score = safe_score(
        result.get(
            "score",
            0,
        )
    )

    if (
        preferences.get("new_opportunity", True)
        and score >= ALERT_THRESHOLD
    ):
        reasons.append("new_opportunity")

    lifecycle = result.get(
        "lifecycle",
        {},
    )

    if isinstance(lifecycle, dict):

        lifecycle_status = str(
            lifecycle.get(
                "status",
                "",
            )
            or ""
        ).lower()

        if (
            preferences.get("ending_soon", True)
            and lifecycle_status == "ending_soon"
            and score >= 60
        ):
            reasons.append("ending_soon")

    risk = result.get(
        "risk_intelligence",
        {},
    )

    if isinstance(risk, dict):

        risk_level = str(
            risk.get(
                "risk_level",
                "",
            )
            or ""
        ).lower()

        if (
            preferences.get("risk_alerts", True)
            and risk_level in {
                "high",
                "critical",
            }
            and score >= 50
        ):
            reasons.append("risk_alerts")

    return reasons


# /CHECK
# ============================================================

async def check(
    update,
    context,
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

        alert_count = sum(
            1
            for result in results
            if should_send_smart_alert(
                result
            )
        )

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

        await query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🪂 Browse Airdrops",
                            callback_data="airdrop:menu",
                        )
                    ]
                ]
            ),
        )

        return

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

        await query.edit_message_text(
            message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🪂 Browse Airdrops",
                            callback_data="airdrop:menu",
                        )
                    ]
                ]
            ),
        )

        return


# ============================================================
# AUTOMATIC SCAN
# ============================================================

async def automatic_scan(
    context,
):

    print(
        "\n⏰ Automatic AirdropRadar scan started..."
    )

    try:

        results = await asyncio.to_thread(
            run_scan_once
        )

        if results is None:

            print(
                "⏳ Automatic scan skipped "
                "because another scan is already running."
            )

            return

        if not results:

            print(
                "📭 No new airdrops found."
            )

            return

        stored_count = store_scan_results(
            results
        )

        print(
            f"💾 Automatic scan stored: "
            f"{stored_count}"
        )

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

            if not should_send_smart_alert(
                result
            ):

                print(
                    f"⏭️ Not smart-alert worthy: "
                    f"{result.get('name', 'Unknown')} "
                    f"(score={score})"
                )

                continue

            alert_candidates += 1

            airdrop_url = str(
                result.get(
                    "url",
                    "",
                )
                or ""
            ).strip()

            if not airdrop_url:

                print(
                    f"⚠️ Skipping alert for "
                    f"{result.get('name', 'Unknown')} "
                    f"because it has no URL."
                )

                continue

            airdrop = dict(result)

            airdrop[
                "smart_alert_reasons"
            ] = get_smart_alert_reasons(
                result
            )

            message = format_airdrop(
                airdrop
            )

            for chat_id in subscribers:

                try:

                    preferences = get_alert_preferences(
                        chat_id
                    )

                    enabled_alerts = get_enabled_smart_alert_reasons(
                        result,
                        preferences,
                    )

                    if not enabled_alerts:

                        print(
                            f"🔕 Alert disabled by preferences for "
                            f"{chat_id}: "
                            f"{result.get('name', 'Unknown')}"
                        )

                        continue

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
                        f"{chat_id}: {error}"
                    )

        print(
            f"🚨 Smart-alert-worthy discoveries: "
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


## ============================================================
# AUTOMATIC MONITORING
# ============================================================

async def automatic_monitoring(
    context,
):

    print(
        "\n🔄 Automatic AirdropRadar monitoring started..."
    )

    try:

        results = await asyncio.to_thread(
            run_tracking_cycle
        )

        if not results:

            print(
                "📭 No airdrops were due for monitoring."
            )

            return

        subscribers = get_subscribers()

        if not subscribers:

            print(
                "👥 No subscribers for monitoring alerts."
            )

            return

        alerts_sent = 0
        changes_found = 0
        smart_alerts_found = 0

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

            # ------------------------------------------------
            # SMART ALERT DATA
            # ------------------------------------------------

            change_detected = result.get(
                "change_detected",
                False,
            )

            new_score = result.get(
                "new_score",
                0,
            )

            lifecycle = result.get(
                "lifecycle",
                {},
            )

            risk_intelligence = result.get(
                "risk_intelligence",
                {},
            )

            lifecycle_status = ""

            if isinstance(
                lifecycle,
                dict,
            ):
                lifecycle_status = str(
                    lifecycle.get(
                        "status",
                        "",
                    )
                ).lower()

            risk_level = ""

            if isinstance(
                risk_intelligence,
                dict,
            ):
                risk_level = str(
                    risk_intelligence.get(
                        "risk_level",
                        "",
                    )
                ).lower()

            # ------------------------------------------------
            # SMART ALERT CONDITIONS
            # ------------------------------------------------

            ending_soon_alert = (
                lifecycle_status == "ending_soon"
                and safe_score(new_score) >= 60
            )

            high_risk_alert = (
                risk_level in (
                    "high",
                    "critical",
                )
                and safe_score(new_score) >= 50
            )

            meaningful_change_alert = (
                change_detected
            )

            should_alert = (
                meaningful_change_alert
                or ending_soon_alert
                or high_risk_alert
            )

            if not should_alert:
                continue

            if meaningful_change_alert:
                changes_found += 1

            if (
                ending_soon_alert
                or high_risk_alert
            ):
                smart_alerts_found += 1

            # ------------------------------------------------
            # BASIC AIRDROP DATA
            # ------------------------------------------------

            airdrop_id = result.get(
                "airdrop_id"
            )

            if not airdrop_id:
                continue

            name = result.get(
                "name",
                "Unknown Airdrop",
            )

            url = result.get(
                "url",
                "",
            )

            # ------------------------------------------------
            # HISTORY ID
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
            # ALERT MESSAGE
            # ------------------------------------------------

            old_score = result.get(
                "old_score",
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

            smart_reasons = []

            if ending_soon_alert:

                smart_reasons.append(
                    "🟠 Ending Soon"
                )

            if high_risk_alert:

                smart_reasons.append(
                    "🔴 High/Critical Risk"
                )

            if smart_reasons:

                smart_prefix = (
                    "🧠 <b>Smart Alert</b>\n"
                    + " • ".join(smart_reasons)
                    + "\n\n"
                )

            else:

                smart_prefix = ""

            message = (
                smart_prefix
                + format_monitoring_alert(
                    name,
                    url,
                    old_score,
                    new_score,
                    old_confidence,
                    new_confidence,
                    change_summary,
                )
            )

            # ------------------------------------------------
            # SEND TO SUBSCRIBERS
            # ------------------------------------------------

            for chat_id in subscribers:

                try:

                    preferences = get_alert_preferences(
                        chat_id
                    )

                    allowed_alerts = []

                    if (
                        meaningful_change_alert
                        and preferences.get("monitoring_changes", True)
                    ):
                        allowed_alerts.append("monitoring_changes")

                    if (
                        ending_soon_alert
                        and preferences.get("ending_soon", True)
                    ):
                        allowed_alerts.append("ending_soon")

                    if (
                        high_risk_alert
                        and preferences.get("risk_alerts", True)
                    ):
                        allowed_alerts.append("risk_alerts")

                    if not allowed_alerts:

                        print(
                            f"Monitoring alert disabled by preferences for {chat_id}: {name}"
                        )

                        continue

                    chat_smart_reasons = []

                    if "ending_soon" in allowed_alerts:
                        chat_smart_reasons.append("Ending Soon")

                    if "risk_alerts" in allowed_alerts:
                        chat_smart_reasons.append("High/Critical Risk")

                    if chat_smart_reasons:

                        chat_smart_prefix = (
                            "<b>Smart Alert</b>\n"
                            + " ? ".join(chat_smart_reasons)
                            + "\n\n"
                        )

                    else:

                        chat_smart_prefix = ""

                    chat_message = (
                        chat_smart_prefix
                        + format_monitoring_alert(
                            name,
                            url,
                            old_score,
                            new_score,
                            old_confidence,
                            new_confidence,
                            change_summary,
                        )
                    )

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

                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=chat_message,
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
        # MONITORING SUMMARY
        # ----------------------------------------------------

        print(
            f"📈 Meaningful changes found: "
            f"{changes_found}"
        )

        print(
            f"🧠 Smart alerts found: "
            f"{smart_alerts_found}"
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
        

async def telegram_error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):
    error = context.error

    if isinstance(error, BadRequest):
        error_text = str(error).lower()

        if "message is not modified" in error_text:
            print(
                "ℹ️ Telegram: message already up to date."
            )
            return

    print(
        f"⚠️ Telegram update error: {error}"
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
    # AIRDROP CALLBACKS
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            airdrop_callback,
            pattern=r"^airdrop:",
        )
    )

    # --------------------------------------------------------
    # ALERT CALLBACKS
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            airdrop_callback,
            pattern=r"^alert:",
        )
    )

    # --------------------------------------------------------
    # GENERAL CALLBACKS
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            general_callback,
            pattern=r"^bot:",
        )
    )

    # --------------------------------------------------------
    # TELEGRAM ERROR HANDLER
    # --------------------------------------------------------

    application.add_error_handler(                                          
        telegram_error_handler
    )

    # --------------------------------------------------------
    # AUTOMATIC SCANNING
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

    print(
        "🪂 Airdrop category browser enabled."
    )

    print(
        "🚀 AirdropRadar is online!"
    )

    application.run_polling()


if __name__ == "__main__":
    main()


