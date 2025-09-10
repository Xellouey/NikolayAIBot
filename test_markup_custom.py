#!/usr/bin/env python
"""Test markup_custom function"""
import json
from keyboards import markup_custom

# Test data
test_json = {
    "inline_keyboard": [
        [{"text": "🌐 Открыть сайт", "url": "https://example.com"}],
        [{"text": "💬 Поддержка", "callback_data": "support"}]
    ]
}

print("Testing markup_custom with valid inline keyboard JSON:")
print(f"Input: {json.dumps(test_json, ensure_ascii=False, indent=2)}")

result = markup_custom(test_json)
print(f"\nResult type: {type(result)}")
print(f"Result: {result}")

if result:
    print("\n✅ markup_custom работает корректно!")
else:
    print("\n❌ markup_custom вернул None!")

# Test with None
print("\n\nTesting with None:")
result_none = markup_custom(None)
print(f"Result: {result_none}")
print("✅ Корректно обрабатывает None" if result_none is None else "❌ Ошибка с None")
