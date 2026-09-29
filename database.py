import sqlite3
import json

from config import DATABASE_NAME


# -----------------------------------------
# AIRDROP TYPES
# -----------------------------------------

AIRDROP_TYPES = {
    "Points": "🎯",
    "Testnet": "🧪",
    "Retroactive": "🔄",
    "Bounty": "🏆",
    "Holder": "👑",
    "Liquidity": "💧",
    "Activity": "🔗",
    "Other": "📦",
}

# -----------------------------------------
# DATABASE CONNECTION
# -----------------------------------------

def get_connection():

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# -----------------------------------------
# CREATE DATABASE
# -----------------------------------------

def create_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS airdrops (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            url TEXT UNIQUE NOT NULL,

            description TEXT,

            source TEXT,

            airdrop_type TEXT DEFAULT 'Other',

            score INTEGER DEFAULT 0,

            confidence TEXT,

            verified BOOLEAN DEFAULT 0,

            verification_level TEXT,

            official_links TEXT,

            warnings TEXT,

            market_signal TEXT,

            defi_signal TEXT,

            risk_signals TEXT,

            intelligence_risk_level TEXT,

            risk_summary TEXT,

            cross_source_matches TEXT,

            matched_sources TEXT,

            cross_source_match_count INTEGER DEFAULT 0,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            last_checked_at TIMESTAMP,

            previous_score INTEGER,

            previous_confidence TEXT,

            last_change_at TIMESTAMP,

            next_check_at TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (

            chat_id INTEGER PRIMARY KEY,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alert_preferences (

            chat_id INTEGER PRIMARY KEY,

            new_opportunity BOOLEAN DEFAULT 1,

            monitoring_changes BOOLEAN DEFAULT 1,

            ending_soon BOOLEAN DEFAULT 1,

            risk_alerts BOOLEAN DEFAULT 1,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            updated_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent_alerts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            chat_id INTEGER NOT NULL,

            airdrop_url TEXT NOT NULL,

            sent_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(
                chat_id,
                airdrop_url
            )
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS airdrop_history (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            airdrop_id INTEGER NOT NULL,

            checked_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            score INTEGER,

            confidence TEXT,

            verification_level TEXT,

            official_links TEXT,

            warnings TEXT,

            market_signal TEXT,

            defi_signal TEXT,

            change_detected BOOLEAN DEFAULT 0,

            change_summary TEXT,

            FOREIGN KEY (
                airdrop_id
            )
            REFERENCES airdrops(id)
            ON DELETE CASCADE
        )
    """)

    # -------------------------------------
    # MONITORING ALERTS
    # -------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitoring_alerts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            chat_id INTEGER NOT NULL,

            airdrop_id INTEGER NOT NULL,

            history_id INTEGER NOT NULL,

            sent_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(
                chat_id,
                history_id
            ),

            FOREIGN KEY (
                airdrop_id
            )
            REFERENCES airdrops(id)
            ON DELETE CASCADE,

            FOREIGN KEY (
                history_id
            )
            REFERENCES airdrop_history(id)
            ON DELETE CASCADE
        )
    """)


        # -------------------------------------
    # PERSONAL TRACKING
    # -------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracked_airdrops (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            chat_id INTEGER NOT NULL,

            airdrop_id INTEGER NOT NULL,

            tracked_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(
                chat_id,
                airdrop_id
            ),

            FOREIGN KEY (
                airdrop_id
            )
            REFERENCES airdrops(id)
            ON DELETE CASCADE
        )
    """)


    # -------------------------------------
    # DATABASE MIGRATION
    # -------------------------------------

    cursor.execute(
        "PRAGMA table_info(airdrops)"
    )

    existing_columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    new_columns = {

        "airdrop_type": "TEXT DEFAULT 'Other'",

        "verification_level": "TEXT",

        "official_links": "TEXT",

        "warnings": "TEXT",

        "market_signal": "TEXT",

        "defi_signal": "TEXT",

        "last_checked_at": "TIMESTAMP",

        "previous_score": "INTEGER",

        "previous_confidence": "TEXT",

        "last_change_at": "TIMESTAMP",

        "next_check_at": "TIMESTAMP",

        "risk_signals": "TEXT",

        "intelligence_risk_level": "TEXT",

        "risk_summary": "TEXT",

        "cross_source_matches": "TEXT",

        "matched_sources": "TEXT",

        "cross_source_match_count": "INTEGER DEFAULT 0",
    }

    for column, column_type in new_columns.items():

        if column not in existing_columns:

            cursor.execute(
                f"""
                ALTER TABLE airdrops
                ADD COLUMN {column}
                {column_type}
                """
            )

    # -------------------------------------
    # NORMALIZE EXISTING AIRDROP TYPES
    # -------------------------------------

    cursor.execute("""
        UPDATE airdrops

        SET airdrop_type = 'Other'

        WHERE
            airdrop_type IS NULL
            OR TRIM(airdrop_type) = ''
    """)

    # -------------------------------------
    # NORMALIZE CROSS-SOURCE COUNTS
    # -------------------------------------

    cursor.execute("""
        UPDATE airdrops

        SET cross_source_match_count = 0

        WHERE cross_source_match_count IS NULL
    """)

    connection.commit()
    connection.close()


# -----------------------------------------
# AIRDROP TYPE HELPERS
# -----------------------------------------

def get_airdrop_types():

    return list(
        AIRDROP_TYPES.keys()
    )


def get_airdrop_type_emoji(
    airdrop_type
):

    return AIRDROP_TYPES.get(
        airdrop_type,
        AIRDROP_TYPES["Other"]
    )


def normalize_airdrop_type(
    airdrop_type
):

    if not airdrop_type:

        return "Other"

    cleaned = str(
        airdrop_type
    ).strip()

    for valid_type in AIRDROP_TYPES:

        if cleaned.lower() == valid_type.lower():

            return valid_type

    return "Other"


# -----------------------------------------
# SAVE AIRDROP
# -----------------------------------------

def save_airdrop(airdrop):

    connection = get_connection()
    cursor = connection.cursor()

    official_links = airdrop.get(
        "official_links",
        []
    )

    warnings = airdrop.get(
        "warnings",
        []
    )

    market_signal = airdrop.get(
        "market_signal",
        {}
    )

    defi_signal = airdrop.get(
        "defi_signal",
        {}
    )

    airdrop_type = normalize_airdrop_type(
        airdrop.get(
            "airdrop_type",
            "Other"
        )
    )

    risk_intelligence = airdrop.get(
        "risk_intelligence",
        {}
    )

    if not isinstance(
        risk_intelligence,
        dict
    ):
        risk_intelligence = {}

    risk_signals = risk_intelligence.get(
        "signals",
        []
    )

    intelligence_risk_level = (
        risk_intelligence.get(
            "risk_level",
            ""
        )
    )

    risk_summary = risk_intelligence.get(
        "summary",
        ""
    )

    # -------------------------------------
    # CROSS-SOURCE INTELLIGENCE
    # -------------------------------------

    cross_source_matches = airdrop.get(
        "cross_source_matches",
        []
    )

    matched_sources = airdrop.get(
        "matched_sources",
        []
    )

    cross_source_match_count = airdrop.get(
        "cross_source_match_count",
        0
    )

    # Ensure count is always an integer
    try:

        cross_source_match_count = int(
            cross_source_match_count
        )

    except (
        TypeError,
        ValueError
    ):

        cross_source_match_count = 0

    # -------------------------------------
    # SAVE / UPDATE AIRDROP
    # -------------------------------------

    cursor.execute("""
        INSERT INTO airdrops
        (
            name,
            url,
            description,
            source,
            airdrop_type,
            score,
            confidence,
            verified,
            verification_level,
            official_links,
            risk_signals,
            intelligence_risk_level,
            risk_summary,
            warnings,
            market_signal,
            defi_signal,
            cross_source_matches,
            matched_sources,
            cross_source_match_count
        )

        VALUES (
            ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?
        )

        ON CONFLICT(url) DO UPDATE SET

            name = excluded.name,

            description = excluded.description,

            source = excluded.source,

            airdrop_type = excluded.airdrop_type,

            score = excluded.score,

            confidence = excluded.confidence,

            verified = excluded.verified,

            verification_level =
                excluded.verification_level,

            official_links =
                excluded.official_links,

            risk_signals =
                excluded.risk_signals,

            intelligence_risk_level =
                excluded.intelligence_risk_level,

            risk_summary =
                excluded.risk_summary,

            warnings =
                excluded.warnings,

            market_signal =
                excluded.market_signal,

            defi_signal =
                excluded.defi_signal,

            cross_source_matches =
                excluded.cross_source_matches,

            matched_sources =
                excluded.matched_sources,

            cross_source_match_count =
                excluded.cross_source_match_count
    """, (

        airdrop.get(
            "name",
            "Unknown"
        ),

        airdrop.get(
            "url",
            ""
        ),

        airdrop.get(
            "description",
            ""
        ),

        airdrop.get(
            "source",
            ""
        ),

        airdrop_type,

        airdrop.get(
            "score",
            0
        ),

        airdrop.get(
            "confidence",
            ""
        ),

        airdrop.get(
            "verified",
            False
        ),

        airdrop.get(
            "verification_level",
            ""
        ),

        json.dumps(
            official_links
        ),

        json.dumps(
            risk_signals
        ),

        intelligence_risk_level,

        risk_summary,

        json.dumps(
            warnings
        ),

        json.dumps(
            market_signal
        ),

        json.dumps(
            defi_signal
        ),

        json.dumps(
            cross_source_matches
        ),

        json.dumps(
            matched_sources
        ),

        cross_source_match_count
    ))

    # -------------------------------------
    # GET AIRDROP ID
    # -------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM airdrops
        WHERE url = ?
        LIMIT 1
        """,
        (
            airdrop.get(
                "url",
                ""
            ),
        )
    )

    row = cursor.fetchone()

    # -------------------------------------
    # INITIAL HISTORY SNAPSHOT
    # -------------------------------------

    if row:

        airdrop_id = row[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM airdrop_history
            WHERE airdrop_id = ?
            """,
            (
                airdrop_id,
            )
        )

        history_exists = cursor.fetchone()[0]

        if history_exists == 0:

            cursor.execute("""
                INSERT INTO airdrop_history
                (
                    airdrop_id,
                    score,
                    confidence,
                    verification_level,
                    official_links,
                    warnings,
                    market_signal,
                    defi_signal,
                    change_detected,
                    change_summary
                )

                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (

                airdrop_id,

                airdrop.get(
                    "score",
                    0
                ),

                airdrop.get(
                    "confidence",
                    ""
                ),

                airdrop.get(
                    "verification_level",
                    ""
                ),

                json.dumps(
                    official_links
                ),

                json.dumps(
                    warnings
                ),

                json.dumps(
                    market_signal
                ),

                json.dumps(
                    defi_signal
                ),

                0,

                "Initial discovery"
            ))

    connection.commit()
    connection.close()


