import asyncio
import aiogram
import config
import logging
import config
import json
from database import user
import keyboards as kb


u = user.User()
bot = aiogram.Bot(config.TOKEN)


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    filename='file.log'
)


async def mailing(message_id, from_id, keyboard, message_info=None):
    logging.info(f'Start mailing {message_id}, from {from_id}')

    users = await u.get_all_users()

    if keyboard is not None:
        if isinstance(keyboard, str):
            keyboard = keyboard.replace('±', ' ')
            keyboard = keyboard.replace("^", "'")
            keyboard = keyboard.replace('^', '"')
            keyboard = keyboard.replace("'", '"')
            keyboard = json.loads(keyboard)
        markup = kb.markup_custom(keyboard)
    else:
        markup = None
    
    # Извлекаем данные о медиа, если есть
    media = None
    media_type = None
    text = ''
    
    if message_info:
        if isinstance(message_info, str):
            # Старый формат - просто текст
            text = message_info
        elif isinstance(message_info, dict):
            # Новый формат с медиа
            text = message_info.get('text', '')
            media = message_info.get('media')
            media_type = message_info.get('media_type')
        
    i = 0
    for user in users:
        user_id = user['user_id']
    
        try:
            if media and media_type:
                # Отправляем медиа с текстом
                if media_type == 'photo':
                    await bot.send_photo(user_id, media, caption=text, reply_markup=markup)
                elif media_type == 'video':
                    await bot.send_video(user_id, media, caption=text, reply_markup=markup)
            else:
                # Отправляем только текст
                if text:
                    await bot.send_message(user_id, text, reply_markup=markup)
                else:
                    # Старый способ - пересылка
                    forwarded_msg = await bot.forward_message(user_id, from_id, message_id)
                    if markup:
                        await bot.edit_message_reply_markup(user_id, forwarded_msg.message_id, reply_markup=markup)
            i += 1
        except Exception as e:
            logging.error(f"Error sending to {user_id}: {e}")
            
    logging.info(f'Success mailing ({i}/{len(users)}) {message_id}, from {from_id}')


def start_mail(message_id, from_id, keyboard):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(mailing(message_id, from_id, keyboard))
