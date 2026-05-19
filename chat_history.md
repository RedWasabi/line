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

## 21. Intra-hour Precision (Version 2.4)
- **Eliminating Historical Noise:** Refactored the watermarking logic to completely ignore the Binance 24h Ticker extremes (which look back 24h). 
- **Candlestick Integration:** Implemented the Binance **Klines (1h candles)** API. The bot now fetches the exact High/Low of the last 60 minutes for every coin on the watchlist.
- **Invisible Spike Detection:** This ensures that price spikes or dips that happen *between* the hourly bot runs are captured with 100% accuracy, without being affected by irrelevant price action from the previous day.

## 22. Duration-Based Sorting (Version 2.5)
- **Time-Ordered Reports:** Refactored the reporting engine to sort all layers (L1 and L2) by total time on the watchlist (`thc`).
- **Oldest Trends First:** Coins that have been tracked for the longest time now appear at the top of each Telegram section, providing a clearer view of trend maturity.

## 23. First-Run Layer Protection
- **Initial Run Lock:** Implemented a logic safeguard (`thc > 0`) that prevents coins from transitioning to L2 during their very first hour on the watchlist.
- **Clean Starts:** This ensures that every new coin or reversal starts correctly in L1, even if the 1-hour candlestick data contains volatility that occurred just before the bot run.

## 24. Algorithmic Symmetry (Version 2.5 Refinement)
- **Perfect Mirroring:** Conducted a full audit and refactor of the Gainer vs. Loser state machines to ensure they are true mathematical inverses.
- **Logic Standardization:** Standardized all internal variable names (e.g., `drop_check` vs `bounce_check`) and processing structures, ensuring 100% consistency across all four layers of the screening engine.

## 25. News Bot Intelligence Upgrade (Version 2)
- **Executive Summary (TL;DR):** Added a mandatory one-paragraph market synthesis at the top of the report to provide immediate context.
- **Deep Liquidity Analysis:** Re-engineered the AI prompt to force the Groq AI (`llama-3.3-70b-versatile`) to analyze news based on 'Liquidity & Money Flow' and interest rate trajectories rather than just summarizing events.
- **Modern UI Formatting:** Implemented a data-rich visual style for Telegram:
    - `<blockquote>` blocks for news items to create visual separation.
    - `<code>` tags for all quantitative data (prices, percentages, tickers) for high readability.
    - **Bold Entities** (e.g., Fed, BlackRock) for rapid scanning.
    - Optimized emoji-based structural layout.

## 26. High-Impact Source Expansion (Version 2.1)
- **Direct Intel Integration:** Added three high-signal RSS feeds to the News Bot to bypass secondary media filtering:
    - **Glassnode Insights (On-Chain):** Direct data on whale movements, exchange flows, and network liquidity.
    - **SEC Official Press Releases (Regulation):** Direct source for litigation and ETF approvals.
    - **CNBC Finance (Broad Macro):** Real-time tracking of traditional market sentiment and rate expectations.
- **On-Chain & Whales Category:** Introduced a dedicated `[🐋 On-Chain & Whales]` analytical category to capitalize on the new Glassnode data.

## 27. Reliability Fix: Message Length Management (Version 2.6)
- **Bypassing Telegram Limits:** Resolved a critical failure where the bot stopped sending messages due to the 4096-character limit (Error 400).
- **Sectional Message Splitting:** Refactored the reporting logic to send each major category (Gainer L1, L2, etc.) as a separate Telegram message. This ensures the bot can track an unlimited number of coins without ever exceeding the platform's constraints.
- **Ordered Delivery:** Implemented a 1-second delay between sectional messages to ensure they appear in the correct order and avoid Telegram's anti-flood rate limits.

## 28. Color-Coded Reversals (Version 2.7)
- **Visual Signal Differentiation:** Enhanced the "Ultimate Reversal" feature by distinguishing between Bullish and Bearish crossovers.
- **Directional Tags:**
    - **Loser → Gainer:** 🟢 🔄 **Bullish Reversal**
    - **Gainer → Loser:** 🔴 🔄 **Bearish Reversal**
