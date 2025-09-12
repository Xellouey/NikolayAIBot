import config
import logging
import utils
from localization import get_text
import keyboards as kb
from datetime import datetime
from aiogram import Bot, types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from states import FSMSupport
from database.support import SupportTicket, TicketMessage
from database.user import User

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s - %(message)s",
)

bot = Bot(config.TOKEN)
router = Router()

# Initialize database models
support_ticket = SupportTicket()
ticket_message = TicketMessage()
user_model = User()


# ===== USER SUPPORT HANDLERS =====

@router.callback_query(F.data == 'cancel_support')
async def cancel_support_inline(call: types.CallbackQuery, state: FSMContext):
    """Cancel support operation via inline button"""
    current_state = await state.get_state()
    
    # Clear state if exists
    if current_state:
        await state.clear()
    
    await call.answer("❌ Отменено")
    
    # Check if user is admin
    is_admin = call.from_user.id in config.ADMINS or call.from_user.id in utils.get_admins()
    
    # Determine if we're in admin responding state
    is_admin_responding = current_state and 'admin_responding' in str(current_state)
    
    if is_admin and is_admin_responding:
        # Admin was responding to ticket, show admin support dashboard
        text, markup = await build_admin_support_dashboard()
        await call.message.edit_text(text, reply_markup=markup)
    else:
        # Regular user or admin in user context - show main menu
        await call.message.edit_text(
            get_text('welcome'),
            reply_markup=kb.markup_main_menu()
        )


@router.callback_query(F.data == 'support')
async def support_menu(call: types.CallbackQuery, state: FSMContext):
    """Show support menu"""
    await state.clear()
    await call.answer()
    
    await call.message.edit_text(
        get_text('support_welcome'),
        reply_markup=kb.markup_support_menu()
    )


@router.callback_query(F.data == 'create_ticket')
async def create_ticket_start(call: types.CallbackQuery, state: FSMContext):
    """Start ticket creation process"""
    await state.set_state(FSMSupport.waiting_subject)
    await call.answer()
    
    # Create inline cancel button
    cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_support")]
    ])
    
    await call.message.edit_text(
        get_text('ticket_subject_prompt'),
        reply_markup=cancel_keyboard
    )


@router.message(FSMSupport.waiting_subject)
async def process_ticket_subject(message: types.Message, state: FSMContext):
    """Process ticket subject"""
    if not message.text or len(message.text.strip()) < 3:
        await message.answer(
            "❌ Тема должна содержать минимум 3 символа. Попробуйте еще раз:",
            reply_markup=kb.markup_cancel()
        )
        return
    
    subject = message.text.strip()[:200]  # Limit subject length
    await state.update_data(subject=subject)
    await state.set_state(FSMSupport.waiting_description)
    
    await message.answer(
        get_text('ticket_description_prompt'),
        reply_markup=kb.markup_cancel()
    )


