import asyncio
import utils
import logging
import keyboards as kb
from decimal import Decimal
from aiogram import types, Router, F, Bot
from database import user, lesson
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states import FSMPurchase
from .client import send_msg
from error_handling import TelegramErrorHandler, validate_telegram_file_id

# Импортируем новые системы обработки ошибок
from errors import handle_errors, global_error_handler, ErrorContext
from message_manager import global_message_manager
from state_manager import safe_state_manager
from database_resilience import resilient_db_operation

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s"
)

u = user.User()
l = lesson.Lesson()
p = lesson.Purchase()
s = lesson.SystemSettings()
promo = lesson.Promocode()

shop_router = Router()


@shop_router.callback_query(F.data == 'catalog')
@handle_errors(main_menu_markup=kb.markup_main_menu(), redirect_on_error=True)
async def show_catalog(call: types.CallbackQuery, state: FSMContext):
    """Показать каталог уроков"""
    await call.answer()
    
    # Очищаем состояние при возврате к каталогу
    await safe_state_manager.safe_clear_state(state, call.from_user.id)
    
    @resilient_db_operation(operation_name="get_catalog_lessons", use_cache=True, cache_key="active_lessons")
    async def get_lessons():
        return await l.get_all_lessons(active_only=True)
    
    lessons = await get_lessons()
    
    if not lessons:
        await global_message_manager.edit_message_safe(
            call.message,
            utils.get_text('admin.messages.no_lessons'),
            kb.markup_main_menu()
        )
        return
    
    text = utils.get_text('messages.catalog_title')
    await global_message_manager.edit_message_safe(
        call.message,
        text,
        kb.markup_catalog(lessons)
    )


@shop_router.callback_query(F.data == 'my_lessons')
@handle_errors(main_menu_markup=kb.markup_main_menu(), redirect_on_error=True)
async def show_my_lessons(call: types.CallbackQuery, state: FSMContext):
    """Показать купленные уроки пользователя"""
    await call.answer()
    
    # Очищаем состояние
    await safe_state_manager.safe_clear_state(state, call.from_user.id)
    
    @resilient_db_operation(operation_name="get_user_purchases", use_cache=True, cache_key=f"user_purchases_{call.from_user.id}")
    async def get_purchases():
        return await p.get_user_purchases(call.from_user.id)
    
    purchases = await get_purchases()
    
    if not purchases:
        await global_message_manager.edit_message_safe(
            call.message,
            utils.get_text('messages.no_lessons'),
            kb.markup_main_menu()
        )
        return
    
    # Извлекаем информацию о уроках из покупок
    lessons = []
    for purchase in purchases:
        lesson_data = {
            'id': purchase['lesson_id'],
            'title': purchase['title']
        }
        lessons.append(lesson_data)
    
    text = utils.get_text('messages.my_lessons_title')
    await global_message_manager.edit_message_safe(
        call.message,
        text,
        kb.markup_my_lessons(lessons)
    )


@shop_router.callback_query(F.data == 'profile')
@handle_errors(main_menu_markup=kb.markup_main_menu(), redirect_on_error=True)
async def show_profile(call: types.CallbackQuery, state: FSMContext):
    """Показать профиль пользователя"""
    await call.answer()
    
    # Очищаем состояние
    await safe_state_manager.safe_clear_state(state, call.from_user.id)
    
    @resilient_db_operation(operation_name="get_user_purchases_count", use_cache=True, cache_key=f"user_profile_{call.from_user.id}")
    async def get_purchases_count():
        purchases = await p.get_user_purchases(call.from_user.id)
        return len(purchases)
    
    lessons_count = await get_purchases_count()
    
    text = utils.get_text('messages.profile_info',
                        full_name=call.from_user.full_name or "Не указано",
                        lessons_count=lessons_count)
    
    await global_message_manager.edit_message_safe(
        call.message,
        text,
        kb.markup_main_menu()
    )


