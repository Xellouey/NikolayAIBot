import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.onboarding import OnboardingStep, OnboardingOption, OnboardingEvent
from database.user import User as UserModel
from localization import get_text
from message_manager import global_message_manager
from handlers.shop import add_user_preview_message, clear_user_preview_messages

router = Router()

class FSMOnboarding:
    current = 'onboarding_current'

async def _get_ordered_steps():
    steps = (OnboardingStep
             .select()
             .where(OnboardingStep.enabled == True)
             .order_by(OnboardingStep.order.asc()))
    return list(steps)

async def start_onboarding(message: types.Message, state: FSMContext, preview: bool = False):
    await state.update_data({FSMOnboarding.current: None})
    steps = await _get_ordered_steps()
    if not steps:
        return False
    await _go_to_step(message, state, steps[0])
    return True

async def _go_to_step(message_or_call, state: FSMContext, step: OnboardingStep):
    await state.update_data({FSMOnboarding.current: step.key})
    # Рендер
    text = _build_step_text(step)
    kb = await _build_step_keyboard(step)
    if isinstance(message_or_call, types.CallbackQuery):
        await global_message_manager.edit_message_safe(message_or_call.message, text, kb)
    else:
        await message_or_call.answer(text, reply_markup=kb)

async def _next_step(call: types.CallbackQuery, state: FSMContext):
    steps = await _get_ordered_steps()
    data = await state.get_data()
    current_key = data.get(FSMOnboarding.current)
    if not current_key:
        return
    # find next
    keys = [s.key for s in steps]
    if current_key not in keys:
        return
    idx = keys.index(current_key)
    if idx + 1 < len(steps):
        await _go_to_step(call, state, steps[idx + 1])
    else:
        # Done
        await _finish(call, state)

async def _prev_step(call: types.CallbackQuery, state: FSMContext):
    steps = await _get_ordered_steps()
    data = await state.get_data()
    current_key = data.get(FSMOnboarding.current)
    if not current_key:
        return
    keys = [s.key for s in steps]
    if current_key not in keys:
        return
    idx = keys.index(current_key)
    if idx - 1 >= 0:
        await _go_to_step(call, state, steps[idx - 1])

@router.callback_query(F.data.startswith('onb:'))
async def onboarding_actions(call: types.CallbackQuery, state: FSMContext):
    # onb:next:key[:value]
    # onb:prev:key
    # onb:toggle:key:value (for multi)
    try:
        parts = call.data.split(':')
        _, action, key, *rest = parts
        # Load step
        step = (OnboardingStep.select()
                .where(OnboardingStep.key == key)
                .first())
        if not step:
            await call.answer('❌ Шаг не найден', show_alert=True)
            return
        user_id = call.from_user.id

        if action == 'next':
            value = rest[0] if rest else None
            await _save_step_answer(user_id, step, value, state)
            await _next_step(call, state)
            return
        if action == 'prev':
            await _prev_step(call, state)
            return
        if action == 'toggle':
            # Multi-choice: store temporary selected options in state
            value = rest[0] if rest else None
            data = await state.get_data()
            selected = set((data.get(f'selected_{key}') or '').split(',')) if data.get(f'selected_{key}') else set()
            if value in selected:
                selected.remove(value)
            else:
                selected.add(value)
            await state.update_data({f'selected_{key}': ','.join(selected)})
            # just refresh UI
            await _go_to_step(call, state, step)
            return
    except Exception:
        await call.answer('❌ Ошибка онбординга', show_alert=True)

