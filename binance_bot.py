import os
import json
import requests
from linebot import LineBotApi
from linebot.models import TextSendMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
GIST_ID = os.environ.get("GIST_ID")
GH_PAT = os.environ.get("GH_PAT")
LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

# Use data-api.binance.vision (Official Public Data Mirror) to bypass US regional blocks on GitHub runners
BINANCE_API_URL = "https://data-api.binance.vision/api/v3/ticker/24hr"
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
            # Basic schema check: ensure items have 'layer' key. If not, reset to avoid crashes.
            if data and not all('layer' in v for v in data.values()):
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
    try:
        response = requests.get(BINANCE_API_URL)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch Binance data: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching Binance data: {e}")
        return []

def send_line_message(text):
    """Sends the report to LINE."""
    if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
        print("LINE credentials not set.")
        return
    try:
        line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
        print("Binance report sent to LINE.")
    except Exception as e:
        print(f"Error sending LINE message: {e}")

def main():
    print("Starting Multi-Layer Binance Screening Bot...")
    
    # 1. Load existing state
    state = load_state()
    
    # 2. Fetch fresh Binance data
    tickers = get_binance_tickers()
    if not tickers:
        return

    # Filter for USDT pairs and significant volume
    usdt_tickers = [t for t in tickers if t['symbol'].endswith('USDT')]
    
    # Sort to find Top 10 Gainers and Top 10 Losers (24h change)
    sorted_tickers = sorted(usdt_tickers, key=lambda x: float(x['priceChangePercent']), reverse=True)
    top_gainers = sorted_tickers[:10]
    top_losers = sorted_tickers[-10:]

    ticker_map = {t['symbol']: t for t in usdt_tickers}
    
    # 3. Add New Coins (Anti-Duplication)
    for t in top_gainers:
        symbol = t['symbol']
        if symbol not in state:
            curr_price = float(t['lastPrice'])
            state[symbol] = {
                "layer": "gainer_l1",
                "st": curr_price,
                "hp": curr_price,
                "lp": None,
                "hc": 0
            }
            print(f"Added {symbol} to Gainer L1")

    for t in top_losers:
        symbol = t['symbol']
        if symbol not in state:
            curr_price = float(t['lastPrice'])
            state[symbol] = {
                "layer": "loser_l1",
                "st": curr_price,
                "lp": curr_price,
                "hp": None,
                "hc": 0
            }
            print(f"Added {symbol} to Loser L1")

    # 4. Process State Transitions
    new_state = {}
    reports = {
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
        layer = coin['layer']
        
        # Transition Logic
        if layer == "gainer_l1":
            # Update HP
            if curr_price > coin['hp']:
                coin['hp'] = curr_price
            
            dh = (coin['hp'] - curr_price) / coin['hp'] * 100
            ip = (curr_price - coin['st']) / coin['st'] * 100
            
            if dh > 15: # Transfer to L2
                coin.update({"layer": "gainer_l2", "lp": curr_price, "hc": 0})
            else:
                reports["gainer_l1"].append(
                    f"• {symbol}\n  Price: {curr_price:,.4f}\n  ST: {coin['st']:,.4f} | HP: {coin['hp']:,.4f}\n  Inc: {ip:+.2f}% | Drop: {dh:.2f}%\n  Vol: ${vol_usd:,.0f}"
                )

        elif layer == "gainer_l2":
            coin['hc'] += 1
            if curr_price < coin['lp']:
                coin['lp'] = curr_price
            
            bp = (curr_price - coin['lp']) / coin['lp'] * 100
            
            if bp > 20: # Promote to L1
                coin.update({"layer": "gainer_l1", "st": curr_price, "hp": curr_price, "hc": 0})
            elif coin['hc'] >= 72 and bp <= 20: # Delist
                print(f"Delisted {symbol} from Gainer L2 (Timeout)")
                continue 
            else:
                reports["gainer_l2"].append(
                    f"• {symbol}\n  Price: {curr_price:,.4f}\n  LP: {coin['lp']:,.4f}\n  Bounce: {bp:+.2f}% | HC: {coin['hc']}h"
                )

        elif layer == "loser_l1":
            if curr_price < coin['lp']:
                coin['lp'] = curr_price
                
            bh = (curr_price - coin['lp']) / coin['lp'] * 100
            dp = (coin['st'] - curr_price) / coin['st'] * 100
            
            if bh > 15: # Transfer to L2
                coin.update({"layer": "loser_l2", "hp": curr_price, "hc": 0})
            else:
                reports["loser_l1"].append(
                    f"• {symbol}\n  Price: {curr_price:,.4f}\n  ST: {coin['st']:,.4f} | LP: {coin['lp']:,.4f}\n  Dec: {dp:.2f}% | Bounce: {bh:.2f}%\n  Vol: ${vol_usd:,.0f}"
                )

        elif layer == "loser_l2":
            coin['hc'] += 1
            if curr_price > coin['hp']:
                coin['hp'] = curr_price
            
            dropp = (coin['hp'] - curr_price) / coin['hp'] * 100
            
            if dropp > 20: # Promote to L1
                coin.update({"layer": "loser_l1", "st": curr_price, "lp": curr_price, "hc": 0})
            elif coin['hc'] >= 72 and dropp <= 20: # Delist
                print(f"Delisted {symbol} from Loser L2 (Timeout)")
                continue
            else:
                reports["loser_l2"].append(
                    f"• {symbol}\n  Price: {curr_price:,.4f}\n  HP: {coin['hp']:,.4f}\n  Drop: {dropp:.2f}% | HC: {coin['hc']}h"
                )
        
        new_state[symbol] = coin

    # 5. Format & Send LINE Message
    final_report = ["📊 Binance Screening Report"]
    
    sections = [
        ("🔥 Gainer (L1 - Momentum)", "gainer_l1"),
        ("🏥 Gainer L2 (Recovery)", "gainer_l2"),
        ("🩸 Loser (L1 - Bottoming)", "loser_l1"),
        ("📉 Loser L2 (Dead Cat)", "loser_l2")
    ]
    
    has_content = False
    for title, key in sections:
        if reports[key]:
            final_report.append(f"\n{title}")
            final_report.extend(reports[key])
            has_content = True

    if has_content:
        send_line_message("\n".join(final_report))
    else:
        print("No active coins to report.")

    # 6. Save State
    save_state(new_state)
    print("Process completed.")

if __name__ == "__main__":
    main()
