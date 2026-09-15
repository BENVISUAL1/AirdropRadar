from html.parser import HTMLParser

from urllib.parse import urljoin, urlparse

from urllib.request import Request, urlopen

from urllib.error import HTTPError, URLError

import ipaddress

import re

import socket

from api_sources import get_project_intelligence


# ============================================================
# SETTINGS
# ============================================================

REQUEST_TIMEOUT = 12


# ============================================================
# IGNORED DOMAINS
# ============================================================

IGNORED_DOMAINS = {
    "airdropalert.com",
    "cointelegraph.com",
    "decrypt.co",
    "coindesk.com",
    "theblock.co",
    "bit.ly",
    "t.co",
    "tinyurl.com",
    "ow.ly",
    "is.gd",
    "buff.ly",
    "cutt.ly",
    "shorturl.at",
    "twitter.com",
    "x.com",
    "t.me",
    "telegram.me",
    "discord.com",
    "discord.gg",
    "medium.com",
    "youtube.com",
    "youtu.be",
    "reddit.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "github.com",
    "gitlab.com",
    "substack.com",
    "galxe.com",
    "layer3.xyz",
    "zealy.io",
    "questn.com",
    "coinmarketcap.com",
    "coingecko.com",
    "defillama.com",
}


# ============================================================
# GENERIC PROJECT WORDS
# ============================================================

GENERIC_PROJECT_WORDS = {
    "finance",
    "financial",
    "protocol",
    "network",
    "chain",
    "blockchain",
    "crypto",
    "token",
    "official",
    "airdrop",
    "app",
    "apps",
    "docs",
    "documentation",
    "foundation",
    "labs",
    "lab",
    "dao",
    "defi",
    "web3",
    "community",
    "platform",
    "project",
    "protocols",
    "exchange",
    "wallet",
    "capital",
    "ventures",
    "markets",
    "market",
    "technology",
    "tech",
}


# ============================================================
# SUSPICIOUS PHRASES
# ============================================================

SUSPICIOUS_PHRASES = [
    "send crypto",
    "send us crypto",
    "guaranteed profit",
    "guaranteed return",
    "double your crypto",
    "double your bitcoin",
    "seed phrase",
    "private key",
    "recovery phrase",
    "deposit crypto",
    "pay fee to claim",
    "withdrawal fee",
    "activate your wallet",
]


# ============================================================
# HTML PARSER
# ============================================================

class PageParser(HTMLParser):

    def __init__(self):
        super().__init__()

        self.links = []

        self.current_link = None

        self.current_text = []

        self.canonical = ""

        self.og_url = ""

    def handle_starttag(
        self,
        tag,
        attrs
    ):
        attributes = dict(attrs)

        # ----------------------------------------------------
        # LINKS
        # ----------------------------------------------------

        if tag == "a":

            href = attributes.get(
                "href",
                ""
            )

            if href:

                self.current_link = href

                self.current_text = []

        # ----------------------------------------------------
        # CANONICAL
        # ----------------------------------------------------

        if tag == "link":

            rel = (
                attributes.get(
                    "rel",
                    ""
                )
                .lower()
            )

            href = attributes.get(
                "href",
                ""
            )

            if (
                "canonical" in rel
                and href
            ):

                self.canonical = href

        # ----------------------------------------------------
        # OPEN GRAPH URL
        # ----------------------------------------------------

        if tag == "meta":

            property_name = (
                attributes.get(
                    "property",
                    ""
                )
                .lower()
            )

            content = attributes.get(
                "content",
                ""
            )

            if (
                property_name == "og:url"
                and content
            ):

                self.og_url = content

    def handle_data(
        self,
        data
    ):

        if self.current_link:

            self.current_text.append(
                data
            )

    def handle_endtag(
        self,
        tag
    ):

        if (
            tag == "a"
            and self.current_link
        ):

            text = " ".join(
                self.current_text
            ).strip()

            self.links.append({
                "url": self.current_link,
                "text": text
            })

            self.current_link = None

            self.current_text = []


