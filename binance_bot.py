import os
import json
import time
import requests
import logging
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration - Constants
GIST_ID = os.environ.get("GIST_ID")
GH_PAT = os.environ.get("GH_PAT")
BINANCE_TELEGRAM_BOT_TOKEN = os.environ.get("BINANCE_TELEGRAM_BOT_TOKEN")
BINANCE_TELEGRAM_CHAT_ID = os.environ.get("BINANCE_TELEGRAM_CHAT_ID")

# Strategy Thresholds
L2_RECOVERY_BOUNCE_PCT = 20.0  # 20% bounce from low moves L2 -> L1
MIN_VOLUME_USD = 1_000_000    # $1M USD minimum daily volume
DELIST_TICKS_LIMIT = 288      # 72 hours (288 * 15m ticks)
REPORT_INTERVAL_SEC = 3300    # ~55 mins (ensures 1 report per hour even with jitter)

# API Endpoints
BINANCE_BASE_URL = "https://data-api.binance.vision/api/v3"
GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"

def get_dynamic_drop_threshold(vol_usd):
    """
    Returns a dynamic drop threshold based on 24h USD volume.
    High liquidity (Institutional) = Lower threshold (6%)
    Medium liquidity (Healthy) = Standard threshold (10%)
    Low liquidity (Retail) = Higher threshold (15%) to filter noise
    """
    if vol_usd >= 20_000_000:
        return 6.0
    elif vol_usd >= 5_000_000:
        return 10.0
    return 15.0

def load_state():
    """Loads the watchlist state from a GitHub Gist."""
    if not GIST_ID or not GH_PAT:
        logger.warning("GIST_ID or GH_PAT not set. Starting with empty state.")
        return {}
    
    headers = {"Authorization": f"token {GH_PAT}"}
    try:
        response = requests.get(GIST_API_URL, headers=headers)
        if response.status_code == 200:
            gist_data = response.json()
            content = gist_data['files']['watchlist.json']['content']
            data = json.loads(content)
            # Basic schema check: ensure coin items have 'layer' key. Ignore metadata.
            coin_values = [v for k, v in data.items() if k != '_metadata' and isinstance(v, dict)]
            if data and coin_values and not all('layer' in v for v in coin_values):
                logger.info("Old schema detected. Resetting state for 4-layer logic.")
                return {}
            return data
        else:
            logger.error(f"Failed to load Gist: {response.status_code} {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Error loading Gist: {e}")
        return {}

