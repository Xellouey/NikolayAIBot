import asyncio
import utils
import logging
import keyboards as kb
from decimal import Decimal
from aiogram import types, Router, F, Bot
from database import user, lesson
from database.lead_magnet import LeadMagnet
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states import FSMPurchase
from message_utils import send_msg
from error_handling import TelegramErrorHandler, validate_telegram_file_id


# Импортируем новые системы обработки ошибок
from errors import handle_errors, global_error_handler, ErrorContext
from message_manager import global_message_manager
from state_manager import safe_state_manager
from database_resilience import resilient_db_operation

# Добавляем импорт глобального bot из bot_instance
from bot_instance import bot
from localization import get_text


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
    
    # Получаем список купленных пользователем уроков
    @resilient_db_operation(operation_name="get_user_purchases", use_cache=True, cache_key=f"user_purchases_{call.from_user.id}")
    async def get_user_purchases():
        return await p.get_user_purchases(call.from_user.id)
    
    user_purchases = await get_user_purchases()
    purchased_lesson_ids = {purchase['lesson_id'] for purchase in user_purchases}
    
    # Фильтруем каталог:
    # 1. Исключаем автоматически созданные лид-магниты
    # 2. Исключаем уроки, которые пользователь уже купил
    catalog_lessons = []
    for lesson in lessons:
        # Исключаем автоматические лид-магниты
        is_auto_lead_magnet = (
            lesson.get('is_free', False) and 
            lesson.get('title', '').strip() == "Бесплатный вводный урок"
        )
        
        # Исключаем уроки, которые пользователь уже купил
        is_already_purchased = lesson['id'] in purchased_lesson_ids
        
        if not is_auto_lead_magnet and not is_already_purchased:
            catalog_lessons.append(lesson)
    
    # Логирование для отладки
    print(f"📚 CATALOG: Всего активных уроков: {len(lessons)}")
    print(f"📚 CATALOG: Покупок пользователя: {len(user_purchases)}")
    print(f"📚 CATALOG: Уроков в каталоге: {len(catalog_lessons)}")
    
    if not catalog_lessons:
        await global_message_manager.edit_message_safe(
            call.message,
            get_text('admin.no_lessons'),
            kb.markup_main_menu()          ) 
        return      
    text = get_text('catalog_title')    
    await global_message_manager.edit_message_safe(
        call.message,
        text,
        await kb.markup_catalog(catalog_lessons),
    )


@shop_router.callback_query(F.data == 'my_lessons')
@handle_errors(main_menu_markup=kb.markup_main_menu(), redirect_on_error=True)
async def show_my_lessons(call: types.CallbackQuery, state: FSMContext): 
    """Показать купленные уроки пользователя"""
    await call.answer()
    # Очищаем состояние
    await safe_state_manager.safe_clear_state(state, call.from_user.id)    
    
    # Get user language
    user_id = call.from_user.id
    user_data = await u.get_user(user_id)
    lang = user_data.get('lang', 'ru') if user_data else 'ru'
    
    # Prepare lessons list
    lessons = []
    
    # Add lead magnet if enabled
    if await LeadMagnet.is_ready():
        lead_label = await LeadMagnet.get_text_for_locale('lessons_label', lang)
        lessons.append({
            'id': 'lead_magnet',
            'title': lead_label or 'Приветственный вводный урок',
            'is_lead': True
        })
    
    # Get purchased lessons
    @resilient_db_operation(operation_name="get_user_purchases_count", use_cache=True, cache_key=f"user_profile_{call.from_user.id}")
    async def get_purchases():        
        return await p.get_user_purchases(call.from_user.id)    
    
    purchases = await get_purchases()
    
    # Add purchased lessons
    for purchase in purchases:
        lesson_obj = await l.get_lesson(purchase['lesson_id'])
        if lesson_obj:
            lesson_data = {
                'id': purchase['lesson_id'],
                'title': lesson_obj.title if hasattr(lesson_obj, 'title') else "Неизвестный урок",
                'is_lead': False
            }
        else:
            lesson_data = {
                'id': purchase['lesson_id'],
                'title': "Неизвестный урок",
                'is_lead': False
            }
        lessons.append(lesson_data)
    
    if not lessons:
        await global_message_manager.edit_message_safe(call.message,
            get_text('no_lessons'), 
            kb.markup_main_menu()
        ) 
        return

    text = get_text('my_lessons_title')    
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
    
    text = get_text('profile_info', full_name=call.from_user.full_name or "Не указано", lessons_count=lessons_count)
    print(f"text = {type(text)}")
    print(f"text = {text}")    
    
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
            get_text('error_occurred'), 
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
            get_text('error_occurred'), 
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
            if call.message is not None:
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
        
        # Определяем, бесплатный ли урок
        is_free_lesson = lesson_data.is_free or float(lesson_data.price_usd) == 0
        
        if is_free_lesson:
            # Бесплатный урок
            text = f"🎁 <b>{lesson_data.title}</b>\n\n🎆 <b>БЕСПЛАТНО!</b>\n\n📝 {lesson_data.description or ''}"
        else:
            # Платный урок
            text = get_text('messages.lesson_details',
                                title=lesson_data.title,
                                price_usd=f"{price_usd:.2f}",
                                price_stars=price_stars,
                                description=lesson_data.description or '')

        # Показываем превью если есть
        if lesson_data.preview_text:
            text += f"\n\n🎬 <b>Превью:</b>\n{lesson_data.preview_text}"

        await global_message_manager.edit_message_safe(
            call.message,
            text,
            kb.markup_lesson_details(lesson_id, user_has_lesson=False, is_free=is_free_lesson)
        )

        # Send preview video if available"   
        if lesson_data.preview_video_file_id:
            try:        
                await bot.send_video(
                    chat_id=call.from_user.id,
                    video=lesson_data.preview_video_file_id,
                    caption="🎬 Превью урока",
                    parse_mode='html'
                )        
            except Exception as e:
                print(f"❌ Ошибка отправки preview_video: {e}")     