# -----------------------------------------
# GET LATEST AIRDROPS
# -----------------------------------------

def get_latest_airdrops(
    limit=10
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            id,

            name,

            url,

            description,

            source,

            score,

            confidence,

            verified,

            verification_level,

            official_links,

            warnings,

            market_signal,

            defi_signal,

            created_at,

            last_checked_at,

            previous_score,

            previous_confidence,

            last_change_at,

            next_check_at,

            airdrop_type,

            risk_signals,

            intelligence_risk_level,

            risk_summary,

            cross_source_matches,

            matched_sources,

            cross_source_match_count

        FROM airdrops

        ORDER BY created_at DESC

        LIMIT ?
    """, (
        limit,
    ))

    results = cursor.fetchall()

    connection.close()

    return results


# -----------------------------------------
# GET AIRDROPS FOR LIFECYCLE FILTERING
# -----------------------------------------

def get_airdrops_for_lifecycle(
    limit=1000
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            url,
            description,
            source,
            score,
            confidence,
            verified,
            verification_level,
            official_links,
            warnings,
            market_signal,
            defi_signal,
            created_at,
            last_checked_at,
            previous_score,
            previous_confidence,
            last_change_at,
            next_check_at,
            airdrop_type,
            risk_signals,
            intelligence_risk_level,
            risk_summary,
            cross_source_matches,
            matched_sources,
            cross_source_match_count

        FROM airdrops

        ORDER BY created_at DESC

        LIMIT ?
    """, (
        limit,
    ))

    results = cursor.fetchall()

    connection.close()

    return results