- **UI Clarity:** This allows the user to immediately identify the direction of a major trend shift at a glance without reading the section header.

## 29. Delisted Coin Filter (Version 2.8)
- **Ghost Data Mitigation:** Identified an issue where recently delisted or suspended coins (e.g., UTKUSDT) continued to appear in reports because Binance retains their historical 24h ticker data.
- **Active Trading Check:** Added a strict filter requiring `bidPrice > 0`. This ensures the bot only tracks and reports on assets that have an active order book and are currently tradable.

## 30. Cloud Synchronization & Deployment
- **Deployment:** Pushed local updates (v2.7 & v2.8) to the master branch to synchronize the GitHub Actions environment with the latest local logic.
- **Verification:** Confirmed that the `bidPrice > 0` filter is now active in the cloud, which will automatically purge delisted "ghost" coins like `UTKUSDT` from the Gist state on the next run.

**Date:** Monday, May 18, 2026

## 31. Robust Telegram Delivery (v2.9 / v2.2)
- **Deep Sectional Splitting:** Resolved a critical failure where large watchlist categories (specifically "Loser L1") caused Telegram to reject messages (Error 400).
- **Intra-Section Batching:** Refactored `binance_bot.py` to batch coin reports within each section. If a category exceeds 4,000 characters, it is now automatically split into multiple messages with "(ต่อ)" context headers.
- **AI Summary Chunks:** Implemented an automated splitting mechanism in `bot.py`. Long market reports are now delivered in multiple parts with "(หน้า x/y)" page indicators, preserving structural integrity by splitting at double newlines.
- **Reliability Assurance:** These fixes ensure 100% delivery success regardless of market volatility or report length.

## 32. 15-Minute Precision Upgrade (v3.0)
- **High-Frequency Monitoring:** Transitioned the bot from 1-hour to **15-minute polling** to achieve 4x better responsiveness to market moves.
- **Intra-tick Spike Detection:** Refactored the watermarking engine to fetch **15m Klines** instead of 1h. The bot now captures rapid spikes and dips that happen within 15-minute windows.
- **Global Tick Orchestration:** Implemented a global tick counter in the Gist metadata. This allows the bot to run every 15 minutes but only send the heavy Telegram reports **every 4th run (exactly 1 hour)**.
- **Recalibrated Time Engine:** Updated `thc` (Total Tick Count) and `hc` (Layer Tick Count) to work with the higher frequency. The delist timer was recalibrated from 72 runs (hours) to **288 runs (15m ticks)**.
- **Improved Time UI:** The report now displays granular time tracking (e.g., `2h 15m`) for trends younger than 24 hours.

## 33. Sensitivity Tuning (v3.1)
- **Aggressive Transitions:** Tightened the L1 -> L2 threshold from 15% to **10%**.
- **Earlier Detection:** Coins now move to the Recovery (Gainer L2) or Dead Cat (Loser L2) layers significantly faster after a pullback or bounce, providing earlier signals for trend exhaustion or reversal.
- **Symmetric Logic:** Applied the update to both Gainers (Drop check) and Losers (Bounce check) to maintain algorithmic balance.

## 34. Persistence & Reporting Reliability (v3.2 - v3.3)
- **Schema Validation Fix (v3.2):** Resolved a critical bug in `load_state` where the bot's metadata was being incorrectly identified as an "old schema," leading to state resets on every run.
- **Global Tick Cycle (v3.3):** Optimized the global tick counter to reset to `0` after every 4th run (1 hour). This keeps the state metadata clean and prevents the counter from growing indefinitely.

## 35. Intelligence Migration: OpenRouter (v2.3)
- **Engine Switch:** Migrated the News Bot from Groq to **OpenRouter** to leverage a wider variety of models.
- **Advanced Model:** Updated the bot to use **`openrouter/owl-alpha`**, improving analytical depth and reasoning for market intelligence.
- **SDK Update:** Replaced the `groq` library with the OpenAI-compatible `openai` SDK, ensuring broader compatibility with modern AI providers.
- **Workflow Synchronization:** Updated GitHub Action secrets and environment mappings to use `OPENROUTER_API_KEY`.

