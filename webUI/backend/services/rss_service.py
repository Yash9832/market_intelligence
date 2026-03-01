from __future__ import annotations

import asyncio
import json
import logging
import re
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set

import aiohttp
import feedparser
import sqlite3

from fastapi import WebSocket


logger = logging.getLogger(__name__)


@dataclass
class Article:
    id: str
    title: str
    description: str
    link: str
    source: str
    published: str
    matched_keywords: List[str]
    timestamp: str


# Minimal but useful set of RSS sources; can be expanded easily
RSS_SOURCES: Dict[str, str] = {
    'BBC Business': 'https://feeds.bbci.co.uk/news/business/rss.xml',
    'BBC Technology': 'https://feeds.bbci.co.uk/news/technology/rss.xml',
    'TechCrunch': 'https://techcrunch.com/feed/',
    'The Verge': 'https://www.theverge.com/rss/index.xml',
    'CNN Business': 'http://rss.cnn.com/rss/money_latest.rss',
    'Reuters Business': 'https://feeds.reuters.com/reuters/businessNews',
}


class SimpleDatabase:
    """Simple SQLite store for deduplication and recent history"""

    def __init__(self, db_path: str = "rss_monitor.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                link TEXT,
                source TEXT,
                published TEXT,
                matched_keywords TEXT,
                timestamp TEXT,
                user_session TEXT DEFAULT "default"
            )
            '''
        )
        conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON articles(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_session ON articles(user_session)')
        conn.commit()
        conn.close()

    def save_article(self, article: Article, user_session: str = "default") -> None:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                '''
                INSERT OR REPLACE INTO articles 
                (id, title, description, link, source, published, matched_keywords, timestamp, user_session)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    article.id,
                    article.title,
                    article.description,
                    article.link,
                    article.source,
                    article.published,
                    ','.join(article.matched_keywords),
                    article.timestamp,
                    user_session,
                ),
            )
            conn.commit()
            conn.close()
        except Exception as exc:
            logger.error(f"Error saving article: {exc}")

    def get_recent_articles(self, hours: int = 24, limit: int = 50, user_session: str = "default"):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            cursor.execute(
                '''
                SELECT * FROM articles 
                WHERE timestamp > ? AND user_session = ?
                ORDER BY timestamp DESC 
                LIMIT ?
                ''',
                (cutoff_time, user_session, limit),
            )
            articles = cursor.fetchall()
            conn.close()
            return articles
        except Exception as exc:
            logger.error(f"Error getting recent articles: {exc}")
            return []


class KeywordMatcher:
    def __init__(self, keywords: List[str]):
        self.keywords = [kw.lower().strip() for kw in keywords if kw.strip()]
        self.patterns: Dict[str, re.Pattern[str]] = {}
        for keyword in self.keywords:
            self.patterns[keyword] = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)

    def find_matches(self, text: str) -> List[str]:
        if not self.keywords:
            return []
        matches: List[str] = []
        text_lower = text.lower()
        for keyword in self.keywords:
            if self.patterns[keyword].search(text):
                matches.append(keyword)
            elif len(keyword.split()) > 1 and keyword in text_lower:
                matches.append(keyword)
        return matches


class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.user_keywords: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self.connections[session_id] = websocket
        self.user_keywords.setdefault(session_id, [])
        logger.info(f"Client {session_id} connected. Total: {len(self.connections)}")

    def disconnect(self, session_id: str) -> None:
        self.connections.pop(session_id, None)
        self.user_keywords.pop(session_id, None)
        logger.info(f"Client {session_id} disconnected. Total: {len(self.connections)}")

    async def send_to_user(self, session_id: str, message: dict) -> None:
        if session_id in self.connections:
            try:
                await self.connections[session_id].send_text(json.dumps(message))
            except Exception as exc:
                logger.error(f"Error sending message to {session_id}: {exc}")
                self.disconnect(session_id)

    def update_user_keywords(self, session_id: str, keywords: List[str]) -> None:
        self.user_keywords[session_id] = [kw.strip() for kw in keywords if kw.strip()]

    def get_user_keywords(self, session_id: str) -> List[str]:
        return self.user_keywords.get(session_id, [])