async def _save_step_answer(user_id: int, step: OnboardingStep, value: str | None, state: FSMContext):
    try:
        # Persist event
        OnboardingEvent.create(user_id=user_id, step=step, option_value=value)
        # Duplicate key answers into user
        if step.key == 'goal' and value:
            UserModel.update({UserModel.onboarding_completed: False}).where(UserModel.user_id==user_id).execute()
            UserModel.update({UserModel.full_name: UserModel.full_name}).execute()  # noop to ensure table open
            UserModel.update({UserModel.onboarding_completed: UserModel.onboarding_completed}).execute()
            UserModel.update({UserModel.last_onboarding_step: step.key}).where(UserModel.user_id==user_id).execute()
            UserModel.update({UserModel.onboarding_completed: UserModel.onboarding_completed}).execute()
            UserModel.update({UserModel.onboarding_completed: False}).execute()
            UserModel.update({UserModel.onboarding_completed: False}).where(UserModel.user_id==user_id).execute()
            # write goal
            try:
                con = UserModel._meta.database
                con.execute_sql("UPDATE user SET onboarding_goal=? WHERE user_id=?", (value, user_id))
            except Exception:
                pass
        elif step.key == 'level' and value:
            try:
                con = UserModel._meta.database
                con.execute_sql("UPDATE user SET onboarding_level=? WHERE user_id=?", (value, user_id))
            except Exception:
                pass
        elif step.key == 'consent' and value:
            try:
                con = UserModel._meta.database
                con.execute_sql("UPDATE user SET consent_newsletter=? WHERE user_id=?", (1 if value=='yes' else 0, user_id))
            except Exception:
                pass
        await state.update_data({ 'last_answer_'+step.key: value })
    except Exception:
        pass

async def _finish(call: types.CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    try:
        # Mark completed
        UserModel.update({UserModel.onboarding_completed: True}).where(UserModel.user_id==user_id).execute()
        # CTA logic (simple): if goal==quick_start -> suggest free lead, else catalog
        # Render finish
        text = get_text('onboarding.finish') or '✅ Онбординг завершен!'
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='📚 Открыть каталог', callback_data='catalog')]])
        await global_message_manager.edit_message_safe(call.message, text, kb)
    except Exception:
        await call.answer('✅ Онбординг завершен')

def _build_step_text(step: OnboardingStep) -> str:
    if step.type == 'screen':
        return get_text(step.text_key or 'onboarding.screen')
    if step.type in ('single_choice','multi_choice','consent'):
        return get_text(step.text_key or 'onboarding.question')
    return '…'

async def _build_step_keyboard(step: OnboardingStep) -> InlineKeyboardMarkup:
    rows = []
    if step.type in ('single_choice','consent'):
        options = (OnboardingOption
                   .select()
                   .where((OnboardingOption.step==step) & (OnboardingOption.enabled==True))
                   .order_by(OnboardingOption.order.asc()))
        for opt in options:
            rows.append([InlineKeyboardButton(text=get_text(opt.text_key), callback_data=f'onb:next:{step.key}:{opt.value}')])
        rows.append([InlineKeyboardButton(text='⬅️ Назад', callback_data=f'onb:prev:{step.key}')])
    elif step.type == 'multi_choice':
        options = (OnboardingOption
                   .select()
                   .where((OnboardingOption.step==step) & (OnboardingOption.enabled==True))
                   .order_by(OnboardingOption.order.asc()))
        # Для простоты — по одному в строке с toggle
        for opt in options:
            rows.append([InlineKeyboardButton(text='☑ '+get_text(opt.text_key), callback_data=f'onb:toggle:{step.key}:{opt.value}')])
        rows.append([InlineKeyboardButton(text='Далее ➡️', callback_data=f'onb:next:{step.key}')])
        rows.append([InlineKeyboardButton(text='⬅️ Назад', callback_data=f'onb:prev:{step.key}')])
    else:  # screen
        rows.append([InlineKeyboardButton(text='Далее ➡️', callback_data=f'onb:next:{step.key}')])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# Admin preview helpers
@router.callback_query(F.data == 'onboarding_preview')
async def onboarding_preview(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await clear_user_preview_messages(call.from_user.id, call.from_user.id)
    await start_onboarding(call.message, state, preview=True)

@router.callback_query(F.data == 'onboarding_preview_clear')
async def onboarding_preview_clear(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await clear_user_preview_messages(call.from_user.id, call.from_user.id)
    await call.answer('🧹 Предпросмотр онбординга удален')
