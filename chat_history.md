# Chat History Summary - Crypto Intelligence Bot Development

**Date:** Friday, May 15, 2026

## 1. Initial Analysis
- Identified the workspace as a Python-based LINE bot that scrapes financial news, summarizes it using Google Gemini (Thai language), and sends it to a LINE user.
- Discovered the automation was originally designed for GitHub Actions.

## 2. Security & Environment Setup
- **Credential Protection:** Configured the bot to use environment variables for `GROQ_API_KEY`, `LINE_ACCESS_TOKEN`, and `LINE_USER_ID`.
- **Git Security:** Created a `.gitignore` file to ensure secrets and virtual environments are never committed.
- **Dependency Management:** Added `groq`, `python-dotenv`, and `tenacity` to `requirements.txt`.

## 3. GitHub Integration & Automation
- **Workflow Restoration:** Recreated the `.github/workflows/schedule.yml` file to enable automated runs via GitHub Actions.
- **Secret Management:** Guided the setup of GitHub Repository Secrets to ensure secure operation in the cloud.
- **Stability Fix:** Removed all "Git push" and "history saving" logic from the bot to prevent repository conflicts during automated runs.

## 4. SDK Migration & Debugging
- **Initial Gemini Upgrade:** Migrated from `google-generativeai` to the modern `google-genai` library.
- **Rate Limit Protection:** Implemented robust retry logic using the `tenacity` library with exponential backoff to handle API errors and 429 (Quota) spikes gracefully.

## 5. News Source Refinement
- **Multi-Source Aggregation:** Configured the bot to aggregate news from high-authority sources:
    - **Federal Reserve** (Official Press Releases)
    - **Bureau of Labor Statistics** (CPI & Economic Data)
    - **CoinDesk** (Crypto Specialist)
    - **Cointelegraph** (Crypto Market Trends)

## 6. Provider Migration (Groq)
- **Engine Switch:** Successfully migrated from Google Gemini to the **Groq API** to overcome free-tier quota limitations and achieve faster inference.
- **Advanced Model:** Updated the bot to use **`llama-3.3-70b-versatile`**, one of the most capable models available on Groq.

## 7. Intelligence & Reporting
- **Market Analyst Persona:** Engineered the prompt to act as a "Senior Crypto Market Analyst" focused on high-impact events.
- **Categorized Reporting:** Organized the LINE output into tagged sections:
    - `[📌 Macro & Fed]`
    - `[🏢 Institutional Activity]`
    - `[⚖️ Regulation & Tech]`
- **Sentiment Analysis:** Added Thai-language summaries and specific Bullish/Bearish reasoning for Bitcoin.

## 8. Schedule Optimization
- **Bangkok Alignment:** Updated the trigger schedule to match the user's local timezone (**Bangkok, UTC+7**).
- **Thrice-Daily Routine:** Set automated runs for **06:00 AM, 12:00 PM, and 06:00 PM Bangkok time** to provide regular market updates.

## 9. Maintenance & Compatibility
- **Node.js Deprecation Fix:** Updated GitHub Action environment variables (`ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION`) and action versions to resolve Node.js 20 deprecation warnings and ensure long-term stability.

## 11. Binance Screening Bot Expansion
- **Bot Creation:** Developed a secondary bot (`binance_bot.py`) dedicated to tracking volatile crypto pairs and detecting market reversals.
- **4-Layer State Machine:** Engineered a sophisticated state-driven watchlist:
    - **Gainer L1 (Momentum):** Tracks coins hitting new highs.
    - **Gainer L2 (Recovery):** Monitors coins for a 20% bounce after a 15% drop from highs.
    - **Loser L1 (Bottoming):** Tracks coins hitting new lows.
    - **Loser L2 (Dead Cat):** Monitors for price drops after a 15% bounce from lows.
- **State Persistence (GitHub Gist):** Implemented remote JSON storage via GitHub Gist to maintain coin states (price, high/low, hour count) between hourly GitHub Action runs.

## 12. Connectivity & Reporting
- **Regional API Mirror:** Resolved connectivity issues on GitHub Runners by switching to `data-api.binance.vision` to bypass US regional blocks on standard Binance endpoints.
- **USD Volume Formatting:** Implemented a `format_usd` helper to display market activity in human-readable strings (e.g., $1.20M, $500K, $2.5B).
- **Consolidated Sectional Reports:** Designed a structured LINE message that group coins by their current layer/state with relevant emojis.

## 13. Dual-Bot Architecture & Credential Separation
- **Independent Channels:** Decoupled the News Bot and Binance Bot by assigning them unique LINE access tokens and user IDs.
- **Credential Refactoring:** Updated both bots to use specific environment variables (`NEWS_` and `BINANCE_` prefixes) to prevent notification overlap.
- **Workflow Optimization:** Updated and debugged GitHub Action workflows to map new secrets and ensure the "Run workflow" triggers remain active.

## 14. Final Status (May 16, 2026)
- The workspace now operates as a **Dual-Bot Suite**:
    - **News Bot:** Professional Macro/Crypto intelligence in Thai.
    - **Binance Bot:** High-frequency, stateful price screening and recovery tracking.
- Both systems are fully automated, persistent, and secured with isolated notification channels.
