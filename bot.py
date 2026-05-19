import os
import time
import feedparser
import requests
import html
import re
import logging
from groq import Groq
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Configuration - Constants
LIMIT_PER_SOURCE = 5
MAX_TOTAL_NEWS = 20
GROQ_MODEL = "llama-3.3-70b-versatile"

RSS_FEEDS = [
    "https://www.federalreserve.gov/newsevents/press/all/2026all.xml", 
    "https://www.bls.gov/feed/bls_latest.rss",                        
    "https://www.coindesk.com/arc/outboundfeeds/rss/",                
    "https://cointelegraph.com/rss",                                  
    "https://insights.glassnode.com/rss",                            
    "https://www.sec.gov/news/pressreleases.rss",                     
    "https://search.cnbc.com/rs/search/combinedcms/view.xml?id=10000664" 
]

# Load environment variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def get_aggregated_news(urls, limit=LIMIT_PER_SOURCE):
    """Scrapes news from multiple RSS URLs with priority tagging for crypto impact (v2.14)."""
    all_news = []
    crypto_keywords = ["crypto", "bitcoin", "btc", "ethereum", "eth", "stablecoin", "etf", "sec", "fed", "inflation", "liquidity"]
    
    for url in urls:
        try:
            logger.info(f"Fetching news from {url}...")
            feed = feedparser.parse(url)
            if not feed.entries:
                continue
            for entry in feed.entries[:limit]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                
                # Check for high-signal keywords to boost analytical depth
                is_priority = any(kw in title.lower() for kw in crypto_keywords)
                priority_tag = "[🔥 HIGH PRIORITY]" if is_priority else ""
                
                if not any(n['title'] == title for n in all_news):
                    all_news.append({
                        "title": f"{priority_tag} {title}", 
                        "summary": summary, 
                        "source": url,
                        "is_priority": is_priority
                    })
        except Exception as e:
            logger.error(f"Error fetching RSS feed {url}: {e}")
            
    # Sort priority news to the top so LLM sees them first
    all_news.sort(key=lambda x: x['is_priority'], reverse=True)
    return all_news

def get_hn_crypto_news(limit=LIMIT_PER_SOURCE):
    """Fetches high-signal crypto/tech news from Hacker News via Algolia API (v2.13)."""
    all_news = []
    # Broad but relevant crypto/blockchain keywords
    query = "crypto OR bitcoin OR ethereum OR blockchain OR stablecoin OR web3"
    # Filter for stories with at least 5 points to ensure some level of community interest/impact
    url = f"https://hn.algolia.com/api/v1/search_by_date?query={query}&tags=story&numericFilters=points>=5&hitsPerPage={limit}"
    
    try:
        logger.info("Fetching news from Hacker News...")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            hits = response.json().get("hits", [])
            for hit in hits:
                title = hit.get("title", "")
                link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
                # Points and Comments serve as an 'Impact' proxy for tech community interest
                points = hit.get("points", 0)
                num_comments = hit.get("num_comments", 0)
                summary = f"Tech Signal: {points} points, {num_comments} comments. URL: {link}"
                
                if not any(n['title'] == title for n in all_news):
                    all_news.append({"title": title, "summary": summary, "source": "Hacker News"})
        else:
            logger.error(f"Hacker News API Error: {response.status_code}")
    except Exception as e:
        logger.error(f"Error fetching Hacker News: {e}")
    
    return all_news

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: logger.warning(f"API busy or error. Retrying in {retry_state.next_action.sleep} seconds... (Attempt {retry_state.attempt_number})")
)
def summarize_market_news(news_items):
    """Summarizes market-moving news using Groq with deep insight and modern HTML formatting."""
    if not GROQ_API_KEY:
        logger.error("Error: GROQ_API_KEY environment variable is not set.")
        return None
    
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = (
        "You are an Elite Macro-Crypto Market Strategist. Analyze the following news items and produce a deep-insight report in THAI. "
        "Your goal is to connect news events to 'Liquidity & Money Flow' and interest rate expectations. "
        "### CORE MISSION: CROSS-SOURCE CORRELATION\n"
        "- Connect Macro data (Fed/Inflation) directly to Crypto Risk Appetite.\n"
        "- Explain how 1st-order events (e.g., Fed Rates) lead to 2nd-order Crypto effects (e.g., Stablecoin minting, Whale behavior).\n"
        "- Identify if multiple sources are pointing to the same liquidity shift.\n\n"
        "### REPORT STRUCTURE (MANDATORY):\n"
        "1. 📊 <b>สรุปภาวะตลาด (Executive Summary):</b>\n"
        "   - One powerful paragraph synthesizing the overall market mood. You MUST correlate macro trends with current crypto price action.\n\n"
        "2. <b>[Category Name]</b>\n"
        "   - Use these categories: [📌 Macro & Fed], [🐋 On-Chain & Whales], [🏢 Institutional Activity], [⚖️ Regulation & Tech].\n"
        "   - Format each news item as:\n"
        "     📰 <b>[Headline]</b>\n"
        "     <blockquote>[Deep analytical summary in Thai focusing on Macro-to-Crypto liquidity correlation]</blockquote>\n"
        "     <b>Impact:</b> [Bullish/Bearish/Neutral] + brief 2nd-order rationale.\n"
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
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "You are a senior macro-financial analyst providing high-signal intelligence for Telegram. CRITICAL: Use ONLY <b>, <i>, <code>, <blockquote>. Strip all attributes. Escape all special characters like <, >, & except for these tags. NOTE: Hacker News data represents technological sentiment and institutional tech shifts."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=3000,
    )
    return completion.choices[0].message.content

