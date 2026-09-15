import json
import re
import time
from difflib import SequenceMatcher
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# =========================================
# AIRDROP RADAR — API SOURCES
# =========================================

COINGECKO_API = (
    "https://api.coingecko.com/api/v3"
)

DEFILLAMA_API = (
    "https://api.llama.fi"
)

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "Chrome/120 Safari/537.36"
)


# =========================================
# REQUEST SETTINGS
# =========================================

REQUEST_TIMEOUT = 15

MAX_RETRIES = 2

COINGECKO_MIN_INTERVAL = 2.0

_last_coingecko_request = 0.0


# =========================================
# RATE LIMIT PROTECTION
# =========================================

def wait_for_coingecko():
    """
    Make sure CoinGecko requests are spaced out.
    """

    global _last_coingecko_request

    current_time = time.monotonic()

    elapsed = (
        current_time
        - _last_coingecko_request
    )

    if elapsed < COINGECKO_MIN_INTERVAL:

        wait_time = (
            COINGECKO_MIN_INTERVAL
            - elapsed
        )

        time.sleep(wait_time)

    _last_coingecko_request = (
        time.monotonic()
    )


# =========================================
# GENERIC API REQUEST
# =========================================

def api_request(
    url,
    api_name="API",
    retries=MAX_RETRIES,
):
    """
    Safely request JSON data from an API.
    """

    is_coingecko = (
        "api.coingecko.com"
        in url.lower()
    )

    attempt = 0

    while attempt <= retries:

        if is_coingecko:
            wait_for_coingecko()

        request = Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
        )

        try:

            with urlopen(
                request,
                timeout=REQUEST_TIMEOUT,
            ) as response:

                data = (
                    response
                    .read()
                    .decode(
                        "utf-8",
                        errors="ignore",
                    )
                )

                try:

                    parsed_data = json.loads(
                        data
                    )

                except json.JSONDecodeError:

                    print(
                        f"⚠️ {api_name} returned "
                        "invalid JSON."
                    )

                    return {
                        "success": False,
                        "data": None,
                    }

                return {
                    "success": True,
                    "data": parsed_data,
                }

        except HTTPError as error:

            status_code = error.code

            # -----------------------------
            # RATE LIMIT
            # -----------------------------

            if status_code == 429:

                if attempt < retries:

                    wait_time = (
                        5 * (2 ** attempt)
                    )

                    print(
                        f"⏳ {api_name} rate "
                        f"limited (429). "
                        f"Retrying in "
                        f"{wait_time}s..."
                    )

                    time.sleep(
                        wait_time
                    )

                    attempt += 1

                    continue

                print(
                    f"⚠️ {api_name} HTTP "
                    "error: 429 "
                    "(rate limited)"
                )

                return {
                    "success": False,
                    "data": None,
                }

            # -----------------------------
            # SERVER ERROR
            # -----------------------------

            if (
                status_code >= 500
                and attempt < retries
            ):

                wait_time = (
                    3 * (2 ** attempt)
                )

                print(
                    f"⏳ {api_name} server "
                    f"error ({status_code}). "
                    f"Retrying in "
                    f"{wait_time}s..."
                )

                time.sleep(
                    wait_time
                )

                attempt += 1

                continue

            # -----------------------------
            # OTHER HTTP ERRORS
            # -----------------------------

            print(
                f"⚠️ {api_name} HTTP "
                f"error: {status_code}"
            )

            return {
                "success": False,
                "data": None,
            }

        except URLError as error:

            if attempt < retries:

                wait_time = (
                    2 * (2 ** attempt)
                )

                print(
                    f"⏳ {api_name} connection "
                    f"problem. Retrying in "
                    f"{wait_time}s..."
                )

                time.sleep(
                    wait_time
                )

                attempt += 1

                continue

            print(
                f"⚠️ {api_name} connection "
                f"error: {error}"
            )

            return {
                "success": False,
                "data": None,
            }

        except Exception as error:

            print(
                f"⚠️ {api_name} API error: "
                f"{error}"
            )

            return {
                "success": False,
                "data": None,
            }

    return {
        "success": False,
        "data": None,
    }


# =========================================
# COINGECKO
# =========================================

def check_coingecko():

    url = (
        f"{COINGECKO_API}/ping"
    )

    result = api_request(
        url,
        "CoinGecko",
    )

    return (
        result["success"]
        if isinstance(
            result,
            dict,
        )
        else False
    )


# =========================================
# NORMALIZE PROJECT NAME
# =========================================