# ============================================================
# DOMAIN HELPERS
# ============================================================

def normalize_domain(
    url
):

    try:

        domain = urlparse(
            url
        ).netloc.lower()

        if "@" in domain:

            domain = domain.split(
                "@",
                1
            )[1]

        if ":" in domain:

            domain = domain.split(
                ":",
                1
            )[0]

        if domain.startswith(
            "www."
        ):

            domain = domain[4:]

        return domain

    except Exception:

        return ""


# ============================================================
# GET DOMAIN PARTS
# ============================================================

def get_domain_parts(
    url
):

    domain = normalize_domain(
        url
    )

    if not domain:

        return []

    parts = domain.split(".")

    return [
        part
        for part in parts
        if part
        and part not in {
            "www",
            "app",
            "docs",
            "blog",
            "www2",
        }
    ]


# ============================================================
# PROJECT NAME WORDS
# ============================================================

def get_project_words(
    project_name
):

    text = clean_project_name(
        project_name
    ).lower()

    words = re.findall(
        r"[a-z0-9]+",
        text
    )

    useful_words = []

    for word in words:

        if len(word) < 3:
            continue

        if word in GENERIC_PROJECT_WORDS:
            continue

        if word.isdigit():
            continue

        if word not in useful_words:

            useful_words.append(
                word
            )

    return useful_words


# ============================================================
# PROJECT DOMAIN CHECK
# ============================================================

def is_project_owned_domain(
    url,
    project_name
):
    domain = normalize_domain(
        url
    )

    if not domain:
        return False

    if is_ignored_domain(
        url
    ):
        return False

    project_words = get_project_words(
        project_name
    )

    if not project_words:
        return False

    domain_parts = get_domain_parts(
        url
    )

    if not domain_parts:
        return False

    # ========================================================
    # SUSPICIOUS DOMAIN LABELS
    #
    # These words commonly appear in fake airdrop,
    # giveaway, claim, and impersonation domains.
    # ========================================================

    suspicious_domain_words = {
        "airdrop",
        "giveaway",
        "claim",
        "rewards",
        "reward",
        "bonus",
        "free",
        "promo",
        "promotions",
        "official",
        "verify",
        "verification",
        "support",
        "wallet",
        "login",
        "secure",
        "security",
        "connect",
        "connectwallet",
    }

    # ========================================================
    # NORMALIZE DOMAIN PARTS
    # ========================================================

    normalized_parts = []

    for part in domain_parts:

        normalized_part = re.sub(
            r"[^a-z0-9]",
            "",
            part.lower()
        )

        if normalized_part:
            normalized_parts.append(
                normalized_part
            )

    # ========================================================
    # PROJECT TOKEN MATCH
    #
    # The project name must appear as a complete domain
    # label, not merely as part of a larger word.
    #
    # Example:
    #
    # ekiden.fi
    # docs.ekiden.fi
    #
    # ✅ valid
    #
    # fake-ekiden.com
    # ekiden-airdrop.com
    #
    # ❌ suspicious
    # ========================================================

    matched_project_word = None

    for word in project_words:

        normalized_word = re.sub(
            r"[^a-z0-9]",
            "",
            word.lower()
        )

        if not normalized_word:
            continue

        if normalized_word in normalized_parts:

            matched_project_word = (
                normalized_word
            )

            break

    if not matched_project_word:
        return False

    # ========================================================
    # CHECK FOR SUSPICIOUS LABELS
    #
    # If another domain label contains obvious scam /
    # impersonation language, do not treat it as official.
    #
    # Example:
    #
    # ekiden-airdrop.com
    # official-ekiden.com
    # ekiden-giveaway.xyz
    #
    # ❌
    # ========================================================

    for part in normalized_parts:

        if part == matched_project_word:
            continue

        for suspicious_word in (
            suspicious_domain_words
        ):

            normalized_suspicious = re.sub(
                r"[^a-z0-9]",
                "",
                suspicious_word.lower()
            )

            if not normalized_suspicious:
                continue

            if normalized_suspicious in part:
                return False

    # ========================================================
    # VALID PROJECT DOMAIN
    # ========================================================

    return True

