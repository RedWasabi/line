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
2.  **Binance Screening Bot (`binance_bot.py`)**:
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