@shop_router.callback_query(lambda F: F.data.startswith('lesson:'))
@handle_errors(main_menu_markup=kb.markup_main_menu(), redirect_on_error=True)
async def show_lesson_details(call: types.CallbackQuery, state: FSMContext):
    """Показать детали урока"""
    await call.answer()
    
    # Очищаем состояние
    await safe_state_manager.safe_clear_state(state, call.from_user.id)
    
    # Проверяем формат callback_data
    if not call.data or ':' not in call.data:
        print(f"❌ Неправильный формат callback_data: {call.data}")
        await global_message_manager.edit_message_safe(
            call.message,
            utils.get_text('messages.error_occurred'),
            kb.markup_main_menu()
        )
        return
        
    lesson_id_str = call.data.split(':')[1]
    
    # Проверяем что lesson_id - это число
    try:
        lesson_id = int(lesson_id_str)
    except ValueError:
        print(f"❌ Неправильный ID урока: {lesson_id_str}")
        await global_message_manager.edit_message_safe(
            call.message,
            utils.get_text('messages.error_occurred'),
            kb.markup_main_menu()
        )
        return
    
    print(f"📚 Получаем данные урока ID: {lesson_id}")
    
    @resilient_db_operation(operation_name="get_lesson_details", use_cache=True, cache_key=f"lesson_{lesson_id}")
    async def get_lesson():
        return await l.get_lesson(lesson_id)
    
    lesson_data = await get_lesson()
    
    if not lesson_data:
        print(f"❌ Урок с ID {lesson_id} не найден")
        await global_message_manager.edit_message_safe(
            call.message,
            "❌ Урок не найден",
            kb.markup_main_menu()
        )
        return
    
    print(f"✅ Урок найден: {lesson_data.title}")
    
    # Увеличиваем счетчик просмотров
    @resilient_db_operation(operation_name="increment_lesson_views")
    async def increment_views():
        return await l.increment_views(lesson_id)
    
    await increment_views()
    
    # Проверяем владение уроком
    @resilient_db_operation(operation_name="check_lesson_ownership")
    async def check_ownership():
        return await p.check_user_has_lesson(call.from_user.id, lesson_id)
    
    user_has_lesson = await check_ownership()
    
    # Рассчитываем цену в звездах
    price_usd = float(lesson_data.price_usd)
    price_stars = await utils.calculate_stars_price(price_usd)
    
    # Показываем детали урока
    if user_has_lesson:
        # Пользователь владеет уроком - показываем контент
        print(f"📚 Пользователь владеет уроком {lesson_id}")
        
        if lesson_data.content_type == 'video' and lesson_data.video_file_id:
            caption = f"📚 <b>{lesson_data.title}</b>\n\n{lesson_data.description or ''}"
            
            # Удаляем сообщение и отправляем видео
            if call.message:
                delete_success = await global_message_manager.delete_message_safe(
                    call.message.chat.id, call.message.message_id
                )
            
            # Отправляем видео с fallback на текст
            video_message = await global_message_manager.send_media_safe(
                chat_id=call.from_user.id,
                media_type='video',
                file_id=lesson_data.video_file_id,
                caption=caption
            )
            
            if video_message:
                # Отправляем кнопку назад
                await global_message_manager.send_message_safe(
                    chat_id=call.from_user.id,
                    text="👆 Урок выше",
                    reply_markup=kb.markup_main_menu()
                )
            else:
                # Fallback на текстовое сообщение
                text = f"📚 <b>{lesson_data.title}</b>\n\n{lesson_data.description or ''}\n\n{lesson_data.text_content or ''}"
                await global_message_manager.send_message_safe(
                    chat_id=call.from_user.id,
                    text=text,
                    reply_markup=kb.markup_main_menu()
                )
        else:
            # Текстовый урок
            text = f"📚 <b>{lesson_data.title}</b>\n\n{lesson_data.description or ''}\n\n{lesson_data.text_content or ''}"
            await global_message_manager.edit_message_safe(
                call.message,
                text,
                kb.markup_main_menu()
            )
    else:
        # Пользователь не владеет уроком - показываем детали и возможность покупки
        print(f"📋 Пользователь не владеет уроком {lesson_id}")
        text = utils.get_text('messages.lesson_details',
                            title=lesson_data.title,
                            price_usd=f"{price_usd:.2f}",
                            price_stars=price_stars,
                            description=lesson_data.description or "")
        
        # Показываем превью если есть
        if lesson_data.preview_text:
            text += f"\n\n🎬 <b>Превью:</b>\n{lesson_data.preview_text}"
        
        await global_message_manager.edit_message_safe(
            call.message,
            text,
            kb.markup_lesson_details(lesson_id, user_has_lesson=False)
        )


