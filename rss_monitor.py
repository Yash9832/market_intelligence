# Interactive Real-time RSS Monitor
# Architecture: RSS Sources → AsyncIO Fetcher → User-defined Keyword Filter → WebSocket → Frontend

import asyncio
import aiohttp
import feedparser
import json
import re
from datetime import datetime, timedelta
from typing import List, Set, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import hashlib
import logging
from dataclasses import dataclass
import sqlite3
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

# RSS Feed Sources - easily configurable
RSS_SOURCES = {
    'BBC Technology': 'https://feeds.bbci.co.uk/news/technology/rss.xml',
    'BBC Business': 'https://feeds.bbci.co.uk/news/business/rss.xml',
    'TechCrunch': 'https://techcrunch.com/feed/',
    # 'Reuters Technology': 'https://feeds.reuters.com/reuters/technologyNews',
    # 'Reuters Business': 'https://feeds.reuters.com/reuters/businessNews',
    'The Verge': 'https://www.theverge.com/rss/index.xml',
    'Ars Technica': 'https://feeds.arstechnica.com/arstechnica/technology-lab',
    'Wired': 'https://www.wired.com/feed/rss',
    'ZDNet': 'https://www.zdnet.com/news/rss.xml',
    'Engadget': 'https://www.engadget.com/rss.xml',
    'MIT Technology Review': 'https://www.technologyreview.com/feed/',
    'Hacker News': 'https://hnrss.org/frontpage',
    'VentureBeat': 'https://venturebeat.com/feed/',
    'TechRadar': 'https://www.techradar.com/rss',
    'CNN Business': 'http://rss.cnn.com/rss/money_latest.rss',
    'Forbes': 'https://www.forbes.com/innovation/feed2/',
    'Fast Company': 'https://www.fastcompany.com/rss.xml',
}

class SimpleDatabase:
    """Simple SQLite database for storing articles with migration support"""
    
    def __init__(self, db_path="rss_monitor.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        
        # Create table with original structure first
        conn.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                link TEXT,
                source TEXT,
                published TEXT,
                matched_keywords TEXT,
                timestamp TEXT
            )
        ''')
        
        # Check if user_session column exists, if not add it
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(articles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_session' not in columns:
            print("Adding user_session column to existing database...")
            conn.execute('ALTER TABLE articles ADD COLUMN user_session TEXT DEFAULT "default"')
        
        # Create indexes
        conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON articles(timestamp)')
        
        # Only create session index if column exists
        if 'user_session' in columns or True:  # True because we just added it above
            conn.execute('CREATE INDEX IF NOT EXISTS idx_session ON articles(user_session)')
        
        conn.commit()
        conn.close()
    
    def reset_db(self):
        """Reset database - useful for testing"""
        try:
            Path(self.db_path).unlink(missing_ok=True)
            self.init_db()
            print("Database reset successfully")
        except Exception as e:
            print(f"Error resetting database: {e}")
    
    def save_article(self, article: Article, user_session: str = "default"):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                INSERT OR REPLACE INTO articles 
                (id, title, description, link, source, published, matched_keywords, timestamp, user_session)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article.id, article.title, article.description, article.link,
                article.source, article.published, ','.join(article.matched_keywords), 
                article.timestamp, user_session
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving article: {e}")
    
    def get_recent_articles(self, hours=24, limit=50, user_session="default"):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            cursor.execute('''
                SELECT * FROM articles 
                WHERE timestamp > ? AND user_session = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (cutoff_time, user_session, limit))
            
            articles = cursor.fetchall()
            conn.close()
            return articles
        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return []

class KeywordMatcher:
    """Simple but effective keyword matching"""
    
    def __init__(self, keywords: List[str]):
        self.keywords = [kw.lower().strip() for kw in keywords if kw.strip()]
        self.patterns = {}
        
        # Pre-compile regex patterns for exact matches
        for keyword in self.keywords:
            self.patterns[keyword] = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
    
    def find_matches(self, text: str) -> List[str]:
        if not self.keywords:
            return []
            
        matches = []
        text_lower = text.lower()
        
        for keyword in self.keywords:
            # Try exact word match first
            if self.patterns[keyword].search(text):
                matches.append(keyword)
            # Fallback to substring match for compound terms
            elif len(keyword.split()) > 1 and keyword in text_lower:
                matches.append(keyword)
        
        return matches