def normalize_project_name(
    name,
):

    if not name:
        return ""

    text = (
        str(name)
        .lower()
        .strip()
    )

    removable_words = [
        "airdrop",
        "token",
        "campaign",
        "claim",
        "rewards",
        "reward",
        "testnet",
        "mainnet",
        "points",
        "retroactive",
        "eligibility",
        "finance",
        "protocol",
        "network",
        "chain",
    ]

    for word in removable_words:

        text = re.sub(
            rf"\b{re.escape(word)}\b",
            " ",
            text,
        )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = " ".join(
        text.split()
    )

    return text


# =========================================
# COINGECKO SEARCH
# =========================================

def search_coin(
    coin_name,
):

    if not coin_name:

        return {
            "success": True,
            "coins": [],
        }

    encoded_name = quote(
        coin_name.strip()
    )

    url = (
        f"{COINGECKO_API}"
        f"/search?query="
        f"{encoded_name}"
    )

    result = api_request(
        url,
        "CoinGecko",
    )

    if not isinstance(
        result,
        dict,
    ):

        return {
            "success": False,
            "coins": [],
        }

    if not result.get(
        "success",
        False,
    ):

        return {
            "success": False,
            "coins": [],
        }

    data = result.get(
        "data"
    )

    if not isinstance(
        data,
        dict,
    ):

        return {
            "success": False,
            "coins": [],
        }

    coins = data.get(
        "coins",
        [],
    )

    if not isinstance(
        coins,
        list,
    ):

        return {
            "success": True,
            "coins": [],
        }

    return {
        "success": True,
        "coins": coins,
    }


# =========================================
# FIND COINGECKO MATCH
# =========================================

def find_coin_match(
    project_name,
):

    cleaned_name = (
        normalize_project_name(
            project_name
        )
    )

    if not cleaned_name:

        return {
            "success": True,
            "match": None,
        }

    search_result = search_coin(
        cleaned_name
    )

    if not search_result.get(
        "success",
        False,
    ):

        return {
            "success": False,
            "match": None,
        }

    results = search_result.get(
        "coins",
        [],
    )

    if not results:

        return {
            "success": True,
            "match": None,
        }

    best_match = None
    best_ratio = 0

    for coin in results[:25]:

        if not isinstance(
            coin,
            dict,
        ):
            continue

        coin_name = (
            normalize_project_name(
                coin.get(
                    "name",
                    "",
                )
            )
        )

        if not coin_name:
            continue

        ratio = SequenceMatcher(
            None,
            cleaned_name,
            coin_name,
        ).ratio()

        if ratio > best_ratio:

            best_ratio = ratio
            best_match = coin

    if (
        best_match
        and best_ratio >= 0.80
    ):

        return {
            "success": True,
            "match": {
                "id": best_match.get(
                    "id",
                    "",
                ),
                "name": best_match.get(
                    "name",
                    "",
                ),
                "symbol": best_match.get(
                    "symbol",
                    "",
                ),
                "market_cap_rank":
                    best_match.get(
                        "market_cap_rank"
                    ),
                "match_score": round(
                    best_ratio * 100
                ),
            },
        }

    return {
        "success": True,
        "match": None,
    }


# =========================================
# COINGECKO DETAILS
# =========================================

def get_coin_details(
    coin_id,
):

    if not coin_id:
        return None

    url = (
        f"{COINGECKO_API}"
        f"/coins/"
        f"{quote(coin_id)}"
    )

    result = api_request(
        url,
        "CoinGecko",
    )

    if not isinstance(
        result,
        dict,
    ):

        return None

    if not result.get(
        "success",
        False,
    ):

        return None

    data = result.get(
        "data"
    )

    if not isinstance(
        data,
        dict,
    ):

        return None

    return data


# =========================================
# PROJECT MARKET SIGNAL
# =========================================

def get_project_market_signal(
    project_name,
):

    match_result = find_coin_match(
        project_name
    )

    if not match_result.get(
        "success",
        False,
    ):

        return {
            "found": False,
            "name": "",
            "symbol": "",
            "market_rank": None,
            "match_score": 0,
            "coin_id": "",
            "signal": "api_unavailable",
        }

    match = match_result.get(
        "match"
    )

    if not match:

        return {
            "found": False,
            "name": "",
            "symbol": "",
            "market_rank": None,
            "match_score": 0,
            "coin_id": "",
            "signal": "no_match",
        }

    match_score = (
        match.get(
            "match_score",
            0,
        )
        or 0
    )

    if match_score < 80:

        return {
            "found": False,
            "name": "",
            "symbol": "",
            "market_rank": None,
            "match_score": 0,
            "coin_id": "",
            "signal": "no_match",
        }

    return {
        "found": True,
        "name": match.get(
            "name",
            "",
        ),
        "symbol": match.get(
            "symbol",
            "",
        ),
        "market_rank": match.get(
            "market_cap_rank"
        ),
        "match_score": match_score,
        "coin_id": match.get(
            "id",
            "",
        ),
        "signal": "strong_name_match",
    }