@router.message(FSMSupport.waiting_description)
async def process_ticket_description(message: types.Message, state: FSMContext):
    """Process ticket description and create ticket"""
    if message.content_type not in ['text', 'photo', 'video', 'document']:
        await message.answer(
            "❌ Отправьте текст, фото, видео или документ:",
            reply_markup=kb.markup_cancel()
        )
        return
    
    try:
        state_data = await state.get_data()
        subject = state_data['subject']
        
        # Prepare description and media data
        description = ""
        message_type = message.content_type
        file_id = None
        
        if message.content_type == 'text':
            description = message.text.strip()[:4000]  # Limit description length
        elif message.content_type == 'photo':
            description = message.caption or "Прикреплено изображение"
            file_id = message.photo[-1].file_id
        elif message.content_type == 'video':
            description = message.caption or "Прикреплено видео"
            file_id = message.video.file_id
        elif message.content_type == 'document':
            description = message.caption or f"Прикреплен документ: {message.document.file_name}"
            file_id = message.document.file_id
        
        if not description or len(description.strip()) < 5:
            await message.answer(
                "❌ Описание должно содержать минимум 5 символов. Попробуйте еще раз:",
                reply_markup=kb.markup_cancel()
            )
            return
        
        # Create ticket
        ticket = await support_ticket.create_ticket(
            user_id=message.from_user.id,
            subject=subject,
            description=description
        )
        
        # Create initial message with description
        await ticket_message.create_message(
            ticket_id=ticket.id,
            sender_id=message.from_user.id,
            sender_type='user',
            message_text=description,
            message_type=message_type,
            file_id=file_id
        )
        
        await state.clear()
        
        # Send confirmation to user
        await message.answer(
            get_text('ticket_created', 
                          ticket_id=ticket.id, 
                          subject=subject),
            reply_markup=kb.markup_remove()
        )
        
        # Send notification to admins (не критично для пользователя)
        try:
            await notify_admins_new_ticket(ticket, message.from_user)
        except Exception as notify_err:
            logging.exception(f"Notify admins failed: {notify_err}")
        
        # Show support menu (не критично)
        try:
            await message.answer(
                get_text('support_welcome'),
                reply_markup=kb.markup_support_menu()
            )
        except Exception as menu_err:
            logging.exception(f"Show support menu failed: {menu_err}")
        
    except Exception as e:
        logging.exception(f"Error creating ticket: {e}")
        await state.clear()
        await message.answer(
            get_text('error_occurred'),
            reply_markup=kb.markup_support_menu()
        )


@router.callback_query(F.data == 'my_tickets')
async def show_user_tickets(call: types.CallbackQuery, state: FSMContext):
    """Show user's tickets"""
    await call.answer()
    
    try:
        tickets = await support_ticket.get_user_tickets(call.from_user.id)
        
        if not tickets:
            try:
                await call.message.edit_text(
                    get_text('no_tickets'),
                    reply_markup=kb.markup_support_menu()
                )
            except TelegramBadRequest as e:
                if 'message is not modified' in str(e).lower():
                    await call.answer("✅ Уже показано сообщение о том, что тикетов нет")
                    return
                raise
            return
        
        text = f"📋 <b>Ваши тикеты</b> ({len(tickets)})\n\nВыберите тикет для просмотра:"
        try:
            await call.message.edit_text(
                text,
                reply_markup=kb.markup_user_tickets(tickets)
            )
        except TelegramBadRequest as e:
            if 'message is not modified' in str(e).lower():
                await call.answer("✅ Уже показан список ваших тикетов")
                return
            raise
        
    except Exception as e:
        logging.exception(f"Error in show_user_tickets: {e}")
        try:
            await call.message.edit_text(
                get_text('error_occurred'),
                reply_markup=kb.markup_support_menu()
            )
        except TelegramBadRequest:
            # Если даже сообщение об ошибке не изменяет текст
            await call.answer("❌ Ошибка отображения. Попробуйте позже.")


@router.callback_query(F.data.startswith('view_ticket:'))
async def view_ticket_details(call: types.CallbackQuery, state: FSMContext):
    """View ticket details"""
    await call.answer()
    
    try:
        ticket_id = int(call.data.split(':')[1])
        ticket = await support_ticket.get_ticket(ticket_id)
        
        # Разрешаем доступ владельцу или админу; сравнение по int на всякий случай
        is_admin = call.from_user.id in config.ADMINS or call.from_user.id in utils.get_admins()
        if not ticket or (not is_admin and int(ticket.user_id) != int(call.from_user.id)):
            await call.message.edit_text(
                "❌ Тикет не найден или доступ запрещен.",
                reply_markup=kb.markup_support_menu()
            )
            return
        
        # Get status text
        status_text = {
            'open': get_text('ticket_status_open'),
            'in_progress': get_text('ticket_status_in_progress'),
            'closed': get_text('ticket_status_closed')
        }.get(ticket.status, ticket.status)
        
        # Determine if admin has responded at least once
        msgs = await ticket_message.get_ticket_messages(ticket_id)
        admin_replied = any(m.get('sender_type') == 'admin' for m in msgs)
        reply_status = '✅ Есть ответ администратора' if admin_replied else '⌛ Ответа администратора пока нет'
        
        # Format created_at
        created_at = ticket.created_at.strftime("%d.%m.%Y %H:%M")
        
        details_text = get_text('ticket_details',
                                ticket_id=ticket.id,
                                subject=ticket.subject,
                                status=status_text,
                                created_at=created_at,
                                description=ticket.description)
        
        text = details_text + f"\n\n{reply_status}"
        
        await call.message.edit_text(
            text,
            reply_markup=kb.markup_ticket_details(ticket_id, ticket.status == 'closed')
        )
        
    except Exception as e:
        logging.exception(f"Error in view_ticket_details: {e}")
        try:
            await call.message.edit_text(
                get_text('error_occurred'),
                reply_markup=kb.markup_support_menu()
            )
        except Exception:
            await call.answer("❌ Ошибка отображения. Попробуйте позже.")


