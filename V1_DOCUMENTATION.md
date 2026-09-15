# 🪂 AirdropRadar V1 Documentation

## 1. Project Overview

AirdropRadar is a Telegram-based crypto airdrop discovery and analysis system.

Its purpose is to:

- Discover potential airdrop opportunities.
- Filter irrelevant discoveries.
- Classify opportunities by their primary participation mechanism.
- Verify available project information.
- Score opportunities.
- Store results in SQLite.
- Monitor stored opportunities for meaningful changes.
- Track historical changes.
- Alert Telegram subscribers.
- Allow users to browse and inspect stored opportunities.

AirdropRadar V1 focuses on building a reliable foundation before adding more advanced functionality.

---

# 2. V1 Processing Pipeline

The V1 pipeline is:

DISCOVER
↓
QUALIFY
↓
CLASSIFY
↓
VERIFY
↓
SCORE
↓
STORE
↓
MONITOR
↓
HISTORY
↓
ALERT
↓
SUBSCRIPTIONS
↓
TELEGRAM INTERFACE

---

# 3. Core Components

## bot.py

Main Telegram bot application.

Responsibilities include:

- Telegram command handling.
- Inline button handling.
- Airdrop browsing.
- Airdrop details.
- Subscriber management.
- Discovery alerts.
- Monitoring alerts.
- Automatic scanning.
- Automatic monitoring.
- Telegram application startup.

Main commands:

- `/start`
- `/help`
- `/airdrop`
- `/latest`
- `/status`
- `/check`
- `/subscribe`
- `/unsubscribe`

---

## config.py

Central application configuration.

Responsibilities:

- Load `.env`.
- Configure database location.
- Configure alert threshold.
- Configure scan interval.
- Define RSS discovery sources.
- Validate the Telegram bot token.

Current defaults:

- Alert threshold: `60`
- Scan interval: `1800` seconds
- Database: `airdrops.db`

---

## scanner.py

Discovery support component.

Used for discovering potential opportunities from configured sources.

---

## filter.py

Main discovery and classification pipeline.

Responsibilities include:

- Running the live scan.
- Qualification/filtering.
- Classification.
- Producing classified airdrop candidates.

Current classifier version:

`2.12.6`

Classifier entry point:

`run_live_classification()`

---

# 4. Airdrop Categories

AirdropRadar V1 uses eight categories:

1. Retroactive
2. Holder
3. Bounty
4. Testnet
5. Points
6. Liquidity
7. Activity
8. Other

The classifier is designed to identify the:

> PRIMARY participation/reward mechanism

rather than simply matching isolated keywords.

The classifier has been calibrated against reviewed records.

Current calibration status:

- Reviewed records: 35
- Mismatches: 0
- Calibration accuracy: 100%

---

# 5. verifier.py

Verification and project intelligence component.

Responsibilities include:

- Checking source pages.
- Checking URL safety.
- Blocking unsafe URLs.
- Blocking URL shorteners.
- Detecting suspicious content.
- Finding project-owned domains.
- Finding official project links.
- Checking market intelligence.
- Checking DeFi intelligence.
- Producing verification status and verification level.

The verifier also handles unavailable pages without automatically treating them as scams.

---

# 6. api_sources.py

External API intelligence component.

Current integrations:

- CoinGecko
- DeFiLlama

The API layer includes:

- Request timeout handling.
- Retry handling.
- Rate-limit handling.
- HTTP error handling.
- Connection error handling.
- Invalid JSON handling.
- CoinGecko request spacing.

Current API intelligence version:

`v6`

---

# 7. scorer.py

Airdrop scoring component.

The scorer produces a score used by AirdropRadar to determine the quality and alert-worthiness of opportunities.

The Telegram discovery alert threshold is configured through:

`ALERT_THRESHOLD`

Current default:

`60`

---

# 8. database.py

SQLite persistence layer.

Current database:

`airdrops.db`

The database stores:

- Airdrop records.
- Classification.
- Scores.
- Confidence.
- Verification information.
- Official links.
- Warnings.
- Market intelligence.
- DeFi intelligence.
- Monitoring timestamps.
- Previous/current score values.
- Previous/current confidence values.
- Change timestamps.
- Next monitoring timestamps.

Database tables:

- `airdrops`
- `airdrop_history`
- `subscribers`
- `sent_alerts`
- `monitoring_alerts`

---

# 9. Monitoring System

## tracker.py

Monitoring component.

Responsibilities include:

- Re-checking stored opportunities.
- Comparing previous and current scores.
- Comparing confidence.
- Detecting meaningful changes.
- Recording monitoring history.
- Tracking changes over time.

V1 also confirms meaningful changes before sending monitoring alerts.

---

# 10. Alert System

AirdropRadar V1 has two major alert systems.

## Discovery Alerts

Sent when a newly discovered opportunity:

- Meets the alert threshold.
- Has a usable URL.
- Has not already been alerted to that subscriber.

Duplicate protection uses the subscriber and airdrop URL.

---

## Monitoring Alerts

Sent when a previously stored opportunity experiences a meaningful change.

Monitoring alerts include:

- Airdrop name.
- Previous score.
- New score.
- Score difference.
- Confidence changes.
- Detected changes.
- Airdrop link.

Monitoring alert history prevents the same monitoring event from being repeatedly sent.

---

# 11. Telegram Subscription System

Users can subscribe with:

`/subscribe`

Users can unsubscribe with:

`/unsubscribe`

Subscription status can be checked through:

`/status`

Subscribers receive automatic alert-worthy discoveries and monitoring alerts.

---

# 12. Category Browser

The Telegram bot provides an interactive category browser.

Users can:

- Browse all airdrops.
- Browse by category.
- Move between pages.
- Open individual airdrop details.
- Return to the category menu.

Pagination currently displays up to 10 airdrops per page.

---

# 13. Airdrop Details

Each stored opportunity can display:

- Name.
- Category.
- Description.
- Score.
- Confidence.
- Verification level.
- Market signal.
- DeFi signal.
- Warnings.
- Official project links.
- Discovery source.

A warning is displayed to users that AirdropRadar does not guarantee legitimacy, eligibility, or payment.

---

# 14. Automatic Jobs

AirdropRadar V1 runs two major automatic jobs.

## Automatic Scanning

The bot automatically scans configured discovery sources according to:

`SCAN_INTERVAL`

Current default:

`1800 seconds`

---

## Automatic Monitoring

Stored opportunities are automatically checked for meaningful changes.

Current monitoring interval:

`3600 seconds`

---

# 15. Current Database State

At the latest V1 integrity check:

- Total airdrops: 114
- High confidence: 27
- Medium confidence: 53
- Low confidence: 34
- Subscribers: 1
- Sent discovery alerts: 28
- Monitoring alerts: 17
- Tracked airdrops: 45
- Detected changes: 32

Current category counts:

- Points: 34
- Testnet: 15
- Retroactive: 0
- Bounty: 2
- Holder: 1
- Liquidity: 16
- Activity: 41
- Other: 5

---

# 16. V1 Health Status

A dedicated health check is available through:

`health_check.py`

Latest health check:

- Database: PASS
- Classifier: PASS
- Verifier: PASS
- API intelligence: PASS
- Tracker: PASS
- Discovery scanner: PASS
- Telegram configuration: PASS

Total:

`7/7 PASSED`

Overall:

`AirdropRadar V1 system health: HEALTHY`

---

# 17. Requirements

Current Python dependencies:

- `python-dotenv>=1.0.0`
- `feedparser>=6.0.0`
- `python-telegram-bot[job-queue]>=21.0`

---

# 18. Environment Configuration

Secrets are stored in:

`.env`

The repository should never contain the real Telegram bot token.

`.env.example` provides the configuration template.

---

# 19. Starting AirdropRadar

From the project directory:

```powershell
python bot.py
