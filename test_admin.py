import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import logging
from aiogram.types import CallbackQuery
from handlers.admin import text_category, edit
from utils import get_admins, get_interface_texts, get_steps

class TestTextCategory(unittest.TestCase):
    def setUp(self):
        logging.getLogger().setLevel(logging.CRITICAL)
        self.mock_call = AsyncMock(spec=CallbackQuery)
        self.mock_call.from_user = MagicMock()
        self.mock_call.from_user.id = 123
        self.mock_call.data = "text_category:messages"
        self.mock_call.answer = AsyncMock()
        self.mock_call.message = MagicMock()
        self.mock_call.message.edit_text = AsyncMock()
        self.mock_state = MagicMock()

    @patch('handlers.admin.config.ADMINS', [123])
    @patch('handlers.admin.utils.get_admins', return_value=[123])
    @patch('handlers.admin.utils.get_interface_texts')
    @patch('handlers.admin.kb.markup_text_keys')
    async def test_text_category_valid_strings(self, mock_markup, mock_get_texts, mock_get_admins, mock_admins):
        """Test with valid string values"""
        valid_texts = {
            "messages": {
                "welcome": "Welcome message",
                "catalog": "Catalog message that is long enough to slice"
            }
        }
        mock_get_texts.return_value = valid_texts

        await text_category(self.mock_call, self.mock_state)
        self.mock_call.answer.assert_called_once()
        self.mock_call.message.edit_text.assert_called_once()
        mock_markup.assert_called_once()

    @patch('handlers.admin.config.ADMINS', [123])
    @patch('handlers.admin.utils.get_admins', return_value=[123])
    @patch('handlers.admin.utils.get_interface_texts')
    @patch('handlers.admin.kb.markup_text_keys')
    async def test_text_category_non_string_value(self, mock_markup, mock_get_texts, mock_get_admins, mock_admins):
        """Test with non-string value, should log warning and convert to str"""
        invalid_texts = {
            "messages": {
                "welcome": "Welcome message",
                "catalog": 123  # int instead of str
            }
        }
        mock_get_texts.return_value = invalid_texts

        with self.assertLogs('root', level='WARNING') as log:
            await text_category(self.mock_call, self.mock_state)
            self.assertIn("Non-string value", log.output[0])
            self.mock_call.answer.assert_called_once()
            self.mock_call.message.edit_text.assert_called_once()
            mock_markup.assert_called_once()

    @patch('handlers.admin.config.ADMINS', [])
    @patch('handlers.admin.utils.get_admins', return_value=[])
    async def test_text_category_access_denied(self, mock_get_admins, mock_admins):
        """Test access denied case"""
        self.mock_call.from_user.id = 999  # not admin

        await text_category(self.mock_call, self.mock_state)
        self.mock_call.answer.assert_called_once()
        self.mock_call.message.edit_text.assert_not_called()

class TestEditFunction(unittest.TestCase):
    def setUp(self):
        logging.getLogger().setLevel(logging.CRITICAL)
        self.mock_call = AsyncMock(spec=CallbackQuery)
        self.mock_call.from_user = MagicMock()
        self.mock_call.from_user.id = 123
        self.mock_call.data = "edit:join"
        self.mock_call.answer = AsyncMock()
        self.mock_call.message = MagicMock()
        self.mock_call.message.chat = MagicMock()
        self.mock_call.message.chat.id = 456
        self.mock_call.message.delete = AsyncMock()
        self.mock_call.message.answer = AsyncMock()
        self.mock_state = AsyncMock()
        self.mock_state.set_state = AsyncMock()
        self.mock_state.update_data = AsyncMock()

    @patch('handlers.admin.utils.get_steps')
    @patch('handlers.admin.kb.markup_edit')
    @patch('handlers.admin.bot.send_message')
    async def test_edit_join_callback(self, mock_send, mock_markup, mock_get_steps):
        mock_steps = {
            'join': {
                'content_type': 'text',
                'text': 'Test text for join'
            }
        }
        mock_get_steps.return_value = mock_steps
        mock_markup.return_value = MagicMock()

        await edit(self.mock_call, self.mock_state)

        self.mock_state.set_state.assert_called_once()
        self.mock_state.update_data.assert_called_with(key='join')
        mock_send.assert_called_once_with(
            chat_id=456,
            text='Test text for join',
            reply_markup=None,
            parse_mode='HTML'
        )
        self.mock_call.answer.assert_called_once()
        self.mock_call.message.delete.assert_called_once()
        self.mock_call.message.answer.assert_called_once_with('👉 Что вы хотите изменить:', reply_markup=mock_markup.return_value)
        mock_get_steps.assert_called_once()

    @patch('handlers.admin.utils.get_steps')
    @patch('handlers.admin.kb.markup_edit')
    @patch('handlers.admin.bot.send_message')
    async def test_edit_start_callback(self, mock_send, mock_markup, mock_get_steps):
        mock_steps = {
            'start': {
                'content_type': 'text',
                'text': 'Test text for start'
            }
        }
        self.mock_call.data = "edit:start"
        mock_get_steps.return_value = mock_steps
        mock_markup.return_value = MagicMock()

        await edit(self.mock_call, self.mock_state)

        self.mock_state.update_data.assert_called_with(key='start')
        mock_send.assert_called_once_with(
            chat_id=456,
            text='Test text for start',
            reply_markup=None,
            parse_mode='HTML'
        )
        self.mock_call.message.answer.assert_called_once_with('👉 Что вы хотите изменить:', reply_markup=mock_markup.return_value)

    @patch('handlers.admin.utils.get_steps')
    @patch('handlers.admin.kb.markup_edit')
    @patch('handlers.admin.bot.send_message')
    async def test_edit_step1_non_text_fallback(self, mock_send, mock_markup, mock_get_steps):
        mock_steps = {
            'step1': {
                'content_type': 'photo',
                'caption': 'Fallback caption',
                'text': None
            }
        }
        self.mock_call.data = "edit:step1"
        mock_get_steps.return_value = mock_steps
        mock_markup.return_value = MagicMock()

        await edit(self.mock_call, self.mock_state)

        self.mock_state.update_data.assert_called_with(key='step1')
        mock_send.assert_called_once_with(
            chat_id=456,
            text='Fallback caption',
            reply_markup=None,
            parse_mode='HTML'
        )
        self.mock_call.answer.assert_called_once()
        self.mock_call.message.delete.assert_called_once()
        self.mock_call.message.answer.assert_called_once()

if __name__ == '__main__':
    unittest.main()