@router.callback_query(F.data.startswith('ticket_conversation:'))
async def show_ticket_conversation(call: types.CallbackQuery, state: FSMContext):
    """Show ticket conversation"""
    await call.answer()
    
    try:
        ticket_id = int(call.data.split(':')[1])
        ticket = await support_ticket.get_ticket(ticket_id)
        
        # Check permissions (user can only see their own tickets, admins can see all)
        is_admin = call.from_user.id in config.ADMINS or call.from_user.id in utils.get_admins()
        if not ticket or (not is_admin and ticket.user_id != call.from_user.id):
            await call.message.edit_text(
                "❌ Тикет не найден или доступ запрещен.",
                reply_markup=kb.markup_support_menu()
            )
            return
        
        # Get conversation messages
        messages = await ticket_message.get_ticket_messages(ticket_id)
        
        conversation_text = f"💬 <b>Переписка по тикету #{ticket_id}</b>\n"
        conversation_text += f"📝 Тема: {ticket.subject}\n\n"
        
        for msg in messages:
            timestamp = msg['created_at'].strftime("%d.%m %H:%M")
            if msg['sender_type'] == 'admin':
                sender_type = "👤 <b>Администратор</b>"
            else:
                sender_type = "👤 <b>Вы</b>"
            
            conversation_text += f"{sender_type} ({timestamp}):\n{msg['message_text']}\n\n"
        
        # Always back to user tickets per requirements
        back_button = [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data='my_tickets'
        )]
        
        await call.message.edit_text(
            conversation_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[back_button])
        )
        
    except Exception as e:
        logging.error(f"Error in show_ticket_conversation: {e}")
        await call.message.edit_text(
            get_text('error_occurred'),
            reply_markup=kb.markup_support_menu()
        )


# ===== HELPER FUNCTIONS =====

async def build_admin_support_dashboard():
    """Build admin support dashboard text and markup"""
    try:
        # Get ticket counts
        counts = await support_ticket.get_tickets_count_by_status()
        
        text = get_text('admin.support_dashboard',
                             total=counts['total'],
                             open=counts['open'],
                             in_progress=counts['in_progress'],
                             closed=counts['closed'])
        
        markup = kb.markup_admin_support_dashboard()
        return text, markup
    except Exception as e:
        logging.error(f"Error in build_admin_support_dashboard: {e}")
        return get_text('error_occurred'), kb.markup_admin_support_dashboard()


# ===== ADMIN SUPPORT HANDLERS =====

