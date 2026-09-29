# 🪂 AirdropRadar V1.1 Documentation

## 1. Project Overview

AirdropRadar is a Telegram-based crypto airdrop intelligence system.

Its purpose is to discover, qualify, classify, verify, score, store, monitor, and explain potential airdrop opportunities.


---

## 2. V1.1 Processing Pipeline

The main processing flow is:

DISCOVER → QUALIFY → CLASSIFY → VERIFY → PARTICIPATION → LIFECYCLE → RISK → SCORE → STORE → MONITOR → HISTORY → ALERT

Each stage contributes information used by later stages.

Unavailable external data is treated as unavailable evidence rather than automatically interpreted as proof of fraud.

---

## 3. Production Components

### bot.py

Telegram interface and user interaction layer.

Responsibilities include:

- Telegram commands.
- Inline keyboards.
- Opportunity browsing.
- Opportunity analysis views.
- My Radar.
- Alert Controls.
- Subscriber management.
- Scan commands.
- Status reporting.

### config.py

Central configuration and environment settings. Sensitive credentials are loaded from environment variables and must not be stored in tracked source files.

### scanner.py

Discovery and scanning layer. Collects candidate opportunities and passes discovered data into the processing pipeline.

### filter.py

Qualification and classification layer. Handles filtering, classification, participation-based category detection, risk integration, verification integration, and scoring integration.

Current classifier version: 2.12.6

Current reviewed calibration:

- Reviewed records: 35
- Mismatches: 0
- Accuracy: 100%

### qualifier.py

Determines whether discovered items meet qualification requirements for further processing.

### verifier.py

Handles verification and evidence collection for discovered opportunities.

### api_sources.py

Provides external API and source integrations used for intelligence signals. Sources may become unavailable, rate-limited, or time out.

### intelligence.py

Provides intelligence used by the scoring and monitoring pipeline.

### scorer.py

Calculates opportunity scores and confidence using available verification, market, DeFi, warning, evidence, and risk signals.

Scores are intelligence signals and are not guarantees.

### database.py

SQLite persistence layer. Stores discovered opportunities and V1.1 intelligence fields, including risk and monitoring information. SQLite foreign-key support is enabled.

### tracker.py

Handles tracking and monitoring of stored opportunities and preserves relevant historical information.

### lifecycle.py

Determines lifecycle state. Supported states include Upcoming, Active, Ending Soon, Ended, and Unknown.

Unknown is used when available evidence is insufficient to determine lifecycle reliably.

### participation.py

Analyzes participation requirements and produces structured intelligence for the Tasks view, including tasks, requirements, estimated time, estimated cost, and difficulty.

These values are estimates and are not guarantees.

### risk_intelligence.py

Analyzes evidence-based risk signals including verification availability, source accessibility, official-source presence, and other warning indicators.

A detected risk signal does not automatically mean an opportunity is a scam.


---

## 4. Opportunity Categories

AirdropRadar currently supports these primary categories:

- 🎯 Points
- 🧪 Testnet
- 🔄 Retroactive
- 🏆 Bounty
- 👑 Holder
- 💧 Liquidity
- 🔗 Activity
- 📦 Other

Classification is based on the detected participation mechanism and classifier rules.

---

## 5. Telegram Commands

The production Telegram command menu includes:

### /start

Displays the AirdropRadar welcome interface and main navigation.

### /airdrop

Opens the category browser for available opportunities.

### /latest

Displays the newest stored opportunities.

### /help

Displays available commands and basic usage information.

### /subscribe

Subscribes the Telegram user to supported alerts.

### /unsubscribe

Removes the Telegram user from alert subscriptions.

### /status

Displays system and database status information.

### /check

Runs a scan and processing cycle.

---

## 6. Opportunity Analysis

An opportunity can expose several intelligence views.

### 📊 Overview

Provides the main opportunity summary, including:

- Opportunity type.
- Score.
- Confidence.
- Verification.
- Risk.
- Lifecycle.
- Market information.
- DeFi information.
- Warnings.
- Source.
- Opportunity link.

### Tasks

Shows detected participation requirements and estimated effort.

### Evidence

Shows evidence AirdropRadar was able to detect or verify, including verification state, discovery source, and official links when detected.

Evidence describes what the system could verify or detect. It does not guarantee legitimacy.

### Risk

Displays risk level and detected risk signals. Risk intelligence is evidence-based and is not a definitive scam verdict.

### Score

Displays:

- Score out of 100.
- Score band.
- Confidence.
- Verification signal.
- Market signal.
- DeFi signal.
- Risk factor.
- Score explanation.


---

## 7. My Radar

My Radar allows users to track individual opportunities.

Users can:

- Track an opportunity.
- View tracked opportunities.
- Open tracked opportunity analysis.
- Untrack opportunities.

Tracked opportunities are stored so monitoring can identify meaningful changes.

---