# -----------------------------------------
# GET AIRDROPS BY TYPE
# -----------------------------------------

def get_airdrops_by_type(
    airdrop_type,
    limit=10
):

    airdrop_type = normalize_airdrop_type(
        airdrop_type
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            id,

            name,

            url,

            description,

            source,

            airdrop_type,

            score,

            confidence,

            verified,

            verification_level,

            official_links,

            warnings,

            market_signal,

            defi_signal,

            created_at,

            cross_source_matches,

            matched_sources,

            cross_source_match_count

        FROM airdrops

        WHERE airdrop_type = ?

        ORDER BY
            score DESC,
            created_at DESC

        LIMIT ?
    """, (
        airdrop_type,
        limit
    ))

    results = cursor.fetchall()

    connection.close()

    return results


# -----------------------------------------
# GET SINGLE AIRDROP
# -----------------------------------------

def get_airdrop_by_id(airdrop_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            id,

            name,

            url,

            description,

            source,

            score,

            confidence,

            verified,

            verification_level,

            official_links,

            warnings,

            market_signal,

            defi_signal,

            created_at,

            last_checked_at,

            previous_score,

            previous_confidence,

            last_change_at,

            next_check_at,

            airdrop_type,

            risk_signals,

            intelligence_risk_level,

            risk_summary,

            cross_source_matches,

            matched_sources,

            cross_source_match_count

        FROM airdrops

        WHERE id = ?
    """, (
        airdrop_id,
    ))

    result = cursor.fetchone()

    connection.close()

    return result