@shop_router.callback_query(lambda F: F.data.startswith('view_lesson:'))
@handle_errors(main_menu_markup=kb.markup_main_menu(), redirect_on_error=True)
async def view_lesson_content(call: types.CallbackQuery, state: FSMContext):
    """Показать содержимое купленного урока"""
    await call.answer()
    
    # Базовое логирование
    print(f"VIEW_LESSON: User {call.from_user.id} accessing lesson {call.data}")
    
    try:
        # Проверяем формат callback_data
        if not call.data or ':' not in call.data:
            await global_message_manager.edit_message_safe(
                call.message,
                "❌ Ошибка: неверный формат данных",
                kb.markup_main_menu()
            )
            return
            
        lesson_id_str = call.data.split(':')[1]
        
        try:
            lesson_id = int(lesson_id_str)
        except ValueError:
            await global_message_manager.edit_message_safe(
                call.message,
                "❌ Ошибка: неверный ID урока",
                kb.markup_main_menu()
            )
            return
            
        # Получаем данные урока
        lesson_data = await l.get_lesson(lesson_id)
        
        if not lesson_data:
            await global_message_manager.edit_message_safe(
                call.message,
                f"❌ Урок с ID {lesson_id} не найден",
                kb.markup_main_menu()
            )
            return
            
        # Проверяем права доступа
        user_has_lesson = await p.check_user_has_lesson(call.from_user.id, lesson_id)
        
        if not user_has_lesson:
            await global_message_manager.edit_message_safe(
                call.message,
                "❌ У вас нет доступа к этому уроку",
                kb.markup_main_menu()
            )
            return
            
        # Увеличиваем счетчик просмотров
        await l.increment_views(lesson_id)
        
        # Показываем содержимое урока
        if lesson_data.content_type == 'video' and lesson_data.video_file_id:
            caption = f"📚 <b>{lesson_data.title}</b>\n\n{lesson_data.description or ''}"
            
            # Удаляем текущее сообщение
            if call.message:
                await global_message_manager.delete_message_safe(
                    call.message.chat.id, call.message.message_id
                )
                
            # Отправляем видео
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
                # Fallback на текстовое сообщение с улучшенным сообщением
                fallback_content = lesson_data.text_content or "🎥 Видео временно недоступно. Попробуйте позже."
                text = f"📚 <b>{lesson_data.title}</b>\n\n{lesson_data.description or ''}\n\n{fallback_content}"
                await global_message_manager.send_message_safe(
                    chat_id=call.from_user.id,
                    text=text,
                    reply_markup=kb.markup_main_menu()
                )
                
        else:
            # Текстовый урок или урок без видео
            # Улучшенная логика для текстовых уроков
            if lesson_data.content_type == 'text':
                # Для текстовых уроков приоритет: text_content, затем description как fallback
                if lesson_data.text_content:
                    content_text = lesson_data.text_content
                elif lesson_data.description:
                    content_text = f"📝 {lesson_data.description}"
                else:
                    content_text = "📝 В этом уроке пока нет содержимого"
            elif lesson_data.content_type == 'video' and not lesson_data.video_file_id:
                content_text = "🎥 В этом уроке пока нет видео"
            elif lesson_data.content_type not in ['text', 'video']:
                content_text = f"📋 Содержимое типа '{lesson_data.content_type}' пока не поддерживается"
            else:
                content_text = "📋 Содержимое урока временно недоступно"
            
            text = f"📚 <b>{lesson_data.title}</b>\n\n{content_text}"
            await global_message_manager.edit_message_safe(
                call.message,
                text,
                kb.markup_main_menu()
            )
        
    except Exception as e:
        print(f"❌ VIEW_LESSON: Ошибка при просмотре урока: {e}")
        
        try:
            await global_message_manager.edit_message_safe(
                call.message,
                f"❌ Произошла ошибка при загрузке урока",
                kb.markup_main_menu()
            )
        except Exception as e2:
            print(f"VIEW_LESSON: Error sending error message: {e2}")


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
                get_text('error_occurred'),
                kb.markup_main_menu()
            ) 
            return
        
        # Check if user already owns this lesson
        user_has_lesson = await p.check_user_has_lesson(call.from_user.id, lesson_id)
        
        if user_has_lesson:
            await global_message_manager.edit_message_safe(
                call.message,
                get_text('messages.lesson_already_owned'), 
                kb.markup_main_menu()
            )
            return
        
        # If it's a free lesson, automatically "purchase" it
        # Проверяем как по флагу is_free, так и по цене $0
        is_free_lesson = (hasattr(lesson_data, 'is_free') and lesson_data.is_free) or float(lesson_data.price_usd) == 0
        if is_free_lesson:
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
                    get_text('messages.lesson_purchased'), 
                    kb.markup_main_menu()
                )

            except Exception as e:
                logging.error(f"Error creating free purchase: {e}")                
                await global_message_manager.edit_message_safe(
                    call.message,
                    get_text('error_occurred'), 
                    kb.markup_main_menu()
                )
            return
    
        # For paid lessons - send invoice for Stars payment (без промокода)
        price_usd = float(lesson_data.price_usd)
        price_stars = await utils.calculate_stars_price(price_usd)
        
        await bot.send_invoice(
            chat_id=call.from_user.id,
            title=lesson_data.title,
            description=lesson_data.description or '',
            payload=str(lesson_id),
            provider_token='',  # Empty for Stars
            currency='XTR',
            prices=[types.LabeledPrice(label=lesson_data.title, amount=price_stars)],
            start_parameter='stars-payment'
        )

        # Update the message to show payment info
        text = f"💳 <b>Оплата урока</b>\n\n📚 {lesson_data.title}\n💰 Цена: {price_stars} ⭐ Stars\n\nНажмите кнопку оплаты ниже."
        await global_message_manager.edit_message_safe(
            call.message,
            text,
            kb.markup_lesson_details(lesson_id, user_has_lesson=False)
        )        
        
    except Exception as e:
        logging.error(f"Error in buy_lesson: {e}")        
        await global_message_manager.edit_message_safe(
            call.message,
            get_text('error_occurred'), kb.markup_main_menu()
        )    