# ============================================================
# PRIVATE / INTERNAL IP CHECK
# ============================================================

def is_private_ip(
    ip_address
):

    try:

        ip = ipaddress.ip_address(
            ip_address
        )

        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )

    except ValueError:

        return True


# ============================================================
# HOSTNAME SAFETY
# ============================================================

def is_safe_hostname(
    hostname
):

    if not hostname:

        return False

    hostname = hostname.strip().lower()

    if hostname == "localhost":

        return False

    # --------------------------------------------------------
    # DIRECT IP ADDRESS
    # --------------------------------------------------------

    try:

        ip = ipaddress.ip_address(
            hostname
        )

        return not is_private_ip(
            str(ip)
        )

    except ValueError:

        pass

    # --------------------------------------------------------
    # RESOLVE HOSTNAME
    # --------------------------------------------------------

    try:

        addresses = socket.getaddrinfo(
            hostname,
            None
        )

    except Exception:

        return False

    if not addresses:

        return False

    for address in addresses:

        ip_address = address[4][0]

        if is_private_ip(
            ip_address
        ):

            return False

    return True


# ============================================================
# IGNORED DOMAIN CHECK
# ============================================================

def is_ignored_domain(
    url
):

    domain = normalize_domain(
        url
    )

    if not domain:

        return True

    for ignored in (
        IGNORED_DOMAINS
    ):

        if (
            domain == ignored
            or domain.endswith(
                "." + ignored
            )
        ):

            return True

    return False


# ============================================================
# URL SAFETY
# ============================================================

def is_safe_url(
    url
):

    try:

        parsed = urlparse(
            url
        )

        if parsed.scheme not in (
            "http",
            "https"
        ):

            return False

        hostname = parsed.hostname

        if not hostname:

            return False

        return is_safe_hostname(
            hostname
        )

    except Exception:

        return False


# ============================================================
# CLEAN PROJECT NAME
# ============================================================

def clean_project_name(
    name
):

    if not name:

        return ""

    text = str(
        name
    ).strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ============================================================
# FETCH PAGE
# ============================================================

def fetch_page(
    url
):
    # --------------------------------------------------------
    # BASIC URL CHECK
    # --------------------------------------------------------
    if not url:
        return None

    # --------------------------------------------------------
    # URL SHORTENERS
    #
    # Shortened URLs are external redirects and are not
    # reliable evidence of official project ownership.
    # Skip them quietly.
    # --------------------------------------------------------
    domain = normalize_domain(url)

    url_shorteners = {
        "bit.ly",
        "t.co",
        "tinyurl.com",
        "ow.ly",
        "is.gd",
        "buff.ly",
        "cutt.ly",
        "shorturl.at",
    }

    if domain in url_shorteners:
        print(
            f"⏭️ Skipping URL shortener: {url}"
        )
        return None

    # --------------------------------------------------------
    # URL SAFETY
    # --------------------------------------------------------
    if not is_safe_url(url):
        print(
            f"⚠️ Unsafe URL blocked: {url}"
        )
        return None

    request = Request(
        url,
        headers={
            "User-Agent":
                (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; "
                    "Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/120 Safari/537.36"
                )
        }
    )

    try:
        with urlopen(
            request,
            timeout=REQUEST_TIMEOUT
        ) as response:

            final_url = response.geturl()

            # ------------------------------------------------
            # REDIRECT SAFETY
            # ------------------------------------------------
            if not is_safe_url(final_url):
                print(
                    "⚠️ Unsafe redirect blocked:"
                )
                print(final_url)
                return None

            content = (
                response.read()
                .decode(
                    "utf-8",
                    errors="ignore"
                )
            )

            return {
                "content": content,
                "final_url": final_url
            }

    except HTTPError as error:

        # ----------------------------------------------------
        # EXPECTED DEAD / UNAVAILABLE PAGE
        # ----------------------------------------------------
        if error.code == 404:
            print(
                f"⏭️ Page not found (404): {url}"
            )
            return None

        # ----------------------------------------------------
        # ACCESS DENIED
        # ----------------------------------------------------
        if error.code in (401, 403):
            print(
                f"⏭️ Page access denied "
                f"({error.code}): {url}"
            )
            return None

        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------
        if error.code == 429:
            print(
                f"⏳ Page rate limited (429): {url}"
            )
            return None

        # ----------------------------------------------------
        # OTHER HTTP ERRORS
        # ----------------------------------------------------
        print(
            f"⚠️ HTTP error "
            f"{error.code}: {url}"
        )
        return None

    except URLError as error:

        print(
            f"⏭️ URL unavailable: {url}"
        )

        return None

    except socket.timeout:

        print(
            f"⏱️ Page request timed out: {url}"
        )

        return None

    except Exception as error:

        print(
            f"⚠️ Page error: {error}"
        )

        return None