@router.callback_query(F.data == 'admin_support')
async def admin_support_dashboard(call: types.CallbackQuery, state: FSMContext):
    """Admin support dashboard"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        await call.message.answer('⚠️ Ошибка доступа')
        return
    
    await call.answer()
    
    try:
        text, markup = await build_admin_support_dashboard()
        
        try:
            await call.message.edit_text(text, reply_markup=markup)
        except Exception as edit_error:
            # If edit fails (message not modified), just answer the callback
            if "message is not modified" in str(edit_error):
                await call.answer("✅ Панель поддержки уже открыта")
            else:
                raise edit_error
        
    except Exception as e:
        logging.error(f"Error in admin_support_dashboard: {e}")
        try:
            await call.message.edit_text(
                get_text('error_occurred'),
                reply_markup=kb.markup_admin_shop(call.from_user.id)
            )
        except:
            # If even error message can't be edited, just answer the callback
            await call.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith('tickets_'))
async def show_tickets_by_status(call: types.CallbackQuery, state: FSMContext):
    """Show tickets filtered by status"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        return
    
    await call.answer()
    
    try:
        # tickets_open -> open, tickets_in_progress -> in_progress
        status = call.data.split('_', 1)[1]
        tickets = await support_ticket.get_all_tickets(status=status)
        
        # Get status name for display
        status_name = {
            'open': '🟢 Открытые',
            'in_progress': '🟡 В работе', 
            'closed': '🔴 Закрытые'
        }.get(status, status)
        
        if not tickets:
            # Make text unique for each status to avoid Telegram "message is not modified" error
            no_tickets_text = f"{status_name} тикеты\n\n❌ Тикетов со статусом '{status_name.lower()}' не найдено.\n\nВыберите другой статус или создайте новый тикет."
            
            try:
                await call.message.edit_text(
                    no_tickets_text,
                    reply_markup=kb.markup_admin_support_dashboard()
                )
            except Exception as edit_error:
                # If edit fails (message not modified), just answer the callback
                if "message is not modified" in str(edit_error):
                    await call.answer("✅ Уже показаны тикеты с этим статусом")
                else:
                    raise edit_error
            return
        
        text = f"{status_name} тикеты\n\nВсего найдено: {len(tickets)}\n\nВыберите тикет:"
        
        try:
            await call.message.edit_text(
                text,
                reply_markup=kb.markup_admin_tickets_list(tickets)
            )
        except Exception as edit_error:
            # If edit fails (message not modified), just answer the callback
            if "message is not modified" in str(edit_error):
                await call.answer("✅ Уже показаны тикеты с этим статусом")
            else:
                raise edit_error
        
    except Exception as e:
        logging.error(f"Error in show_tickets_by_status: {e}")
        try:
            await call.message.edit_text(
                get_text('error_occurred'),
                reply_markup=kb.markup_admin_support_dashboard()
            )
        except:
            # If even error message can't be edited, just answer the callback
            await call.answer("❌ Произошла ошибка")


@router.callback_query(F.data.startswith('admin_ticket:'))
async def admin_view_ticket(call: types.CallbackQuery, state: FSMContext):
    """Admin view ticket details"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        return
    
    await call.answer()
    
    try:
        ticket_id = int(call.data.split(':')[1])
        ticket = await support_ticket.get_ticket(ticket_id)
        
        if not ticket:
            await call.message.edit_text(
                "❌ Тикет не найден.",
                reply_markup=kb.markup_admin_support_dashboard()
            )
            return
        
        # Get user info
        user_info = await user_model.get_user(ticket.user_id)
        user_name = user_info.get('full_name', 'Неизвестно') if user_info else 'Неизвестно'
        
        # Format timestamps
        created_at = ticket.created_at.strftime("%d.%m.%Y %H:%M")
        updated_at = ticket.updated_at.strftime("%d.%m.%Y %H:%M")
        
        # Status text
        status_text = {
            'open': '🟢 Открыт',
            'in_progress': '🟡 В работе',
            'closed': '🔴 Закрыт'
        }.get(ticket.status, ticket.status)
        
        text = get_text('admin.ticket_details_admin',
                             ticket_id=ticket.id,
                             user_name=user_name,
                             user_id=ticket.user_id,
                             subject=ticket.subject,
                             status=status_text,
                             created_at=created_at,
                             updated_at=updated_at,
                             description=ticket.description)
        
        await call.message.edit_text(
            text,
            reply_markup=kb.markup_admin_ticket_actions(ticket_id, ticket.status == 'closed')
        )
        
    except Exception as e:
        logging.error(f"Error in admin_view_ticket: {e}")
        await call.message.edit_text(
            get_text('error_occurred'),
            reply_markup=kb.markup_admin_support_dashboard()
        )


@router.callback_query(F.data.startswith('respond_ticket:'))
async def admin_respond_ticket(call: types.CallbackQuery, state: FSMContext):
    """Start admin response to ticket"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        return
    
    await call.answer()
    
    try:
        ticket_id = int(call.data.split(':')[1])
        await state.set_state(FSMSupport.admin_responding)
        await state.update_data(ticket_id=ticket_id)
        
        # Create inline cancel button for admin
        cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_support")]
        ])
        
        await call.message.edit_text(
            get_text('admin.admin_response_prompt'),
            reply_markup=cancel_keyboard
        )
        
    except Exception as e:
        logging.error(f"Error in admin_respond_ticket: {e}")
        await call.message.edit_text(
            get_text('error_occurred'),
            reply_markup=kb.markup_admin_support_dashboard()
        )