@shop_router.callback_query(F.data.startswith('pay:'))
async def pay_with_optional_promocode(call: types.CallbackQuery, state: FSMContext):
    """Initiate payment with optional promocode applied"""
    await call.answer()
    try:
        parts = call.data.split(':')
        # Expected format: pay:{lesson_id}:{promocode or 'none'}
        if len(parts) < 3:
            await call.message.edit_text(get_text('error_occurred'), reply_markup=kb.markup_main_menu())
            return
        _, lesson_id_str, promo_code = parts[0], parts[1], ':'.join(parts[2:])  # allow colon in future
        lesson_id = int(lesson_id_str)
        promo_code = None if promo_code in (None, '', 'none', 'None') else promo_code.strip().upper()
        
        lesson_data = await l.get_lesson(lesson_id)
        if not lesson_data:
            await call.message.edit_text(get_text('error_occurred'), reply_markup=kb.markup_main_menu())
            return
        
        original_price = float(lesson_data.price_usd)
        final_price_usd = original_price
        
        if promo_code:
            # Re-validate promocode before payment
            promocode_data, error_msg = await promo.validate_promocode(promo_code)
            if not promocode_data:
                # Промокод недействителен — показываем без скидки
                await call.message.edit_text(get_text('promocode_invalid'), reply_markup=kb.markup_back_to_lesson(lesson_id))
                return
            final_price_usd, _ = await promo.calculate_discount(promocode_data, original_price)
        
        final_stars = await utils.calculate_stars_price(final_price_usd)
        
        # Send invoice with payload including promocode (if any)
        payload = f"{lesson_id}|{promo_code}" if promo_code else str(lesson_id)
        await bot.send_invoice(
            chat_id=call.from_user.id,
            title=lesson_data.title,
            description=lesson_data.description or '',
            payload=payload,
            provider_token='',  # Empty for Stars
            currency='XTR',
            prices=[types.LabeledPrice(label=lesson_data.title, amount=final_stars)],
            start_parameter='stars-payment'
        )
        
        text = f"💳 <b>Оплата урока</b>\n\n📚 {lesson_data.title}\n💰 Цена: {final_stars} ⭐ Stars\n\nНажмите кнопку оплаты ниже."
        await call.message.edit_text(text, reply_markup=kb.markup_lesson_details(lesson_id, user_has_lesson=False))
    except Exception as e:
        logging.error(f"Error in pay_with_optional_promocode: {e}")
        await call.message.edit_text(get_text('error_occurred'), reply_markup=kb.markup_main_menu())


