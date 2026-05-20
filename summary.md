# Technical Summary: Binance Screening Bot Intelligence Engine

**Version:** 3.6 (Volume Sentiment & Dynamic Volatility)
**Architecture:** Multi-Layer State Machine with Volume-Weighted Intelligence

---

## 1. Multi-Layer State Machine
The bot tracks coins across four distinct behavioral layers to classify market regimes:

### 🟢 Gainer Flow (Bullish)
- **L1 - Momentum (`gainer_l1`)**: The coin is in a sustained upward trend. 
    - *Metric:* Tracks Session High (`hp`).
- **L2 - Recovery (`gainer_l2`)**: The coin has pulled back from its high and is searching for a bottom.
    - *Metric:* Tracks Session Low (`lp`) and Bounce %.
    - *Exit:* Returns to L1 if bounce > 20% or delists after 72 hours of inactivity.

### 🔴 Loser Flow (Bearish)
- **L1 - Bottoming (`loser_l1`)**: The coin is in a sustained downward trend.
    - *Metric:* Tracks Session Low (`lp`).
- **L2 - Dead Cat (`loser_l2`)**: The coin has bounced from its low but remains in a bearish structure.
    - *Metric:* Tracks Session High (`hp`) and Drop %.
    - *Exit:* Returns to L1 (Bottoming) if drop from bounce peak > 20% or delists after 72 hours.

---

## 2. Dynamic Volatility Thresholds
The bot replaces fixed percentage drops with volume-weighted sensitivity. High-liquidity coins are more sensitive to reversals, while low-liquidity coins are given more room to filter out "wick" noise.

| Volume Zone | 24h USD Volume | L1 -> L2 Threshold | Rationale |
| :--- | :--- | :--- | :--- |
| **🐳 Institutional** | > $20,000,000 | **6.0%** | Statistically significant move for high liquidity. |
| **🐬 Healthy** | $5M - $20M | **10.0%** | Standard mid-cap behavior baseline. |
| **🐟 Retail** | $1M - $5M | **15.0%** | Widen buffer to ignore low-liquidity noise. |

---

## 3. Volume Sentiment Analysis (RVol)
The bot uses **Relative Volume (RVol)** to gauge trader conviction. It calculates the ratio between the current 15m candle volume and the average volume of the previous 5 hours.

- **Formula**: `Current_15m_Vol / Average(Previous_19_Klines)`
- **Sentiment Mapping**:
    - **⚡ Explosive / 🔥 Spiking** (`RVol > 3.5x`): Massive conviction; high probability of a major move.
    - **📈 Growing** (`RVol > 2.0x`): Healthy trending interest.
    - **💤 Fading** (`RVol < 0.5x`): Exhaustion; momentum is stalling.
    - **🧊 Lost** (`RVol < 0.3x`): Interest has completely evaporated; high risk of trend failure.

---

## 4. Discovery & Surveillance Algorithms

### Ultimate Reversal (Trend Crossover)
If a coin in a "Loser" state suddenly enters the Top 10 Gainers (or vice-versa), the bot performs an **Ultimate Reversal**, resetting its state and tagging it with a 🔄 Bullish/Bearish Reversal emoji in Telegram.

### Surge Discovery (Top 20 Scan)
The bot scans the Top 20 24h Gainers/Losers. 
- If a coin is in the Top 10, it is added to L1 immediately.
- If a coin is between Rank 11-20 but has **Explosive Volume (RVol > 3.5x)**, it is added to the watchlist immediately to catch breakouts before they hit the main list.

---

## 5. Reporting & Infrastructure
- **Intra-tick Precision**: Uses 15-minute Klines to capture spikes and dips that occur between polling cycles.
- **Hourly Telegram Reports**: Gates notifications using `REPORT_INTERVAL_SEC` (~55 mins) while maintaining high-frequency (15m) state polling.
- **Persistence**: State is stored in a GitHub Gist (`watchlist.json`) to survive server restarts.
- **Metrics Tracked**:
    - `ST`: Start Price (Price at discovery).
    - `Net %`: Total performance from `ST` to current price.
    - `HC/THC`: Tick counters to track time on list and delisting deadlines.
