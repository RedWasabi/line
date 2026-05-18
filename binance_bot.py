import os
import json
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GIST_ID = os.environ.get("GIST_ID")
GH_PAT = os.environ.get("GH_PAT")
BINANCE_TELEGRAM_BOT_TOKEN = os.environ.get("BINANCE_TELEGRAM_BOT_TOKEN")
BINANCE_TELEGRAM_CHAT_ID = os.environ.get("BINANCE_TELEGRAM_CHAT_ID")

# Use data-api.binance.vision (Official Public Data Mirror) to bypass US regional blocks on GitHub runners
BINANCE_BASE_URL = "https://data-api.binance.vision/api/v3"
GIST_API_URL = f"https://api.github.com/gists/{GIST_ID}"

def load_state():
    """Loads the watchlist state from a GitHub Gist."""
    if not GIST_ID or not GH_PAT:
        print("GIST_ID or GH_PAT not set. Starting with empty state.")
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
                print("Old schema detected. Resetting state for 4-layer logic.")
                return {}
            return data
        else:
            print(f"Failed to load Gist: {response.status_code} {response.text}")
            return {}
    except Exception as e:
        print(f"Error loading Gist: {e}")
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
            print("State saved to Gist successfully.")
        else:
            print(f"Failed to save Gist: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error saving Gist: {e}")

def get_binance_tickers():
    """Fetches all 24h tickers from Binance."""
    url = f"{BINANCE_BASE_URL}/ticker/24hr"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch Binance data: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching Binance data: {e}")
        return []

def get_recent_high_low(symbol):
    """Fetches the high and low of the last two 15m candles to capture intra-tick spikes."""
    url = f"{BINANCE_BASE_URL}/klines"
    params = {"symbol": symbol, "interval": "15m", "limit": 2}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            klines = response.json()
            if not klines:
                return None, None
            # Extract High (index 2) and Low (index 3) from both candles
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            return max(highs), min(lows)
        else:
            print(f"Klines API Error for {symbol}: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Error fetching Klines for {symbol}: {e}")
        return None, None

