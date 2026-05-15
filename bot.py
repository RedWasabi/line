import os
import time
import feedparser
from google import genai
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError
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
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

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
    """Summarizes market-moving news using Gemini with strict categorization and Thai output."""
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY environment variable is not set.")
        return None
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Highly structured prompt for Categorized Analysis
    prompt = (
        "You are a Senior Crypto Market Analyst specializing in Macro-Economics and Institutional Flows. "
        "Analyze the following news items and produce a report in THAI using the EXACT format below.\n\n"
        "### TASK:\n"
        "1. FILTER for high-impact events: Jerome Powell speeches, Fed decisions, CPI/Inflation data, BlackRock/MicroStrategy moves, SEC/Regulatory actions.\n"
        "2. CATEGORIZE the news into three specific tags: [📌 Macro & Fed], [🏢 Institutional Activity], and [⚖️ Regulation & Tech].\n"
        "3. For each news item, provide a concise Thai summary and a 'Market Sentiment' (Bullish/Bearish/Neutral) for Bitcoin with a brief reason.\n\n"
        "### FORMAT RULES:\n"
        "- Use clear headers for each tag.\n"
        "- Use bullet points.\n"
        "- If a category has no relevant news, write: 'ไม่มีข่าวสำคัญในหมวดหมู่นี้'\n"
        "- Keep it professional and concise.\n\n"
        "--- NEWS DATA ---\n"
    )
    
    for item in news_items:
        prompt += f"Source: {item['source']}\nTitle: {item['title']}\nSummary: {item['summary']}\n\n"
        
    response = client.models.generate_content(
        model='gemini-1.5-flash-lite',
        contents=prompt
    )
    return response.text

def send_line_message(text):
    """Sends the summarized text to LINE."""
    if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
        print("Error: LINE_ACCESS_TOKEN or LINE_USER_ID environment variable is not set.")
        return False
        
    try:
        line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
        print("Categorized market analysis sent successfully via LINE.")
        return True
    except LineBotApiError as e:
        print(f"Line Bot API Error: {e.status_code} {e.error.message}")
        return False
    except Exception as e:
        print(f"Error sending LINE message: {e}")
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
        
    # 3. Send to LINE
    print("Sending categorized intelligence report to LINE...")
    send_line_message(summary_text)
    
    print("Process completed.")

if __name__ == "__main__":
    main()
