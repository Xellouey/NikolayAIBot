"""
Тесты для админ-панели и системы редактирования текстов
"""
import pytest
import asyncio
import json
import os
import sys
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiogram import types
from aiogram.fsm.context import FSMContext
from handlers.admin import (
    promocodes_menu, 
    text_settings_menu,
    currency_rate_menu,
    statistics_menu,
    save_text_value
)
from states import FSMSettings
import config
import utils


class TestAdminHandlers:
    """Тесты для обработчиков админ-панели"""
    
    @pytest.fixture
    def mock_call(self):
        """Создаём мок для CallbackQuery"""
        call = MagicMock(spec=types.CallbackQuery)
        call.from_user = MagicMock()
        call.from_user.id = 123456789  # ID админа
        call.from_user.full_name = "Test Admin"
        call.message = MagicMock()
        call.message.edit_text = AsyncMock()
        call.answer = AsyncMock()
        call.data = "test_callback"
        return call
    
    @pytest.fixture
    def mock_state(self):
        """Создаём мок для FSMContext"""
        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()
        state.set_state = AsyncMock()
        state.update_data = AsyncMock()
        state.get_data = AsyncMock(return_value={})
        return state
    
    @pytest.fixture
    def mock_message(self):
        """Создаём мок для Message"""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 123456789
        message.from_user.full_name = "Test Admin"
        message.text = "Тестовый текст"
        message.answer = AsyncMock()
        return message
    
    @pytest.mark.asyncio
    async def test_promocodes_handler_exists(self, mock_call, mock_state):
        """Тест: обработчик промокодов существует и отвечает"""
        # Устанавливаем админа
        with patch('config.ADMINS', [123456789]):
            with patch('utils.get_admins', return_value=[]):
                await promocodes_menu(mock_call, mock_state)
                
                # Проверяем, что был вызван answer
                mock_call.answer.assert_called_once()
                
                # Проверяем, что сообщение было изменено
                mock_call.message.edit_text.assert_called_once()
                args = mock_call.message.edit_text.call_args
                
                # Проверяем, что в тексте есть "Промокоды"
                assert 'промокод' in args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_text_settings_handler_exists(self, mock_call, mock_state):
        """Тест: обработчик настроек текстов существует и отвечает"""
        with patch('config.ADMINS', [123456789]):
            with patch('utils.get_admins', return_value=[]):
                await text_settings_menu(mock_call, mock_state)
                
                mock_call.answer.assert_called_once()
                mock_call.message.edit_text.assert_called_once()
                
                args = mock_call.message.edit_text.call_args
                assert 'настройки текстов' in args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_currency_rate_handler_exists(self, mock_call, mock_state):
        """Тест: обработчик курса валют существует и отвечает"""
        with patch('config.ADMINS', [123456789]):
            with patch('utils.get_admins', return_value=[]):
                # Мокаем получение курса
                with patch('database.lesson.SystemSettings.get_usd_to_stars_rate', 
                          new_callable=AsyncMock, return_value=50):
                    await currency_rate_menu(mock_call, mock_state)
                    
                    mock_call.answer.assert_called_once()
                    mock_call.message.edit_text.assert_called_once()
                    
                    args = mock_call.message.edit_text.call_args
                    assert 'курс' in args[0][0].lower()
                    assert 'USD' in args[0][0]
    
    @pytest.mark.asyncio
    async def test_statistics_handler_exists(self, mock_call, mock_state):
        """Тест: обработчик статистики существует и отвечает"""
        with patch('config.ADMINS', [123456789]):
            with patch('utils.get_admins', return_value=[]):
                # Мокаем все методы получения статистики
                with patch('database.user.User.get_total_users', new_callable=AsyncMock, return_value=100):
                    with patch('database.user.User.get_users_count_since', new_callable=AsyncMock, return_value=10):
                        with patch('database.lesson.Purchase.get_sales_stats', new_callable=AsyncMock, 
                                  return_value={'count': 50, 'total': 1000}):
                            with patch('database.lesson.Purchase.get_sales_stats_period', new_callable=AsyncMock,
                                      return_value={'count': 5, 'total': 100}):
                                with patch('database.lesson.Lesson.get_all_lessons', new_callable=AsyncMock,
                                          return_value=[{}, {}, {}]):
                                    with patch('database.lesson.Promocode.get_all_promocodes', new_callable=AsyncMock,
                                              return_value=[]):
                                        await statistics_menu(mock_call, mock_state)
                                        
                                        mock_call.answer.assert_called_once()
                                        mock_call.message.edit_text.assert_called_once()
                                        
                                        args = mock_call.message.edit_text.call_args
                                        assert 'статистика' in args[0][0].lower()
    
    @pytest.mark.asyncio
    async def test_non_admin_access_denied(self, mock_call, mock_state):
        """Тест: не-админ не может получить доступ"""
        # Устанавливаем не-админа
        mock_call.from_user.id = 999999999
        
        with patch('config.ADMINS', [123456789]):
            with patch('utils.get_admins', return_value=[]):
                await promocodes_menu(mock_call, mock_state)
                
                # Проверяем, что был вызван answer с ошибкой
                mock_call.answer.assert_called_once_with('⚠️ Ошибка доступа')
                
                # Проверяем, что сообщение НЕ было изменено
                mock_call.message.edit_text.assert_not_called()