@shop_router.callback_query(lambda F: F.data.startswith('view_lesson:'))
@handle_errors(main_menu_markup=kb.markup_main_menu(), redirect_on_error=True)
async def view_owned_lesson(call: types.CallbackQuery, state: FSMContext):
    """Просмотр урока из моих уроков"""
    await call.answer()
    
    # Очищаем состояние
    await safe_state_manager.safe_clear_state(state, call.from_user.id)
    
    lesson_id = int(call.data.split(':')[1])
    
    # Проверяем владение уроком
    @resilient_db_operation(operation_name="check_lesson_ownership_view")
    async def check_ownership():
        return await p.check_user_has_lesson(call.from_user.id, lesson_id)
    
    user_has_lesson = await check_ownership()
    
    if not user_has_lesson:
        await global_message_manager.edit_message_safe(
            call.message,
            utils.get_text('messages.access_denied'),
            kb.markup_main_menu()
        )
        return
        
    @resilient_db_operation(operation_name="get_owned_lesson_data", use_cache=True, cache_key=f"lesson_{lesson_id}")
    async def get_lesson_data():
        return await l.get_lesson(lesson_id)
    
    lesson_data = await get_lesson_data()
    
    if not lesson_data:
        await global_message_manager.edit_message_safe(
            call.message,
            utils.get_text('messages.error_occurred'),
            kb.markup_main_menu()
        )
        return
    
    # Показываем контент урока поскольку пользователь владеет им
    if lesson_data.content_type == 'video' and lesson_data.video_file_id:
        caption = f"📚 <b>{lesson_data.title}</b>\n\n{lesson_data.description or ''}"
        
        # Удаляем сообщение и отправляем видео
        await global_message_manager.delete_message_safe(
            call.message.chat.id, call.message.message_id
        )
        
        video_message = await global_message_manager.send_media_safe(
            chat_id=call.from_user.id,
            media_type='video',
            file_id=lesson_data.video_file_id,
            caption=caption
        )
        
        if video_message:
            # Отправляем кнопку назад
            await global_message_manager.send_message_safe(
                chat_id=call.from_user.id,
                text="👆 Ваш урок выше",
                reply_markup=kb.markup_main_menu()
            )
        else:
            # Fallback на текст
            text = f"📚 <b>{lesson_data.title}</b>\n\n{lesson_data.description or ''}\n\n{lesson_data.text_content or ''}"
            await global_message_manager.send_message_safe(
                chat_id=call.from_user.id,
                text=text,
                reply_markup=kb.markup_main_menu()
            )
    else:
        # Текстовый урок
        text = f"📚 <b>{lesson_data.title}</b>\n\n{lesson_data.description or ''}\n\n{lesson_data.text_content or ''}"
        await global_message_manager.edit_message_safe(
            call.message,
            text,
            kb.markup_main_menu()
        )


@shop_router.callback_query(lambda F: F.data.startswith('buy:'))
@handle_errors(main_menu_markup=kb.markup_main_menu(), redirect_on_error=True)
async def buy_lesson(call: types.CallbackQuery, state: FSMContext):
    """Start lesson purchase process"""
    await call.answer()
    
    try:
        lesson_id = int(call.data.split(':')[1])
        lesson_data = await l.get_lesson(lesson_id)
        
        if not lesson_data:
            await global_message_manager.edit_message_safe(
                call.message,
                utils.get_text('messages.error_occurred'),
                kb.markup_main_menu()
            )
            return
        
        # Check if user already owns this lesson
        user_has_lesson = await p.check_user_has_lesson(call.from_user.id, lesson_id)
        
        if user_has_lesson:
            await global_message_manager.edit_message_safe(
                call.message,
                utils.get_text('messages.lesson_already_owned'),
                kb.markup_main_menu()
            )
            return
        
        # If it's a free lesson, automatically "purchase" it
        if lesson_data.is_free:
            try:
                await p.create_purchase(
                    user_id=call.from_user.id,
                    lesson_id=lesson_id,
                    price_paid_usd=0,
                    price_paid_stars=0,
                    payment_id="free_lesson"
                )
                
                await l.increment_purchases(lesson_id)
                
                await global_message_manager.edit_message_safe(
                    call.message,
                    utils.get_text('messages.lesson_purchased'),
                    kb.markup_main_menu()
                )
                
            except Exception as e:
                logging.error(f"Error creating free purchase: {e}")
                await global_message_manager.edit_message_safe(
                    call.message,
                    utils.get_text('messages.error_occurred'),
                    kb.markup_main_menu()
                )
            return
        
        # For paid lessons - show purchase confirmation with current timestamp to make it unique
        price_usd = float(lesson_data.price_usd)
        price_stars = await utils.calculate_stars_price(price_usd)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        text = f"📋 <b>Подтверждение покупки</b> ({timestamp})\n\n📚 {lesson_data.title}\n💰 Цена: ${price_usd:.2f} ({price_stars} ⭐)\n\n🚧 Платежи через Telegram Stars временно недоступны.\n\n💬 Обратитесь в поддержку для покупки урока."
        
        await global_message_manager.edit_message_safe(
            call.message,
            text,
            kb.markup_lesson_details(lesson_id, user_has_lesson=False)
        )
        
    except Exception as e:
        logging.error(f"Error in buy_lesson: {e}")
        await global_message_manager.edit_message_safe(
            call.message,
            utils.get_text('messages.error_occurred'),
            kb.markup_main_menu()
        )


