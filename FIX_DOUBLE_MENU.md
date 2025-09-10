# ✅ Исправлено дублирование главного меню

## Проблема
После команды `/start` главное меню показывалось два раза.

## Причина
В коде было два места, где отправлялось главное меню:
1. В функции `send_lead_lesson()` (строка 78-82)
2. В функции `start()` (строки 147-150)

## Решение
Удалено дублирующее отправление меню из функции `start()`, оставлено только в `send_lead_lesson()`.

## Изменения в файле `handlers/client.py`:

### Было:
```python
# Send intro video (lead lesson)
await send_lead_lesson(message, bot, lang)

# Mark onboarding as completed
await u.mark_onboarding_complete(user_id)

# Show catalog (вызывало ошибку)
from .shop import show_catalog
try:
    await show_catalog(types.CallbackQuery.from_message(message, data='catalog'), state)
except Exception as e:
    logging.error(f"Error showing catalog: {e}")

# Send main menu after (дублирование!)
await asyncio.sleep(1)
await message.answer(
    get_text('after_video', lang),
    reply_markup=kb.markup_main_menu()
)
```

### Стало:
```python
# Send intro video (lead lesson) - this will also show the main menu
await send_lead_lesson(message, bot, lang)

# Mark onboarding as completed
await u.mark_onboarding_complete(user_id)
```

## Результат
Теперь последовательность работает правильно:
1. Приветственное сообщение
2. Видео лид-магнит (если есть)
3. Сообщение "Отличное начало!"
4. **Главное меню (показывается только один раз)**

## Статус: ✅ ИСПРАВЛЕНО