# -----------------------------------------
# GET AIRDROP TYPE COUNT
# -----------------------------------------

def get_airdrop_type_count(
    airdrop_type
):

    airdrop_type = normalize_airdrop_type(
        airdrop_type
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)

        FROM airdrops

        WHERE airdrop_type = ?
    """, (
        airdrop_type,
    ))

    result = cursor.fetchone()

    connection.close()

    return result[0]


# -----------------------------------------
# GET ALL AIRDROP TYPE COUNTS
# -----------------------------------------

def get_airdrop_type_counts():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            airdrop_type,

            COUNT(*)

        FROM airdrops

        GROUP BY airdrop_type
    """)

    rows = cursor.fetchall()

    connection.close()

    counts = {
        airdrop_type: 0
        for airdrop_type in AIRDROP_TYPES
    }

    for airdrop_type, count in rows:

        normalized = normalize_airdrop_type(
            airdrop_type
        )

        counts[normalized] += count

    return counts


# -----------------------------------------
# UPDATE AIRDROP TYPE
# -----------------------------------------

def update_airdrop_type(
    airdrop_id,
    airdrop_type
):

    airdrop_type = normalize_airdrop_type(
        airdrop_type
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE airdrops

        SET airdrop_type = ?

        WHERE id = ?
    """, (
        airdrop_type,
        airdrop_id
    ))

    connection.commit()

    updated = cursor.rowcount > 0

    connection.close()

    return updated


# -----------------------------------------
# DATABASE COUNTS
# -----------------------------------------

def get_airdrop_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM airdrops"
    )

    result = cursor.fetchone()

    connection.close()

    return result[0]


def get_total_airdrops():

    return get_airdrop_count()


# -----------------------------------------
# CONFIDENCE STATISTICS
# -----------------------------------------

def get_high_confidence_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM airdrops
        WHERE score >= 60
    """)

    result = cursor.fetchone()

    connection.close()

    return result[0]


def get_medium_confidence_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM airdrops
        WHERE score >= 40
        AND score < 60
    """)

    result = cursor.fetchone()

    connection.close()

    return result[0]


def get_low_confidence_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM airdrops
        WHERE score < 40
    """)

    result = cursor.fetchone()

    connection.close()

    return result[0]


# -----------------------------------------
# SUBSCRIBERS
# -----------------------------------------

def add_subscriber(chat_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO subscribers
        (chat_id)

        VALUES (?)
    """, (chat_id,))

    connection.commit()
    connection.close()


def remove_subscriber(chat_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM subscribers
        WHERE chat_id = ?
        """,
        (chat_id,)
    )

    connection.commit()
    connection.close()


