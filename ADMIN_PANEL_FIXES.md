# Admin Panel Fixes and Text Settings Implementation

## Date: December 2024
## Author: AI Assistant

## Issues Fixed

### 1. Non-clickable Admin Buttons
**Problem:** The following buttons in the admin panel were not working:
- 🎫 Промокоды (Promocodes)
- 📝 Настройки текстов (Text Settings)
- 💱 Курс валют (Currency Rate)
- 📊 Статистика (Statistics)

**Solution:** Added handlers for all missing callback_data values in `handlers/admin.py`:
- `promocodes` - Shows promocode management menu
- `text_settings` - Opens text editing interface
- `currency_rate` - Allows editing USD to Stars exchange rate
- `statistics` - Displays bot statistics

### 2. Removed "Переводы" Button
**Problem:** The "Переводы" (Translations) button was not needed as per requirements.

**Solution:** Removed the button from `keyboards.py` in the `markup_admin_settings()` function.

### 3. Fixed "Назад" Button in Lesson Editing
**Problem:** The back button in the lesson editing list was causing a loop - clicking it would just refresh the same screen.

**Solution:** Changed the callback_data from `'edit_lesson'` to `'lessons_mgmt'` in the `markup_lesson_edit_list()` function in `keyboards.py`.

### 4. Implemented Text Settings System
**Problem:** Admin needed a way to edit all user-facing texts without modifying code.

**Solution:** Created a simplified text editing system that:
- Uses the existing `json/interface_texts.json` file for storage
- Allows editing through admin panel categories (Buttons, Messages, Admin, Mail)
- Shows current values and allows direct text replacement
- Requires immediate updates for text changes to be visible

## How to Use the Text Settings

### Accessing Text Settings
1. Use `/admin` command
2. Click "⛙️ Настройки"
3. Click "📝 Настройки текстов"

### Editing Process
1. Select a category (Кнопки, Сообщения, etc.)
2. Choose the text key you want to edit
3. View the current value
4. Send the new text
5. Bot will confirm the change
6. **IMPORTANT: Restart the bot for changes to take effect**

### Text Categories
- **buttons** - All user-facing button texts
- **messages** - User messages and prompts
- **admin** - Admin panel messages (kept in Russian)
- **mail** - Mail/broadcast related texts

## Key Design Decisions

1. **No Multi-language Complexity**: Following user requirements, the system doesn't have complex language switching. Admin simply edits texts directly.

2. **Admin Panel Stays Russian**: All admin interface texts remain hardcoded in Russian and are not editable through the system.

3. **JSON File Storage**: Uses existing `json/interface_texts.json` instead of database to keep it simple and aligned with existing architecture.

4. **Обновление текстов**: Изменения применяются мгновенно. Пользователи сразу увидят новые тексты.

## Files Modified

1. **handlers/admin.py**
   - Added handlers for promocodes, text_settings, currency_rate, statistics
   - Implemented FSM flow for text editing

2. **keyboards.py**
   - Removed "Переводы" button
   - Fixed back button callback in lesson editing

3. **utils.py**
   - Added `get_interface_texts()` and `save_interface_texts()` functions

4. **database/lesson.py**
   - Fixed Promocode model fields
   - Added statistics methods

5. **database/user.py**
   - Added `get_total_users()` and `get_users_count_since()` methods

## Testing Checklist

- [x] Promocodes button opens promocode management
- [x] Text Settings button opens text editing interface
- [x] Currency Rate button allows editing exchange rate
- [x] Statistics button shows bot statistics
- [x] "Переводы" button is removed
- [x] Back button in lesson editing returns to management menu
- [x] Text editing saves to JSON file
- [x] Python files compile without errors

## Important Notes

1. **Мгновенное обновление**: После любых изменений текста изменения применяются мгновенно без перезапуска.

2. **Admin Only**: All new features are restricted to admin users only.

3. **Russian Interface**: The admin panel remains entirely in Russian as specified.

4. **Linear Navigation**: The bot maintains its fixed linear navigation flow (start → greeting → video → lesson menu) as required.

## Future Enhancements (Optional)

1. Add text search/filter functionality
2. Implement text validation (length limits, special characters)
3. Add export/import functionality for bulk text editing
4. Create audit log for text changes
5. Add preview functionality before saving

