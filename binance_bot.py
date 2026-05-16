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

def load_watchlist():
    """Loads the watchlist from a GitHub Gist."""
    if not GIST_ID or not GH_PAT:
        print("GIST_ID or GH_PAT not set. Starting with empty watchlist.")
        return {}
    
    headers = {"Authorization": f"token {GH_PAT}"}
    try:
        response = requests.get(GIST_API_URL, headers=headers)
        if response.status_code == 200:
            gist_data = response.json()
            content = gist_data['files']['watchlist.json']['content']
            return json.loads(content)
        else:
            print(f"Failed to load Gist: {response.status_code} {response.text}")
            return {}
    except Exception as e:
        print(f"Error loading Gist: {e}")
        return {}

def save_watchlist(watchlist):
    """Saves the watchlist to the GitHub Gist."""
    if not GIST_ID or not GH_PAT:
        return
    
    headers = {
        "Authorization": f"token {GH_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "files": {
            "watchlist.json": {
                "content": json.dumps(watchlist, indent=2)
            }
        }
    }
    try:
        response = requests.patch(GIST_API_URL, headers=headers, json=data)
        if response.status_code == 200:
            print("Watchlist saved to Gist successfully.")
        else:
            print(f"Failed to save Gist: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error saving Gist: {e}")

def get_binance_tickers():
    """Fetches all 24h tickers from Binance and filters for USDT pairs."""
    try:
        response = requests.get(BINANCE_API_URL)
        if response.status_code == 200:
            tickers = response.json()
            # Filter for USDT pairs and ensure they are actually coins (not leveraged tokens or stable pairs if possible, but keeping it simple as requested)
            usdt_tickers = [t for t in tickers if t['symbol'].endswith('USDT')]
            return usdt_tickers
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
    print("Starting Binance Price Tracking Bot...")
    
    # 1. Load existing watchlist
    watchlist = load_watchlist()
    
    # 2. Fetch fresh Binance data
    tickers = get_binance_tickers()
    if not tickers:
        return

    # Sort to find Top 10 Gainers and Top 10 Losers (24h change)
    sorted_tickers = sorted(tickers, key=lambda x: float(x['priceChangePercent']), reverse=True)
    top_gainers = sorted_tickers[:10]
    top_losers = sorted_tickers[-10:]

    # Map current tickers for easy lookup
    ticker_map = {t['symbol']: t for t in tickers}
    
    # 3. Process Watchlist
    new_watchlist = {}
    delisted_coins = []
    report_lines = ["📊 Binance Hourly Watchlist Report"]
    
    # Combine existing watchlist symbols and new top 10s
    all_monitored_symbols = set(watchlist.keys()) | {t['symbol'] for t in top_gainers} | {t['symbol'] for t in top_losers}
    
    for symbol in all_monitored_symbols:
        if symbol not in ticker_map:
            continue
            
        ticker = ticker_map[symbol]
        curr_price = float(ticker['lastPrice'])
        vol_usd = float(ticker['quoteVolume'])
        
        # Determine if it's a new entry or update
        if symbol in watchlist:
            entry = watchlist[symbol]
            extreme_price = entry['extreme_price']
            last_hour_price = entry.get('last_hour_price', curr_price)
            coin_type = entry['type']
            
            # Update extreme price
            if coin_type == "gainer":
                if curr_price > extreme_price:
                    extreme_price = curr_price
                # Check Delist: Dropped 15% from high
                if curr_price <= (extreme_price * 0.85):
                    delisted_coins.append(f"{symbol} (High reversed -15%)")
                    continue
            else: # loser
                if curr_price < extreme_price:
                    extreme_price = curr_price
                # Check Delist: Rose 15% from low
                if curr_price >= (extreme_price * 1.15):
                    delisted_coins.append(f"{symbol} (Low reversed +15%)")
                    continue
        else:
            # New Entry
            coin_type = "gainer" if any(t['symbol'] == symbol for t in top_gainers) else "loser"
            extreme_price = curr_price
            last_hour_price = curr_price
            
        # Calculate 1h change
        hour_change = ((curr_price - last_hour_price) / last_hour_price * 100) if last_hour_price else 0
        
        # Update/Add to new watchlist
        new_watchlist[symbol] = {
            "type": coin_type,
            "extreme_price": extreme_price,
            "last_hour_price": curr_price # Update for next hour
        }
        
        # Add to report
        type_icon = "📈" if coin_type == "gainer" else "📉"
        report_lines.append(
            f"\n{type_icon} {symbol}\n"
            f"Price: {curr_price:,.4f}\n"
            f"1h Change: {hour_change:+.2f}%\n"
            f"Vol USD: ${vol_usd:,.0f}"
        )

    if delisted_coins:
        report_lines.append("\n\n🚫 Removed from Watchlist:")
        for coin in delisted_coins:
            report_lines.append(f"- {coin}")

    if len(report_lines) > 1:
        send_line_message("\n".join(report_lines))
    else:
        print("Watchlist is empty, no report sent.")

    # 4. Save state
    save_watchlist(new_watchlist)
    print("Process completed.")

if __name__ == "__main__":
    main()
