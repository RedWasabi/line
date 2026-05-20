# Project Status: Crypto Intelligence & Binance Watchlist Bot

**Date:** Tuesday, May 19, 2026
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
2.  **Binance Screening Bot (`binance_bot.py`)**:
    - **Unified Reporting Architecture (v3.8)**:
        - **5-List Structure**: Streamlined reports from 7 sections down to 5 (Surges, Gainer L1/L2, Loser L1/L2).
        - **Inline Sentiment Emojis**: Integrated 🧊 (Lost) and 💤 (Fading) indicators directly into main lists to preserve data density while improving skimmability.
    - **Discovery Scope Expansion (v3.7)**:
        - **Top 30 Scan**: Increased surveillance range from Top 20 to Top 30 Gainers/Losers.
        - **Enhanced Breakout Detection**: Allows high-conviction (RVol > 3.5x) coins to be discovered deeper in the leaderboard.
    - **Volume Sentiment Analysis (v3.6)**:
    - **Dynamic Volatility Thresholds (v3.5)**:
        - **Volume-Weighted Sensitivity**: Replaced the static 10% threshold with a dynamic `get_dynamic_drop_threshold` function.
        - **Institutional (>20M)**: 6% (sensitive for high liquidity).
        - **Healthy (5M-20M)**: 10% (standard mid-cap).
        - **Retail (1M-5M)**: 15% (noise reduction for low liquidity).
    - **Enhanced L2 Tracking (v3.5)**: 
        - Reports now display the **Starting Price (ST)** for L2 recovery/dead-cat states.
        - Added **Net % Change** metric to track total performance from discovery to current price.
    - **Structural Hardening (v3.4)**:
        - **Timestamp-Based Reporting**: Replaced fragile tick-based counters with absolute time checks (`REPORT_INTERVAL_SEC`), ensuring reliable hourly reports despite cloud runner jitter.
        - **Logging Migration**: Implemented the `logging` module for professional auditing.
        - **Configuration Constants**: Externalized all thresholds (10% drop, 20% bounce, delist timers) to the top of the file for easy recalibration.
    - **Global Tick Reset (v3.3)**: Optimized state metadata.
    - **15-Minute Precision (v3.0)**: Upgraded to fetch data every 15 minutes.
    - **Intra-tick Spike Detection**: Uses 15m Klines.
    - **4-Layer State Machine**: L1 Momentum, L2 Recovery, L1 Bottoming, L2 Dead Cat.
    - **Duration-Based Sorting (v2.5)**: Sorted by time on watchlist.
    - **Ultimate Reversal (v2.2)**: 🔄 Trend Reversed tag.
    - **Quality Control**: Strict $1,000,000 daily volume filter.
    - **Reliability Fix (v2.9)**: Intra-section batching and split-message support.
3.  **Infrastructure**:
    - GitHub Gist for persistent state.
    - `data-api.binance.vision` for regional bypass.
    - **Trigger Optimization**: External API dispatches for precision timing.

## 🟡 Ongoing Monitoring
- **Reporting Intervals**: Verifying that `REPORT_INTERVAL_SEC` correctly gates Telegram notifications while maintaining 15-minute polling.

## 🚀 Future Ideas
- **Volume Surge Detection**: Mark coins with 2x average hourly volume.
- **RSI Overlays**: Include RSI status for L1 momentum coins.
- **Auto-Scale List**: Dynamically adjust the Top 10 limit based on market volatility.
