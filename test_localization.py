"""
Test script for localization system
"""
from localization import Localization, get_text

def test_localization():
    print("🧪 Тестирование системы локализации\n")
    print("=" * 50)
    
    # Test Russian (default)
    print("\n🇷🇺 Русский язык (по умолчанию):")
    print(f"  welcome: {get_text('welcome', 'ru')}")
    print(f"  btn_catalog: {get_text('btn_catalog', 'ru')}")
    print(f"  btn_back: {get_text('btn_back', 'ru')}")
    
    # Test English
    print("\n🇬🇧 English:")
    print(f"  welcome: {get_text('welcome', 'en')}")
    print(f"  btn_catalog: {get_text('btn_catalog', 'en')}")
    print(f"  btn_back: {get_text('btn_back', 'en')}")
    
    # Test Spanish
    print("\n🇪🇸 Español:")
    print(f"  welcome: {get_text('welcome', 'es')}")
    print(f"  btn_catalog: {get_text('btn_catalog', 'es')}")
    print(f"  btn_back: {get_text('btn_back', 'es')}")
    
    # Test formatting
    print("\n📝 Тест форматирования:")
    print(f"  lesson_price (ru): {get_text('lesson_price', 'ru', price=100)}")
    print(f"  lesson_price (en): {get_text('lesson_price', 'en', price=100)}")
    
    # Test adding new translation
    print("\n➕ Добавление нового перевода:")
    success = Localization.set_translation('welcome', 'de', '👋 Willkommen in der KI-Schule!')
    if success:
        print(f"  ✅ Немецкий перевод добавлен")
        print(f"  welcome (de): {get_text('welcome', 'de')}")
    else:
        print(f"  ❌ Ошибка добавления перевода")
    
    # Show all available keys
    print("\n🔑 Доступные ключи:")
    keys = Localization.get_all_keys()
    for i, key in enumerate(keys, 1):
        print(f"  {i}. {key}")
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    test_localization()