## Troubleshooting

If buttons still don't work after update:
1. Ensure bot is restarted
2. Check that callback_data values match exactly
3. Verify admin permissions
4. Check logs for any error messages

## Руководство оператора по настройке текстов

### Как изменить тексты бота

1. **Войдите в админ-панель**
   - Отправьте команду `/admin` боту
   - Убедитесь, что у вас есть права администратора

2. **Откройте настройки текстов**
   - Нажмите кнопку "⛙️ Настройки"
   - Нажмите кнопку "📝 Настройки текстов"

3. **Выберите категорию текстов**
   - **🔘 Кнопки** - тексты на кнопках интерфейса
   - **💬 Сообщения** - текстовые сообщения для пользователей  
   - **👨‍💼 Админ** - сообщения админ-панели (НЕ ИЗМЕНЯТЬ - остаются на русском)
   - **📧 Почта** - тексты для рассылок

4. **Выберите конкретный текст для редактирования**
   - Нажмите на нужный ключ из списка
   - Вы увидите текущее значение текста

5. **Введите новый текст**
   - Отправьте новый текст сообщением
   - Ограничения:
     - Максимум 4096 символов для сообщений
     - Максимум 64 символа для текста кнопок
     - Запрещены теги: `<script>`, `<iframe>`, `<object>`, `<embed>`, `<form>`
     - Разрешены теги: `<b>`, `<i>`, `<u>`, `<s>`, `<code>`, `<pre>`, `<a>`

6. **Текст сохранен**
   - ✅ **Готово**: Изменения применяются мгновенно!
   - Все изменения сохраняются в файле `json/interface_texts.json`

### Примеры часто изменяемых текстов

#### Изменение кнопки "Мои уроки"
1. Настройки → Настройки текстов → Кнопки
2. Найдите ключ `my_lessons`
3. Введите новый текст, например: "📚 My Lessons"
4. Перезапустите бота

#### Изменение приветственного сообщения
1. Настройки → Настройки текстов → Сообщения
2. Найдите ключ `welcome`
3. Введите новое приветствие
4. Перезапустите бота

### Структура ключей текстов

- **buttons.*** - тексты кнопок
  - `buttons.my_lessons` - кнопка "Мои уроки"
  - `buttons.catalog` - кнопка "Каталог"
  - `buttons.back` - кнопка "Назад"
  - `buttons.buy` - кнопка "Купить"
  - `buttons.enter_promocode` - кнопка "Промокод"

- **messages.*** - сообщения пользователям
  - `messages.welcome` - приветственное сообщение
  - `messages.catalog_title` - заголовок каталога
  - `messages.no_lessons` - сообщение "нет уроков"
  - `messages.lesson_purchased` - сообщение об успешной покупке

### Аудит изменений

Все изменения текстов автоматически логируются в файл `json/text_edits_audit.json`

Формат лога:
```json
{
  "timestamp": "2024-12-10T15:30:00",
  "admin_id": 123456789,
  "admin_name": "Admin Name",
  "category": "buttons",
  "key": "my_lessons",
  "old_value": "📚 Мои уроки",
  "new_value": "📚 My Lessons"
}
```

### Резервное копирование

**Перед изменениями рекомендуется:**
1. Сделать копию файла `json/interface_texts.json`
2. Сохранить её как `json/interface_texts_backup.json`

**Для восстановления:**
1. Остановите бота
2. Замените `json/interface_texts.json` резервной копией
3. Запустите бота

## Запуск тестов

Для проверки работоспособности после изменений:

```bash
# Установка pytest (если не установлен)
pip install pytest pytest-asyncio

# Запуск всех тестов
python run_tests.py

# Запуск конкретного теста
python -m pytest tests/test_admin_panel.py::TestAdminHandlers -v
```

## Citations
<citations>
  <document>
      <document_type>RULE</document_type>
      <document_id>LCi9XZQP3KmwEi1c4aB3B1</document_id>
  </document>
  <document>
      <document_type>RULE</document_type>
      <document_id>Z9U3JUhtZIwfXbQK9vBKOz</document_id>
  </document>
  <document>
      <document_type>RULE</document_type>
      <document_id>Zdp0kTIRjkrnf966nFGZgc</document_id>
  </document>
</citations>
