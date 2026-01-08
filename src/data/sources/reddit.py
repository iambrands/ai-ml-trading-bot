"""Reddit API data source."""

from datetime import datetime, timedelta
from typing import List, Optional

import praw

from ..models import SocialPost, SocialSentiment
from ...config.settings import get_settings
from ...utils.logging import get_logger

logger = get_logger(__name__)


class RedditDataSource:
    """Reddit API integration for social sentiment."""

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None,
        subreddits: Optional[List[str]] = None,
    ):
        """
        Initialize Reddit data source.

        Args:
            client_id: Reddit client ID
            client_secret: Reddit client secret
            user_agent: User agent string
            subreddits: List of subreddits to monitor
        """
        settings = get_settings()
        self.client_id = client_id or settings.reddit_client_id
        self.client_secret = client_secret or settings.reddit_client_secret
        self.user_agent = user_agent or settings.reddit_user_agent
        self.subreddits = subreddits or ["politics", "worldnews", "cryptocurrency", "sports"]

        self.client = None
        if self.client_id and self.client_secret:
            try:
                self.client = praw.Reddit(
                    client_id=self.client_id, client_secret=self.client_secret, user_agent=self.user_agent
                )
            except Exception as e:
                logger.warning("Failed to initialize Reddit client", error=str(e))
        else:
            logger.warning("Reddit API credentials not provided, Reddit fetching will be disabled")

    async def fetch_posts(
        self, query: str, subreddits: Optional[List[str]] = None, max_posts: int = 50, min_score: int = 5
    ) -> List[SocialPost]:
        """
        Fetch Reddit posts matching query.

        Args:
            query: Search query
            subreddits: List of subreddits to search
            max_posts: Maximum posts per subreddit
            min_score: Minimum upvote score

        Returns:
            List of SocialPost objects
        """
        if not self.client:
            return []

        if subreddits is None:
            subreddits = self.subreddits

        posts = []
        try:
            for subreddit_name in subreddits:
                try:
                    subreddit = self.client.subreddit(subreddit_name)
                    search_results = subreddit.search(query, limit=min(max_posts, 100), sort="hot")

                    for submission in search_results:
                        if submission.score < min_score:
                            continue

                        post = SocialPost(
                            id=str(submission.id),
                            platform="reddit",
                            text=f"{submission.title} {submission.selftext}"[:1000],  # Limit text length
                            author=str(submission.author) if submission.author else "unknown",
                            created_at=datetime.fromtimestamp(submission.created_utc),
                            engagement=submission.score + submission.num_comments,
                        )
                        posts.append(post)

                except Exception as e:
                    logger.warning("Failed to fetch from subreddit", subreddit=subreddit_name, error=str(e))
                    continue

            logger.info("Fetched Reddit posts", query=query, count=len(posts))
            return posts

        except Exception as e:
            logger.error("Failed to fetch Reddit posts", query=query, error=str(e))
            return []

    async def fetch_sentiment(
        self, query: str, subreddits: Optional[List[str]] = None, max_posts: int = 50
    ) -> Optional[SocialSentiment]:
        """
        Fetch aggregated sentiment for query.

        Args:
            query: Search query
            subreddits: List of subreddits to search
            max_posts: Maximum posts per subreddit

        Returns:
            SocialSentiment object or None
        """
        posts = await self.fetch_posts(query, subreddits=subreddits, max_posts=max_posts)

        if not posts:
            return None

        # Calculate sentiment metrics
        sentiment_scores = [p.sentiment_score for p in posts if p.sentiment_score is not None]

        if not sentiment_scores:
            return SocialSentiment(
                platform="reddit",
                average_sentiment=0.0,
                sentiment_std=0.0,
                volume=len(posts),
                velocity=0.0,
                top_posts=posts[:10],
            )

        import numpy as np

        return SocialSentiment(
            platform="reddit",
            average_sentiment=float(np.mean(sentiment_scores)),
            sentiment_std=float(np.std(sentiment_scores)),
            volume=len(posts),
            velocity=0.0,
            top_posts=sorted(posts, key=lambda x: x.engagement, reverse=True)[:10],
        )

