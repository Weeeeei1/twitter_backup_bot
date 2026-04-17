"""Telegram media uploader."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Union

from telegram import Bot
from telegram.error import TelegramError


logger = logging.getLogger(__name__)


class MediaUploader:
    """Uploader for Telegram."""

    # Telegram file size limits
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB for bots
    MAX_VIDEO_SIZE = 2000 * 1024 * 1024  # 2GB with local server
    MAX_PHOTO_SIZE = 20 * 1024 * 1024  # 20MB for photos

    def __init__(self, bot: Bot):
        """Initialize uploader."""
        self.bot = bot

    async def upload_video(
        self,
        file_path: str,
        chat_id: int,
        caption: Optional[str] = None,
        duration: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        thumb_path: Optional[str] = None,
    ) -> Optional[str]:
        """Upload video to Telegram chat."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        file_size = os.path.getsize(file_path)

        try:
            with open(file_path, "rb") as video_file:
                if thumb_path and os.path.exists(thumb_path):
                    with open(thumb_path, "rb") as thumb_file:
                        message = await self.bot.send_video(
                            chat_id=chat_id,
                            video=video_file,
                            caption=caption,
                            duration=duration,
                            width=width,
                            height=height,
                            thumb=thumb_file,
                            disable_notification=True,
                        )
                else:
                    message = await self.bot.send_video(
                        chat_id=chat_id,
                        video=video_file,
                        caption=caption,
                        duration=duration,
                        width=width,
                        height=height,
                        disable_notification=True,
                    )

            logger.info(
                f"Uploaded video to {chat_id}, file_id: {message.video.file_id}"
            )
            return message.video.file_id

        except TelegramError as e:
            logger.error(f"Failed to upload video: {e}")
            return None

    async def upload_photo(
        self,
        file_path: str,
        chat_id: int,
        caption: Optional[str] = None,
    ) -> Optional[str]:
        """Upload photo to Telegram chat."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        try:
            with open(file_path, "rb") as photo_file:
                message = await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo_file,
                    caption=caption,
                    disable_notification=True,
                )

            logger.info(
                f"Uploaded photo to {chat_id}, file_id: {message.photo[-1].file_id}"
            )
            return message.photo[-1].file_id

        except TelegramError as e:
            logger.error(f"Failed to upload photo: {e}")
            return None

    async def upload_document(
        self,
        file_path: str,
        chat_id: int,
        caption: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Optional[str]:
        """Upload as document."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        try:
            with open(file_path, "rb") as doc_file:
                message = await self.bot.send_document(
                    chat_id=chat_id,
                    document=doc_file,
                    caption=caption,
                    filename=filename,
                    disable_notification=True,
                )

            logger.info(
                f"Uploaded document to {chat_id}, file_id: {message.document.file_id}"
            )
            return message.document.file_id

        except TelegramError as e:
            logger.error(f"Failed to upload document: {e}")
            return None

    async def upload_media_group(
        self,
        file_paths: list,
        chat_id: int,
        captions: Optional[list] = None,
    ) -> Optional[list]:
        """Upload multiple media as album."""
        if not file_paths:
            return None

        media_objects = []

        try:
            for i, file_path in enumerate(file_paths):
                if not os.path.exists(file_path):
                    continue

                ext = os.path.splitext(file_path)[1].lower()
                caption = captions[i] if captions and i < len(captions) else None

                if ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
                    with open(file_path, "rb") as photo_file:
                        # For albums, we need InputMediaPhoto
                        from telegram import InputMediaPhoto

                        media_objects.append(
                            InputMediaPhoto(photo_file, caption=caption)
                        )
                elif ext in [".mp4", ".mov", ".avi", ".mkv"]:
                    with open(file_path, "rb") as video_file:
                        from telegram import InputMediaVideo

                        media_objects.append(
                            InputMediaVideo(video_file, caption=caption)
                        )
                else:
                    with open(file_path, "rb") as doc_file:
                        from telegram import InputMediaDocument

                        media_objects.append(
                            InputMediaDocument(doc_file, caption=caption)
                        )

            if media_objects:
                messages = await self.bot.send_media_group(
                    chat_id=chat_id,
                    media=media_objects,
                    disable_notification=True,
                )
                file_ids = [
                    msg.photo[-1].file_id if msg.photo else msg.document.file_id
                    for msg in messages
                ]
                return file_ids

        except TelegramError as e:
            logger.error(f"Failed to upload media group: {e}")
            return None

        return None

    def get_file_id_from_path(self, file_path: str) -> str:
        """Get file ID from path (for already uploaded files)."""
        return os.path.basename(file_path)
