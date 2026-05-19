import os
import time
import feedparser
import requests
import html
import re
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
            feed = feedparser.parse(url)
            if not feed.entries:
                continue
            for entry in feed.entries[:limit_per_source]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
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
        "- Use <b>...</b> for bold headers and important entities.\n"
        "- Use <code>...</code> tags ONLY for price values or short tickers.\n"
        "- Use <blockquote>...</blockquote> for the analytical summary text.\n"
        "- Use ONLY Telegram-compatible HTML tags: <b>, <i>, <code>, <blockquote>.\n"
        "- NEVER use <br>, <p>, or <div> tags.\n"
        "--- NEWS DATA ---\n"
    )
    
    for item in news_items:
        prompt += f"Source: {item['source']}\nTitle: {item['title']}\nSummary: {item['summary']}\n\n"
        
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a senior macro-financial analyst providing high-signal intelligence for Telegram. CRITICAL: Use ONLY <b>, <i>, <code>, <blockquote>. Strip all attributes. Escape all special characters like <, >, & except for these tags."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=3000,
    )
    return completion.choices[0].message.content

def bulletproof_sanitizer(text):
    """Deeply sanitizes LLM output to ensure perfect Telegram HTML compatibility (v2.10)."""
    # 1. First, escape all existing HTML characters to neutralize hallucinations
    # We temporarily replace whitelisted tags with placeholders to protect them
    protected_tags = ["<b>", "</b>", "<i>", "</i>", "<code>", "</code>", "<blockquote>", "</blockquote>"]
    for i, tag in enumerate(protected_tags):
        text = text.replace(tag, f"__TAG_{i}__")
    
    # Escape everything else (handles stray <, >, &)
    text = html.escape(text, quote=False)
    
    # Restore protected tags and strip attributes from any hallucinated versions
    for i, tag in enumerate(protected_tags):
        text = text.replace(f"__TAG_{i}__", tag)
    
    # 2. Strip any hallucinated tag attributes (e.g., <blockquote class="..."> -> <blockquote>)
    text = re.sub(r'<(b|i|code|blockquote)\s+[^>]*>', r'<\1>', text, flags=re.IGNORECASE)
    
    # 3. Final cleanup: Remove completely unsupported tags
    text = re.sub(r'</?(?!b|i|code|blockquote)[a-z0-9]+(?:\s+[^>]*)?>', '', text, flags=re.IGNORECASE)
    
    return text.strip()

def split_message(text, max_length=4000):
    """Splits long reports into chunks while preserving HTML tag balance (v2.10)."""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
            
        # Try to split at a double newline for clean structural breaks
        split_at = text.rfind('\n\n', 0, max_length)
        if split_at == -1:
            split_at = text.rfind('\n', 0, max_length)
        if split_at == -1:
            split_at = max_length
            
        part = text[:split_at]
        
        # Tag Balance Check: Ensure we don't split inside a blockquote
        open_tags = []
        for match in re.finditer(r'<(/?)(b|i|code|blockquote)>', part):
            if match.group(1) == "": # Opening tag
                open_tags.append(match.group(2))
            else: # Closing tag
                if open_tags and open_tags[-1] == match.group(2):
                    open_tags.pop()
        
        # Close all open tags for this part
        for tag in reversed(open_tags):
            part += f"</{tag}>"
            
        parts.append(part)
        
        # Prepare remaining text: Re-open tags in the next part
        text = text[split_at:].lstrip()
        reopen_prefix = "".join([f"<{tag}>" for tag in open_tags])
        text = reopen_prefix + text
        
        # Safety progress check
        if split_at == 0:
            parts.append(text)
            break
            
    return parts

def send_telegram_message(text):
    """Sends the summarized text to Telegram with support for pagination (v2.10)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: Telegram credentials not set.")
        return False

    # 1. Sanitize
    clean_text = bulletproof_sanitizer(text)
    
    # 2. Split
    parts = split_message(clean_text)
    total_parts = len(parts)
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    success = True
    for i, part in enumerate(parts):
        page_indicator = f" (หน้า {i+1}/{total_parts})" if total_parts > 1 else ""
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": part + page_indicator,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print(f"Telegram part {i+1} sent successfully.")
            else:
                print(f"Telegram API Error (Part {i+1}): {response.status_code} {response.text}")
                success = False
        except Exception as e:
            print(f"Error sending Telegram message part {i+1}: {e}")
            success = False
        
        if i < total_parts - 1:
            time.sleep(1) # Anti-flood delay
            
    return success

def main():
    print("Starting Crypto Intelligence Bot (v2.11 - Groq Bulletproof)...")
    
    news_items = get_aggregated_news(RSS_FEEDS, limit_per_source=5)
    if not news_items:
        print("No news items retrieved. Exiting.")
        return
    
    if len(news_items) > 20:
        news_items = news_items[:20]
        
    print(f"Analyzing {len(news_items)} news items...")
    summary_text = summarize_market_news(news_items)
    
    if not summary_text:
        print("Failed to generate report. Exiting.")
        return

    print("Processing and sending report to Telegram...")
    send_telegram_message(summary_text)
    
    print("Process completed.")

if __name__ == "__main__":
    main()