class TestTextValidation:
    """Тесты валидации текстов"""
    
    @pytest.fixture
    def mock_message(self):
        """Создаём мок для Message"""
        message = MagicMock(spec=types.Message)
        message.from_user = MagicMock()
        message.from_user.id = 123456789
        message.from_user.full_name = "Test Admin"
        message.answer = AsyncMock()
        return message
    
    @pytest.fixture
    def mock_state(self):
        """Создаём мок для FSMContext с данными"""
        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()
        state.get_data = AsyncMock(return_value={
            'text_category': 'messages',
            'text_key': 'test_key'
        })
        return state
    
    @pytest.mark.asyncio
    async def test_text_too_long(self, mock_message, mock_state):
        """Тест: слишком длинный текст отклоняется"""
        # Создаём текст длиннее 4096 символов
        mock_message.text = "a" * 5000
        
        with patch('utils.get_interface_texts', return_value={}):
            with patch('utils.save_interface_texts'):
                await save_text_value(mock_message, mock_state)
                
                # Проверяем, что была отправлена ошибка
                mock_message.answer.assert_called_once()
                args = mock_message.answer.call_args
                assert 'слишком длинный' in args[0][0].lower()
                
                # Проверяем, что состояние НЕ было очищено
                mock_state.clear.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_button_text_too_long(self, mock_message, mock_state):
        """Тест: слишком длинный текст кнопки отклоняется"""
        mock_message.text = "a" * 100  # Больше 64 символов
        mock_state.get_data = AsyncMock(return_value={
            'text_category': 'buttons',  # Категория кнопок
            'text_key': 'test_button'
        })
        
        with patch('utils.get_interface_texts', return_value={}):
            with patch('utils.save_interface_texts'):
                await save_text_value(mock_message, mock_state)
                
                mock_message.answer.assert_called_once()
                args = mock_message.answer.call_args
                assert 'кнопки слишком длинный' in args[0][0].lower()
                mock_state.clear.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_dangerous_html_tags(self, mock_message, mock_state):
        """Тест: опасные HTML теги отклоняются"""
        mock_message.text = "<script>alert('hack')</script>"
        
        with patch('utils.get_interface_texts', return_value={}):
            with patch('utils.save_interface_texts'):
                await save_text_value(mock_message, mock_state)
                
                mock_message.answer.assert_called_once()
                args = mock_message.answer.call_args
                assert 'недопустимые HTML теги' in args[0][0]
                mock_state.clear.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_valid_text_saved(self, mock_message, mock_state):
        """Тест: корректный текст сохраняется"""
        mock_message.text = "Новый текст для кнопки"
        
        with patch('utils.get_interface_texts', return_value={'messages': {}}):
            with patch('utils.save_interface_texts') as mock_save:
                # Мокаем файловые операции для аудита
                with patch('builtins.open', create=True):
                    with patch('json.load', return_value=[]):
                        with patch('json.dump'):
                            await save_text_value(mock_message, mock_state)
                            
                            # Проверяем, что save был вызван
                            mock_save.assert_called_once()
                            
                            # Проверяем, что состояние было очищено
                            mock_state.clear.assert_called_once()
                            
                            # Проверяем сообщение об успехе
                            mock_message.answer.assert_called_once()
                            args = mock_message.answer.call_args
                            assert 'успешно изменен' in args[0][0].lower()


class TestGetTextFallback:
    """Тесты для функции get_text и её fallback логики"""
    
    def test_get_text_from_json(self):
        """Тест: get_text читает из json/interface_texts.json"""
        from localization import get_text, _load_interface_texts
        
        # Мокаем загрузку JSON
        mock_texts = {
            'buttons': {
                'test': 'Тестовая кнопка'
            },
            'messages': {
                'welcome': 'Добро пожаловать!'
            }
        }
        
        with patch('localization._load_interface_texts', return_value=mock_texts):
            # Тест с точечной нотацией
            assert get_text('buttons.test') == 'Тестовая кнопка'
            assert get_text('messages.welcome') == 'Добро пожаловать!'
            
            # Тест с btn_ префиксом
            assert get_text('btn_test') == 'Тестовая кнопка'
    
    def test_get_text_fallback_to_default(self):
        """Тест: get_text возвращается к DEFAULT_TEXTS если нет в JSON"""
        from localization import get_text
        
        with patch('localization._load_interface_texts', return_value={}):
            # Должен вернуть из DEFAULT_TEXTS
            result = get_text('welcome')
            assert 'школу по нейросетям' in result  # Часть дефолтного текста
    
    def test_get_text_with_formatting(self):
        """Тест: get_text поддерживает форматирование"""
        from localization import get_text
        
        mock_texts = {
            'messages': {
                'test_format': 'Привет, {name}! У вас {count} уроков.'
            }
        }
        
        with patch('localization._load_interface_texts', return_value=mock_texts):
            result = get_text('messages.test_format', name='Иван', count=5)
            assert result == 'Привет, Иван! У вас 5 уроков.'


class TestBackButtonFix:
    """Тесты исправления кнопки "назад" в редактировании уроков"""
    
    def test_back_button_callback_data(self):
        """Тест: кнопка "назад" в списке редактирования имеет правильный callback_data"""
        from keyboards import markup_lesson_edit_list
        
        # Создаём тестовые уроки
        lessons = [
            {'id': 1, 'title': 'Урок 1', 'is_active': True, 'is_free': False, 'price_usd': 10}
        ]
        
        keyboard = markup_lesson_edit_list(lessons)
        
        # Находим кнопку "Назад"
        back_button = None
        for row in keyboard.inline_keyboard:
            for button in row:
                if 'Назад' in button.text:
                    back_button = button
                    break
        
        assert back_button is not None, "Кнопка 'Назад' не найдена"
        assert back_button.callback_data == 'lessons_mgmt', \
            f"Неправильный callback_data: {back_button.callback_data}"


if __name__ == '__main__':
    # Запуск тестов
    pytest.main([__file__, '-v'])
