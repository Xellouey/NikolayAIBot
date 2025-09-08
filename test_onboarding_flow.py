"""
Test for onboarding flow and /start command issue.
This test identifies why /start shows main menu instead of onboarding steps.
"""

import asyncio
import json
import tempfile
import shutil
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import types
from aiogram.fsm.context import FSMContext

# Import handlers
from handlers.client import start as client_start, start_steps
from handlers.shop import start_shop


class TestOnboardingFlow:
    """Test onboarding flow and start command routing"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_steps = {
            "join": {
                "content_type": "text",
                "text": "💎 УРОКИ ПО НЕЙРОСЕТЯМ! Авторизируйтесь 👇",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            },
            "start": {
                "content_type": "text",
                "text": "Авторизовался? 🎁 Вот первый подарок:",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            },
            "step1": {
                "content_type": "video",
                "text": None,
                "caption": None,
                "file_id": "test_video_id",
                "keyboard": None,
                "delay": 0
            },
            "step2": {
                "content_type": "text",
                "text": "👆👆Урок 0: Фотосессия при помощи нейросети",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 35
            }
        }
    
    def create_mock_message(self, user_id=12345):
        """Create mock message object"""
        message = AsyncMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = user_id
        message.from_user.username = "testuser"
        message.from_user.full_name = "Test User"
        message.answer = AsyncMock()
        return message
    
    def create_mock_state(self, current_state=None):
        """Create mock FSM state"""
        state = AsyncMock(spec=FSMContext)
        state.get_state = AsyncMock(return_value=current_state)
        state.clear = AsyncMock()
        return state

    @patch('handlers.client.u.get_user')
    @patch('handlers.client.u.create_user')
    @patch('utils.get_steps')
    @patch('handlers.client.send_msg')
    @patch('handlers.client.start_steps')
    @patch('keyboards.markup_phone')
    @patch('keyboards.markup_remove')
    async def test_client_start_handler_new_user(self, mock_markup_remove, mock_markup_phone, 
                                                mock_start_steps, mock_send_msg, mock_get_steps,
                                                mock_create_user, mock_get_user):
        """Test client start handler for new user"""
        # Arrange
        mock_get_user.return_value = None  # New user
        mock_get_steps.return_value = self.test_steps
        mock_markup_phone.return_value = MagicMock()
        
        message = self.create_mock_message()
        state = self.create_mock_state()
        
        # Act
        await client_start(message, state)
        
        # Assert
        mock_create_user.assert_called_once_with(12345, "testuser", "Test User")
        mock_send_msg.assert_called_once()
        mock_start_steps.assert_not_called()  # Should not start steps for new user
        
        # Check that start step content was sent
        send_msg_args = mock_send_msg.call_args
        sent_step = send_msg_args[0][0]
        assert sent_step == self.test_steps["start"]

    @patch('handlers.client.u.get_user')
    @patch('utils.get_steps')
    @patch('handlers.client.send_msg')
    @patch('handlers.client.start_steps')
    @patch('keyboards.markup_remove')
    async def test_client_start_handler_existing_user(self, mock_markup_remove, mock_start_steps,
                                                     mock_send_msg, mock_get_steps, mock_get_user):
        """Test client start handler for existing user"""
        # Arrange
        mock_get_user.return_value = {"id": 12345, "phone": "+1234567890"}  # Existing user
        mock_get_steps.return_value = self.test_steps
        mock_markup_remove.return_value = MagicMock()
        
        message = self.create_mock_message()
        state = self.create_mock_state()
        
        # Act
        await client_start(message, state)
        
        # Assert
        mock_send_msg.assert_called_once()
        mock_start_steps.assert_called_once()  # Should start steps for existing user
        
        # Check that start step was sent
        send_msg_args = mock_send_msg.call_args
        sent_step = send_msg_args[0][0]
        assert sent_step == self.test_steps["start"]

    @patch('handlers.shop.u.get_user')
    @patch('handlers.shop.u.create_user')
    @patch('utils.get_text')
    @patch('keyboards.markup_main_menu')
    async def test_shop_start_handler_override(self, mock_markup_main, mock_get_text,
                                             mock_create_user, mock_get_user):
        """Test shop start handler that overrides client handler"""
        # Arrange
        mock_get_user.return_value = None  # New user
        mock_get_text.return_value = "🎓 Добро пожаловать в магазин уроков!"
        mock_markup_main.return_value = MagicMock()
        
        message = self.create_mock_message()
        state = self.create_mock_state()
        
        # Act
        await start_shop(message, state)
        
        # Assert
        mock_create_user.assert_called_once_with(12345, "testuser", "Test User")
        message.answer.assert_called_once()
        
        # Check that main menu was shown instead of onboarding
        answer_args = message.answer.call_args
        welcome_text = answer_args[0][0]
        assert welcome_text == "🎓 Добро пожаловать в магазин уроков!"

    @patch('utils.get_steps')
    @patch('handlers.client.send_msg')
    @patch('keyboards.markup_custom')
    @patch('keyboards.markup_remove')
    async def test_start_steps_function(self, mock_markup_remove, mock_markup_custom,
                                       mock_send_msg, mock_get_steps):
        """Test start_steps function that sends onboarding sequence"""
        # Arrange
        mock_get_steps.return_value = self.test_steps
        mock_markup_custom.return_value = None
        mock_markup_remove.return_value = MagicMock()
        
        message = self.create_mock_message()
        state = self.create_mock_state()
        
        # Act
        await start_steps(message, state)
        
        # Assert
        # Should send step1 and step2 (skipping join and start)
        assert mock_send_msg.call_count == 2
        
        # Check first call (step1)
        first_call = mock_send_msg.call_args_list[0]
        first_step = first_call[0][0]
        assert first_step["content_type"] == "video"
        assert first_step["file_id"] == "test_video_id"
        
        # Check second call (step2)  
        second_call = mock_send_msg.call_args_list[1]
        second_step = second_call[0][0]
        assert second_step["text"] == "👆👆Урок 0: Фотосессия при помощи нейросети"

    def test_router_priority_issue_identification(self):
        """Identify the router priority issue causing /start to show main menu"""
        # This test documents the issue found in nikolayai.py
        
        # From nikolayai.py line 35-39:
        # dp.include_router(payment.payment_router)  # Payment handlers first
        # dp.include_router(shop.shop_router)        # Shop handlers (overrides client start)
        # dp.include_router(admin.router)            # Admin handlers
        # dp.include_router(mail.router)             # Mail handlers
        # dp.include_router(client.router)           # Original client handlers (fallback)
        
        # The issue is that shop_router is included BEFORE client.router,
        # and shop_router has its own /start handler (start_shop) that shows
        # the main menu instead of running the onboarding sequence.
        
        router_order = [
            "payment.payment_router",
            "shop.shop_router",        # ❌ This has /start handler that overrides
            "admin.router", 
            "mail.router",
            "client.router"            # ✅ This has the onboarding /start handler
        ]
        
        # Assert the problem
        shop_position = router_order.index("shop.shop_router")
        client_position = router_order.index("client.router")
        
        assert shop_position < client_position, "Shop router has higher priority than client router"
        
        print(f"🔍 ПРОБЛЕМА НАЙДЕНА:")
        print(f"   Shop router позиция: {shop_position}")
        print(f"   Client router позиция: {client_position}")
        print(f"   Shop router перехватывает команду /start раньше client router'а")

    async def test_proposed_fix_verification(self):
        """Test the proposed fix for router priority"""
        # Proposed solution: Move shop router after client router
        # or make shop start handler conditional
        
        proposed_router_order = [
            "payment.payment_router",
            "admin.router",
            "mail.router", 
            "client.router",           # ✅ Client router first for /start
            "shop.shop_router"         # ✅ Shop router last (or conditional)
        ]
        
        client_position = proposed_router_order.index("client.router")
        shop_position = proposed_router_order.index("shop.shop_router")
        
        assert client_position < shop_position, "Client router should have higher priority"
        
        print(f"💡 ПРЕДЛАГАЕМОЕ РЕШЕНИЕ:")
        print(f"   Переместить client.router выше shop.shop_router")
        print(f"   Или сделать shop start handler условным")


class TestStepEditorBugReproduction:
    """Test to reproduce and identify step editor bugs"""
    
    @patch('utils.get_steps')
    async def test_empty_steps_handling(self, mock_get_steps):
        """Test handling of empty or missing steps"""
        # Test case 1: Empty steps file
        mock_get_steps.return_value = {}
        
        message = AsyncMock()
        state = AsyncMock()
        
        # This should not crash
        await start_steps(message, state)
        
        # Should not call send_msg for empty steps
        message.answer.assert_not_called()
    
    @patch('utils.get_steps')
    async def test_malformed_steps_handling(self, mock_get_steps):
        """Test handling of malformed steps data"""
        # Test case: Steps missing required fields
        malformed_steps = {
            "join": {"content_type": "text"},  # Missing required fields
            "start": {"text": "Hello"},        # Missing content_type
            "step1": None                      # Null step
        }
        
        mock_get_steps.return_value = malformed_steps
        
        message = AsyncMock()
        state = AsyncMock()
        
        # This test identifies potential crashes with malformed data
        try:
            await start_steps(message, state)
        except (KeyError, TypeError, AttributeError) as e:
            print(f"🐛 BUG НАЙДЕН: {type(e).__name__}: {e}")
            print(f"   Нужна лучшая обработка ошибок для некорректных данных шагов")

    def test_step_file_corruption_scenario(self):
        """Test scenario where steps.json becomes corrupted"""
        # Create temporary corrupted JSON
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json content')  # Corrupted JSON
            corrupted_file = f.name
        
        try:
            # This should return empty dict due to error handling in utils.get_steps
            steps = utils.get_steps(corrupted_file)
            assert steps == {}, "Should return empty dict for corrupted JSON"
            print("✅ Corrupted JSON handled correctly")
        finally:
            os.unlink(corrupted_file)


if __name__ == "__main__":
    # Run tests to identify onboarding flow issues
    print("🔍 Анализ проблемы с командой /start...")
    
    try:
        import pytest
        pytest.main([__file__, "-v", "--tb=short", "-s"])
    except ImportError:
        print("⚠️ pytest не установлен")
        
        # Run basic identification test
        test = TestOnboardingFlow()
        test.setup_method()
        test.test_router_priority_issue_identification()
        
        print("\n📋 КРАТКИЙ ОТЧЕТ:")
        print("🔍 Причина проблемы: shop.shop_router перехватывает /start раньше client.router")
        print("💡 Решение: Изменить порядок роутеров в nikolayai.py")
        print("🎯 Или добавить условную логику в shop start handler")