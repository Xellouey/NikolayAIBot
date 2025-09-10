import logging
import keyboards as kb
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states import FSMMail

router = Router()

@router.message(F.text == "❌ Отмена")
async def universal_cancel(message: types.Message, state: FSMContext):
    """Универсальный обработчик кнопки отмены"""
    current_state = await state.get_state()
    
    logging.info(f"Кнопка отмены нажата. Состояние: {current_state}, пользователь: {message.from_user.id}")
    
    # Если есть активное состояние FSMMail
    if current_state and "FSMMail" in current_state:
        logging.info("Отменяем рассылку")
        await state.clear()
        await message.answer("❌ Рассылка отменена", reply_markup=kb.markup_remove())
        
        # Импортируем admin здесь, чтобы избежать циклической зависимости
        from handlers.admin import admin
        await admin(message, state)
        logging.info("Возврат в админ-меню")
        return
    
    # Для других состояний
    if current_state:
        logging.info(f"Очищаем состояние {current_state}")
        await state.clear()
        await message.answer("❌ Операция отменена", reply_markup=kb.markup_remove())
        
        # Проверяем, является ли пользователь админом
        import config
        import utils
        data_admins = utils.get_admins()
        
        if message.from_user.id in config.ADMINS or message.from_user.id in data_admins:
            from handlers.admin import admin
            await admin(message, state)
        return
    
    # Если нет состояния
    logging.debug("Нет активного состояния для отмены")
    await message.answer("Нечего отменять", reply_markup=kb.markup_remove())