class WebSocketManager:
    """Manage WebSocket connections with user sessions"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}  # session_id -> websocket
        self.user_keywords: Dict[str, List[str]] = {}  # session_id -> keywords
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.connections[session_id] = websocket
        self.user_keywords[session_id] = []
        logger.info(f"Client {session_id} connected. Total: {len(self.connections)}")
    
    def disconnect(self, session_id: str):
        if session_id in self.connections:
            del self.connections[session_id]
        if session_id in self.user_keywords:
            del self.user_keywords[session_id]
        logger.info(f"Client {session_id} disconnected. Total: {len(self.connections)}")
    
    async def send_to_user(self, session_id: str, message: dict):
        if session_id in self.connections:
            try:
                await self.connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)
    
    def update_user_keywords(self, session_id: str, keywords: List[str]):
        self.user_keywords[session_id] = [kw.strip() for kw in keywords if kw.strip()]
        logger.info(f"Updated keywords for {session_id}: {self.user_keywords[session_id]}")
    
    def get_user_keywords(self, session_id: str) -> List[str]:
        return self.user_keywords.get(session_id, [])

class RSSMonitor:
    """Main RSS monitoring class with user-specific keyword filtering"""
    
    def __init__(self):
        self.db = SimpleDatabase()
        self.websocket_manager = WebSocketManager()
        self.seen_articles: Dict[str, Set[str]] = {}  # session_id -> set of article_ids
        self.running = False
    
    def _load_seen_articles(self, session_id: str):
        """Load seen article IDs from database for a specific user session"""
        if session_id not in self.seen_articles:
            self.seen_articles[session_id] = set()
            
        recent_articles = self.db.get_recent_articles(hours=48, user_session=session_id)
        self.seen_articles[session_id] = {article[0] for article in recent_articles}
        logger.info(f"Loaded {len(self.seen_articles[session_id])} seen articles for {session_id}")
    
    async def fetch_rss_feed(self, session: aiohttp.ClientSession, name: str, url: str, 
                            session_id: str, keywords: List[str]) -> List[Article]:
        """Fetch and parse a single RSS feed for specific user keywords"""
        if not keywords:
            return []
            
        try:
            async with session.get(url, timeout=30) as response:
                content = await response.text()
            
            # Parse RSS feed
            feed = feedparser.parse(content)
            articles = []
            
            keyword_matcher = KeywordMatcher(keywords)
            
            for entry in feed.entries:
                # Create unique ID
                article_id = hashlib.md5(f"{session_id}{entry.link}{entry.title}".encode()).hexdigest()
                
                # Skip if already seen
                if article_id in self.seen_articles.get(session_id, set()):
                    continue
                
                # Extract content
                title = entry.get('title', '')
                description = entry.get('description', '') or entry.get('summary', '')
                full_text = f"{title} {description}"
                
                # Check for keyword matches
                matches = keyword_matcher.find_matches(full_text)
                
                if matches:
                    article = Article(
                        id=article_id,
                        title=title[:200],  # Limit title length
                        description=description[:500],  # Limit description
                        link=entry.get('link', ''),
                        source=name,
                        published=entry.get('published', ''),
                        matched_keywords=matches,
                        timestamp=datetime.now().isoformat()
                    )
                    
                    articles.append(article)
                    if session_id not in self.seen_articles:
                        self.seen_articles[session_id] = set()
                    self.seen_articles[session_id].add(article_id)
            
            if articles:
                logger.info(f"Found {len(articles)} new matching articles from {name} for {session_id}")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching {name}: {e}")
            return []
    
    async def process_feeds_for_user(self, session_id: str):
        """Process all RSS feeds for a specific user's keywords"""
        keywords = self.websocket_manager.get_user_keywords(session_id)
        if not keywords:
            return 0
        
        # Ensure user has seen articles tracking
        if session_id not in self.seen_articles:
            self._load_seen_articles(session_id)
        
        async with aiohttp.ClientSession() as session:
            # Create tasks for all feeds
            tasks = [
                self.fetch_rss_feed(session, name, url, session_id, keywords) 
                for name, url in RSS_SOURCES.items()
            ]
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_articles = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Feed processing error for {session_id}: {result}")
                    continue
                all_articles.extend(result)
            
            # Process new articles
            for article in all_articles:
                # Save to database
                self.db.save_article(article, session_id)
                
                # Send real-time notification to specific user
                notification = {
                    "type": "new_article",
                    "article": {
                        "id": article.id,
                        "title": article.title,
                        "description": article.description,
                        "link": article.link,
                        "source": article.source,
                        "published": article.published,
                        "matched_keywords": article.matched_keywords,
                        "timestamp": article.timestamp
                    }
                }
                
                await self.websocket_manager.send_to_user(session_id, notification)
                logger.info(f"New article for {session_id}: {article.title[:50]}... (Keywords: {', '.join(article.matched_keywords)})")
            
            return len(all_articles)
    
    async def run_monitor(self, check_interval: int = 180):
        """Run the monitoring loop for all connected users"""
        self.running = True
        logger.info(f"Starting RSS monitor")
        logger.info(f"Monitoring {len(RSS_SOURCES)} RSS sources")
        logger.info(f"Check interval: {check_interval} seconds")
        
        while self.running:
            try:
                start_time = datetime.now()
                
                # Process feeds for each connected user
                total_new_articles = 0
                active_sessions = list(self.websocket_manager.connections.keys())
                
                for session_id in active_sessions:
                    try:
                        new_articles = await self.process_feeds_for_user(session_id)
                        total_new_articles += new_articles
                        
                        # Send status update to user
                        keywords = self.websocket_manager.get_user_keywords(session_id)
                        status_message = {
                            "type": "status_update",
                            "data": {
                                "timestamp": datetime.now().isoformat(),
                                "new_articles": new_articles,
                                "total_sources": len(RSS_SOURCES),
                                "keywords": keywords,
                                "active": bool(keywords)
                            }
                        }
                        await self.websocket_manager.send_to_user(session_id, status_message)
                        
                    except Exception as e:
                        logger.error(f"Error processing feeds for {session_id}: {e}")
                
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Cycle complete: {total_new_articles} new articles across {len(active_sessions)} users in {processing_time:.1f}s")
                
                # Wait before next cycle
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(30)  # Wait 30s on error
    
    def stop_monitor(self):
        self.running = False

