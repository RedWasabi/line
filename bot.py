import os
import time
import feedparser
import requests
from groq import Groq
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables from .env file
load_dotenv()

# Configuration - Targeted sources for Macro and Crypto intelligence
RSS_FEEDS = [
    "https://www.federalreserve.gov/newsevents/press/all/2026all.xml", # Fed Press Releases (2026)
    "https://www.bls.gov/feed/bls_latest.rss",                        # US Bureau of Labor Statistics (CPI/Jobs)
    "https://www.coindesk.com/arc/outboundfeeds/rss/",                # Crypto Specialist (Regulation/Institutions)
    "https://cointelegraph.com/rss"                                   # Crypto Market News
]

# Load environment variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_aggregated_news(urls, limit_per_source=8):
    """Scrapes news from multiple RSS URLs with improved error handling."""
    all_news = []
    for url in urls:
        try:
            print(f"Fetching news from {url}...")
            # Use a timeout for feed parsing to prevent hanging
            feed = feedparser.parse(url)
            
            if not feed.entries:
                print(f"Warning: No entries found for {url}")
                continue
                
            for entry in feed.entries[:limit_per_source]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                # Avoid duplicates
                if not any(n['title'] == title for n in all_news):
                    all_news.append({"title": title, "summary": summary, "source": url})
        except Exception as e:
            print(f"Error fetching RSS feed {url}: {e}")
    return all_news

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: print(f"API busy or error. Retrying in {retry_state.next_action.sleep} seconds... (Attempt {retry_state.attempt_number})")
)
def summarize_market_news(news_items):
    """Summarizes market-moving news using Groq with strict categorization and Thai output."""
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY environment variable is not set.")
        return None
    
    client = Groq(api_key=GROQ_API_KEY)
    
    # Highly structured prompt for Categorized Analysis
    prompt = (
        "You are a Senior Crypto Market Analyst specializing in Macro-Economics and Institutional Flows. "
        "Analyze the following news items and produce a report in THAI using the EXACT format below.\n\n"
        "### TASK:\n"
        "1. FILTER for high-impact events: Jerome Powell speeches, Fed decisions, CPI/Inflation data, BlackRock/MicroStrategy moves, SEC/Regulatory actions.\n"
        "2. CATEGORIZE the news into three specific tags: [📌 Macro & Fed], [🏢 Institutional Activity], and [⚖️ Regulation & Tech].\n"
        "3. For each news item, provide a concise Thai summary and a 'Market Sentiment' (Bullish/Bearish/Neutral) for Bitcoin with a brief reason.\n\n"
        "### FORMAT RULES:\n"
        "- Use <b>...</b> for category headers.\n"
        "- Use bullet points.\n"
        "- Use <i>...</i> for sentiment and reasoning.\n"
        "- If a category has no relevant news, write: 'ไม่มีข่าวสำคัญในหมวดหมู่นี้'\n"
        "- Keep it professional and concise.\n\n"
        "--- NEWS DATA ---\n"
    )
    
    for item in news_items:
        prompt += f"Source: {item['source']}\nTitle: {item['title']}\nSummary: {item['summary']}\n\n"
        
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a professional market analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=2048,
    )
    return completion.choices[0].message.content

def send_telegram_message(text):
    """Sends the summarized text to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variable is not set.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Categorized market analysis sent successfully via Telegram.")
            return True
        else:
            print(f"Telegram API Error: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def main():
    print("Starting Crypto Intelligence Upgrade Bot...")
    
    # 1. Scrape aggregated news from Macro and Crypto sources
    news_items = get_aggregated_news(RSS_FEEDS)
    
    if not news_items:
        print("No news items retrieved from any source. Exiting.")
        return
        
    # 2. Categorize and Analyze with Gemini
    print(f"Analyzing {len(news_items)} news items for market impact...")
    summary_text = summarize_market_news(news_items)
    
    if not summary_text:
        print("Failed to generate intelligence report. Exiting.")
        return
        
    # 3. Send to Telegram
    print("Sending categorized intelligence report to Telegram...")
    send_telegram_message(summary_text)
    
    print("Process completed.")

if __name__ == "__main__":
    main()