def save_state(state):
    """Saves the watchlist state to the GitHub Gist."""
    if not GIST_ID or not GH_PAT:
        return
    
    headers = {
        "Authorization": f"token {GH_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "files": {
            "watchlist.json": {
                "content": json.dumps(state, indent=2)
            }
        }
    }
    try:
        response = requests.patch(GIST_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            logger.info("State saved to Gist successfully.")
        else:
            logger.error(f"Failed to save Gist: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"Error saving Gist: {e}")

def get_binance_tickers():
    """Fetches all 24h tickers from Binance."""
    url = f"{BINANCE_BASE_URL}/ticker/24hr"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch Binance data: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching Binance data: {e}")
        return []

def get_volume_stats(symbol, limit=21):
    """
    Fetches klines to calculate recent high/low and Relative Volume (RVol).
    limit=21 allows for 1 current kline + 20 previous klines for average.
    """
    url = f"{BINANCE_BASE_URL}/klines"
    params = {"symbol": symbol, "interval": "15m", "limit": limit}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            klines = response.json()
            if not klines or len(klines) < 2:
                return None, None, 0.0
            
            # High/Low from last 2 candles (intra-tick spikes)
            recent_highs = [float(k[2]) for k in klines[-2:]]
            recent_lows = [float(k[3]) for k in klines[-2:]]
            
            # RVol Calculation (Current 15m candle volume vs average of previous 20)
            current_vol = float(klines[-1][5]) # Volume is index 5
            prev_vols = [float(k[5]) for k in klines[:-1]]
            avg_vol = sum(prev_vols) / len(prev_vols) if prev_vols else 0
            
            rvol = current_vol / avg_vol if avg_vol > 0 else 0
            
            return max(recent_highs), min(recent_lows), rvol
        else:
            logger.error(f"Klines API Error for {symbol}: {response.status_code}")
            return None, None, 0.0
    except Exception as e:
        logger.error(f"Error fetching Klines for {symbol}: {e}")
        return None, None, 0.0

def get_volume_sentiment(rvol):
    """Returns a sentiment tag and emoji based on RVol."""
    if rvol >= 5.0:
        return "🚀 <b>Explosive</b>", "⚡"
    elif rvol >= 3.5:
        return "🔥 <b>Spiking</b>", "🔥"
    elif rvol >= 2.0:
        return "📈 <b>Growing</b>", "📈"
    elif rvol <= 0.3:
        return "🧊 <b>Lost</b>", "🧊"
    elif rvol <= 0.5:
        return "💤 <b>Fading</b>", "💤"
    return None, None

def send_telegram_message(text):
    """Sends the report to Telegram."""
    if not BINANCE_TELEGRAM_BOT_TOKEN or not BINANCE_TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials not set.")
        return
    url = f"https://api.telegram.org/bot{BINANCE_TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": BINANCE_TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            logger.info("Binance report part sent to Telegram.")
        else:
            logger.error(f"Telegram API Error: {response.status_code} {response.text}")
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")

def format_usd(value):
    """Formats large USD values into readable strings (e.g., $1.2M, $500K)."""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.2f}K"
    return f"${value:.2f}"

def format_price(price):
    """Formats prices with dynamic precision based on value."""
    if price == 0:
        return "0.0000"
    if price < 0.0001:
        return f"{price:.8f}"
    if price < 0.01:
        return f"{price:.6f}"
    return f"{price:,.4f}"

def format_time(ticks):
    """Formats 15-min ticks into '0d 00h' or '0h 00m' strings."""
    total_minutes = ticks * 15
    d = total_minutes // (24 * 60)
    h = (total_minutes % (24 * 60)) // 60
    m = total_minutes % 60
    if d > 0:
        return f"{d}d {h:02d}h"
    return f"{h}h {m:02d}m"

def get_volume_zone(vol_usd):
    """Classifies volume into three zones with emojis."""
    if vol_usd >= 20_000_000:
        return "🐳 <b>Institutional</b>"
    elif vol_usd >= 5_000_000:
        return "🐬 <b>Healthy</b>"
    else:
        return "🐟 <b>Retail</b>"

def main():
    logger.info("Starting Multi-Layer Binance Screening Bot (v3.4 - Structural Hardening)...")
    
    # 1. Load existing state
    state_full = load_state()
    # Separate metadata from coins
    metadata = state_full.pop('_metadata', {"last_report_time": 0})
    state = state_full
    
    # Absolute Time-based Reporting Check
    now = time.time()
    time_since_last = now - metadata.get('last_report_time', 0)
    should_send = time_since_last >= REPORT_INTERVAL_SEC
    
    if should_send:
        metadata['last_report_time'] = now
        logger.info(f"Report Triggered: {time_since_last/60:.1f} minutes since last report.")
    else:
        logger.info(f"Monitoring: {time_since_last/60:.1f} minutes since last report. Waiting for trigger.")
    
    # Global Increment: Initialize 'thc' if missing, then increment for all existing coins
    for symbol in state:
        if 'thc' not in state[symbol]:
            state[symbol]['thc'] = state[symbol].get('hc', 0)
        state[symbol]['thc'] += 1
    
    # 2. Fetch fresh Binance data
    tickers = get_binance_tickers()
    if not tickers:
        return

    # Filter for USDT pairs, significant volume, and active trading
    usdt_tickers = [
        t for t in tickers 
        if t['symbol'].endswith('USDT') 
        and float(t['quoteVolume']) >= MIN_VOLUME_USD
        and float(t.get('bidPrice', 0)) > 0
    ]
    
    # Sort to find Top 30 Gainers and Top 30 Losers (24h change)
    sorted_tickers = sorted(usdt_tickers, key=lambda x: float(x['priceChangePercent']), reverse=True)
    top_gainers = sorted_tickers[:30]
    top_losers = sorted_tickers[-30:]

    ticker_map = {t['symbol']: t for t in usdt_tickers}
    
    # 3. Add New Coins & Handle Trend Crossovers (Ultimate Reversal & Surge Discovery)
    # Filter for candidates: Top 10 by price OR any of Top 30 with RVol > 3.5
    for i, t in enumerate(top_gainers):
        symbol = t['symbol']
        curr_price = float(t['lastPrice'])
        
        # We check volume stats for discovery if not in state
        rvol = 0.0
        is_surge = False
        if symbol not in state:
            _, _, rvol = get_volume_stats(symbol)
            is_surge = rvol > 3.5

        # Add if in Top 10 OR is a Volume Surge candidate in Top 30
        if symbol not in state or state[symbol]['layer'].startswith('loser'):
            if i < 10 or is_surge:
                if symbol in state:
                    logger.info(f"🔄 Reversal: Moving {symbol} from Loser to Gainer L1")
                
                state[symbol] = {
                    "layer": "gainer_l1",
                    "st": curr_price,
                    "hp": curr_price,
                    "lp": None,
                    "hc": 0,
                    "thc": 0,
                    "rev": True if symbol in state else False,
                    "rvol": rvol
                }
                logger.info(f"Added {symbol} to Gainer L1{' (Surge Discovery)' if is_surge else ''}")

    for i, t in enumerate(top_losers):
        symbol = t['symbol']
        curr_price = float(t['lastPrice'])
        
        rvol = 0.0
        is_surge = False
        if symbol not in state:
            _, _, rvol = get_volume_stats(symbol)
            is_surge = rvol > 3.5

        if symbol not in state or state[symbol]['layer'].startswith('gainer'):
            if i < 10 or is_surge:
                if symbol in state:
                    logger.info(f"🔄 Reversal: Moving {symbol} from Gainer to Loser L1")
                    
                state[symbol] = {
                    "layer": "loser_l1",
                    "st": curr_price,
                    "lp": curr_price,
                    "hp": None,
                    "hc": 0,
                    "thc": 0,
                    "rev": True if symbol in state else False,
                    "rvol": rvol
                }
                logger.info(f"Added {symbol} to Loser L1{' (Surge Discovery)' if is_surge else ''}")

    # 4. Process State Transitions & Collect Data for Reports
    new_state = {}
    report_data = {
        "gainer_l1": [],
        "gainer_l2": [],
        "loser_l1": [],
        "loser_l2": [],
        "surges": []
    }
    
    for symbol, coin in state.items():
        if symbol not in ticker_map:
            continue
            
        ticker = ticker_map[symbol]
        curr_price = float(ticker['lastPrice'])
        vol_usd = float(ticker['quoteVolume'])
        ch24 = float(ticker['priceChangePercent'])
        
        # Fetch Intra-tick Spikes (15m Klines) & Calculate RVol
        k_high, k_low, rvol = get_volume_stats(symbol)
        coin['rvol'] = rvol # Update stored rvol
        
        current_layer = coin['layer']
        
        # Determine dynamic threshold for L1 -> L2 transition based on volume
        l1_to_l2_threshold = get_dynamic_drop_threshold(vol_usd)
        
        if current_layer == "gainer_l1":
            # Track Session High (Momentum)
            obs_high = max(curr_price, k_high) if k_high else curr_price
            coin['hp'] = max(coin['hp'], obs_high)
            
            # Check for Drop -> Move to L2 (Recovery)
            drop_check = (coin['hp'] - curr_price) / coin['hp'] * 100
            if drop_check > l1_to_l2_threshold and coin['thc'] > 0:
                coin.update({"layer": "gainer_l2", "lp": curr_price, "hc": 0})
                
        elif current_layer == "gainer_l2":
            coin['hc'] += 1
            # Track Session Low (Correction Bottom)
            obs_low = min(curr_price, k_low) if k_low else curr_price
            coin['lp'] = min(coin['lp'] if coin['lp'] is not None else curr_price, obs_low)
            
            # Check for Bounce -> Move back to L1 (Momentum)
            bounce_check = (curr_price - coin['lp']) / coin['lp'] * 100
            if bounce_check > L2_RECOVERY_BOUNCE_PCT:
                coin.update({"layer": "gainer_l1", "st": curr_price, "hp": curr_price, "lp": None, "hc": 0})
            elif coin['hc'] >= DELIST_TICKS_LIMIT:
                logger.info(f"Delisted {symbol} from Gainer L2 (Timeout)")
                continue

        elif current_layer == "loser_l1":
            # Track Session Low (Bottoming)
            obs_low = min(curr_price, k_low) if k_low else curr_price
            coin['lp'] = min(coin['lp'] if coin['lp'] is not None else curr_price, obs_low)
            
            # Check for Bounce -> Move to L2 (Dead Cat)
            bounce_check = (curr_price - coin['lp']) / coin['lp'] * 100
            if bounce_check > l1_to_l2_threshold and coin['thc'] > 0: # Threshold is symmetric for L1->L2
                coin.update({"layer": "loser_l2", "hp": curr_price, "hc": 0})

        elif current_layer == "loser_l2":
            coin['hc'] += 1
            # Track Session High (Bounce Peak)
            obs_high = max(curr_price, k_high) if k_high else curr_price
            coin['hp'] = max(coin['hp'] if coin['hp'] is not None else curr_price, obs_high)
            
            # Check for Drop -> Move back to L1 (Bottoming)
            drop_check = (coin['hp'] - curr_price) / coin['hp'] * 100
            if drop_check > L2_RECOVERY_BOUNCE_PCT:
                coin.update({"layer": "loser_l1", "st": curr_price, "lp": curr_price, "hp": None, "hc": 0})
            elif coin['hc'] >= DELIST_TICKS_LIMIT:
                logger.info(f"Delisted {symbol} from Loser L2 (Timeout)")
                continue

        # Collect data for Reports (Only if we are sending)
        if should_send:
            final_layer = coin['layer']
            item_data = {
                "symbol": symbol,
                "coin": coin.copy(),
                "curr_price": curr_price,
                "vol_usd": vol_usd,
                "ch24": ch24,
                "rvol": rvol
            }
            report_data[final_layer].append(item_data)
            
            # Discovery Logic for Surge List
            if rvol > 3.0:
                report_data["surges"].append(item_data)
        
        if 'rev' in coin:
            coin['rev'] = False
        new_state[symbol] = coin

    # Sort and Format Reports
    if should_send:
        final_report_strings = {k: [] for k in report_data.keys()}
        
        # Helper to avoid duplicate logic in reporting
        for layer_key, coins_list in report_data.items():
            # Sort by time on watchlist (thc) for standard layers, or RVol for surges
            if layer_key == "surges":
                sorted_coins = sorted(coins_list, key=lambda x: x['rvol'], reverse=True)
            else:
                sorted_coins = sorted(coins_list, key=lambda x: x['coin']['thc'], reverse=True)
            
            for item in sorted_coins:
                symbol = item['symbol']
                coin = item['coin']
                curr_price = item['curr_price']
                vol_usd = item['vol_usd']
                ch24 = item['ch24']
                rvol = item['rvol']
                
                thc_str = format_time(coin['thc'])
                p_str = format_price(curr_price)
                st_str = format_price(coin['st']) if coin['st'] else "N/A"
                
                # Volume Sentiment Tag
                sent_tag, sent_emoji = get_volume_sentiment(rvol)
                vol_sent_str = f" | Vol: {sent_tag} (<b>{rvol:.1f}x</b>)" if sent_tag else f" | Vol: <b>{rvol:.1f}x</b>"
                
                # Visual Skimmability Tag (Emoji Only) for main lists
                status_emoji = f" {sent_emoji}" if sent_emoji in ["🧊", "💤"] else ""
                
                rev_tag = ""
                if coin.get('rev'):
                    if layer_key.startswith('gainer'):
                        rev_tag = " 🟢 🔄 <b>Bullish Reversal</b>"
                    else:
                        rev_tag = " 🔴 🔄 <b>Bearish Reversal</b>"
                
                vol_zone = get_volume_zone(vol_usd)
                
                if layer_key == "gainer_l1":
                    hp_str = format_price(coin['hp'])
                    ip = (curr_price - coin['st']) / coin['st'] * 100
                    dh = (coin['hp'] - curr_price) / coin['hp'] * 100
                    final_report_strings["gainer_l1"].append(
                        f"<b>• {symbol}</b>{status_emoji}{rev_tag}\n"
                        f"  Price: <code>{p_str}</code> (24h: <b>{ch24:+.2f}%</b>)\n"
                        f"  ST: <code>{st_str}</code> | HP: <code>{hp_str}</code>{vol_sent_str}\n"
                        f"  Inc: <b>{ip:+.2f}%</b> | Drop: <b>{dh:.2f}%</b>\n"
                        f"  Vol: {vol_zone} (<i>{format_usd(vol_usd)}</i>)\n"
                        f"  Time: {thc_str}"
                    )
                elif layer_key == "gainer_l2":
                    lp_str = format_price(coin['lp'])
                    bp = (curr_price - coin['lp']) / coin['lp'] * 100
                    np = (curr_price - coin['st']) / coin['st'] * 100
                    rem_str = format_time(max(0, DELIST_TICKS_LIMIT - coin['hc']))
                    final_report_strings["gainer_l2"].append(
                        f"<b>• {symbol}</b>{status_emoji}{rev_tag}\n"
                        f"  Price: <code>{p_str}</code> (24h: <b>{ch24:+.2f}%</b>)\n"
                        f"  ST: <code>{st_str}</code> | LP: <code>{lp_str}</code>{vol_sent_str}\n"
                        f"  Net: <b>{np:+.2f}%</b> | Bounce: <b>{bp:+.2f}%</b>\n"
                        f"  Vol: {vol_zone} (<i>{format_usd(vol_usd)}</i>)\n"
                        f"  Time: {thc_str} | Delist in: <i>{rem_str}</i>"
                    )
                elif layer_key == "loser_l1":
                    lp_str = format_price(coin['lp'])
                    dp = (coin['st'] - curr_price) / coin['st'] * 100
                    bh = (curr_price - coin['lp']) / coin['lp'] * 100
                    final_report_strings["loser_l1"].append(
                        f"<b>• {symbol}</b>{status_emoji}{rev_tag}\n"
                        f"  Price: <code>{p_str}</code> (24h: <b>{ch24:+.2f}%</b>)\n"
                        f"  ST: <code>{st_str}</code> | LP: <code>{lp_str}</code>{vol_sent_str}\n"
                        f"  Dec: <b>{dp:.2f}%</b> | Bounce: <b>{bh:.2f}%</b>\n"
                        f"  Vol: {vol_zone} (<i>{format_usd(vol_usd)}</i>)\n"
                        f"  Time: {thc_str}"
                    )
                elif layer_key == "loser_l2":
                    hp_str = format_price(coin['hp'])
                    dropp = (coin['hp'] - curr_price) / coin['hp'] * 100
                    np = (coin['st'] - curr_price) / coin['st'] * 100
                    rem_str = format_time(max(0, DELIST_TICKS_LIMIT - coin['hc']))
                    final_report_strings["loser_l2"].append(
                        f"<b>• {symbol}</b>{status_emoji}{rev_tag}\n"
                        f"  Price: <code>{p_str}</code> (24h: <b>{ch24:+.2f}%</b>)\n"
                        f"  ST: <code>{st_str}</code> | HP: <code>{hp_str}</code>{vol_sent_str}\n"
                        f"  Net: <b>{np:+.2f}%</b> | Drop: <b>{dropp:.2f}%</b>\n"
                        f"  Vol: {vol_zone} (<i>{format_usd(vol_usd)}</i>)\n"
                        f"  Time: {thc_str} | Delist in: <i>{rem_str}</i>"
                    )
                elif layer_key == "surges":
                    final_report_strings["surges"].append(
                        f"<b>• {symbol}</b>{status_emoji} | {sent_tag} (<b>{rvol:.1f}x</b>)\n"
                        f"  Price: <code>{p_str}</code> | 24h: <b>{ch24:+.2f}%</b>\n"
                        f"  Vol: {vol_zone} (<i>{format_usd(vol_usd)}</i>)"
                    )

        # 5. Format & Send Telegram Messages
        header = "📊 <b>Binance Screening Report (Hourly)</b>"
        
        sections = [
            ("🚀 <b>Volume Surge (High Interest)</b>", "surges"),
            ("🔥 <b>Gainer (L1 - Momentum)</b>", "gainer_l1"),
            ("🏥 <b>Gainer L2 (Recovery)</b>", "gainer_l2"),
            ("🩸 <b>Loser (L1 - Bottoming)</b>", "loser_l1"),
            ("📉 <b>Loser L2 (Dead Cat)</b>", "loser_l2")
        ]
        
        first_section_msg = True
        for title, key in sections:
            items = final_report_strings[key]
            if not items:
                continue
                
            current_msg = ""
            if first_section_msg:
                current_msg += header + "\n"
                first_section_msg = False
            
            current_msg += f"\n{title}\n"
            
            for item in items:
                if len(current_msg) + len(item) + 2 > 4000:
                    send_telegram_message(current_msg.strip())
                    time.sleep(1)
                    current_msg = f"{title} (ต่อ)\n\n{item}\n"
                else:
                    current_msg += item + "\n"
            
            if current_msg:
                send_telegram_message(current_msg.strip())
                time.sleep(1)

    # 6. Save State
    new_state['_metadata'] = metadata
    save_state(new_state)
    logger.info("Process completed successfully.")

if __name__ == "__main__":
    main()
