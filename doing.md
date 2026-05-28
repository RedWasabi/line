# Project Status: Crypto Intelligence & Binance Watchlist Bot

**Date:** Saturday, May 23, 2026
**Status:** ✅ Dual-Bot Architecture Hardened for Personal Use

## 🟢 Completed Tasks
1.  **Macro News Bot (`bot.py`)**:
    - **Structural Hardening (v2.12)**:
        - Migrated from `print` to the `logging` module for better process tracking.
        - Externalized news limits and model selection as constants.
    - **Groq Restoration (v2.11)**:
        - Migrated back to Groq API using `llama-3.3-70b-versatile`.
    - **Bulletproof Delivery Fix (v2.10)**:
        - Implemented a "Bulletproof Sanitizer" that strips tag attributes and escapes special characters.
        - Refined splitting logic for HTML tag balance across paginated messages.
    - **High-Impact Sources (v2.1)**: Integrated Glassnode, SEC, and CNBC Finance.
    - **Telegram Migration**: Unlimited messages via `TELEGRAM_BOT_TOKEN`.
    - **Hacker News Integration (v2.13)**: 
        - Integrated high-signal tech news via Algolia HN Search API.
        - Implemented `points` and `num_comments` filters to prioritize community engagement signal.
    - **Macro-Crypto Correlation Engine (v2.14)**:
        - **Intelligent Filtering**: Implemented keyword-based priority tagging (e.g., Fed, Inflation, Liquidity) to surface high-impact macro news.
        - **Causal Analysis**: LLM prompt now mandates "Cross-Source Correlation"—linking macro events (1st-order) to crypto liquidity/adoption shifts (2nd-order).
        - **Priority Sorting**: High-signal news is presented first to ensure analytical focus on market-moving themes.
    - **Institutional Feed Expansion (v2.15)**:
        - **The Block (RSS)**: Added for institutional-grade deep research and crypto policy insights.
        - **ZeroHedge (RSS)**: Integrated for macro-liquidity contrarian analysis and alternative financial signals.
        - **BIS (RSS)**: Added Bank of International Settlements speeches to capture global central bank regulatory signaling.
    - **Quantitative Intelligence Upgrade (v2.16)**:
        - **DefiLlama Integration**: Implemented 24h Stablecoin Net Flow tracking to gauge market liquidity.
        - **Whale Alert Integration**: Added real-time tracking of transactions >$500k to detect institutional conviction.
        - **Quantitative-to-Qualitative Correlation**: Re-engineered the AI prompt to mandate cross-referencing news headlines against actual on-chain money movements.
2.  **Binance Screening Bot (`binance_bot.py`)**:
    - **L1 Delist Exemption (v3.11)**:
        - Removed the 10-day global delisting limit for coins in the L1 (Momentum/Bottoming) layers to allow indefinite tracking of active trends.
    - **Unified Reporting Architecture (v3.10)**:
        - **3-List Structure**: Streamlined reports from 5 sections down to 3 (Surges, Gainer L1/L2). Loser L1/L2 lists have been disabled but preserved in source code.
        - **Inline Sentiment Indicators**: Integrated 🧊 (Lost) and 💤 (Fading) emojis directly next to symbols to preserve vertical space without losing data.
    - **Global Cleanup Algorithm (v3.9)**:
        - **10-Day Timeout (Exempting L1)**: Automatically delists any coin that has been on the watchlist for more than 10 days (960 ticks) if it is in an L2 layer, to prevent bloat while keeping active L1 trends.
    - **Discovery Scope Expansion (v3.7)**:
        - **Top 30 Scan**: Increased surveillance range from Top 20 to Top 30 Gainers/Losers.
        - **Enhanced Breakout Detection**: Allows high-conviction (RVol > 3.5x) coins to be discovered deeper in the leaderboard.
    - **Volume Sentiment Analysis (v3.6)**:
        - **Relative Volume (RVol)**: Implemented 5-hour lookback algorithm for conviction tracking.
        - **Dynamic Tagging**: Added tags for ⚡ Explosive, 🔥 Spiking, 📈 Growing, 💤 Fading, and 🧊 Lost interest.
    - **Dynamic Volatility Thresholds (v3.5)**:
        - **Volume-Weighted Sensitivity**: Institutional (6%), Healthy (10%), Retail (15%).
    - **Enhanced L2 Tracking (v3.5)**: 
        - Reports now display the **Starting Price (ST)** and **Net % Change** from discovery.
    - **Structural Hardening (v3.4)**:
        - **Timestamp-Based Reporting**: Replaced tick-based counters with absolute time checks (`REPORT_INTERVAL_SEC`).
        - **Logging & Constants**: Professional auditing and easy threshold recalibration.
    - **15-Minute Precision (v3.0)**: Upgraded to fetch data every 15 minutes with Intra-tick Spike Detection.
    - **4-Layer State Machine**: L1 Momentum, L2 Recovery, L1 Bottoming, L2 Dead Cat.
    - **Ultimate Reversal (v2.2)**: 🔄 Trend Reversed detection.
3.  **Security & Maintenance**:
    - **Public Repo Readiness**: Completed comprehensive workspace scan for hardcoded secrets. Confirmed 100% environment variable coverage for credentials.
    - **Infrastructure**: GitHub Gist for persistent state. `data-api.binance.vision` for regional bypass.

## 🟢 Deployment Status
- **v3.11 Ready**: Binance Bot v3.11 changes (L1 exemption from 10-day delisting) are ready.

## 🟡 Ongoing Monitoring
- **Reporting Intervals**: Verifying that `REPORT_INTERVAL_SEC` correctly gates Telegram notifications while maintaining 15-minute polling.

## 🚀 Future Ideas
- **Volume Surge Detection**: Mark coins with 2x average hourly volume.
- **RSI Overlays**: Include RSI status for L1 momentum coins.
- **Auto-Scale List**: Dynamically adjust the Top 10 limit based on market volatility.