@router.message(FSMSupport.admin_responding)
async def process_admin_response(message: types.Message, state: FSMContext):
    """Process admin response"""
    if message.content_type not in ['text', 'photo', 'video', 'document']:
        await message.answer(
            "❌ Отправьте текст, фото, видео или документ:",
            reply_markup=kb.markup_cancel()
        )
        return
    
    try:
        state_data = await state.get_data()
        ticket_id = state_data['ticket_id']
        
        # Get ticket info
        ticket = await support_ticket.get_ticket(ticket_id)
        if not ticket:
            await state.clear()
            await message.answer(
                "❌ Тикет не найден.",
                reply_markup=kb.markup_admin_support_dashboard()
            )
            return
        
        # Prepare response data
        response_text = ""
        message_type = message.content_type
        file_id = None
        
        if message.content_type == 'text':
            response_text = message.text.strip()
        elif message.content_type == 'photo':
            response_text = message.caption or "Прикреплено изображение"
            file_id = message.photo[-1].file_id
        elif message.content_type == 'video':
            response_text = message.caption or "Прикреплено видео"
            file_id = message.video.file_id
        elif message.content_type == 'document':
            response_text = message.caption or f"Прикреплен документ: {message.document.file_name}"
            file_id = message.document.file_id
        
        # Create admin message
        await ticket_message.create_message(
            ticket_id=ticket_id,
            sender_id=message.from_user.id,
            sender_type='admin',
            message_text=response_text,
            message_type=message_type,
            file_id=file_id
        )
        
        # Update ticket status to in_progress if it was open
        if ticket.status == 'open':
            await support_ticket.update_ticket(ticket_id, status='in_progress')
        
        await state.clear()
        
        # Notify user about response
        await notify_user_response(ticket, message.from_user)
        
        await message.answer(
            get_text('admin.response_sent'),
            reply_markup=kb.markup_remove()
        )
        
        # Return to admin dashboard
        text, markup = await build_admin_support_dashboard()
        await message.answer(text, reply_markup=markup)
        
    except Exception as e:
        logging.error(f"Error in process_admin_response: {e}")
        await state.clear()
        await message.answer(
            get_text('error_occurred'),
            reply_markup=kb.markup_admin_support_dashboard()
        )


