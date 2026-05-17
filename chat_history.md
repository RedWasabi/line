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

## 14. Trigger Precision (External Cron)
- **Eliminating Delays:** Replaced the unreliable native GitHub `schedule` trigger (which had 2+ hour delays) with `repository_dispatch`.
- **API Integration:** Configured workflows to listen for `trigger-binance` and `trigger-news` events.
- **Precision Control:** Moved scheduling logic to an external provider (cron-job.org) for exact, minute-perfect triggers via the GitHub API.

## 15. Final Status (May 16, 2026)
- The workspace now operates as a **High-Precision Dual-Bot Suite**:
    - **News Bot:** Professional Macro/Crypto intelligence in Thai.
    - **Binance Bot:** High-frequency, stateful price screening and recovery tracking.
- Both systems are fully automated, persistent, secured, and triggered with minute-level accuracy.

**Date:** Sunday, May 17, 2026

## 16. Advanced Price Tracking (Version 2)
- **Logic Evolution:** Transitioned from static current-price snapshots to **"Persistent Session Watermarks"**.
- **Merge-High/Merge-Low:** Updated `binance_bot.py` to continually merge the stored `hp`/`lp` with Binance's **24h High/Low ticker extremes** during every hourly run.
- **Intra-hour Precision:** This ensures that the bot captures "invisible" spikes and dips that occur between hourly runs, providing 100% accurate "Drop %" and "Bounce %" calculations compared to the real chart.
- Time Tracking: Implemented 0d 00h formatting for both total time on watchlist (thc) and L2 delist timers (hc).

## 17. Telegram Migration & UI Enhancement
- **Platform Pivot:** Migrated from LINE to **Telegram Bot API** to bypass the 300-message monthly limit and achieve unlimited free notifications.
- **Workflow Secret Mapping:** Updated GitHub Action YAML files to map new `TELEGRAM_` and `BINANCE_TELEGRAM_` secrets, ensuring secure delivery in the cloud.
- **High-Fidelity UI:** Implemented **HTML Rich-Text formatting**:
    - **Bold Headers** for better visual hierarchy.
    - **Monospaced (Fixed-Width) Fonts** via `<code>` tags for prices to ensure numerical alignment.
    - **Italicized Insights** for sentiment and metadata.
- **Handshake Protocol:** Documented the requirement for the user to initiate a `/start` command with each bot to enable message delivery.

## 18. Algorithm Precision & UI Fixes (Version 2.1)
- **Transition Continuity:** Resolved a logic flaw where coins would disappear from reports for one run during layer transitions (e.g., L1 -> L2). Implemented a two-pass processing model.
- **Dynamic Price Formatting:** Added a smart formatter that automatically increases precision (up to 8 decimals) for low-priced assets like DENT or SHIB, preventing "0.0000" display errors.
- **Live Market context:** Integrated the **Binance 24h Change %** directly into the reports, providing immediate verification that data is fresh even if session-based metrics (Inc/Drop) are stable.
- **Timer Correction:** Fixed the "Delist in" logic to show time remaining (countdown from 72h) rather than time elapsed.

## 19. Trend Crossovers & Quality Control (Version 2.2)
- **Ultimate Reversal (Crossovers):** Implemented logic to allow coins to "cross over" between categories. If a coin in a Loser state becomes a Binance Top Gainer, it is automatically moved to Gainer L1 (and vice versa).
- **Trend Labeling:** Added a visual **🔄 Trend Reversed** tag to the Telegram report to highlight these crossover events.
- **Volume Quality Filter:** Implemented a mandatory **$1,000,000 USD** daily volume threshold. The bot now ignores illiquid "dead" coins, ensuring the Top 10 lists only contain meaningful market movers.
- **Limitless L1 Monitoring:** Confirmed and optimized the L1 layers to track an unlimited number of coins as long as they maintain their primary trend, while keeping the 3-day (72h) cleanup timer strictly for the L2 recovery/dead-cat zones.

## 20. Liquidity Zone Classification (Version 2.3)
- **Visual Liquidity Context:** Added a multi-tier volume classification system to the Telegram reports to help the user identify coins susceptible to manipulation.
- **Emoji-Based Tiering:**
    - 🐟 **Retail:** $1M - $5M USD (High risk of single-whale manipulation).
    - 🐬 **Healthy:** $5M - $20M USD (Sustainable retail/mid-cap activity).
    - 🐳 **Institutional:** >$20M USD (Large market caps, high liquidity).
- **Safety First:** Maintained the strict $1M minimum filter to completely eliminate the "Whale Danger Zone" (<$1M).