# ============================================================
# FIND PROJECT LINKS
# ============================================================

def find_project_links(
    base_url,
    links,
    project_name
):

    candidates = []

    for link in links:

        raw_url = link.get(
            "url",
            ""
        )

        if not raw_url:

            continue

        absolute_url = urljoin(
            base_url,
            raw_url
        )

        if not is_safe_url(
            absolute_url
        ):

            continue

        if is_ignored_domain(
            absolute_url
        ):

            continue

        text = link.get(
            "text",
            ""
        ).lower()

        domain = normalize_domain(
            absolute_url
        ).lower()

        # ----------------------------------------------------
        # PROJECT OWNERSHIP
        # ----------------------------------------------------

        project_owned = (
            is_project_owned_domain(
                absolute_url,
                project_name
            )
        )

        score = 0

        # ----------------------------------------------------
        # PROJECT DOMAIN = MAJOR SIGNAL
        # ----------------------------------------------------

        if project_owned:

            score += 10

        # ----------------------------------------------------
        # PROJECT NAME IN LINK TEXT
        # ----------------------------------------------------

        project_words = get_project_words(
            project_name
        )

        for word in project_words:

            if word in text:

                score += 2

        # ----------------------------------------------------
        # RELEVANT LINK KEYWORDS
        # ----------------------------------------------------

        relevant_words = [
            "official",
            "website",
            "app",
            "docs",
            "claim",
            "airdrop",
            "token",
            "network",
            "protocol",
            "campaign",
            "quest",
            "rewards",
        ]

        for keyword in relevant_words:

            if keyword in text:

                score += 1

        # ----------------------------------------------------
        # ONLY KEEP MEANINGFUL CANDIDATES
        # ----------------------------------------------------

        if score > 0:

            candidates.append({
                "url": absolute_url,
                "score": score,
                "text": link.get(
                    "text",
                    ""
                ),
                "project_owned":
                    project_owned,
                "domain":
                    domain,
            })

    candidates.sort(
        key=lambda item:
        item["score"],
        reverse=True
    )

    return candidates


# ============================================================
# CHECK LINK
# ============================================================

def check_link(
    url
):

    result = fetch_page(
        url
    )

    if not result:

        return False

    return True


# ============================================================
# CHECK SUSPICIOUS CONTENT
# ============================================================

def find_warnings(
    content
):

    if not content:

        return []

    text = re.sub(
        r"<[^>]+>",
        " ",
        content
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    ).lower()

    warnings = []

    for phrase in (
        SUSPICIOUS_PHRASES
    ):

        if phrase in text:

            warnings.append(
                phrase
            )

    return warnings


