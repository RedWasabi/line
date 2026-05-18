import os
import time
import feedparser
import requests
from openai import OpenAI
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
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
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
    """Summarizes market-moving news using OpenRouter with deep insight and modern HTML formatting."""
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        return None
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )
    
    # Advanced V2 Prompt: Elite Analyst Persona + Modern UI Formatting
    prompt = (
        "You are an Elite Macro-Crypto Market Strategist. Analyze the following news items and produce a deep-insight report in THAI. "
        "Your goal is to connect news events to 'Liquidity & Money Flow' and interest rate expectations.\n\n"
        "### REPORT STRUCTURE (MANDATORY):\n"
        "1. 📊 <b>สรุปภาวะตลาด (Executive Summary):</b>\n"
        "   - One powerful paragraph synthesizing the overall market mood and the most critical macro theme (e.g., Fed posture, inflation trajectory, institutional shifts).\n\n"
        "2. <b>[Category Name]</b>\n"
        "   - Use these categories: [📌 Macro & Fed], [🐋 On-Chain & Whales], [🏢 Institutional Activity], [⚖️ Regulation & Tech].\n"
        "   - Use <blockquote>...</blockquote> for each news item under a category.\n"
        "   - Inside the blockquote: <b>[Headline]</b> followed by a deep analytical summary in Thai.\n"
        "   - Focus on *why* this matters for liquidity or capital flight.\n"
        "   - Use <i>Impact:</i> [Bullish/Bearish/Neutral] + brief reason.\n\n"
        "### FORMATTING RULES (STRICT):\n"
        "- Use <b>...</b> for bold headers and key entities (e.g., <b>Fed</b>, <b>BlackRock</b>).\n"
        "- ALWAYS wrap all numbers, percentages, dates, and asset tickers in <code>...</code> tags (e.g., <code>$65,000</code>, <code>+3.4%</code>, <code>BTC</code>).\n"
        "- Use structural emojis for professional visual scanning.\n"
        "- If a category has no relevant news, write: 'ไม่มีความเคลื่อนไหวสำคัญในหมวดหมู่นี้'\n\n"
        "--- NEWS DATA ---\n"
    )
    
    for item in news_items:
        prompt += f"Source: {item['source']}\nTitle: {item['title']}\nSummary: {item['summary']}\n\n"
        
    completion = client.chat.completions.create(
        model="openrouter/owl-alpha",
        messages=[
            {"role": "system", "content": "You are a senior macro-financial analyst providing high-signal intelligence for Telegram. CRITICAL: Use ONLY Telegram-compatible HTML tags: <b>, <i>, <code>, <blockquote>. NEVER use <br>, <p>, or <div>. Use newlines (\n) for line breaks."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=3000,
    )
    return completion.choices[0].message.content

def send_telegram_message(text):
    """Sends the summarized text to Telegram, splitting if it exceeds the 4,096 character limit.
    Ensures HTML tags are properly closed and reopened across parts.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variable is not set.")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    MAX_LEN = 4000
    
    def get_open_tags(html_part):
        """Helper to find unclosed tags in a string."""
        tags = ["b", "i", "code", "blockquote"]
        open_tags = []
        import re
        # Find all tags
        all_tags = re.findall(r"<(/?)(b|i|code|blockquote)>", html_part)
        for is_closing, tag_name in all_tags:
            if is_closing:
                if open_tags and open_tags[-1] == tag_name:
                    open_tags.pop()
            else:
                open_tags.append(tag_name)
        return open_tags

    parts = []
    remaining_text = text
    active_tags = []

    while len(remaining_text) > MAX_LEN or active_tags:
        # Determine the chunk size. Leave room for closing/opening tags.
        # Estimate: each tag needs 10-15 chars for closing/opening.
        buffer = 150 # Safety buffer for tags and page indicators
        limit = MAX_LEN - buffer
        
        if len(remaining_text) <= limit and not active_tags:
            parts.append(remaining_text)
            break
            
        # Find a good split point
        split_idx = remaining_text.rfind("\n\n", 0, limit)
        if split_idx == -1:
            split_idx = remaining_text.rfind("\n", 0, limit)
        if split_idx == -1:
            split_idx = limit
            
        current_chunk = remaining_text[:split_idx]
        
        # Balance tags for this chunk
        new_open_tags = get_open_tags(current_chunk)
        
        # Final text for this part starts with current active tags from previous part
        prefix = "".join([f"<{t}>" for t in active_tags])
        
        # Tags that need to be closed at the end of this chunk
        all_active_now = active_tags + new_open_tags
        suffix = "".join([f"</{t}>" for t in reversed(all_active_now)])
        
        parts.append(prefix + current_chunk + suffix)
        
        # Prepare for next loop
        remaining_text = remaining_text[split_idx:].strip()
        active_tags = all_active_now
        
        # If we have no remaining text but active tags (shouldn't happen with good LLM), break
        if not remaining_text:
            break

    # If the loop finished and there's still a tiny bit of text left
    if remaining_text:
        prefix = "".join([f"<{t}>" for t in active_tags])
        parts.append(prefix + remaining_text)

    success = True
    for i, part in enumerate(parts):
        page_indicator = f" (หน้า {i+1}/{len(parts)})"
        current_text = part + page_indicator

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": current_text,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print(f"Telegram part {i+1} sent successfully.")
            else:
                print(f"Telegram API Error (Part {i+1}): {response.status_code} {response.text}")
                # Log the failing part for debugging (truncated)
                print(f"Content Sample: {current_text[:100]}...{current_text[-100:]}")
                success = False
            if len(parts) > 1:
                time.sleep(1.5)
        except Exception as e:
            print(f"Error sending Telegram part {i+1}: {e}")
            success = False
            
    return success

def main():
    print("Starting Crypto Intelligence Upgrade Bot...")
    
    # 1. Scrape aggregated news from Macro and Crypto sources
    # Limit per source to 5 to keep the total manageable
    news_items = get_aggregated_news(RSS_FEEDS, limit_per_source=5)
    
    if not news_items:
        print("No news items retrieved from any source. Exiting.")
        return
    
    # Cap total news items at 20 to ensure performance and prevent token overflow
    if len(news_items) > 20:
        print(f"Capping news items from {len(news_items)} to 20 for optimal analysis.")
        news_items = news_items[:20]
        
    # 2. Categorize and Analyze with OpenRouter
    print(f"Analyzing {len(news_items)} news items for market impact...")
    summary_text = summarize_market_news(news_items)
    
    if not summary_text:
        print("Failed to generate intelligence report. Exiting.")
        return

    # Post-processing: Remove unsupported HTML tags like <br> which cause Telegram 400 errors
    summary_text = summary_text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        
    # 3. Send to Telegram
    print("Sending categorized intelligence report to Telegram...")
    send_telegram_message(summary_text)
    
    print("Process completed.")

if __name__ == "__main__":
    main()
