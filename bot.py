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
    "https://cointelegraph.com/rss",                                  # Crypto Market News
    "https://insights.glassnode.com/rss",                            # Glassnode Insights (On-chain/Whales)
    "https://www.sec.gov/news/pressreleases.rss",                     # SEC Press Releases (Regulatory)
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?id=10000664" # CNBC Finance (Broad Macro)
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
    """Summarizes market-moving news using Groq with deep insight and modern HTML formatting."""
    if not GROQ_API_KEY:
        print("Error: GROQ_API_KEY environment variable is not set.")
        return None
    
    client = Groq(api_key=GROQ_API_KEY)
    
    # Advanced V2 Prompt: Elite Analyst Persona + Modern UI Formatting
    prompt = (
        "You are an Elite Macro-Crypto Market Strategist. Analyze the following news items and produce a deep-insight report in THAI. "
        "Your goal is to connect news events to 'Liquidity & Money Flow' and interest rate expectations.\n\n"
        "### REPORT STRUCTURE (MANDATORY):\n"
        "1. 📊 <b>สรุปภาวะตลาด (Executive Summary):</b>\n"
        "   - One powerful paragraph synthesizing the overall market mood and the most critical macro theme.\n\n"
        "2. <b>[Category Name]</b>\n"
        "   - Use these categories: [📌 Macro & Fed], [🐋 On-Chain & Whales], [🏢 Institutional Activity], [⚖️ Regulation & Tech].\n"
        "   - Format each news item as:\n"
        "     📰 <b>[Headline]</b>\n"
        "     <blockquote>[Deep analytical summary in Thai]</blockquote>\n"
        "     <b>Impact:</b> [Bullish/Bearish/Neutral] + brief reason.\n"
        "   - Separate individual news items with a blank line.\n\n"
        "### FORMATTING RULES (STRICT):\n"
        "- Use <b>...</b> for bold headers and important entities (e.g., <b>Fed</b>, <b>BlackRock</b>).\n"
        "- Use <code>...</code> tags ONLY for price values or short tickers (e.g., <code>$65,000</code>, <code>BTC</code>). Do NOT use it for long sentences.\n"
        "- Use <blockquote>...</blockquote> for the analytical summary text.\n"
        "- Use structural emojis for professional visual scanning.\n"
        "- If a category has no relevant news, write: 'ไม่มีความเคลื่อนไหวสำคัญในหมวดหมู่นี้'\n\n"
        "--- NEWS DATA ---\n"
    )
    
    for item in news_items:
        prompt += f"Source: {item['source']}\nTitle: {item['title']}\nSummary: {item['summary']}\n\n"
        
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a senior macro-financial analyst providing high-signal intelligence for Telegram. CRITICAL: Use ONLY Telegram-compatible HTML tags: <b>, <i>, <code>, <blockquote>. NEVER use <br>, <p>, or <div>. Output ACTUAL newlines, not the literal character \\n."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=3000,
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
            print("Telegram message sent successfully.")
            return True
        else:
            print(f"Telegram API Error: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False

def main():
    print("Starting Crypto Intelligence Bot (Groq Simple)...")
    
    # 1. Scrape aggregated news from Macro and Crypto sources
    news_items = get_aggregated_news(RSS_FEEDS, limit_per_source=5)
    
    if not news_items:
        print("No news items retrieved. Exiting.")
        return
    
    # Cap total news items at 20
    if len(news_items) > 20:
        news_items = news_items[:20]
        
    # 2. Categorize and Analyze with Groq
    print(f"Analyzing {len(news_items)} news items...")
    summary_text = summarize_market_news(news_items)
    
    if not summary_text:
        print("Failed to generate report. Exiting.")
        return

    # Basic cleanup
    summary_text = summary_text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    summary_text = summary_text.replace("\\n", "\n")
        
    # 3. Send to Telegram
    print("Sending report to Telegram...")
    send_telegram_message(summary_text)
    
    print("Process completed.")

if __name__ == "__main__":
    main()