def get_subscribers():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT chat_id FROM subscribers"
    )

    results = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in results
    ]

def create_alert_preferences(chat_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO alert_preferences (
            chat_id,
            new_opportunity,
            monitoring_changes,
            ending_soon,
            risk_alerts
        )
        VALUES (?, 1, 1, 1, 1)
    """, (chat_id,))

    connection.commit()
    connection.close()


def get_alert_preferences(chat_id):

    create_alert_preferences(chat_id)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            new_opportunity,
            monitoring_changes,
            ending_soon,
            risk_alerts
        FROM alert_preferences
        WHERE chat_id = ?
    """, (chat_id,))

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return {
            "new_opportunity": True,
            "monitoring_changes": True,
            "ending_soon": True,
            "risk_alerts": True,
        }

    return {
        "new_opportunity": bool(result[0]),
        "monitoring_changes": bool(result[1]),
        "ending_soon": bool(result[2]),
        "risk_alerts": bool(result[3]),
    }


def set_alert_preference(
    chat_id,
    preference,
    enabled
):

    allowed_preferences = {
        "new_opportunity",
        "monitoring_changes",
        "ending_soon",
        "risk_alerts",
    }

    if preference not in allowed_preferences:
        return False

    create_alert_preferences(chat_id)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        f"""
        UPDATE alert_preferences

        SET
            {preference} = ?,
            updated_at = CURRENT_TIMESTAMP

        WHERE chat_id = ?
        """,
        (1 if enabled else 0, chat_id)
    )

    connection.commit()

    updated = cursor.rowcount > 0

    connection.close()

    return updated


def get_subscriber_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM subscribers"
    )

    result = cursor.fetchone()

    connection.close()

    return result[0]


# -----------------------------------------
# DUPLICATE ALERT PROTECTION
# -----------------------------------------

def alert_exists(
    chat_id,
    airdrop_url
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM sent_alerts

        WHERE chat_id = ?
        AND airdrop_url = ?

        LIMIT 1
    """, (
        chat_id,
        airdrop_url
    ))

    result = cursor.fetchone()

    connection.close()

    return result is not None


def record_alert(
    chat_id,
    airdrop_url
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO sent_alerts
        (
            chat_id,
            airdrop_url
        )

        VALUES (?, ?)
    """, (
        chat_id,
        airdrop_url
    ))

    connection.commit()
    connection.close()



# -----------------------------------------
# LATEST MONITORING HISTORY
# -----------------------------------------

def get_latest_monitoring_history_id(
    airdrop_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM monitoring_history
        WHERE airdrop_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (
        airdrop_id,
    ))

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return None

    return result[0]



# -----------------------------------------
# MONITORING ALERT DUPLICATE PROTECTION
# -----------------------------------------

def monitoring_alert_exists(
    chat_id,
    history_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1

        FROM monitoring_alerts

        WHERE chat_id = ?
        AND history_id = ?

        LIMIT 1
    """, (
        chat_id,
        history_id
    ))

    result = cursor.fetchone()

    connection.close()

    return result is not None


def record_monitoring_alert(
    chat_id,
    airdrop_id,
    history_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO monitoring_alerts
        (
            chat_id,
            airdrop_id,
            history_id
        )

        VALUES (?, ?, ?)
    """, (
        chat_id,
        airdrop_id,
        history_id
    ))

    connection.commit()
    connection.close()


def get_monitoring_alert_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM monitoring_alerts"
    )

    result = cursor.fetchone()

    connection.close()

    return result[0]


# -----------------------------------------
# ALERT STATISTICS
# -----------------------------------------

def get_sent_alert_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM sent_alerts"
    )

    result = cursor.fetchone()

    connection.close()

    return result[0]


# -----------------------------------------
# INTELLIGENCE BACKFILL
# -----------------------------------------