# =========================================
# DEFILLAMA
# =========================================

def check_defillama():

    url = (
        f"{DEFILLAMA_API}/v2/protocols"
    )

    result = api_request(
        url,
        "DeFiLlama",
    )

    if not isinstance(
        result,
        dict,
    ):

        return False

    if not result.get(
        "success",
        False,
    ):

        return False

    return isinstance(
        result.get(
            "data"
        ),
        list,
    )


# =========================================
# GET PROTOCOLS
# =========================================

def get_defillama_protocols():

    url = (
        f"{DEFILLAMA_API}/v2/protocols"
    )

    result = api_request(
        url,
        "DeFiLlama",
    )

    if not isinstance(
        result,
        dict,
    ):

        return {
            "success": False,
            "protocols": [],
        }

    if not result.get(
        "success",
        False,
    ):

        return {
            "success": False,
            "protocols": [],
        }

    protocols = result.get(
        "data"
    )

    if not isinstance(
        protocols,
        list,
    ):

        return {
            "success": False,
            "protocols": [],
        }

    return {
        "success": True,
        "protocols": protocols,
    }


# =========================================
# NORMALIZE DEFILLAMA PROTOCOL
# =========================================

def normalize_protocol(
    protocol,
):

    if not isinstance(
        protocol,
        dict,
    ):

        return None

    name = protocol.get(
        "name",
        "",
    )

    if not isinstance(
        name,
        str,
    ):

        name = ""

    name = name.strip()

    slug = protocol.get(
        "slug",
        "",
    )

    if not isinstance(
        slug,
        str,
    ):

        slug = ""

    slug = slug.strip()

    if not name:
        return None

    return {
        "name": name,
        "slug": slug,
        "symbol": protocol.get(
            "symbol",
            "",
        ),
        "category": protocol.get(
            "category",
            "",
        ),
        "chains": protocol.get(
            "chains",
            [],
        ),
        "tvl": protocol.get(
            "tvl"
        ),
        "url": protocol.get(
            "url",
            "",
        ),
        "logo": protocol.get(
            "logo",
            "",
        ),
        "source": "defillama",
    }


# =========================================
# FIND DEFILLAMA PROTOCOL
# =========================================

def find_defillama_protocol(
    project_name,
):

    cleaned_name = (
        normalize_project_name(
            project_name
        )
    )

    if not cleaned_name:

        return {
            "success": True,
            "match": None,
        }

    protocol_result = (
        get_defillama_protocols()
    )

    if not protocol_result.get(
        "success",
        False,
    ):

        return {
            "success": False,
            "match": None,
        }

    protocols = protocol_result.get(
        "protocols",
        [],
    )

    if not protocols:

        return {
            "success": True,
            "match": None,
        }

    best_match = None
    best_ratio = 0

    for protocol in protocols:

        if not isinstance(
            protocol,
            dict,
        ):
            continue

        protocol_name = (
            normalize_project_name(
                protocol.get(
                    "name",
                    "",
                )
            )
        )

        if not protocol_name:
            continue

        ratio = SequenceMatcher(
            None,
            cleaned_name,
            protocol_name,
        ).ratio()

        if ratio > best_ratio:

            best_ratio = ratio
            best_match = protocol

    if (
        best_match
        and best_ratio >= 0.80
    ):

        normalized = (
            normalize_protocol(
                best_match
            )
        )

        if normalized:

            normalized["match_score"] = (
                round(
                    best_ratio * 100
                )
            )

            return {
                "success": True,
                "match": normalized,
            }

    return {
        "success": True,
        "match": None,
    }


# =========================================
# PROJECT DEFI SIGNAL
# =========================================

