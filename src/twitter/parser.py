"""Tweet parser for extracting structured data."""

import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.twitter.client import TwitterClient


logger = logging.getLogger(__name__)


class TweetParser:
    """Parser for tweet data."""

    @staticmethod
    def parse_tweet_url(url: str) -> Optional[Dict[str, str]]:
        """Parse Twitter URL to extract username and tweet ID."""
        patterns = [
            r"(?:https?://)?(?:twitter\.com|x\.com)/(\w+)/status/(\d+)",
            r"(?:twitter\.com|x\.com)/(\w+)/status/(\d+)",
        ]

        for pattern in patterns:
            match = re.match(pattern, url)
            if match:
                return {
                    "username": match.group(1),
                    "tweet_id": match.group(2),
                }

        return None

    @staticmethod
    def parse_profile_url(url: str) -> Optional[str]:
        """Parse Twitter profile URL to extract username."""
        patterns = [
            r"(?:https?://)?(?:twitter\.com|x\.com)/(\w+)/?$",
            r"(?:twitter\.com|x\.com)/(\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1).rstrip("/")

        return None

    @staticmethod
    def format_tweet_text(tweet: Dict[str, Any]) -> str:
        """Format tweet as readable text."""
        lines = []

        # Header
        author = tweet.get(
            "author_display_name", tweet.get("author_username", "Unknown")
        )
        username = tweet.get("author_username", "")
        lines.append(f"**@{username}** ({author})")

        # Posted time
        if tweet.get("posted_at"):
            try:
                dt = datetime.fromisoformat(tweet["posted_at"].replace("Z", "+00:00"))
                lines.append(f"🕐 {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            except (ValueError, TypeError):
                pass

        # Content
        text = tweet.get("text", "")
        if text:
            lines.append("")
            lines.append(text)

        # Stats
        stats = []
        if tweet.get("likes"):
            stats.append(f"❤️ {tweet['likes']}")
        if tweet.get("retweets"):
            stats.append(f"🔁 {tweet['retweets']}")
        if tweet.get("replies"):
            stats.append(f"💬 {tweet['replies']}")
        if tweet.get("views"):
            stats.append(f"👁 {tweet['views']}")

        if stats:
            lines.append("")
            lines.append(" ".join(stats))

        # Media
        if tweet.get("media"):
            lines.append("")
            lines.append(f"📎 {len(tweet['media'])} 个媒体附件")

        # URL
        if tweet.get("url"):
            lines.append("")
            lines.append(f"🔗 {tweet['url']}")

        return "\n".join(lines)

    @staticmethod
    def format_thread(tweets: List[Dict[str, Any]]) -> str:
        """Format a thread of tweets."""
        if not tweets:
            return "🧵 空线程"

        lines = [f"🧵 线程 ({len(tweets)} 条推文)", ""]

        for i, tweet in enumerate(tweets, 1):
            lines.append(f"**第 {i} 条:**")
            lines.append(TweetParser.format_tweet_text(tweet))
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def extract_thread_chain(tweet: Dict[str, Any]) -> List[str]:
        """Extract tweet IDs in a thread chain."""
        chain = []
        current = tweet

        while current.get("reply_to_tweet_id"):
            chain.append(current["reply_to_tweet_id"])
            # Note: In real implementation, we'd need to fetch parent tweets
            break  # For now, just the immediate parent

        return chain
