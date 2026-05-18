# Project Status: Crypto Intelligence & Binance Watchlist Bot

**Date:** Monday, May 18, 2026
**Status:** ✅ Dual-Bot Architecture Fully Operational

## 🟢 Completed Tasks
1.  **Macro News Bot (`bot.py`)**:
    - Thai-language summaries via Groq (Llama 3.3 70B).
    - **High-Impact Sources (v2.1)**: Integrated Glassnode (On-chain), SEC (Regulatory), and CNBC Finance (Macro).
    - **Executive Summary (v2)**: Added top-level TL;DR for market mood.
    - **Deep Insight (v2)**: Focus on 'Liquidity & Money Flow' and interest rate trajectory.
    - **Modern UI (v2)**: Enhanced formatting with blockquotes, monospace data (<code>), and rich emojis.
    - **Analytics Categories**: [📌 Macro & Fed], [🐋 On-Chain & Whales], [🏢 Institutional Activity], [⚖️ Regulation & Tech].
    - **Telegram Migration**: Unlimited messages via `TELEGRAM_BOT_TOKEN`.
    - **Reliability Fix (v2.2)**: Implemented automated multi-part delivery with "(หน้า x/y)" page indicators for long AI summaries.
    - **External Trigger**: `repository_dispatch` (type: `trigger-news`).
2.  **Binance Screening Bot (`binance_bot.py`)**:
    - **15-Minute Precision (v3.0)**: Upgraded to fetch data every 15 minutes while maintaining consolidated hourly Telegram reports.
    - **Intra-tick Spike Detection**: Uses 15m Klines for 4x better responsiveness to pumps and dumps.
    - **Global Tick Tracking**: Orchestrates reporting frequency via Gist state metadata.
    - **4-Layer State Machine**: L1 Momentum, L2 Recovery, L1 Bottoming, L2 Dead Cat.
    - **Duration-Based Sorting (v2.5)**: All report sections are now sorted by time on watchlist (longest at the top).
    - **Algorithmic Symmetry**: Perfectly mirrored logic for Gainers and Losers (Drop vs Bounce) for 100% mathematical consistency.
    - **Intra-hour Precision (v2.4)**: Uses Binance Klines (1h candles) to capture "invisible" spikes/dips.
    - **First-Run Protection**: Logic fix to ensure all coins start in L1 for their first appearance.
    - **Liquidity Zones (v2.3)**: Visual emojis for volume: 🐟 Retail, 🐬 Healthy, 🐳 Institutional.
    - **Ultimate Reversal (v2.2)**: Seamlessly crossover between categories with 🔄 Trend Reversed tag.
    - **Quality Control**: Strict $1,000,000 daily volume filter.
    - **Algorithm Fix (v2.1)**: Continuous tracking during transitions.
    - **High-Precision UI**: Dynamic 8-decimal price formatting.
    - **Live Metrics**: Live Binance 24h Change % included.
    - **Corrected Timer**: 'Delist in' counts down from 72h (L2 only).
    - **Reliability Fix (v2.9)**: Enhanced sectional splitting. If a single layer (e.g., Loser L1) exceeds the character limit, it is automatically broken into multiple messages with "(ต่อ)" context tags.
    - **Color-Coded Reversals (v2.7)**: Visual 🟢 Bullish / 🔴 Bearish tags for trend crossovers.
    - **Delisted Filter (v2.8)**: Excludes suspended/delisted coins by requiring an active bid price (`bidPrice > 0`).
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