class RSSMonitor:
    def __init__(self):
        self.db = SimpleDatabase()
        self.websocket_manager = WebSocketManager()
        self.seen_articles: Dict[str, Set[str]] = {}
        self.running = False

    def _load_seen_articles(self, session_id: str) -> None:
        if session_id not in self.seen_articles:
            self.seen_articles[session_id] = set()
        recent_articles = self.db.get_recent_articles(hours=48, user_session=session_id)
        self.seen_articles[session_id] = {article[0] for article in recent_articles}

    async def fetch_rss_feed(
        self,
        session: aiohttp.ClientSession,
        name: str,
        url: str,
        session_id: str,
        keywords: List[str],
    ) -> List[Article]:
        if not keywords:
            return []
        try:
            async with session.get(url, timeout=30) as response:
                content = await response.text()
            feed = feedparser.parse(content)
            articles: List[Article] = []
            keyword_matcher = KeywordMatcher(keywords)
            for entry in feed.entries:
                article_id = hashlib.md5(f"{session_id}{entry.get('link','')}{entry.get('title','')}".encode()).hexdigest()
                if article_id in self.seen_articles.get(session_id, set()):
                    continue
                title = entry.get('title', '')
                description = entry.get('description', '') or entry.get('summary', '')
                full_text = f"{title} {description}"
                matches = keyword_matcher.find_matches(full_text)
                if matches:
                    article = Article(
                        id=article_id,
                        title=title[:200],
                        description=description[:500],
                        link=entry.get('link', ''),
                        source=name,
                        published=entry.get('published', ''),
                        matched_keywords=matches,
                        timestamp=datetime.now().isoformat(),
                    )
                    articles.append(article)
                    self.seen_articles.setdefault(session_id, set()).add(article_id)
            return articles
        except Exception as exc:
            logger.error(f"Error fetching {name}: {exc}")
            return []

    async def process_feeds_for_user(self, session_id: str) -> int:
        keywords = self.websocket_manager.get_user_keywords(session_id)
        if not keywords:
            return 0
        if session_id not in self.seen_articles:
            self._load_seen_articles(session_id)
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.fetch_rss_feed(session, name, url, session_id, keywords)
                for name, url in RSS_SOURCES.items()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            all_articles: List[Article] = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Feed processing error for {session_id}: {result}")
                    continue
                all_articles.extend(result)
            for article in all_articles:
                self.db.save_article(article, session_id)
                await self.websocket_manager.send_to_user(
                    session_id,
                    {
                        "type": "new_article",
                        "article": {
                            "id": article.id,
                            "title": article.title,
                            "description": article.description,
                            "link": article.link,
                            "source": article.source,
                            "published": article.published,
                            "matched_keywords": article.matched_keywords,
                            "timestamp": article.timestamp,
                        },
                    },
                )
            return len(all_articles)

    async def run_monitor(self, check_interval: int = 180) -> None:
        self.running = True
        while self.running:
            try:
                active_sessions = list(self.websocket_manager.connections.keys())
                for session_id in active_sessions:
                    try:
                        new_articles = await self.process_feeds_for_user(session_id)
                        keywords = self.websocket_manager.get_user_keywords(session_id)
                        await self.websocket_manager.send_to_user(
                            session_id,
                            {
                                "type": "status_update",
                                "data": {
                                    "timestamp": datetime.now().isoformat(),
                                    "new_articles": new_articles,
                                    "total_sources": len(RSS_SOURCES),
                                    "keywords": keywords,
                                    "active": bool(keywords),
                                },
                            },
                        )
                    except Exception as exc:
                        logger.error(f"Error processing feeds for {session_id}: {exc}")
                await asyncio.sleep(check_interval)
            except Exception as exc:
                logger.error(f"Monitor loop error: {exc}")
                await asyncio.sleep(30)

    def stop(self) -> None:
        self.running = False


# Singleton instance used across the app
rss_monitor = RSSMonitor()