def get_project_defi_signal(
    project_name,
):

    match_result = (
        find_defillama_protocol(
            project_name
        )
    )

    if not match_result.get(
        "success",
        False,
    ):

        return {
            "found": False,
            "protocol": "",
            "slug": "",
            "category": "",
            "chains": [],
            "tvl": 0,
            "match_score": 0,
            "url": "",
            "signal": "api_unavailable",
        }

    match = match_result.get(
        "match"
    )

    if not match:

        return {
            "found": False,
            "protocol": "",
            "slug": "",
            "category": "",
            "chains": [],
            "tvl": 0,
            "match_score": 0,
            "url": "",
            "signal": "no_match",
        }

    match_score = (
        match.get(
            "match_score",
            0,
        )
        or 0
    )

    if match_score < 80:

        return {
            "found": False,
            "protocol": "",
            "slug": "",
            "category": "",
            "chains": [],
            "tvl": 0,
            "match_score": 0,
            "url": "",
            "signal": "no_match",
        }

    return {
        "found": True,
        "protocol": match.get(
            "name",
            "",
        ),
        "slug": match.get(
            "slug",
            "",
        ),
        "category": match.get(
            "category",
            "",
        ),
        "chains": match.get(
            "chains",
            [],
        ),
        "tvl": match.get(
            "tvl",
            0,
        ) or 0,
        "match_score": match_score,
        "url": match.get(
            "url",
            "",
        ),
        "signal": "defi_protocol_match",
    }


# =========================================
# COMBINED PROJECT INTELLIGENCE
# =========================================

def get_project_intelligence(
    project_name,
):

    print(
        f"🔎 Checking market data: "
        f"{project_name}"
    )

    market_signal = (
        get_project_market_signal(
            project_name
        )
    )

    print(
        f"🔎 Checking DeFi ecosystem: "
        f"{project_name}"
    )

    defi_signal = (
        get_project_defi_signal(
            project_name
        )
    )

    return {
        "market_signal": market_signal,
        "defi_signal": defi_signal,
    }


# =========================================
# TEST
# =========================================

if __name__ == "__main__":

    print(
        "🔌 Testing AirdropRadar "
        "API intelligence v6...\n"
    )

    # -------------------------------------
    # COINGECKO
    # -------------------------------------

    print(
        "1️⃣ CoinGecko"
    )

    if check_coingecko():

        print(
            "✅ CoinGecko API is reachable."
        )

    else:

        print(
            "❌ CoinGecko API unavailable."
        )

    # -------------------------------------
    # COINGECKO SEARCH TEST
    # -------------------------------------

    print(
        "\n🔎 Searching for Bitcoin..."
    )

    market_signal = (
        get_project_market_signal(
            "Bitcoin"
        )
    )

    if market_signal["found"]:

        print(
            f"✅ Match: "
            f"{market_signal['name']}"
        )

        print(
            f"🔤 Symbol: "
            f"{market_signal['symbol']}"
        )

        print(
            f"🎯 Match: "
            f"{market_signal['match_score']}%"
        )

        print(
            f"📊 Market rank: "
            f"{market_signal['market_rank']}"
        )

    elif (
        market_signal["signal"]
        == "api_unavailable"
    ):

        print(
            "⚠️ CoinGecko unavailable."
        )

    else:

        print(
            "⚠️ No strong match."
        )

    # -------------------------------------
    # DEFILLAMA
    # -------------------------------------

    print(
        "\n2️⃣ DeFiLlama"
    )

    if check_defillama():

        print(
            "✅ DeFiLlama API is reachable."
        )

    else:

        print(
            "❌ DeFiLlama API unavailable."
        )

    # -------------------------------------
    # DEFILLAMA SEARCH TEST
    # -------------------------------------

    print(
        "\n🔎 Searching for Aave..."
    )

    defi_signal = (
        get_project_defi_signal(
            "Aave"
        )
    )

    if defi_signal["found"]:

        print(
            f"✅ Protocol: "
            f"{defi_signal['protocol']}"
        )

        print(
            f"📂 Category: "
            f"{defi_signal['category']}"
        )

        print(
            f"🎯 Match: "
            f"{defi_signal['match_score']}%"
        )

        chains = (
            defi_signal.get(
                "chains",
                [],
            )
        )

        print(
            f"⛓️ Chains: "
            f"{', '.join(chains[:5])}"
        )

        print(
            f"💰 TVL: "
            f"{defi_signal['tvl']}"
        )

    elif (
        defi_signal["signal"]
        == "api_unavailable"
    ):

        print(
            "⚠️ DeFiLlama unavailable."
        )

    else:

        print(
            "⚠️ No strong protocol match."
        )