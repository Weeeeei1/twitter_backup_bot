"""Media downloader using yt-dlp."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import yt_dlp


logger = logging.getLogger(__name__)


class MediaDownloader:
    """Media downloader using yt-dlp."""

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize downloader."""
        self.output_dir = output_dir or tempfile.mkdtemp(prefix="twitter_media_")
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    async def download_video(self, url: str) -> Optional[Dict]:
        """Download video from URL."""
        return await self._download(
            url,
            formats=["bestvideo+bestaudio/best", "best"],
            merge_output_format="mp4",
        )

    async def download_image(self, url: str) -> Optional[Dict]:
        """Download image from URL."""
        return await self._download(
            url,
            formats=["jpeg", "jpg", "png", "webp"],
            merge_output_format=None,
        )

    async def download_media(
        self, url: str, media_type: str = "video"
    ) -> Optional[Dict]:
        """Download media based on type."""
        if "video" in media_type.lower():
            return await self.download_video(url)
        elif "image" in media_type.lower():
            return await self.download_image(url)
        else:
            return await self.download_video(url)

    async def _download(
        self,
        url: str,
        formats: List[str],
        merge_output_format: Optional[str] = None,
    ) -> Optional[Dict]:
        """Internal download method."""
        loop = asyncio.get_event_loop()

        ydl_opts = {
            "outtmpl": f"{self.output_dir}/%(id)s.%(ext)s",
            "format": "/".join(formats),
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
        }

        if merge_output_format:
            ydl_opts["merge_output_format"] = merge_output_format

        def _do_download():
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info:
                        return {
                            "id": info.get("id"),
                            "title": info.get("title"),
                            "filename": ydl.prepare_filename(info),
                            "ext": info.get("ext"),
                            "duration": info.get("duration"),
                            "thumbnail": info.get("thumbnail"),
                            "view_count": info.get("view_count"),
                            "like_count": info.get("like_count"),
                        }
            except Exception as e:
                logger.error(f"Download failed for {url}: {e}")
                return None

        try:
            result = await loop.run_in_executor(None, _do_download)
            return result
        except Exception as e:
            logger.error(f"Download error for {url}: {e}")
            return None

    async def download_twitter_media(self, tweet_url: str) -> List[Dict]:
        """Download all media from a Twitter URL."""
        return await self._download(
            tweet_url,
            formats=["bestvideo+bestaudio/best"],
            merge_output_format="mp4",
        )

    def get_file_path(self, filename: str) -> str:
        """Get full path to downloaded file."""
        return os.path.join(self.output_dir, filename)

    def cleanup_file(self, filepath: str) -> bool:
        """Delete a downloaded file."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            logger.error(f"Failed to cleanup {filepath}: {e}")
        return False

    async def cleanup_all(self) -> None:
        """Clean up all downloaded files."""
        try:
            for filename in os.listdir(self.output_dir):
                filepath = os.path.join(self.output_dir, filename)
                if os.path.isfile(filepath):
                    os.remove(filepath)
        except Exception as e:
            logger.error(f"Failed to cleanup output dir: {e}")
