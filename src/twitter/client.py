"""Twitter API client using twscrape."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from twscrape import API
from twscrape.models import Tweet, User

from src.config import settings


logger = logging.getLogger(__name__)


class TwitterClient:
    """Twitter API client wrapper."""

    def __init__(self):
        """Initialize Twitter client."""
        self.api: Optional[API] = None
        self._cookies_loaded = False
        self._accounts: List[Dict[str, str]] = []

    async def initialize(self, cookies: Optional[List[Dict]] = None) -> None:
        """Initialize API with cookies."""
        if cookies is None:
            cookies = json.loads(settings.twitter_cookies)

        self._accounts = cookies

        # Create API instance
        self.api = API()

        # Add cookies for guest access
        for cookie in cookies:
            if cookie.get("name") in ("auth_token", "ct0"):
                await self.api.pool.add_account(
                    username=cookie.get("name", "guest"),
                    password="",
                    email="",
                    email_password="",
                )

        # Note: For full functionality, you need to login with real credentials
        # For now, we try to use guest tokens
        try:
            await self.api.pool.login_all()
        except Exception as e:
            logger.warning(f"Login failed, trying guest mode: {e}")

        self._cookies_loaded = True
        logger.info("Twitter client initialized")

    async def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user profile information."""
        if not self.api:
            raise RuntimeError("Twitter client not initialized")

        try:
            user = await self.api.user_by_login(username)
            return {
                "id": str(user.id),
                "username": user.username,
                "display_name": user.displayname,
                "bio": user.biography,
                "followers_count": user.followers,
                "following_count": user.following,
                "tweets_count": user.statuses_count,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        except Exception as e:
            logger.error(f"Failed to get user info for {username}: {e}")
            return None

    async def get_user_tweets(
        self,
        username: str,
        limit: int = 100,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get tweets for a user."""
        if not self.api:
            raise RuntimeError("Twitter client not initialized")

        try:
            tweets = await self.api.user_tweets(username, limit=limit)

            result = []
            for tweet in tweets:
                tweet_data = self._parse_tweet(tweet)
                if since and tweet.postedAt:
                    if tweet.postedAt < since:
                        continue
                if until and tweet.postedAt:
                    if tweet.postedAt > until:
                        continue
                result.append(tweet_data)

            return result
        except Exception as e:
            logger.error(f"Failed to get tweets for {username}: {e}")
            return []

    async def get_tweets_and_replies(
        self,
        username: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get tweets and replies for a user."""
        if not self.api:
            raise RuntimeError("Twitter client not initialized")

        try:
            tweets = await self.api.user_tweets_and_replies(username, limit=limit)
            return [self._parse_tweet(t) for tweet in tweets]
        except Exception as e:
            logger.error(f"Failed to get tweets/replies for {username}: {e}")
            return []

    async def get_tweet_by_id(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Get single tweet by ID."""
        if not self.api:
            raise RuntimeError("Twitter client not initialized")

        try:
            tweet = await self.api.tweet_details(int(tweet_id))
            return self._parse_tweet(tweet)
        except Exception as e:
            logger.error(f"Failed to get tweet {tweet_id}: {e}")
            return None

    async def search_tweets(
        self,
        query: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Search tweets by query."""
        if not self.api:
            raise RuntimeError("Twitter client not initialized")

        try:
            tweets = await self.api.search(query, limit=limit)
            result = []
            for tweet in tweets:
                tweet_data = self._parse_tweet(tweet)
                if since and tweet.postedAt:
                    if tweet.postedAt < since:
                        continue
                result.append(tweet_data)
            return result
        except Exception as e:
            logger.error(f"Search failed for {query}: {e}")
            return []

    def _parse_tweet(self, tweet: Tweet) -> Dict[str, Any]:
        """Parse tweet object to dict."""
        media = []
        if tweet.media:
            for m in tweet.media:
                media.append(
                    {
                        "type": m.type if hasattr(m, "type") else "unknown",
                        "url": m.url if hasattr(m, "url") else str(m),
                    }
                )

        return {
            "id": str(tweet.id),
            "text": tweet.rawContent,
            "author_username": tweet.user.username if tweet.user else "unknown",
            "author_display_name": tweet.user.displayname if tweet.user else "Unknown",
            "author_id": str(tweet.user.id) if tweet.user else None,
            "posted_at": tweet.postedAt.isoformat() if tweet.postedAt else None,
            "likes": tweet.likeCount if hasattr(tweet, "likeCount") else 0,
            "retweets": tweet.retweetCount if hasattr(tweet, "retweetCount") else 0,
            "replies": tweet.replyCount if hasattr(tweet, "replyCount") else 0,
            "views": tweet.viewCount if hasattr(tweet, "viewCount") else 0,
            "is_reply": tweet.replyCount > 0 if hasattr(tweet, "replyCount") else False,
            "is_retweet": tweet.retweetCount > 0
            if hasattr(tweet, "retweetCount")
            else False,
            "is_thread": hasattr(tweet, "inReplyToTweetId") and tweet.inReplyToTweetId,
            "reply_to_tweet_id": str(tweet.inReplyToTweetId)
            if hasattr(tweet, "inReplyToTweetId") and tweet.inReplyToTweetId
            else None,
            "reply_to_username": None,  # twscrape may not provide this directly
            "media": media,
            "url": f"https://x.com/{tweet.user.username if tweet.user else 'unknown'}/status/{tweet.id}"
            if tweet.user
            else None,
        }

    async def close(self) -> None:
        """Close client."""
        if self.api:
            # twscrape cleanup if needed
            pass
        self._cookies_loaded = False
        logger.info("Twitter client closed")


# Global client instance
_twitter_client: Optional[TwitterClient] = None


async def get_twitter_client() -> TwitterClient:
    """Get or create Twitter client instance."""
    global _twitter_client
    if _twitter_client is None:
        _twitter_client = TwitterClient()
        await _twitter_client.initialize()
    return _twitter_client