@shop_router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery, state: FSMContext): 
    """Process pre-checkout query for Stars payment"""
    await pre_checkout_q.answer(ok=True)


@shop_router.message(F.successful_payment)
async def process_successful_payment(message: types.Message, state: FSMContext): 
    """Process successful Stars payment"""
    try:
        # Поддерживаем payload как просто lesson_id или lesson_id|PROMOCODE
        payload = message.successful_payment.invoice_payload or ""
        promo_code_used = None
        try:
            if '|' in payload:
                lesson_id_str, promo_code_used = payload.split('|', 1)
                lesson_id = int(lesson_id_str)
                promo_code_used = (promo_code_used or '').strip() or None
            else:
                lesson_id = int(payload)
        except Exception:
            # Нестандартный payload — пытаемся извлечь хотя бы lesson_id из total_amount контекста
            lesson_id = int(payload) if payload.isdigit() else None
        
        price_stars = message.successful_payment.total_amount
        price_usd = price_stars / await s.get_usd_to_stars_rate()  # Reverse calculate USD
        
        if lesson_id is None:
            await message.answer(get_text('error_occurred'), reply_markup=kb.markup_main_menu())
            return
        
        user_has_lesson = await p.check_user_has_lesson(message.from_user.id, lesson_id)
        
        if not user_has_lesson:
            await p.create_purchase(
                user_id=message.from_user.id,
                lesson_id=lesson_id,
                price_paid_usd=price_usd,
                price_paid_stars=price_stars,
                payment_id=message.successful_payment.provider_payment_charge_id,
                promocode_used=promo_code_used
            )
            
            # Увеличиваем usage_count у промокода, если применялся
            if promo_code_used:
                try:
                    await promo.use_promocode(promo_code_used)
                except Exception as e:
                    logging.error(f"Failed to increment promocode usage for {promo_code_used}: {e}")
            
            await l.increment_purchases(lesson_id)
            
            await message.answer(
                "✅ <b>Оплата прошла успешно!</b>\n\nУрок добавлен в ваши покупки.\nТеперь он доступен в разделе «Мои уроки».",
                reply_markup=kb.markup_main_menu(),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                "ℹ️ Урок уже у вас есть!",
                reply_markup=kb.markup_main_menu()
            )
    except Exception as e:
        logging.error(f"Error in process_successful_payment: {e}")        
        await message.answer(
                get_text('error_occurred'),
                reply_markup=kb.markup_main_menu()            )  


