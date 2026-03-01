import asyncpraw
import asyncio
from datetime import datetime
import json

class AsyncRedditCollector:
    def __init__(self, client_id, client_secret, user_agent):
        self.reddit = asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
    async def search_posts_by_keywords(self, keywords, subreddits, limit=5):
        posts = []
        for keyword in keywords:
            for subreddit_name in subreddits:
                try:
                    subreddit = await self.reddit.subreddit(subreddit_name)
                    search_results = subreddit.search(keyword, limit=limit, sort='relevance')
                    async for post in search_results:
                        post_data = {
                            'id': post.id,
                            'title': post.title,
                            'selftext': post.selftext,
                            'score': post.score,
                            'num_comments': post.num_comments,
                            'created_utc': datetime.fromtimestamp(post.created_utc).isoformat(),
                            'author': str(post.author) if post.author else '[deleted]',
                            'subreddit': subreddit_name,
                            'keyword': keyword,
                            'url': post.url,
                            'upvote_ratio': post.upvote_ratio,
                            'source': 'Reddit'
                        }
                        posts.append(post_data)
                except Exception as e:
                    # Consider logging error details here
                    pass
        
        # Select top 5 by score
        sorted_posts = sorted(posts, key=lambda x: x['score'], reverse=True)[:5]
        return sorted_posts

async def get_top_5_reddit_discussions_json(keywords, limit=5):
    subreddits = [
        'investing', 'stocks', 'SecurityAnalysis', 'ValueInvesting',
        'technology', 'artificial', 'MachineLearning', 'startups',
        'entrepreneur', 'business'
    ]
    reddit_client_id = "your_client_id"
    reddit_client_secret = "your_client_secret"
    reddit_user_agent = "SmartResearchAssistant/1.0"

    collector = AsyncRedditCollector(reddit_client_id, reddit_client_secret, reddit_user_agent)
    posts = await collector.search_posts_by_keywords(keywords, subreddits, limit=limit)

    return json.dumps({"top_discussions": posts}, indent=2, ensure_ascii=False)


