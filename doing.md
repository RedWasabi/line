# Project Status: Crypto Intelligence & Binance Watchlist Bot

**Date:** Saturday, May 16, 2026
**Status:** ✅ Dual-Bot Architecture Fully Operational

## 🟢 Completed Tasks
1.  **Macro News Bot (`bot.py`)**:
    - Thai-language summaries via Groq (Llama 3.3 70B).
    - **Telegram Migration**: Unlimited messages via `TELEGRAM_BOT_TOKEN`.
    - **UI Enhancement**: HTML Bold/Italic rich-text formatting.
    - **External Trigger**: `repository_dispatch` (type: `trigger-news`).
2.  **Binance Screening Bot (`binance_bot.py`)**:
    - **4-Layer State Machine**: L1 Momentum, L2 Recovery, L1 Bottoming, L2 Dead Cat.
    - **Version 2 Tracking**: Persistent Session Watermarks (ticker merge).
    - **Telegram Migration**: Unlimited messages via `BINANCE_TELEGRAM_BOT_TOKEN`.
    - **High-Fidelity UI**: Monospaced fonts for prices, bold headers, card-style layout.
    - **Reporting**: USD Volume (M/B), `0d 00h` time tracking.
    - **External Trigger**: `repository_dispatch` (type: `trigger-binance`).
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