def get_all_airdrops():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            id,

            name,

            url,

            description,

            source

        FROM airdrops

        ORDER BY id ASC
    """)

    results = cursor.fetchall()

    connection.close()

    return results


def update_airdrop_intelligence(
    airdrop_id,
    market_signal,
    defi_signal,
    score,
    confidence,
    verification_level,
    official_links,
    warnings
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE airdrops

        SET

            score = ?,

            confidence = ?,

            verification_level = ?,

            official_links = ?,

            warnings = ?,

            market_signal = ?,

            defi_signal = ?

        WHERE id = ?
    """, (

        score,

        confidence,

        verification_level,

        json.dumps(
            official_links
        ),

        json.dumps(
            warnings
        ),

        json.dumps(
            market_signal
        ),

        json.dumps(
            defi_signal
        ),

        airdrop_id
    ))

    connection.commit()
    connection.close()


# -----------------------------------------
# TRACKING
# -----------------------------------------

def track_airdrop(
    chat_id,
    airdrop_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO tracked_airdrops
        (
            chat_id,
            airdrop_id
        )
        VALUES (?, ?)
    """, (
        chat_id,
        airdrop_id
    ))

    connection.commit()

    tracked = cursor.rowcount > 0

    connection.close()

    return tracked


def untrack_airdrop(
    chat_id,
    airdrop_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM tracked_airdrops

        WHERE chat_id = ?
        AND airdrop_id = ?
    """, (
        chat_id,
        airdrop_id
    ))

    connection.commit()

    removed = cursor.rowcount > 0

    connection.close()

    return removed


def is_airdrop_tracked(
    chat_id,
    airdrop_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1

        FROM tracked_airdrops

        WHERE chat_id = ?
        AND airdrop_id = ?

        LIMIT 1
    """, (
        chat_id,
        airdrop_id
    ))

    result = cursor.fetchone()

    connection.close()

    return result is not None


def get_tracked_airdrops(
    chat_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            a.id,
            a.name,
            a.url,
            a.description,
            a.source,
            a.airdrop_type,
            a.score,
            a.confidence,
            a.verification_level,
            a.intelligence_risk_level,
            t.tracked_at

        FROM tracked_airdrops t

        INNER JOIN airdrops a
            ON a.id = t.airdrop_id

        WHERE t.chat_id = ?

        ORDER BY
            t.tracked_at DESC
    """, (
        chat_id,
    ))

    results = cursor.fetchall()

    connection.close()

    return results


def get_airdrops_for_tracking(
    limit=10
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            id,

            name,

            url,

            description,

            source,

            score,

            confidence,

            verified,

            verification_level,

            official_links,

            warnings,

            market_signal,

            defi_signal,

            last_checked_at,

            previous_score,

            previous_confidence,

            last_change_at,

            next_check_at,

            cross_source_matches,

            matched_sources,

            cross_source_match_count

        FROM airdrops

        WHERE
            next_check_at IS NULL
            OR next_check_at <= CURRENT_TIMESTAMP

        ORDER BY

            CASE
                WHEN last_checked_at IS NULL
                THEN 0
                ELSE 1
            END,

            last_checked_at ASC

        LIMIT ?
    """, (
        limit,
    ))

    results = cursor.fetchall()

    connection.close()

    return results


def get_airdrop_tracking_state(
    airdrop_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            id,

            name,

            url,

            score,

            confidence,

            verification_level,

            official_links,

            warnings,

            market_signal,

            defi_signal,

            last_checked_at,

            previous_score,

            previous_confidence,

            last_change_at,

            next_check_at,

            cross_source_matches,

            matched_sources,

            cross_source_match_count

        FROM airdrops

        WHERE id = ?

        LIMIT 1
    """, (
        airdrop_id,
    ))

    result = cursor.fetchone()

    connection.close()

    return result


# -----------------------------------------
# GET TRACKING HISTORY
# -----------------------------------------