# ============================================================
# EXTRACT URLS FROM STORED DATA
# ============================================================

def extract_urls_from_text(
    text
):

    if not text:

        return []

    urls = re.findall(
        r'https?://[^\s<>"\']+',
        str(text)
    )

    cleaned = []

    for url in urls:

        url = url.rstrip(
            ".,);]}"
        )

        if not url:

            continue

        if not is_safe_url(
            url
        ):

            continue

        if is_ignored_domain(
            url
        ):

            continue

        if url not in cleaned:

            cleaned.append(
                url
            )

    return cleaned


# ============================================================
# FIND STORED PROJECT LINKS
# ============================================================

def find_stored_project_links(
    airdrop
):

    stored_links = []

    fields = [
        airdrop.get(
            "description",
            ""
        ),
        airdrop.get(
            "official_links",
            ""
        ),
        airdrop.get(
            "links",
            ""
        ),
    ]

    for field in fields:

        if isinstance(
            field,
            list
        ):

            for item in field:

                stored_links.extend(
                    extract_urls_from_text(
                        item
                    )
                )

        else:

            stored_links.extend(
                extract_urls_from_text(
                    field
                )
            )

    unique_links = []

    for link in stored_links:

        if link not in unique_links:

            unique_links.append(
                link
            )

    return unique_links[:10]


# ============================================================
# FILTER STORED PROJECT LINKS
# ============================================================

def filter_stored_project_links(
    links,
    project_name
):

    project_links = []

    for link in links:

        if is_project_owned_domain(
            link,
            project_name
        ):

            project_links.append(
                link
            )

    return project_links


# ============================================================
# PROJECT INTELLIGENCE
# ============================================================

def get_intelligence(
    name
):

    print(
        f"🪙 Checking project "
        f"intelligence: {name}"
    )

    result = {
        "market_signal": {},
        "defi_signal": {},
        "intelligence_status":
            "unavailable",
    }

    try:

        intelligence = (
            get_project_intelligence(
                name
            )
        )

        if not isinstance(
            intelligence,
            dict
        ):

            print(
                "⚠️ Intelligence "
                "returned invalid data."
            )

            return result

        result[
            "market_signal"
        ] = intelligence.get(
            "market_signal",
            {}
        )

        result[
            "defi_signal"
        ] = intelligence.get(
            "defi_signal",
            {}
        )

        market = result[
            "market_signal"
        ]

        defi = result[
            "defi_signal"
        ]

        market_available = (
            isinstance(
                market,
                dict
            )
            and (
                "error" not in market
                or market.get(
                    "found",
                    False
                )
            )
        )

        defi_available = (
            isinstance(
                defi,
                dict
            )
            and (
                "error" not in defi
                or defi.get(
                    "found",
                    False
                )
            )
        )

        if (
            market_available
            or defi_available
        ):

            result[
                "intelligence_status"
            ] = "available"

    except Exception as error:

        print(
            f"⚠️ Intelligence check "
            f"failed: {error}"
        )

    return result


# ============================================================
# WEBSITE INSPECTION
# ============================================================

