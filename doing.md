# Project Status: Crypto Intelligence & Binance Watchlist Bot

**Date:** Saturday, May 16, 2026
**Status:** ✅ Dual-Bot Architecture Fully Operational

## 🟢 Completed Tasks
1.  **Macro News Bot (`bot.py`)**:
    - Thai-language summaries via Groq (Llama 3.3 70B).
    - **Independent Channel**: Now uses `NEWS_LINE_ACCESS_TOKEN`.
    - **External Trigger**: Migrated to `repository_dispatch` (type: `trigger-news`) for precise scheduling.
2.  **Binance Screening Bot (`binance_bot.py`)**:
    - **4-Layer State Machine**: L1 Momentum, L2 Recovery, L1 Bottoming, L2 Dead Cat.
    - **Version 2 Tracking**: Uses **Persistent Session Watermarks** (merging session extremes with 24h ticker highs/lows) to capture intra-hour spikes and dips.
    - **Transition Logic**: L1 -> L2 (15% reversal), L2 -> L1 (20% recovery), L2 Timeout (72h delist).
    - **Reporting**: USD Volume formatting (M/B), `0d 00h` time tracking for total duration (`thc`) and delist countdowns (`hc`).
    - **Independent Channel**: Uses `BINANCE_LINE_ACCESS_TOKEN`.
    - **External Trigger**: `repository_dispatch` (type: `trigger-binance`) for hourly precision.
3.  **Infrastructure**:
    - GitHub Gist for persistent state.
    - `data-api.binance.vision` for reliable connectivity.
    - **Trigger Optimization**: Replaced native GitHub cron (delayed) with external API dispatches.

## 🟡 Ongoing Monitoring
- **State Migration**: Verified Gist schema automatically updates to the 4-layer model.
- **Workflow Health**: Ensuring YAML fixes resolved the Action trigger availability.

## 🚀 Future Ideas
- **Volume Surge Detection**: Mark coins with 2x average hourly volume.
- **Manual Control**: Add a workflow trigger to force-delist or manually add a specific coin to a layer.
- **RSI Overlays**: Include RSI status for L1 momentum coins.
