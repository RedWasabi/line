# Project Status: Crypto Intelligence & Binance Watchlist Bot

**Date:** Saturday, May 16, 2026
**Status:** ✅ 4-Layer Screening Bot Deployed

## 🟢 Completed Tasks
1.  **Macro News Bot (`bot.py`)**:
    - Native GitHub Actions cron schedule (06:00, 12:00, 18:00 Bangkok time).
    - Thai-language summaries via Groq (Llama 3.3 70B).
2.  **Binance Screening Bot (`binance_bot.py`)**:
    - **4-Layer State Machine**:
        - **🔥 Gainer L1 (Momentum)**: Tracks top gainers and their drop from highs.
        - **🏥 Gainer L2 (Recovery)**: Tracks recovery bounce after a 15% drop.
        - **🩸 Loser L1 (Bottoming)**: Tracks top losers and their bounce from lows.
        - **📉 Loser L2 (Dead Cat)**: Tracks price drops after a 15% bounce from lows.
    - **Transition Logic**:
        - L1 -> L2: 15% reversal from extreme.
        - L2 -> L1: 20% bounce/drop recovery.
        - L2 Timeout: Automatically delisted after 72 hours if no recovery.
    - **Anti-Duplication**: Prevents adding coins already tracked in any layer.
    - **Consolidated Report**: Single LINE message with clear section headers and emojis.
3.  **Infrastructure**:
    - Using GitHub Gist for persistent JSON memory.
    - Using `data-api.binance.vision` for reliable connectivity.

## 🟡 Ongoing Monitoring
- **State Migration**: Monitoring the first run to ensure the old Gist schema is safely reset/updated to the new 4-layer schema.
- **Hour Count Accuracy**: Verifying that `hc` (Hour Count) correctly tracks time for L2 delisting.

## 🚀 Future Ideas
- **Volume Surge Detection**: Mark coins with 2x average hourly volume.
- **Manual Intervention**: Add a GitHub Action trigger to manually add/remove specific coins.
- **RSI Overlays**: Add RSI status to the L1 reports.