@shop_router.callback_query(F.data.startswith('promocode:'))
async def enter_promocode(call: types.CallbackQuery, state: FSMContext): 
    """Enter promocode for lesson"""
    await call.answer()

    try: 
        lesson_id = int(call.data.split(':')[1])
        await state.update_data(lesson_id=lesson_id)
        await state.set_state(FSMPurchase.promocode)
        # ВАЖНО: ReplyKeyboardMarkup нельзя передать в edit_text — отправляем новое сообщение
        await call.message.answer(
            get_text('enter_promocode'),
            reply_markup=kb.markup_cancel()
        )
    except Exception as e:
        logging.error(f"Error in enter_promocode: {e}")
        await call.message.edit_text(
            get_text('error_occurred'),
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
                get_text('error_occurred'),
                reply_markup=kb.markup_main_menu()
            )
            return
        
        promocode_text = message.text.strip().upper()        
        # Validate promocode
        promocode_data, error_msg = await promo.validate_promocode(promocode_text)
        
        if not promocode_data:
            await message.answer(
                get_text('promocode_invalid'), 
                reply_markup=kb.markup_cancel()            )
            return        
        
        # Get lesson data
        lesson_data = await l.get_lesson(lesson_id)        
        
        if not lesson_data:
            await state.clear()
            await message.answer(
                get_text('error_occurred'), 
                reply_markup=kb.markup_main_menu()
            )
            return        
        
        original_price = float(lesson_data.price_usd)
        
        # Calculate discount using the calculate_discount method from Promocode model
        final_price, discount_amount = await promo.calculate_discount(promocode_data, original_price)
        
        final_stars = await utils.calculate_stars_price(final_price)
        
        # Show applied promocode and offer to pay with discount
        text = get_text(
            'promocode_applied',
            discount=f"{discount_amount:.2f}",
            final_price=f"{final_price:.2f}",
            final_stars=final_stars
        )
        
        # Очистим состояние и спрячем реплай-клавиатуру "Отмена"
        await state.clear()
        try:
            await message.answer(" ", reply_markup=kb.markup_remove())
        except Exception:
            pass
        
        # Показываем подтверждение оплаты с промокодом
        await message.answer(
            text,
            reply_markup=kb.markup_payment_confirm(lesson_id, final_price, final_stars, promocode=promocode_text)
        )
        
    except Exception as e: 
        logging.error(f"Error in process_promocode: {e}")
        await state.clear()
        await message.answer(
            get_text('error_occurred'), 
            reply_markup=kb.markup_main_menu()
        )                


@shop_router.callback_query(F.data == 'lead_magnet:play')
async def play_lead_magnet(call: types.CallbackQuery, state: FSMContext): 
    """Play lead magnet video again"""
    await call.answer()
    
    try:
        # Get lead magnet configuration
        lead_magnet = await LeadMagnet.get_lead_magnet()
        if not lead_magnet or not lead_magnet.video_file_id:
            await call.answer("❌ Видео недоступно")
            return
        
        # Get user language
        user_id = call.from_user.id
        user_data = await u.get_user(user_id)
        lang = user_data.get('lang', 'ru') if user_data else 'ru'
        
        # Get greeting text for user's locale
        greeting_text = await LeadMagnet.get_text_for_locale('greeting_text', lang)
        
        # Send video with greeting caption
        await bot.send_video(
            chat_id=user_id,
            video=lead_magnet.video_file_id,
            caption=f"🎬 {greeting_text}",
            parse_mode='HTML'
        )
        
        # Send back to my lessons
        await call.message.edit_text(
            get_text('my_lessons_title'),
            reply_markup=kb.markup_my_lessons(await get_user_lessons_for_markup(user_id))
        )
        
    except Exception as e:
        logging.error(f"Error playing lead magnet: {e}")
        await call.answer("❌ Ошибка воспроизведения")


async def get_user_lessons_for_markup(user_id):
    """Helper to get user lessons for markup"""
    lessons = []
    
    # Get user language
    user_data = await u.get_user(user_id)
    lang = user_data.get('lang', 'ru') if user_data else 'ru'
    
    # Add lead magnet if enabled
    if await LeadMagnet.is_ready():
        lead_label = await LeadMagnet.get_text_for_locale('lessons_label', lang)
        lessons.append({
            'id': 'lead_magnet',
            'title': lead_label or 'Приветственный вводный урок',
            'is_lead': True
        })
    
    # Get purchased lessons
    purchases = await p.get_user_purchases(user_id)
    for purchase in purchases:
        lesson_obj = await l.get_lesson(purchase['lesson_id'])
        if lesson_obj:
            lessons.append({
                'id': purchase['lesson_id'],
                'title': lesson_obj.title if hasattr(lesson_obj, 'title') else "Неизвестный урок",
                'is_lead': False
            })
    
    return lessons


@shop_router.callback_query(F.data == 'back_main')
async def back_to_main(call: types.CallbackQuery, state: FSMContext): 
    """Ретурн to main menu"""
    await call.answer()
    await state.clear()  # Clear any active states
    
    try:
        text = get_text('welcome')
        await call.message.edit_text(
            text,
            reply_markup=kb.markup_main_menu()
        )
    except Exception as e:
        logging.error(f"Error in back_to_main: {e}")          
        await call.message.edit_text(
            get_text('welcome'),
            reply_markup=kb.markup_main_menu()
        )