def bulletproof_sanitizer(text):
    """Deeply sanitizes LLM output to ensure perfect Telegram HTML compatibility (v2.10)."""
    # 1. First, escape all existing HTML characters to neutralize hallucinations
    protected_tags = ["<b>", "</b>", "<i>", "</i>", "<code>", "</code>", "<blockquote>", "</blockquote>"]
    for i, tag in enumerate(protected_tags):
        text = text.replace(tag, f"__TAG_{i}__")
    
    # Escape everything else (handles stray <, >, &)
    text = html.escape(text, quote=False)
    
    # Restore protected tags
    for i, tag in enumerate(protected_tags):
        text = text.replace(f"__TAG_{i}__", tag)
    
    # 2. Strip any hallucinated tag attributes
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
            
        split_at = text.rfind('\n\n', 0, max_length)
        if split_at == -1:
            split_at = text.rfind('\n', 0, max_length)
        if split_at == -1:
            split_at = max_length
            
        part = text[:split_at]
        
        open_tags = []
        for match in re.finditer(r'<(/?)(b|i|code|blockquote)>', part):
            if match.group(1) == "": # Opening tag
                open_tags.append(match.group(2))
            else: # Closing tag
                if open_tags and open_tags[-1] == match.group(2):
                    open_tags.pop()
        
        for tag in reversed(open_tags):
            part += f"</{tag}>"
            
        parts.append(part)
        
        text = text[split_at:].lstrip()
        reopen_prefix = "".join([f"<{tag}>" for tag in open_tags])
        text = reopen_prefix + text
        
        if split_at == 0:
            parts.append(text)
            break
            
    return parts

def send_telegram_message(text):
    """Sends the summarized text to Telegram with support for pagination (v2.10)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Error: Telegram credentials not set.")
        return False

    clean_text = bulletproof_sanitizer(text)
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
                logger.info(f"Telegram part {i+1} sent successfully.")
            else:
                logger.error(f"Telegram API Error (Part {i+1}): {response.status_code} {response.text}")
                success = False
        except Exception as e:
            logger.error(f"Error sending Telegram message part {i+1}: {e}")
            success = False
        
        if i < total_parts - 1:
            time.sleep(1) 
            
    return success

def main():
    logger.info("Starting Crypto Intelligence Bot (v2.14 - Macro-Crypto Correlation Engine)...")
    
    # 1. Fetch RSS feeds
    news_items = get_aggregated_news(RSS_FEEDS, limit=LIMIT_PER_SOURCE)
    
    # 2. Fetch Hacker News (Silicon Valley Tech Perspective)
    hn_news = get_hn_crypto_news(limit=LIMIT_PER_SOURCE)
    if hn_news:
        news_items.extend(hn_news)
        
    if not news_items:
        logger.warning("No news items retrieved. Exiting.")
        return
    
    if len(news_items) > MAX_TOTAL_NEWS:
        logger.info(f"Clipping news items from {len(news_items)} to {MAX_TOTAL_NEWS}")
        news_items = news_items[:MAX_TOTAL_NEWS]
        
    logger.info(f"Analyzing {len(news_items)} news items...")
    summary_text = summarize_market_news(news_items)
    
    if not summary_text:
        logger.error("Failed to generate report. Exiting.")
        return

    logger.info("Processing and sending report to Telegram...")
    send_telegram_message(summary_text)
    
    logger.info("Process completed successfully.")

if __name__ == "__main__":
    main()

