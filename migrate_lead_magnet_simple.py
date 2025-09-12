"""
Миграция для упрощения лид-магнита - убираем языки
"""
import json
import logging
from database.lead_magnet import LeadMagnet

logging.basicConfig(level=logging.INFO)

def migrate():
    """Упрощаем поля лид-магнита"""
    try:
        # Получаем текущую конфигурацию
        lead_magnet = LeadMagnet.get_or_none(LeadMagnet.id == 1)
        
        if not lead_magnet:
            print("❌ Лид-магнит не найден в БД, создаём...")
            LeadMagnet.create(
                id=1,
                enabled=False,
                greeting_text='Добро пожаловать! Это вводный урок.',
                lessons_label='Приветственный вводный урок',
                video_file_id=None
            )
            print("✅ Лид-магнит создан с простыми текстовыми полями")
            return
        
        # Если поля содержат JSON, извлекаем текст
        changed = False
        
        # Обрабатываем greeting_text
        if lead_magnet.greeting_text.startswith('{'):
            try:
                texts = json.loads(lead_magnet.greeting_text)
                # Берём русский текст или первый доступный
                new_text = texts.get('ru', None)
                if not new_text and texts:
                    new_text = list(texts.values())[0]
                if new_text:
                    lead_magnet.greeting_text = new_text
                    changed = True
                    print(f"✅ Приветственный текст преобразован: {new_text[:50]}...")
            except:
                pass
        
        # Обрабатываем lessons_label
        if lead_magnet.lessons_label.startswith('{'):
            try:
                labels = json.loads(lead_magnet.lessons_label)
                # Берём русский текст или первый доступный
                new_label = labels.get('ru', None)
                if not new_label and labels:
                    new_label = list(labels.values())[0]
                if new_label:
                    lead_magnet.lessons_label = new_label
                    changed = True
                    print(f"✅ Название в уроках преобразовано: {new_label}")
            except:
                pass
        
        if changed:
            lead_magnet.save()
            print("✅ Миграция завершена! Поля теперь содержат простой текст без языков")
        else:
            print("ℹ️ Миграция не требуется - поля уже в простом текстовом формате")
            
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")

if __name__ == "__main__":
    migrate()