def send_telegram_message(text):
    """Sends the report to Telegram."""
    if not BINANCE_TELEGRAM_BOT_TOKEN or not BINANCE_TELEGRAM_CHAT_ID:
        print("Telegram credentials not set.")
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
            print("Binance report sent to Telegram.")
        else:
            print(f"Telegram API Error: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

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
    print("Starting Multi-Layer Binance Screening Bot (15m Frequency)...")
    
    # 1. Load existing state
    state_full = load_state()
    # Separate metadata from coins
    metadata = state_full.pop('_metadata', {"tick": 0})
    state = state_full
    
    metadata['tick'] += 1
    # Send Telegram every 4th run (1 hour)
    should_send = (metadata['tick'] % 4 == 0)
    if should_send:
        metadata['tick'] = 0  # Reset to 0 after reporting to keep it clean
    print(f"Run Tick: {metadata['tick']} | Should send report: {should_send}")
    
    # Global Increment: Initialize 'thc' if missing, then increment for all existing coins
    for symbol in state:
        if 'thc' not in state[symbol]:
            state[symbol]['thc'] = state[symbol].get('hc', 0)
        state[symbol]['thc'] += 1
    
    # 2. Fetch fresh Binance data
    tickers = get_binance_tickers()
    if not tickers:
        return

    # Filter for USDT pairs, significant volume (>$1M), and active trading (bidPrice > 0)
    usdt_tickers = [
        t for t in tickers 
        if t['symbol'].endswith('USDT') 
        and float(t['quoteVolume']) >= 1_000_000
        and float(t.get('bidPrice', 0)) > 0
    ]
    
    # Sort to find Top 10 Gainers and Top 10 Losers (24h change)
    sorted_tickers = sorted(usdt_tickers, key=lambda x: float(x['priceChangePercent']), reverse=True)
    top_gainers = sorted_tickers[:10]
    top_losers = sorted_tickers[-10:]

    ticker_map = {t['symbol']: t for t in usdt_tickers}
    
    # 3. Add New Coins & Handle Trend Crossovers (Ultimate Reversal)
    for t in top_gainers:
        symbol = t['symbol']
        curr_price = float(t['lastPrice'])
        
        # New coin OR Trend Crossover (Loser -> Gainer)
        if symbol not in state or state[symbol]['layer'].startswith('loser'):
            if symbol in state:
                print(f"🔄 Reversal: Moving {symbol} from Loser to Gainer L1")
            
            state[symbol] = {
                "layer": "gainer_l1",
                "st": curr_price,
                "hp": curr_price,
                "lp": None,
                "hc": 0,
                "thc": 0,
                "rev": True if symbol in state else False
            }
            print(f"Added {symbol} to Gainer L1")

    for t in top_losers:
        symbol = t['symbol']
        curr_price = float(t['lastPrice'])
        
        # New coin OR Trend Crossover (Gainer -> Loser)
        if symbol not in state or state[symbol]['layer'].startswith('gainer'):
            if symbol in state:
                print(f"🔄 Reversal: Moving {symbol} from Gainer to Loser L1")
                
            state[symbol] = {
                "layer": "loser_l1",
                "st": curr_price,
                "lp": curr_price,
                "hp": None,
                "hc": 0,
                "thc": 0,
                "rev": True if symbol in state else False
            }
            print(f"Added {symbol} to Loser L1")

    # 4. Process State Transitions & Collect Data for Reports
    new_state = {}
    # Use objects to store data before sorting
    report_data = {
        "gainer_l1": [],
        "gainer_l2": [],
        "loser_l1": [],
        "loser_l2": []
    }
    
    for symbol, coin in state.items():
        if symbol not in ticker_map:
            continue
            
        ticker = ticker_map[symbol]
        curr_price = float(ticker['lastPrice'])
        vol_usd = float(ticker['quoteVolume'])
        ch24 = float(ticker['priceChangePercent'])
        
        # Fetch Intra-tick Spikes (15m Klines)
        k_high, k_low = get_recent_high_low(symbol)
        
        # Pass 1: Handle Transitions & Updates
        current_layer = coin['layer']
        
        if current_layer == "gainer_l1":
            # Track Session High (Momentum)
            obs_high = max(curr_price, k_high) if k_high else curr_price
            coin['hp'] = max(coin['hp'], obs_high)
            
            # Check for 10% Drop -> Move to L2 (Recovery)
            drop_check = (coin['hp'] - curr_price) / coin['hp'] * 100
            if drop_check > 10 and coin['thc'] > 0:
                coin.update({"layer": "gainer_l2", "lp": curr_price, "hc": 0})
                
        elif current_layer == "gainer_l2":
            coin['hc'] += 1
            # Track Session Low (Correction Bottom)
            obs_low = min(curr_price, k_low) if k_low else curr_price
            coin['lp'] = min(coin['lp'] if coin['lp'] is not None else curr_price, obs_low)
            
            # Check for 20% Bounce -> Move back to L1 (Momentum)
            bounce_check = (curr_price - coin['lp']) / coin['lp'] * 100
            if bounce_check > 20:
                coin.update({"layer": "gainer_l1", "st": curr_price, "hp": curr_price, "lp": None, "hc": 0})
            elif coin['hc'] >= 288: # 72 hours * 4 ticks/hr
                print(f"Delisted {symbol} from Gainer L2 (Timeout)")
                continue

        elif current_layer == "loser_l1":
            # Track Session Low (Bottoming)
            obs_low = min(curr_price, k_low) if k_low else curr_price
            coin['lp'] = min(coin['lp'] if coin['lp'] is not None else curr_price, obs_low)
            
            # Check for 10% Bounce -> Move to L2 (Dead Cat)
            bounce_check = (curr_price - coin['lp']) / coin['lp'] * 100
            if bounce_check > 10 and coin['thc'] > 0:
                coin.update({"layer": "loser_l2", "hp": curr_price, "hc": 0})

        elif current_layer == "loser_l2":
            coin['hc'] += 1
            # Track Session High (Bounce Peak)
            obs_high = max(curr_price, k_high) if k_high else curr_price
            coin['hp'] = max(coin['hp'] if coin['hp'] is not None else curr_price, obs_high)
            
            # Check for 20% Drop -> Move back to L1 (Bottoming)
            drop_check = (coin['hp'] - curr_price) / coin['hp'] * 100
            if drop_check > 20:
                coin.update({"layer": "loser_l1", "st": curr_price, "lp": curr_price, "hp": None, "hc": 0})
            elif coin['hc'] >= 288: # 72 hours * 4 ticks/hr
                print(f"Delisted {symbol} from Loser L2 (Timeout)")
                continue

        # Collect data for Pass 2 (Only if we are sending)
        if should_send:
            final_layer = coin['layer']
            report_data[final_layer].append({
                "symbol": symbol,
                "coin": coin.copy(),
                "curr_price": curr_price,
                "vol_usd": vol_usd,
                "ch24": ch24
            })
        
        # Reset reversal tag after processing
        if 'rev' in coin:
            coin['rev'] = False
        new_state[symbol] = coin

    # Pass 2: Sort and Format Reports (Only if we are sending)
    if should_send:
        final_report_strings = {k: [] for k in report_data.keys()}
        
        for layer_key, coins_list in report_data.items():
            # Sort by total tick count (thc) descending: longest at the top
            sorted_coins = sorted(coins_list, key=lambda x: x['coin']['thc'], reverse=True)
            
            for item in sorted_coins:
                symbol = item['symbol']
                coin = item['coin']
                curr_price = item['curr_price']
                vol_usd = item['vol_usd']
                ch24 = item['ch24']
                
                thc_str = format_time(coin['thc'])
                p_str = format_price(curr_price)
                st_str = format_price(coin['st']) if coin['st'] else "N/A"
                # Determine Reversal Tag with "Colors" (Emojis)
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
                        f"<b>• {symbol}</b>{rev_tag}\n"
                        f"  Price: <code>{p_str}</code> (24h: <b>{ch24:+.2f}%</b>)\n"
                        f"  ST: <code>{st_str}</code> | HP: <code>{hp_str}</code>\n"
                        f"  Inc: <b>{ip:+.2f}%</b> | Drop: <b>{dh:.2f}%</b>\n"
                        f"  Vol: {vol_zone} (<i>{format_usd(vol_usd)}</i>)\n"
                        f"  Time: {thc_str}"
                    )
                elif layer_key == "gainer_l2":
                    lp_str = format_price(coin['lp'])
                    bp = (curr_price - coin['lp']) / coin['lp'] * 100
                    rem_str = format_time(max(0, 288 - coin['hc']))
                    final_report_strings["gainer_l2"].append(
                        f"<b>• {symbol}</b>{rev_tag}\n"
                        f"  Price: <code>{p_str}</code> (24h: <b>{ch24:+.2f}%</b>)\n"
                        f"  LP: <code>{lp_str}</code> | Bounce: <b>{bp:+.2f}%</b>\n"
                        f"  Vol: {vol_zone} (<i>{format_usd(vol_usd)}</i>)\n"
                        f"  Time: {thc_str} | Delist in: <i>{rem_str}</i>"
                    )
                elif layer_key == "loser_l1":
                    lp_str = format_price(coin['lp'])
                    dp = (coin['st'] - curr_price) / coin['st'] * 100
                    bh = (curr_price - coin['lp']) / coin['lp'] * 100
                    final_report_strings["loser_l1"].append(
                        f"<b>• {symbol}</b>{rev_tag}\n"
                        f"  Price: <code>{p_str}</code> (24h: <b>{ch24:+.2f}%</b>)\n"
                        f"  ST: <code>{st_str}</code> | LP: <code>{lp_str}</code>\n"
                        f"  Dec: <b>{dp:.2f}%</b> | Bounce: <b>{bh:.2f}%</b>\n"
                        f"  Vol: {vol_zone} (<i>{format_usd(vol_usd)}</i>)\n"
                        f"  Time: {thc_str}"
                    )
                elif layer_key == "loser_l2":
                    hp_str = format_price(coin['hp'])
                    dropp = (coin['hp'] - curr_price) / coin['hp'] * 100
                    rem_str = format_time(max(0, 288 - coin['hc']))
                    final_report_strings["loser_l2"].append(
                        f"<b>• {symbol}</b>{rev_tag}\n"
                        f"  Price: <code>{p_str}</code> (24h: <b>{ch24:+.2f}%</b>)\n"
                        f"  HP: <code>{hp_str}</code> | Drop: <b>{dropp:.2f}%</b>\n"
                        f"  Vol: {vol_zone} (<i>{format_usd(vol_usd)}</i>)\n"
                        f"  Time: {thc_str} | Delist in: <i>{rem_str}</i>"
                    )

        # 5. Format & Send Telegram Messages
        header = "📊 <b>Binance Screening Report (Hourly)</b>"
        
        sections = [
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
    print("Process completed.")

if __name__ == "__main__":
    main()
