"""Twitter/X API data source."""

from datetime import datetime
from typing import List, Optional

import tweepy

from ..models import SocialPost, SocialSentiment
from ...config.settings import get_settings
from ...utils.logging import get_logger

logger = get_logger(__name__)


class TwitterDataSource:
    """Twitter/X API integration for social sentiment."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_token_secret: Optional[str] = None,
    ):
        """
        Initialize Twitter data source.

        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: Access token
            access_token_secret: Access token secret
        """
        settings = get_settings()
        self.api_key = api_key or settings.twitter_api_key
        self.api_secret = api_secret or settings.twitter_api_secret
        self.access_token = access_token or settings.twitter_access_token
        self.access_token_secret = access_token_secret or settings.twitter_access_token_secret

        self.client = None
        if all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
            try:
                auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
                auth.set_access_token(self.access_token, self.access_token_secret)
                self.client = tweepy.API(auth, wait_on_rate_limit=True)
            except Exception as e:
                logger.warning("Failed to initialize Twitter client", error=str(e))
        else:
            logger.warning("Twitter API credentials not provided, Twitter fetching will be disabled")

    async def fetch_tweets(self, query: str, max_tweets: int = 100, min_followers: int = 100) -> List[SocialPost]:
        """
        Fetch tweets matching query.

        Args:
            query: Search query
            max_tweets: Maximum number of tweets to fetch
            min_followers: Minimum followers to filter accounts

        Returns:
            List of SocialPost objects
        """
        if not self.client:
            return []

        try:
            tweets = self.client.search_tweets(q=query, count=min(max_tweets, 100), lang="en", tweet_mode="extended")

            posts = []
            for tweet in tweets:
                # Filter by follower count if available
                if hasattr(tweet.user, "followers_count") and tweet.user.followers_count < min_followers:
                    continue

                post = SocialPost(
                    id=str(tweet.id),
                    platform="twitter",
                    text=tweet.full_text if hasattr(tweet, "full_text") else tweet.text,
                    author=tweet.user.screen_name,
                    created_at=tweet.created_at.replace(tzinfo=None),
                    engagement=tweet.favorite_count + tweet.retweet_count,
                )
                posts.append(post)

            logger.info("Fetched tweets", query=query, count=len(posts))
            return posts

        except Exception as e:
            logger.error("Failed to fetch tweets", query=query, error=str(e))
            return []

    async def fetch_sentiment(self, query: str, max_tweets: int = 100) -> Optional[SocialSentiment]:
        """
        Fetch aggregated sentiment for query.

        Args:
            query: Search query
            max_tweets: Maximum tweets to analyze

        Returns:
            SocialSentiment object or None
        """
        posts = await self.fetch_tweets(query, max_tweets=max_tweets)

        if not posts:
            return None

        # Calculate sentiment metrics (sentiment scores should be set by sentiment analyzer)
        sentiment_scores = [p.sentiment_score for p in posts if p.sentiment_score is not None]

        if not sentiment_scores:
            return SocialSentiment(
                platform="twitter",
                average_sentiment=0.0,
                sentiment_std=0.0,
                volume=len(posts),
                velocity=0.0,
                top_posts=posts[:10],
            )

        import numpy as np

        return SocialSentiment(
            platform="twitter",
            average_sentiment=float(np.mean(sentiment_scores)),
            sentiment_std=float(np.std(sentiment_scores)),
            volume=len(posts),
            velocity=0.0,  # Would calculate rate of change over time
            top_posts=sorted(posts, key=lambda x: x.engagement, reverse=True)[:10],
        )