@shop_router.callback_query(lambda F: F.data.startswith('promocode:'))
async def enter_promocode(call: types.CallbackQuery, state: FSMContext):
    """Enter promocode for lesson"""
    await call.answer()
    
    try:
        lesson_id = int(call.data.split(':')[1])
        
        await state.update_data(lesson_id=lesson_id)
        await state.set_state(FSMPurchase.promocode)
        
        await call.message.edit_text(
            utils.get_text('messages.enter_promocode'),
            reply_markup=kb.markup_cancel()
        )
        
    except Exception as e:
        logging.error(f"Error in enter_promocode: {e}")
        await call.message.edit_text(
            utils.get_text('messages.error_occurred'),
            reply_markup=kb.markup_main_menu()
        )


@shop_router.message(FSMPurchase.promocode)
async def process_promocode(message: types.Message, state: FSMContext):
    """Process entered promocode"""
    try:
        state_data = await state.get_data()
        lesson_id = state_data.get('lesson_id')
        
        if not lesson_id:
            await state.clear()
            await message.answer(
                utils.get_text('messages.error_occurred'),
                reply_markup=kb.markup_main_menu()
            )
            return
        
        promocode_text = message.text.strip().upper()
        
        # Validate promocode
        promocode_data, error_msg = await promo.validate_promocode(promocode_text)
        
        if not promocode_data:
            await message.answer(
                utils.get_text('messages.promocode_invalid'),
                reply_markup=kb.markup_cancel()
            )
            return
        
        # Get lesson data
        lesson_data = await l.get_lesson(lesson_id)
        
        if not lesson_data:
            await state.clear()
            await message.answer(
                utils.get_text('messages.error_occurred'),
                reply_markup=kb.markup_main_menu()
            )
            return
        
        # Calculate discount
        original_price = float(lesson_data.price_usd)
        discount_amount = 0
        
        if promocode_data.discount_amount_usd:
            discount_amount = float(promocode_data.discount_amount_usd)
        elif promocode_data.discount_percent:
            discount_amount = original_price * (promocode_data.discount_percent / 100)
        
        final_price = max(0, original_price - discount_amount)
        final_stars = await utils.calculate_stars_price(final_price)
        
        # Show applied promocode
        text = utils.get_text('messages.promocode_applied',
                             discount=f"{discount_amount:.2f}",
                             final_price=f"{final_price:.2f}",
                             final_stars=final_stars)
        
        await state.clear()
        await message.answer(
            text,
            reply_markup=kb.markup_lesson_details(lesson_id, user_has_lesson=False)
        )
        
    except Exception as e:
        logging.error(f"Error in process_promocode: {e}")
        await state.clear()
        await message.answer(
            utils.get_text('messages.error_occurred'),
            reply_markup=kb.markup_main_menu()
        )


@shop_router.callback_query(F.data == 'back_main')
async def back_to_main(call: types.CallbackQuery, state: FSMContext):
    """Return to main menu"""
    await call.answer()
    await state.clear()  # Clear any active states
    
    try:
        text = utils.get_text('messages.welcome')
        await call.message.edit_text(
            text,
            reply_markup=kb.markup_main_menu()
        )
    except Exception as e:
        logging.error(f"Error in back_to_main: {e}")
        await call.message.edit_text(
            utils.get_text('messages.welcome'),
            reply_markup=kb.markup_main_menu()
        )


# Shop start handler removed - onboarding handled by client.router
# Users access shop via main menu after completing onboarding