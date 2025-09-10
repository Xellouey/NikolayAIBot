#!/usr/bin/env python
"""
Unit tests for media-aware mailing() function using mocks.
"""
import sys
import os
import unittest
from unittest.mock import AsyncMock, MagicMock

# Ensure project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import keyboards as kb
import mail as mail_module


def make_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "Open", "url": "https://example.com"}],
        ]
    }


class TestMailingWithMedia(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mock users
        self.users = [{"user_id": 111}, {"user_id": 222}]
        mail_module.u.get_all_users = AsyncMock(return_value=self.users)

        # Mock bot methods
        self.bot = mail_module.bot
        self.bot.send_photo = AsyncMock()
        self.bot.send_video = AsyncMock()
        self.bot.send_message = AsyncMock()
        self.bot.forward_message = AsyncMock(return_value=type("Fwd", (), {"message_id": 777}))
        self.bot.edit_message_reply_markup = AsyncMock()

    async def test_photo_path(self):
        keyboard = make_keyboard()
        message_info = {"text": "Caption text", "media": "photo_file_id", "media_type": "photo"}

        await mail_module.mailing(message_id=1, from_id=999, keyboard=keyboard, message_info=message_info)

        # send_photo called for each user
        self.assertEqual(self.bot.send_photo.await_count, len(self.users))
        # Others not used
        self.bot.send_video.assert_not_called()
        self.bot.forward_message.assert_not_called()
        self.bot.send_message.assert_not_called()

    async def test_video_path(self):
        keyboard = make_keyboard()
        message_info = {"text": "Video caption", "media": "video_file_id", "media_type": "video"}

        await mail_module.mailing(message_id=2, from_id=999, keyboard=keyboard, message_info=message_info)

        self.assertEqual(self.bot.send_video.await_count, len(self.users))
        self.bot.send_photo.assert_not_called()
        self.bot.forward_message.assert_not_called()
        self.bot.send_message.assert_not_called()

    async def test_text_only_path(self):
        keyboard = make_keyboard()
        message_info = {"text": "Just text", "media": None, "media_type": None}

        await mail_module.mailing(message_id=3, from_id=999, keyboard=keyboard, message_info=message_info)

        self.assertEqual(self.bot.send_message.await_count, len(self.users))
        self.bot.send_photo.assert_not_called()
        self.bot.send_video.assert_not_called()
        self.bot.forward_message.assert_not_called()

    async def test_backward_compat_string_message(self):
        keyboard = make_keyboard()
        message_info = "Legacy text message"

        await mail_module.mailing(message_id=4, from_id=999, keyboard=keyboard, message_info=message_info)

        self.assertEqual(self.bot.send_message.await_count, len(self.users))
        self.bot.send_photo.assert_not_called()
        self.bot.send_video.assert_not_called()
        self.bot.forward_message.assert_not_called()

    async def test_fallback_forward_when_no_info(self):
        keyboard = make_keyboard()

        await mail_module.mailing(message_id=5, from_id=999, keyboard=keyboard, message_info=None)

        # Should forward and then edit reply markup
        self.assertEqual(self.bot.forward_message.await_count, len(self.users))
        self.assertEqual(self.bot.edit_message_reply_markup.await_count, len(self.users))
        self.bot.send_message.assert_not_called()
        self.bot.send_photo.assert_not_called()
        self.bot.send_video.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)