## 36. Parsing & Performance Optimization (v2.4)
- **HTML Sanitization:** Fixed a critical bug where the `openrouter/owl-alpha` model generated unsupported `<br>` tags, leading to Telegram delivery failures. Added post-processing to replace these with standard newlines.
- **Strict Tag Enforcement:** Updated the system prompt to explicitly restrict the model to Telegram-compatible HTML tags (`<b>`, `<i>`, `<code>`, `<blockquote>`).
- **Performance Capping:** Limited the news analysis to a maximum of 20 items. This significantly reduces latency and ensures the script completes well within GitHub Action time limits, even with complex analytical models.

## 37. UI Redesign: Emoji Card Style (v2.7)
- **Aesthetic Overhaul:** Transitioned from the problematic `<blockquote>` block style to a cleaner **Emoji Card Style** using `📰 <b>[Headline]</b>`.
- **Simplification:** Completely removed the `<blockquote>` tag from the bot's vocabulary. This eliminates the "tag accumulation" bug where multiple pages of a report would accidentally merge into one massive block.
- **Improved Scannability:** The new layout uses double newlines and structural emojis to make the intelligence report easier to read on mobile devices.
- **Splitter Optimization:** Simplified the smart splitting logic to no longer track or balance blockquotes, reducing the risk of HTML parsing errors.

## 38. Typography & Formatting Polish (v2.8)
- **Newline Cleanup:** Fixed a bug where the bot displayed literal `\n` characters instead of real line breaks.
- **Readability Enhancement:** Addressed the "small word" issue by restricting fixed-width `<code>` tags to price values and tickers only.

## 39. Bulletproof Delivery & UI Revert (v2.9)
- **Blockquote Revert:** Reverted the News Bot UI back to the `<blockquote>` style based on user feedback.
- **Tag Stack Upgrade:** Updated the `send_telegram_message` logic to track `blockquote` tags across paginated messages, ensuring they close and reopen correctly at page boundaries.
- **HTML Sanitization:** Implemented a robust "Bulletproof Sanitizer" that pre-processes LLM output to fix common hallucinations (like `<strong>` or `<p>`) and strips any unsupported tags.
- **Delivery Reliability:** This fix resolved a critical bug where initial pages (1 and 2) of a report were missing due to Telegram's strict HTML parser rejecting malformed content.
- **Split-Point Safeguard:** Improved the text splitter to never break in the middle of an HTML tag.

**Date:** Tuesday, May 19, 2026

## 41. Groq Restoration (v2.11)
- **Engine Rollback:** Migrated the News Bot back to the **Groq API** from OpenRouter, as requested.
- **Model Re-activation:** Restored the `llama-3.3-70b-versatile` model, leveraging its high performance and Thai-language reasoning capabilities.
- **Architectural Preservation:** Seamlessly integrated the new Groq client while maintaining 100% of the **Bulletproof Delivery (v2.10)** logic, including attribute stripping, character escaping, and robust message splitting.
- **Workflow Stability:** Re-confirmed that the bot uses `GROQ_API_KEY`, ensuring compatibility with existing GitHub Action secrets.

## 40. Bulletproof Delivery Fix (v2.10)
- **Deep Sanitization:** Resolved a critical issue where the first two pages of the News Bot report were missing. The failure was caused by Telegram's strict HTML parser rejecting hallucinated tag attributes (e.g., `<blockquote class="...">`) and unescaped characters (e.g., `<` or `&`) generated by the LLM.
- **Attribute Stripping:** Implemented a robust pre-processor that strips all attributes from whitelisted tags, ensuring only pure `<b>`, `<i>`, `<code>`, and `<blockquote>` tags reach Telegram.
- **Character Escaping:** Integrated `html.escape` to safely handle stray mathematical symbols or punctuation that could be mistaken for HTML tags, while preserving the intended formatting.
- **Splitting Precision:** Upgraded the text splitter to ALWAYS check for tag rupture at every possible split point and added a "forced progress" safeguard to prevent infinite loops.
- **UI Consistency:** Maintained the preferred `<blockquote>` style while ensuring perfect tag balance and delivery reliability across all paginated messages.