## 8. Alert Controls

Users can control supported notification settings through the Alert Controls interface.

Alert settings are handled independently from opportunity browsing and analysis.

---

## 9. Monitoring and Alerts

AirdropRadar monitors stored opportunities for meaningful changes.

Monitoring can consider signals such as:

- Score changes.
- TVL changes.
- Market-rank changes.
- Market or DeFi disappearance.
- Other tracked intelligence changes.

Historical snapshots help prevent a single temporary source problem from being treated as a confirmed disappearance when confirmation is required.

The system distinguishes unavailable external data from confirmed negative evidence.

---

## 10. Current Database State

Current database snapshot:

- Total discoveries: 129
- High confidence: 14
- Medium confidence: 99
- Low confidence: 16
- Subscribers: 0

Current category distribution:

- Activity: 46
- Bounty: 2
- Holder: 3
- Liquidity: 16
- Other: 5
- Points: 39
- Retroactive: 0
- Testnet: 18

These values represent the database state at the time this documentation was prepared and will change as new scans are performed.


---

## 11. Testing and Hardening

V1.1 automated testing currently passes:

42 passed in 21.72s

Test collection:

42 tests collected

Production module compilation passes for:

- bot.py
- database.py
- filter.py
- scanner.py
- scorer.py
- tracker.py
- lifecycle.py
- participation.py
- risk_intelligence.py

V1.1 integration testing covered:

- /start
- /airdrop
- Category browsing
- Opportunity analysis
- Overview
- Tasks
- Evidence
- Risk
- Score
- My Radar
- Track
- Untrack
- Alert Controls
- /latest
- /status
- /check
- /subscribe
- /unsubscribe
- /help

---

## 12. UTF-8 and Emoji Repair

The Telegram bot previously contained UTF-8 mojibake caused by incorrectly decoded emoji characters.

The repaired bot file was tested for common mojibake markers.

Result:

Remaining mojibake markers: 0

Syntax check: PASS

The repaired bot was subsequently run and verified successfully.

All new documentation should remain UTF-8 encoded.

---

## 13. Environment and Secrets

Sensitive configuration must remain in .env.

The real Telegram bot token must never be:

- Written into Python source code.
- Added to documentation.
- Committed to Git.
- Posted publicly.

.env is excluded from Git tracking.

Before the final V1.1 push and freeze:

1. Restore the real Telegram bot token in local .env.
2. Run a final real-token Telegram smoke test.
3. Run the final automated test suite.
4. Confirm .env and the real token are not staged.
5. Confirm the working tree and commit contain no secrets.
6. Only then push and freeze V1.1.

---

## 14. Git Checkpoint

The current hardening checkpoint is:

9050b92 AirdropRadar V1.1 hardening checkpoint

The checkpoint contains the V1.1 production changes and hardening work.

At the time of documentation preparation, the working tree had been clean after the checkpoint commit.

Development backup files and temporary scripts are excluded from the production Git checkpoint.

---

## 15. V1.1 Development Status

V1.1 implementation and hardening work is substantially complete.

Completed areas include:

- Risk Intelligence.
- UTF-8/emoji repair.
- Alert Controls.
- My Radar tracking.
- Database support.
- Existing V1 compatibility.
- Telegram command flows.
- Opportunity analysis views.
- Integration testing.
- Hardening test suite.

Documentation is the current V1.1 completion step.

---

## 16. Important Intelligence Principles

AirdropRadar provides intelligence, not guarantees.

Important principles:

1. A missing source does not automatically mean a scam.
2. A detected risk signal does not automatically mean a scam.
3. Verification describes what the system could confirm.
4. Scores are intelligence signals, not guarantees.
5. Participation estimates are estimates, not guarantees.
6. Lifecycle states depend on available evidence.
7. External APIs can fail, timeout, or rate-limit requests.
8. Historical evidence can be used to confirm meaningful changes.
9. Users should review available evidence before acting on an opportunity.

---

## 17. Requirements

The project dependencies are listed in:


requirements.txt

The environment must have the required Python dependencies installed before running the bot or test suite.

---

## 18. Running AirdropRadar

From the project directory:

`powershell
python bot.py
`

For automated tests:

`powershell
python -m pytest -q
`

For production module compilation:

`powershell
python -m py_compile bot.py database.py filter.py scanner.py scorer.py tracker.py lifecycle.py participation.py risk_intelligence.py
`

---

## 19. V1.1 Finalization Rule

AirdropRadar V1.1 follows this completion sequence:

BUILD → TEST → INTEGRATE → VERIFY → DOCUMENT → CHECKPOINT → FINAL SMOKE TEST → FREEZE

The final freeze should only happen after the real Telegram token has been restored locally, the final Telegram smoke test passes, automated tests pass, secrets are confirmed absent from Git, and the final production state is verified.

---

**AirdropRadar V1.1 — Documentation**
