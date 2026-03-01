import requests
from datetime import datetime, timedelta
import json
from deep_translator import GoogleTranslator
from langdetect import detect


NEWSAPI_KEY = "ed8747cf52b849e7aaafa8a3934d29e1"
NEWSAPI_URL = "https://newsapi.org/v2/everything"


def translate_text_to_en(text: str) -> str:
    if not text:
        return text
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except Exception:
        return text


def detect_english(text: str) -> bool:
    if not text:
        return False
    try:
        return detect(text).startswith("en")
    except Exception:
        return False


def fetch_newsapi_articles(keyword: str, max_results=5, days=7):
    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=days)

    params = {
        "q": keyword,
        "from": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "to": to_date.strftime("%Y-%m-%dT%H:%M:%S"),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": max_results,
        "apiKey": NEWSAPI_KEY
    }

    r = requests.get(NEWSAPI_URL, params=params, timeout=10)
    data = r.json()

    if data.get("status") != "ok":
        return []

    articles = data.get("articles", [])
    enriched = []

    for art in articles:
        title = art.get("title")
        url = art.get("url")
        source = art.get("source", {}).get("name")
        date = art.get("publishedAt")
        text = art.get("content") or art.get("description") or ""
        translated_flag = False

        is_en = detect_english(text)

        if not is_en and text:
            new_text = translate_text_to_en(text)
            if new_text != text:
                translated_flag = True
                text = new_text

        enriched.append({
            "title": title,
            "url": url,
            "date": date,
            "source": source,
            "language": "en" if is_en else "other",
            "article_text": text,
            "translated": translated_flag
        })

    return enriched


def format_top_k_articles_json(articles, k=5):
    top_articles = articles[:k]
    formatted = []

    for i, art in enumerate(top_articles, 1):
        text_preview = art.get("article_text", "")
        if text_preview:
            text_preview = text_preview[:400] + ("..." if len(text_preview) > 400 else "")

        formatted.append({
            "rank": i,
            "title": art.get("title"),
            "source": art.get("source"),
            "date": art.get("date"),
            "url": art.get("url"),
            "snippet": text_preview or None,
            "translated": art.get("translated")
        })

    return json.dumps({"top_articles": formatted}, indent=2, ensure_ascii=False)


def get_top_5_news_json_by_keyword(keyword: str, max_results=5) -> str:
    articles = fetch_newsapi_articles(keyword, max_results=max_results, days=7)
    return format_top_k_articles_json(articles, k=max_results)

# Example usage:
if __name__ == "__main__":
    keyword_input = "nvidia"
    top_news_json = get_top_5_news_json_by_keyword(keyword_input)
    print(top_news_json)
