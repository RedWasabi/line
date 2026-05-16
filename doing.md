# Project Status: Crypto Intelligence & Binance Watchlist Bot

**Date:** Saturday, May 16, 2026
**Status:** ✅ Dual-Bot Architecture Fully Operational

## 🟢 Completed Tasks
1.  **Macro News Bot (`bot.py`)**:
    - Native GitHub Actions cron schedule (06:00, 12:00, 18:00 Bangkok time).
    - Thai-language summaries via Groq (Llama 3.3 70B).
    - **Independent Channel**: Now uses `NEWS_LINE_ACCESS_TOKEN`.
2.  **Binance Screening Bot (`binance_bot.py`)**:
    - **4-Layer State Machine**:
        - **🔥 Gainer L1 (Momentum)**: Tracks top gainers and their drop from highs.
        - **🏥 Gainer L2 (Recovery)**: Tracks recovery bounce after a 15% drop.
        - **🩸 Loser L1 (Bottoming)**: Tracks top losers and their bounce from lows.
        - **📉 Loser L2 (Dead Cat)**: Tracks price drops after a 15% bounce from lows.
    - **Transition Logic**: L1 -> L2 (15% reversal), L2 -> L1 (20% recovery), L2 Timeout (72h delist).
    - **Reporting**: USD Volume formatting (M/B) and separated sections.
    - **Independent Channel**: Now uses `BINANCE_LINE_ACCESS_TOKEN`.
3.  **Infrastructure**:
    - GitHub Gist for persistent state.
    - `data-api.binance.vision` for reliable connectivity.
    - **Separated Secrets**: `NEWS_` and `BINANCE_` prefixes for clear credential management.

## 🟡 Ongoing Monitoring
- **State Migration**: Verified Gist schema automatically updates to the 4-layer model.
- **Workflow Health**: Ensuring YAML fixes resolved the Action trigger availability.

## 🚀 Future Ideas
- **Volume Surge Detection**: Mark coins with 2x average hourly volume.
- **Manual Control**: Add a workflow trigger to force-delist or manually add a specific coin to a layer.
- **RSI Overlays**: Include RSI status for L1 momentum coins.