# FastAPI Application
app = FastAPI(title="Interactive RSS Monitor", description="Real-time RSS monitoring with custom keyword searches")

# Global monitor instance
monitor = RSSMonitor()

@app.on_event("startup")
async def startup_event():
    # Start monitoring in background (check every 3 minutes)
    asyncio.create_task(monitor.run_monitor(check_interval=180))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await monitor.websocket_manager.connect(websocket, session_id)
    try:
        while True:
            # Handle client messages
            message = await websocket.receive_text()
            data = json.loads(message)
            
            if data["type"] == "set_keywords":
                # Update user's keywords
                keywords = data["keywords"]
                monitor.websocket_manager.update_user_keywords(session_id, keywords)
                
                # Send confirmation
                await monitor.websocket_manager.send_to_user(session_id, {
                    "type": "keywords_updated",
                    "keywords": keywords
                })
                
                # Load seen articles for this user
                monitor._load_seen_articles(session_id)
                
            elif data["type"] == "get_recent":
                # Send recent articles to client
                recent = monitor.db.get_recent_articles(hours=6, limit=20, user_session=session_id)
                for article_data in recent:
                    article_dict = {
                        "type": "recent_article",
                        "article": {
                            "id": article_data[0],
                            "title": article_data[1],
                            "description": article_data[2],
                            "link": article_data[3],
                            "source": article_data[4],
                            "published": article_data[5],
                            "matched_keywords": article_data[6].split(',') if article_data[6] else [],
                            "timestamp": article_data[7]
                        }
                    }
                    await monitor.websocket_manager.send_to_user(session_id, article_dict)
                    
    except WebSocketDisconnect:
        monitor.websocket_manager.disconnect(session_id)