def get_airdrop_history(
    airdrop_id,
    limit=20
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            id,

            airdrop_id,

            checked_at,

            score,

            confidence,

            verification_level,

            official_links,

            warnings,

            market_signal,

            defi_signal,

            change_detected,

            change_summary

        FROM airdrop_history

        WHERE airdrop_id = ?

        ORDER BY checked_at DESC, id DESC

        LIMIT ?
    """, (
        airdrop_id,
        limit
    ))

    results = cursor.fetchall()

    connection.close()

    return results


# -----------------------------------------
# GET PREVIOUS TRACKING SNAPSHOT
# -----------------------------------------

def get_previous_tracking_snapshot(
    airdrop_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            id,

            airdrop_id,

            checked_at,

            score,

            confidence,

            verification_level,

            official_links,

            warnings,

            market_signal,

            defi_signal,

            change_detected,

            change_summary

        FROM airdrop_history

        WHERE airdrop_id = ?

        ORDER BY checked_at DESC, id DESC

        LIMIT 2
    """, (
        airdrop_id,
    ))

    results = cursor.fetchall()

    connection.close()

    if len(results) < 2:

        return None

    return results[1]


# -----------------------------------------
# GET CURRENT + PREVIOUS SNAPSHOT
# -----------------------------------------

def get_tracking_comparison(
    airdrop_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT

            id,

            airdrop_id,

            checked_at,

            score,

            confidence,

            verification_level,

            official_links,

            warnings,

            market_signal,

            defi_signal,

            change_detected,

            change_summary

        FROM airdrop_history

        WHERE airdrop_id = ?

        ORDER BY checked_at DESC, id DESC

        LIMIT 2
    """, (
        airdrop_id,
    ))

    rows = cursor.fetchall()

    connection.close()

    if len(rows) < 2:

        return None

    def snapshot_to_dict(row):

        return {

            "id": row[0],

            "airdrop_id": row[1],

            "checked_at": row[2],

            "score": row[3],

            "confidence": row[4],

            "verification_level": row[5],

            "official_links": safe_json_loads(
                row[6],
                []
            ),

            "warnings": safe_json_loads(
                row[7],
                []
            ),

            "market_signal": safe_json_loads(
                row[8],
                {}
            ),

            "defi_signal": safe_json_loads(
                row[9],
                {}
            ),

            "change_detected": bool(
                row[10]
            ),

            "change_summary": row[11] or ""
        }

    return {

        "current": snapshot_to_dict(
            rows[0]
        ),

        "previous": snapshot_to_dict(
            rows[1]
        )
    }


# -----------------------------------------
# SAFE JSON LOADER
# -----------------------------------------

def safe_json_loads(
    value,
    default=None
):

    if default is None:

        default = {}

    if value is None:

        return default

    if isinstance(
        value,
        (
            dict,
            list
        )
    ):

        return value

    try:

        return json.loads(
            value
        )

    except (
        json.JSONDecodeError,
        TypeError
    ):

        return default


# -----------------------------------------
# UPDATE TRACKING STATE
# -----------------------------------------

def update_airdrop_tracking(
    airdrop_id,
    score,
    confidence,
    verification_level,
    official_links,
    warnings,
    market_signal,
    defi_signal,
    change_detected=False,
    change_summary="",
    next_check_at=None
):

    connection = get_connection()
    cursor = connection.cursor()

    # -------------------------------------
    # GET CURRENT STATE
    # -------------------------------------

    cursor.execute("""
        SELECT

            score,

            confidence

        FROM airdrops

        WHERE id = ?

        LIMIT 1
    """, (
        airdrop_id,
    ))

    current = cursor.fetchone()

    if not current:

        connection.close()

        return False

    current_score = current[0]

    current_confidence = current[1]

    # -------------------------------------
    # UPDATE AIRDROP
    # -------------------------------------

    if change_detected:

        cursor.execute("""
            UPDATE airdrops

            SET

                previous_score = ?,

                previous_confidence = ?,

                score = ?,

                confidence = ?,

                verification_level = ?,

                official_links = ?,

                warnings = ?,

                market_signal = ?,

                defi_signal = ?,

                last_checked_at = CURRENT_TIMESTAMP,

                last_change_at = CURRENT_TIMESTAMP,

                next_check_at = ?

            WHERE id = ?
        """, (

            current_score,

            current_confidence,

            score,

            confidence,

            verification_level,

            json.dumps(
                official_links
            ),

            json.dumps(
                warnings
            ),

            json.dumps(
                market_signal
            ),

            json.dumps(
                defi_signal
            ),

            next_check_at,

            airdrop_id
        ))

    else:

        cursor.execute("""
            UPDATE airdrops

            SET

                score = ?,

                confidence = ?,

                verification_level = ?,

                official_links = ?,

                warnings = ?,

                market_signal = ?,

                defi_signal = ?,

                last_checked_at = CURRENT_TIMESTAMP,

                next_check_at = ?

            WHERE id = ?
        """, (

            score,

            confidence,

            verification_level,

            json.dumps(
                official_links
            ),

            json.dumps(
                warnings
            ),

            json.dumps(
                market_signal
            ),

            json.dumps(
                defi_signal
            ),

            next_check_at,

            airdrop_id
        ))

    # -------------------------------------
    # SAVE NEW HISTORY SNAPSHOT
    # -------------------------------------

    cursor.execute("""
        INSERT INTO airdrop_history
        (
            airdrop_id,

            score,

            confidence,

            verification_level,

            official_links,

            warnings,

            market_signal,

            defi_signal,

            change_detected,

            change_summary
        )

        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, (

        airdrop_id,

        score,

        confidence,

        verification_level,

        json.dumps(
            official_links
        ),

        json.dumps(
            warnings
        ),

        json.dumps(
            market_signal
        ),

        json.dumps(
            defi_signal
        ),

        1 if change_detected else 0,

        change_summary or ""
    ))

    connection.commit()
    connection.close()

    return True


