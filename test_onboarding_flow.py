import unittest
from unittest.mock import AsyncMock, MagicMock
from aiogram import Bot, Dispatcher
from aiogram.types import Message, User, Chat
from aiogram.fsm.context import FSMContext
from handlers.client import start
from database import user, lesson
import asyncio

class TestOnboardingFlow(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = AsyncMock(spec=Bot)
        self.dp = Dispatcher()
        self.user = User(id=1, is_bot=False, first_name="Test", username="testuser")
        self.chat = Chat(id=1, type="private")
        self.message = Message(
            message_id=1,
            from_user=self.user,
            chat=self.chat,
            text="/start",
            bot=self.bot
        )
        self.state = FSMContext(self.dp.storage, self.bot, self.chat, self.user)
        
        # Mock database operations
        self.u = user.User()
        self.u.create_user = AsyncMock()
        self.u.get_user = AsyncMock(return_value=None)
        self.u.mark_onboarding_complete = AsyncMock()
        self.u.check_onboarding_status = AsyncMock(return_value=False)
        
        # Mock lesson and purchase
        self.l = lesson.Lesson()
        self.l.ensure_lead_magnet = AsyncMock(return_value=1)
        self.l.get_lesson = AsyncMock(return_value={
            'title': 'Test Lesson',
            'description': 'Test desc',
            'video_file_id': 'test_video_id',
            'document_file_id': 'test_doc_id',
            'text_content': 'Test content'
        })
        
        self.p = lesson.Purchase()
        self.p.check_user_has_lesson = AsyncMock(return_value=False)
        self.p.create_purchase = AsyncMock()

    async def test_onboarding_flow(self):
        # Mock utils.get_steps
        self.message.text = "/start"
        self.message.from_user = self.user
        
        # Mock bot.send_video and bot.send_document calls
        self.bot.send_video = AsyncMock()
        self.bot.send_document = AsyncMock()
        self.bot.send_message = AsyncMock()
        
        # Run the start handler
        await start(self.message, self.state, self.bot)
        
        # Check if lead lesson was sent
        self.bot.send_video.assert_called()
        self.bot.send_document.assert_called()
        self.assertGreaterEqual(len(self.bot.send_message.call_args_list), 1)
        
        # Check if onboarding marked complete
        self.u.mark_onboarding_complete.assert_called_once_with(self.user.id)
        
        # Check if purchase was created
        self.p.create_purchase.assert_called_once_with(
            user_id=self.user.id,
            lesson_id=1,
            price_paid_usd=0,
            price_paid_stars=0,
            payment_id="lead_magnet"
        )

if __name__ == '__main__':
    asyncio.run(unittest.main())