@router.callback_query(F.data.startswith('close_ticket:'))
async def admin_close_ticket(call: types.CallbackQuery, state: FSMContext):
    """Close ticket"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        return
    
    await call.answer()
    
    try:
        ticket_id = int(call.data.split(':')[1])
        ticket = await support_ticket.get_ticket(ticket_id)
        
        if not ticket:
            await call.message.edit_text(
                "❌ Тикет не найден.",
                reply_markup=kb.markup_admin_support_dashboard()
            )
            return
        
        # Close ticket
        await support_ticket.close_ticket(ticket_id)
        
        # Notify user
        await notify_user_ticket_closed(ticket, call.from_user)
        
        await call.answer("✅ Тикет закрыт!")
        
        # Refresh admin dashboard
        await admin_support_dashboard(call, state)
        
    except Exception as e:
        logging.error(f"Error in admin_close_ticket: {e}")
        await call.message.edit_text(
            get_text('error_occurred'),
            reply_markup=kb.markup_admin_support_dashboard()
        )


@router.callback_query(F.data == 'support_stats')
async def show_support_statistics(call: types.CallbackQuery, state: FSMContext):
    """Show support statistics"""
    data_admins = utils.get_admins()
    
    if call.from_user.id not in config.ADMINS and call.from_user.id not in data_admins:
        await call.answer()
        return
    
    await call.answer()
    
    try:
        # Get statistics
        counts = await support_ticket.get_tickets_count_by_status()
        all_tickets = await support_ticket.get_all_tickets()
        
        # Calculate average response time, tickets per day, etc.
        today_tickets = [t for t in all_tickets if t['created_at'].date() == datetime.now().date()]
        week_tickets = [t for t in all_tickets if (datetime.now() - t['created_at']).days <= 7]
        
        text = f"📊 **Статистика поддержки**\n\n"
        text += f"🎫 Всего тикетов: {counts['total']}\n"
        text += f"🟢 Открытых: {counts['open']}\n"
        text += f"🟡 В работе: {counts['in_progress']}\n"
        text += f"🔴 Закрытых: {counts['closed']}\n\n"
        text += f"📅 За сегодня: {len(today_tickets)}\n"
        text += f"📅 За неделю: {len(week_tickets)}\n"
        
        await call.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="◀️ Назад", 
                    callback_data='admin_support'
                )]
            ])
        )
        
    except Exception as e:
        logging.error(f"Error in show_support_statistics: {e}")
        await call.message.edit_text(
            get_text('error_occurred'),
            reply_markup=kb.markup_admin_support_dashboard()
        )


# ===== USER RESPOND HANDLERS =====

@router.callback_query(F.data.startswith('user_respond_ticket:'))
async def user_respond_ticket(call: types.CallbackQuery, state: FSMContext):
    """Start user response to ticket"""
    await call.answer()
    try:
        ticket_id = int(call.data.split(':')[1])
        ticket = await support_ticket.get_ticket(ticket_id)
        if not ticket or int(ticket.user_id) != int(call.from_user.id):
            await call.message.edit_text(
                "❌ Тикет не найден или доступ запрещен.",
                reply_markup=kb.markup_support_menu()
            )
            return
        await state.set_state(FSMSupport.waiting_response)
        await state.update_data(ticket_id=ticket_id)
        # Нужна ИНЛАЙН-клавиатура для edit_text
        cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_support")]
        ])
        await call.message.edit_text(
            "✍️ Введите ваш ответ по тикету:\n\n(Можно отправить текст, фото, видео или документ)",
            reply_markup=cancel_keyboard
        )
    except Exception as e:
        logging.exception(f"Error in user_respond_ticket: {e}")
        await call.message.edit_text(
            get_text('error_occurred'),
            reply_markup=kb.markup_support_menu()
        )


@router.message(FSMSupport.waiting_response)
async def process_user_response(message: types.Message, state: FSMContext):
    """Process user response to ticket"""
    if message.content_type not in ['text', 'photo', 'video', 'document']:
        await message.answer(
            "❌ Отправьте текст, фото, видео или документ:",
            reply_markup=kb.markup_cancel()
        )
        return
    try:
        state_data = await state.get_data()
        ticket_id = state_data.get('ticket_id')
        ticket = await support_ticket.get_ticket(ticket_id)
        if not ticket or int(ticket.user_id) != int(message.from_user.id):
            await state.clear()
            await message.answer(
                "❌ Тикет не найден или доступ запрещен.",
                reply_markup=kb.markup_support_menu()
            )
            return
        # Prepare response
        response_text = ""
        message_type = message.content_type
        file_id = None
        if message.content_type == 'text':
            response_text = message.text.strip()
        elif message.content_type == 'photo':
            response_text = message.caption or "Прикреплено изображение"
            file_id = message.photo[-1].file_id
        elif message.content_type == 'video':
            response_text = message.caption or "Прикреплено видео"
            file_id = message.video.file_id
        elif message.content_type == 'document':
            response_text = message.caption or f"Прикреплен документ: {message.document.file_name}"
            file_id = message.document.file_id
        # Save message
        await ticket_message.create_message(
            ticket_id=ticket_id,
            sender_id=message.from_user.id,
            sender_type='user',
            message_text=response_text,
            message_type=message_type,
            file_id=file_id
        )
        # Optionally, mark ticket 'in_progress' if admin had responded before
        await support_ticket.update_ticket(ticket_id, status='in_progress' if ticket.status == 'open' else ticket.status)
        await state.clear()
        await message.answer(
            "✅ Ответ отправлен!",
            reply_markup=kb.markup_remove()
        )
        # Return to support menu
        await message.answer(
            get_text('support_welcome'),
            reply_markup=kb.markup_support_menu()
        )
    except Exception as e:
        logging.exception(f"Error in process_user_response: {e}")
        await state.clear()
        await message.answer(
            get_text('error_occurred'),
            reply_markup=kb.markup_support_menu()
        )

# ===== NOTIFICATION FUNCTIONS =====

async def notify_admins_new_ticket(ticket, user):
    """Notify admins about new ticket"""
    try:
        # Надежное формирование списка админов
        base_admins = list(config.ADMINS or [])
        extra_admins = utils.get_admins() or []
        if not isinstance(extra_admins, list):
            logging.warning(f"utils.get_admins() вернул {type(extra_admins)}, ожидается list. Использую пустой список.")
            extra_admins = []
        # Уникализируем и фильтруем нечисловые значения
        combined = []
        for a in base_admins + extra_admins:
            try:
                val = int(a)
                if val not in combined:
                    combined.append(val)
            except Exception:
                logging.warning(f"Пропускаю некорректный admin id: {a}")
        admin_ids = combined
        
        user_name = user.full_name or "Неизвестно"
        created_at = ticket.created_at.strftime("%d.%m.%Y %H:%M")
        
        text = get_text('admin.new_ticket_notification',
                             subject=ticket.subject,
                             user_name=user_name,
                             user_id=ticket.user_id,
                             created_at=created_at)
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(admin_id, text)
            except Exception as e:
                logging.error(f"Failed to notify admin {admin_id}: {e}")
                
    except Exception as e:
        logging.error(f"Error in notify_admins_new_ticket: {e}")


async def notify_user_response(ticket, admin_user):
    """Notify user about admin response"""
    try:
        text = get_text('ticket_response_notification',
                             ticket_id=ticket.id,
                             subject=ticket.subject)
        
        await bot.send_message(ticket.user_id, text)
        
    except Exception as e:
        logging.error(f"Error in notify_user_response: {e}")


async def notify_user_ticket_closed(ticket, admin_user):
    """Notify user about ticket closure"""
    try:
        text = get_text('ticket_closed_notification',
                             ticket_id=ticket.id,
                             subject=ticket.subject)
        
        await bot.send_message(ticket.user_id, text)
        
    except Exception as e:
        logging.error(f"Error in notify_user_ticket_closed: {e}")


# ===== CANCEL HANDLER =====

@router.message(F.text.lower() == '❌ отмена')
async def cancel_support_operation(message: types.Message, state: FSMContext):
    """Cancel support operation"""
    current_state = await state.get_state()
    
    if current_state and 'FSMSupport' in str(current_state):
        await state.clear()
        
        is_admin = message.from_user.id in config.ADMINS or message.from_user.id in utils.get_admins()
        
        if is_admin:
            await message.answer('❌ Отменено', reply_markup=kb.markup_remove())
            # Show admin dashboard
            text, markup = await build_admin_support_dashboard()
            await message.answer(text, reply_markup=markup)
        else:
            await message.answer(
                '❌ Отменено',
                reply_markup=kb.markup_remove()
            )
            await message.answer(
                get_text('welcome'),
                reply_markup=kb.markup_main_menu()
            )
