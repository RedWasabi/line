# Project Status: Crypto Intelligence & Binance Watchlist Bot

**Date:** Saturday, May 16, 2026
**Status:** ✅ Fully Operational

## 🟢 Completed Tasks
1.  **Macro News Bot (`bot.py`)**:
    - Native GitHub Actions cron schedule (06:00, 12:00, 18:00 Bangkok time).
    - Thai-language summaries via Groq (Llama 3.3 70B).
2.  **Binance Watchlist Bot (`binance_bot.py`)**:
    - **Connectivity Fix**: Using `data-api.binance.vision` to bypass US regional blocks on GitHub Actions runners.
    - **Separated Reports**: Report organized into distinct "TOP GAINERS" and "TOP LOSERS" sections.
    - **Stateful Persistence**: Uses GitHub Gist (`watchlist.json`) to track price extremes and 1-hour changes.
    - **15% Reversal Rule**: Automatically delists coins that reverse 15% from their recorded high (gainers) or low (losers).
    - **Hourly Execution**: Workflow `.github/workflows/binance.yml` configured and verified.
3.  **Infrastructure**:
    - Configured `GIST_ID` and `GH_PAT` secrets for remote memory.
    - Configured `LINE_ACCESS_TOKEN` and `LINE_USER_ID` for notifications.

## 🟡 Ongoing Monitoring
- **1h Change Accuracy**: Ensuring the Gist-based price tracking correctly calculates the hourly delta.
- **Watchlist Growth**: Monitoring the total number of coins tracked over time to ensure the LINE message stays within size limits.

## 🚀 Future Ideas
- **Volume Spike Alerts**: Trigger messages if volume increases by X% in one hour.
- **RSI Filtering**: Only add coins to watchlist if RSI is not overbought/oversold.
- **Manual Control**: Add a way to manually add/remove coins from the Gist watchlist via a separate command.
