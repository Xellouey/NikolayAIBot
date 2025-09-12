import asyncio
import logging
from aiogram import types
from unittest.mock import MagicMock, AsyncMock
from handlers.shop import show_catalog
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.DEBUG)

async def test_catalog():
    """Test catalog when no paid lessons available"""
    print("=== Тестирование каталога без платных уроков ===")
    
    # Create mock CallbackQuery
    call = MagicMock(spec=types.CallbackQuery)
    call.from_user = MagicMock()
    call.from_user.id = 123456
    call.from_user.language_code = 'ru'
    call.answer = AsyncMock()
    
    # Create mock message
    call.message = MagicMock()
    call.message.edit_text = AsyncMock()
    call.message.answer = AsyncMock()
    call.data = 'catalog'
    
    # Create state
    storage = MemoryStorage()
    state = FSMContext(bot=MagicMock(), storage=storage, key=storage.key_builder(user_id=123456, chat_id=123456))
    
    try:
        # Call the handler
        await show_catalog(call, state)
        print("✅ Каталог обработан без ошибок")
        
        # Check what was called
        if call.message.edit_text.called:
            args = call.message.edit_text.call_args
            print(f"📝 Текст сообщения: {args[0][0] if args and args[0] else 'No text'}")
            
    except Exception as e:
        print(f"❌ Ошибка при обработке каталога: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_catalog())