def inspect_candidate(
    airdrop
):

    # --------------------------------------------------------
    # BASIC CANDIDATE DATA
    # --------------------------------------------------------

    name = clean_project_name(
        airdrop.get(
            "name",
            "Unknown"
        )
    )

    candidate_url = (
        airdrop.get(
            "url",
            ""
        )
    )

    description = (
        airdrop.get(
            "description",
            ""
        )
    )

    source = (
        airdrop.get(
            "source",
            ""
        )
    )

    result = {

        "name":
            name,

        "url":
            candidate_url,

        "description":
            description,

        "source":
            source,

        # ----------------------------------------------------
        # VERIFICATION
        # ----------------------------------------------------

        "official_links":
            [],

        "warnings":
            [],

        "basic_checks_passed":
            False,

        "verification_level":
            "unknown",

        "verification_status":
            "unavailable",

        "verification_available":
            False,

        "verified":
            False,

        "source_access":
            "unknown",

        # ----------------------------------------------------
        # PROJECT DOMAIN EVIDENCE
        # ----------------------------------------------------

        "project_domains":
            [],

        "external_links":
            [],

        # ----------------------------------------------------
        # INTELLIGENCE
        # ----------------------------------------------------

        "market_signal":
            {},

        "defi_signal":
            {},

        "market_status":
            "unavailable",

        "defi_status":
            "unavailable",

        "intelligence_status":
            "unavailable",
    }

    # ========================================================
    # STORED LINKS
    # ========================================================

    stored_links = (
        find_stored_project_links(
            airdrop
        )
    )

    stored_project_links = (
        filter_stored_project_links(
            stored_links,
            name
        )
    )

    # Only treat project-owned domains
    # as official links.

    for link in stored_project_links:

        if link not in result[
            "official_links"
        ]:

            result[
                "official_links"
            ].append(
                link
            )

    # ========================================================
    # CANDIDATE PAGE
    # ========================================================

    page = fetch_page(
        candidate_url
    )

    page_unreachable = (
        page is None
    )

    # ========================================================
    # PAGE UNAVAILABLE
    # ========================================================

    if page_unreachable:

        result[
            "source_access"
        ] = "unavailable"

        result[
            "verification_status"
        ] = "unavailable"

        result[
            "verification_available"
        ] = False

        result[
            "verification_level"
        ] = "source_unavailable"

        print(
            "⚠️ Candidate page "
            "unreachable."
        )

        print(
            "➡️ Source unavailable "
            "does not mean scam."
        )

        print(
            "➡️ Continuing with "
            "stored candidate data."
        )

    # ========================================================
    # PAGE AVAILABLE
    # ========================================================

    else:

        result[
            "source_access"
        ] = "available"

        result[
            "verification_available"
        ] = True

        content = page[
            "content"
        ]

        final_url = page[
            "final_url"
        ]

        # ----------------------------------------------------
        # WARNINGS
        # ----------------------------------------------------

        warnings = find_warnings(
            content
        )

        result[
            "warnings"
        ].extend(
            warnings
        )

        # ----------------------------------------------------
        # PARSE LINKS
        # ----------------------------------------------------

        parser = PageParser()

        try:

            parser.feed(
                content
            )

        except Exception as error:

            print(
                f"⚠️ HTML parsing "
                f"issue: {error}"
            )

        links = parser.links

        # ----------------------------------------------------
        # PROJECT LINKS
        # ----------------------------------------------------

        possible_links = (
            find_project_links(
                final_url,
                links,
                name
            )
        )

        reachable_project_links = 0

        unreachable_project_links = 0

        checked_domains = set()

        for item in possible_links:

            link_url = item[
                "url"
            ]

            domain = normalize_domain(
                link_url
            )

            if domain in checked_domains:

                continue

            checked_domains.add(
                domain
            )

            reachable = check_link(
                link_url
            )

            # ------------------------------------------------
            # PROJECT-OWNED LINK
            # ------------------------------------------------

            if item.get(
                "project_owned",
                False
            ):

                if reachable:

                    reachable_project_links += 1

                    if link_url not in result[
                        "official_links"
                    ]:

                        result[
                            "official_links"
                        ].append(
                            link_url
                        )

                else:

                    unreachable_project_links += 1

            # ------------------------------------------------
            # EXTERNAL LINK
            #
            # Useful for campaign discovery,
            # but NOT proof of ownership.
            # ------------------------------------------------

            else:

                if reachable:

                    if link_url not in result[
                        "external_links"
                    ]:

                        result[
                            "external_links"
                        ].append(
                            link_url
                        )

            # ------------------------------------------------
            # KEEP OUTPUT CLEAN
            # ------------------------------------------------

            if (
                len(
                    result[
                        "official_links"
                    ]
                ) >= 5
            ):

                break

        # ----------------------------------------------------
        # PROJECT DOMAIN EVIDENCE
        # ----------------------------------------------------

        for link in result[
            "official_links"
        ]:

            domain = normalize_domain(
                link
            )

            if (
                domain
                and domain not in result[
                    "project_domains"
                ]
            ):

                result[
                    "project_domains"
                ].append(
                    domain
                )

        # ----------------------------------------------------
        # VERIFICATION STATE
        # ----------------------------------------------------

        if (
            not result[
                "warnings"
            ]
            and reachable_project_links >= 1
        ):

            result[
                "verification_level"
            ] = "strong_signals"

            result[
                "verification_status"
            ] = "verified"

        elif (
            not result[
                "warnings"
            ]
            and (
                len(
                    result[
                        "official_links"
                    ]
                ) >= 1
                or unreachable_project_links >= 1
            )
        ):

            result[
                "verification_level"
            ] = "some_signals"

            result[
                "verification_status"
            ] = "available"

        elif not result[
            "warnings"
        ]:

            result[
                "verification_level"
            ] = "no_warnings"

            result[
                "verification_status"
            ] = "available"

        else:

            result[
                "verification_level"
            ] = "warnings_found"

            result[
                "verification_status"
            ] = "failed"

    # ========================================================
    # BASIC VERIFICATION
    # ========================================================

    if page_unreachable:

        result[
            "basic_checks_passed"
        ] = False

        result[
            "verified"
        ] = False

    else:

        result[
            "basic_checks_passed"
        ] = (
            len(
                result[
                    "warnings"
                ]
            ) == 0
            and bool(
                candidate_url
            )
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # A candidate is verified ONLY when we have:
        #
        # 1. No suspicious warnings
        # 2. A reachable project-owned domain
        #
        # Intelligence does NOT establish verification.
        # ----------------------------------------------------

        result[
            "verified"
        ] = (
            result[
                "basic_checks_passed"
            ]
            and result[
                "verification_status"
            ] == "verified"
            and len(
                result[
                    "project_domains"
                ]
            ) >= 1
        )

    # ========================================================
    # PROJECT INTELLIGENCE
    # ========================================================

    intelligence = get_intelligence(
        name
    )

    result[
        "market_signal"
    ] = intelligence.get(
        "market_signal",
        {}
    )

    result[
        "defi_signal"
    ] = intelligence.get(
        "defi_signal",
        {}
    )

    result[
        "intelligence_status"
    ] = intelligence.get(
        "intelligence_status",
        "unavailable"
    )

    # ========================================================
    # MARKET STATUS
    # ========================================================

    market = result[
        "market_signal"
    ]

    if isinstance(
        market,
        dict
    ):

        if market.get(
            "found",
            False
        ):

            result[
                "market_status"
            ] = "available"

        elif market.get(
            "error"
        ):

            result[
                "market_status"
            ] = "unavailable"

        else:

            result[
                "market_status"
            ] = "checked_no_match"

    # ========================================================
    # DEFI STATUS
    # ========================================================

    defi = result[
        "defi_signal"
    ]

    if isinstance(
        defi,
        dict
    ):

        if defi.get(
            "found",
            False
        ):

            result[
                "defi_status"
            ] = "available"

        elif defi.get(
            "error"
        ):

            result[
                "defi_status"
            ] = "unavailable"

        else:

            result[
                "defi_status"
            ] = "checked_no_match"

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return result


# ============================================================
# PUBLIC VERIFIER FUNCTION
# ============================================================

def verify_candidate(
    airdrop
):

    return inspect_candidate(
        airdrop
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "🔎 Testing AirdropRadar "
        "verifier v10...\n"
    )

    test_airdrop = {

        "name":
            "Bitcoin",

        "url":
            "https://example.com",

        "description":
            "Bitcoin airdrop test",

        "source":
            "test"
    }

    result = verify_candidate(
        test_airdrop
    )

    print(
        "\n🪂 "
        f"{result['name']}"
    )

    print(
        f"🔗 "
        f"{result['url']}"
    )

    print(
        f"🛡️ Basic checks passed: "
        f"{result['basic_checks_passed']}"
    )

    print(
        f"📊 Verification level: "
        f"{result['verification_level']}"
    )

    print(
        f"📌 Verification status: "
        f"{result['verification_status']}"
    )

    print(
        f"🌐 Source access: "
        f"{result['source_access']}"
    )

    print(
        f"🔎 Verification available: "
        f"{result['verification_available']}"
    )

    print(
        f"🛡️ Verified: "
        f"{result['verified']}"
    )

    print(
        f"🧠 Intelligence status: "
        f"{result['intelligence_status']}"
    )

    # ========================================================
    # MARKET SIGNAL
    # ========================================================

    market = result[
        "market_signal"
    ]

    if market.get(
        "found",
        False
    ):

        print(
            "\n🪙 CoinGecko market signal:"
        )

        print(
            f"✅ Project: "
            f"{market.get('name', '')}"
        )

        print(
            f"🔤 Symbol: "
            f"{market.get('symbol', '')}"
        )

        print(
            f"🎯 Match score: "
            f"{market.get('match_score', 0)}%"
        )

        print(
            f"📊 Market rank: "
            f"{market.get('market_rank')}"
        )

    elif (
        result[
            "market_status"
        ] == "unavailable"
    ):

        print(
            "\n🪙 CoinGecko:"
            " Unavailable."
        )

    else:

        print(
            "\n🪙 CoinGecko:"
            " Checked — no match."
        )

    # ========================================================
    # DEFI SIGNAL
    # ========================================================

    defi = result[
        "defi_signal"
    ]

    if defi.get(
        "found",
        False
    ):

        print(
            "\n🧩 DeFiLlama signal:"
        )

        print(
            f"✅ Protocol: "
            f"{defi.get('protocol', '')}"
        )

        print(
            f"🎯 Match score: "
            f"{defi.get('match_score', 0)}%"
        )

        print(
            f"💰 TVL: "
            f"{defi.get('tvl', 0)}"
        )

    elif (
        result[
            "defi_status"
        ] == "unavailable"
    ):

        print(
            "\n🧩 DeFiLlama:"
            " Unavailable."
        )

    else:

        print(
            "\n🧩 DeFiLlama:"
            " Checked — no protocol match."
        )

    # ========================================================
    # PROJECT DOMAINS
    # ========================================================

    print(
        "\n🏠 Project-owned domains:"
    )

    for domain in result[
        "project_domains"
    ]:

        print(
            f"✅ {domain}"
        )

    if not result[
        "project_domains"
    ]:

        print(
            "❌ No project-owned "
            "domains detected."
        )

    # ========================================================
    # PROJECT LINKS
    # ========================================================

    print(
        "\n🌐 Official project links:"
    )

    for link in result[
        "official_links"
    ]:

        print(
            f"✅ {link}"
        )

    if not result[
        "official_links"
    ]:

        print(
            "❌ No project links detected."
        )

    # ========================================================
    # EXTERNAL LINKS
    # ========================================================

    print(
        "\n🔗 External campaign links:"
    )

    for link in result[
        "external_links"
    ][:5]:

        print(
            f"• {link}"
        )

    if not result[
        "external_links"
    ]:

        print(
            "None detected."
        )

    # ========================================================
    # WARNINGS
    # ========================================================

    print(
        "\n⚠️ Warnings:"
    )

    if result[
        "warnings"
    ]:

        for warning in result[
            "warnings"
        ]:

            print(
                f"🚨 {warning}"
            )

    else:

        print(
            "✅ No suspicious "
            "content detected."
        )