@app.get("/")
async def dashboard():
    """Interactive dashboard with keyword input and real-time updates"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Interactive RSS Monitor</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
            .keyword-input { background: white; margin: 20px auto; max-width: 800px; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            .input-group { margin-bottom: 15px; }
            .input-group label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
            .keyword-field { width: 100%; padding: 12px 15px; border: 2px solid #e1e1e1; border-radius: 8px; font-size: 16px; transition: border-color 0.3s; }
            .keyword-field:focus { outline: none; border-color: #667eea; }
            .button-group { display: flex; gap: 10px; flex-wrap: wrap; }
            .btn { padding: 12px 20px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.3s; }
            .btn-primary { background: #667eea; color: white; }
            .btn-primary:hover { background: #5a67d8; }
            .btn-secondary { background: #e2e8f0; color: #4a5568; }
            .btn-secondary:hover { background: #cbd5e0; }
            .status { padding: 15px; text-align: center; margin: 20px; border-radius: 8px; font-weight: 600; }
            .status.connected { background: #48bb78; color: white; }
            .status.disconnected { background: #f56565; color: white; }
            .status.inactive { background: #ed8936; color: white; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .article { background: white; margin: 20px 0; padding: 25px; border-radius: 12px; box-shadow: 0 3px 15px rgba(0,0,0,0.1); transition: transform 0.2s; }
            .article:hover { transform: translateY(-2px); }
            .article.new { border-left: 5px solid #48bb78; animation: slideIn 0.5s ease-out; }
            @keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
            .article-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px; }
            .article-source { background: #667eea; color: white; padding: 6px 15px; border-radius: 20px; font-size: 0.85em; font-weight: bold; }
            .article-time { color: #666; font-size: 0.9em; }
            .article-title { font-size: 1.3em; margin: 15px 0; line-height: 1.4; }
            .article-title a { color: #2d3748; text-decoration: none; }
            .article-title a:hover { color: #667eea; text-decoration: underline; }
            .article-description { color: #4a5568; line-height: 1.6; margin: 15px 0; }
            .keywords { margin-top: 15px; }
            .keyword { background: #ffd700; padding: 5px 12px; margin: 3px; border-radius: 15px; font-size: 0.85em; display: inline-block; font-weight: 600; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: white; padding: 25px; border-radius: 12px; text-align: center; box-shadow: 0 3px 15px rgba(0,0,0,0.1); }
            .stat-number { font-size: 2.5em; font-weight: bold; color: #667eea; }
            .stat-label { color: #666; margin-top: 8px; font-weight: 500; }
            .no-articles { text-align: center; color: #666; padding: 50px; background: white; border-radius: 12px; }
            .keyword-suggestions { margin-top: 10px; }
            .suggestion { display: inline-block; background: #e2e8f0; padding: 5px 10px; margin: 3px; border-radius: 15px; font-size: 0.8em; cursor: pointer; }
            .suggestion:hover { background: #cbd5e0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📡 Interactive RSS Monitor</h1>
            <p>Real-time news monitoring with custom keyword searches</p>
        </div>
        
        <div class="container">
            <div class="keyword-input">
                <div class="input-group">
                    <label for="keywords">Enter Keywords (comma-separated):</label>
                    <input type="text" id="keywords" class="keyword-field" 
                           placeholder="e.g., artificial intelligence, Tesla, cryptocurrency, startup funding">
                    <div class="keyword-suggestions">
                        <strong>Popular suggestions:</strong>
                        <span class="suggestion" onclick="addSuggestion('artificial intelligence')">AI</span>
                        <span class="suggestion" onclick="addSuggestion('machine learning')">Machine Learning</span>
                        <span class="suggestion" onclick="addSuggestion('cryptocurrency')">Cryptocurrency</span>
                        <span class="suggestion" onclick="addSuggestion('startup')">Startup</span>
                        <span class="suggestion" onclick="addSuggestion('Tesla')">Tesla</span>
                        <span class="suggestion" onclick="addSuggestion('Apple')">Apple</span>
                        <span class="suggestion" onclick="addSuggestion('Google')">Google</span>
                        <span class="suggestion" onclick="addSuggestion('climate change')">Climate Change</span>
                    </div>
                </div>
                <div class="button-group">
                    <button class="btn btn-primary" onclick="startMonitoring()">Start Monitoring</button>
                    <button class="btn btn-secondary" onclick="stopMonitoring()">Stop Monitoring</button>
                    <button class="btn btn-secondary" onclick="clearArticles()">Clear Articles</button>
                </div>
            </div>
            
            <div id="status" class="status disconnected">Connecting...</div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="total-articles">0</div>
                    <div class="stat-label">New Articles</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="sources-count">17</div>
                    <div class="stat-label">RSS Sources</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="keywords-count">0</div>
                    <div class="stat-label">Active Keywords</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="last-check">--</div>
                    <div class="stat-label">Last Check</div>
                </div>
            </div>
            
            <div id="articles">
                <div class="no-articles">
                    <h3>Ready to Monitor!</h3>
                    <p>Enter your keywords above and click "Start Monitoring" to begin receiving live news updates.</p>
                </div>
            </div>
        </div>
        
        <script>
            const sessionId = 'user_' + Math.random().toString(36).substr(2, 9);
            let ws = null;
            let articleCount = 0;
            let isMonitoring = false;
            
            function connectWebSocket() {
                ws = new WebSocket(`ws://${window.location.host}/ws/${sessionId}`);
                const status = document.getElementById('status');
                
                ws.onopen = function(event) {
                    status.textContent = 'Connected - Enter keywords to start monitoring';
                    status.className = 'status inactive';
                };
                
                ws.onclose = function(event) {
                    status.textContent = 'Disconnected - Trying to reconnect...';
                    status.className = 'status disconnected';
                    
                    // Try to reconnect after 3 seconds
                    setTimeout(connectWebSocket, 3000);
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'new_article' || data.type === 'recent_article') {
                        addArticle(data.article, data.type === 'new_article');
                    } else if (data.type === 'status_update') {
                        updateStats(data.data);
                    } else if (data.type === 'keywords_updated') {
                        document.getElementById('keywords-count').textContent = data.keywords.length;
                        const status = document.getElementById('status');
                        if (data.keywords.length > 0) {
                            status.textContent = `Monitoring active for: ${data.keywords.join(', ')}`;
                            status.className = 'status connected';
                            isMonitoring = true;
                        }
                    }
                };
            }
            
            function addSuggestion(keyword) {
                const keywordField = document.getElementById('keywords');
                const currentValue = keywordField.value.trim();
                
                if (currentValue) {
                    keywordField.value = currentValue + ', ' + keyword;
                } else {
                    keywordField.value = keyword;
                }
            }
            
            function startMonitoring() {
                const keywordsInput = document.getElementById('keywords').value.trim();
                if (!keywordsInput) {
                    alert('Please enter at least one keyword!');
                    return;
                }
                
                const keywords = keywordsInput.split(',').map(k => k.trim()).filter(k => k);
                
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'set_keywords',
                        keywords: keywords
                    }));
                    
                    // Request recent articles
                    setTimeout(() => {
                        ws.send(JSON.stringify({ type: 'get_recent' }));
                    }, 500);
                }
            }
            
            function stopMonitoring() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'set_keywords',
                        keywords: []
                    }));
                }
                
                const status = document.getElementById('status');
                status.textContent = 'Monitoring stopped - Enter keywords to restart';
                status.className = 'status inactive';
                
                document.getElementById('keywords-count').textContent = '0';
                isMonitoring = false;
            }
            
            function clearArticles() {
                const articles = document.getElementById('articles');
                articles.innerHTML = '<div class="no-articles"><h3>Articles Cleared</h3><p>New articles will appear here.</p></div>';
                articleCount = 0;
                document.getElementById('total-articles').textContent = '0';
            }
            
            function addArticle(article, isNew) {
                const articlesContainer = document.getElementById('articles');
                
                // Remove "no articles" message
                const noArticlesMsg = articlesContainer.querySelector('.no-articles');
                if (noArticlesMsg) noArticlesMsg.remove();
                
                const articleDiv = document.createElement('div');
                articleDiv.className = 'article' + (isNew ? ' new' : '');
                
                const publishedTime = new Date(article.published || article.timestamp).toLocaleString();
                
                articleDiv.innerHTML = `
                    <div class="article-header">
                        <span class="article-source">${article.source}</span>
                        <span class="article-time">${publishedTime}</span>
                    </div>
                    <div class="article-title">
                        <a href="${article.link}" target="_blank" rel="noopener">${article.title}</a>
                    </div>
                    <div class="article-description">${article.description}</div>
                    <div class="keywords">
                        ${article.matched_keywords.map(k => `<span class="keyword">${k}</span>`).join('')}
                    </div>
                `;
                
                // Add to top
                articlesContainer.insertBefore(articleDiv, articlesContainer.firstChild);
                
                // Keep only last 100 articles
                while (articlesContainer.children.length > 100) {
                    articlesContainer.removeChild(articlesContainer.lastChild);
                }
                
                if (isNew) {
                    articleCount++;
                    document.getElementById('total-articles').textContent = articleCount;
                }
            }
            
            function updateStats(data) {
                document.getElementById('keywords-count').textContent = data.keywords.length;
                document.getElementById('last-check').textContent = new Date(data.timestamp).toLocaleTimeString();
                
                if (data.active) {
                    const status = document.getElementById('status');
                    status.textContent = `Active - Found ${data.new_articles} new articles. Keywords: ${data.keywords.join(', ')}`;
                    status.className = 'status connected';
                }
            }
            
            // Handle Enter key in keyword input
            document.getElementById('keywords').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    startMonitoring();
                }
            });
            
            // Initialize connection
            connectWebSocket();
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    # This starts uvicorn programmatically when running the file directly.
    import uvicorn
    uvicorn.run("rss_monitor:app", host="0.0.0.0", port=8000, reload=True)
    # If your file is at top-level (not inside backend package), use:
    # uvicorn.run("rss_monitor:app", host="0.0.0.0", port=8000, reload=True)