# -----------------------------------------
# TRACKING STATISTICS
# -----------------------------------------

def get_tracking_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM airdrops
        WHERE last_checked_at IS NOT NULL
    """)

    result = cursor.fetchone()

    connection.close()

    return result[0]


def get_change_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM airdrop_history
        WHERE change_detected = 1
    """)

    result = cursor.fetchone()

    connection.close()

    return result[0]


# -----------------------------------------
# TEST
# -----------------------------------------

if __name__ == "__main__":

    create_database()

    print(
        "🗄️ Database v1.1 ready!"
    )

    print(
        f"🪂 Total airdrops: "
        f"{get_total_airdrops()}"
    )

    print(
        f"🟢 High confidence: "
        f"{get_high_confidence_count()}"
    )

    print(
        f"🟡 Medium confidence: "
        f"{get_medium_confidence_count()}"
    )

    print(
        f"🔴 Low confidence: "
        f"{get_low_confidence_count()}"
    )

    print(
        f"👥 Subscribers: "
        f"{get_subscriber_count()}"
    )

    print(
        f"📨 Sent alerts: "
        f"{get_sent_alert_count()}"
    )

    print(
        f"🔔 Monitoring alerts: "
        f"{get_monitoring_alert_count()}"
    )

    print(
        f"🔄 Tracked airdrops: "
        f"{get_tracking_count()}"
    )

    print(
        f"📈 Detected changes: "
        f"{get_change_count()}"
    )

    # -------------------------------------
    # AIRDROP TYPE COUNTS
    # -------------------------------------

    print(
        "\n🪂 Airdrop categories:"
    )

    type_counts = get_airdrop_type_counts()

    for airdrop_type, count in type_counts.items():

        emoji = get_airdrop_type_emoji(
            airdrop_type
        )

        print(
            f"   {emoji} "
            f"{airdrop_type}: "
            f"{count}"
        )

    # -------------------------------------
    # AIRDROPS COLUMNS
    # -------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "PRAGMA table_info(airdrops)"
    )

    columns = cursor.fetchall()

    connection.close()

    print(
        "\n📋 Airdrop database columns:"
    )

    for column in columns:

        print(
            f"   • {column[1]}"
        )

    # -------------------------------------
    # DATABASE TABLES
    # -------------------------------------

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    )

    tables = cursor.fetchall()

    connection.close()

    print(
        "\n📋 Database tables:"
    )

    for table in tables:

        print(
            f"   • {table[0]}"
        )

    print(
        "\n🪂 Airdrop categories: ENABLED"
    )

    print(
        "🔄 Tracking system: ENABLED"
    )

    print(
        "📈 Change history: ENABLED"
    )

    print(
        "🧾 Previous/current comparison: ENABLED"
    )

    print(
        "🔔 Monitoring alerts: ENABLED"
    )

    print(
        "🔗 Cross-source matching: ENABLED"
    )

    print(
        "🛡️ Existing database preserved."
    )