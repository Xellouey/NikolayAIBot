"""
🧪 Тест обработчика уроков без запуска полного бота
"""

import unittest
from database import lesson

class TestLessonHandlers(unittest.TestCase):
    def setUp(self):
        self.l = lesson.Lesson()
        self.p = lesson.Purchase()

    async def test_create_lesson(self):
        lesson_id = await self.l.create_lesson(
            title="Test Lesson",
            description="Test description",
            price_usd=10.00
        )
        self.assertGreater(lesson_id, 0)

    async def test_get_lesson(self):
        # Create test lesson
        lesson_id = await self.l.create_lesson(
            title="Get Test Lesson",
            description="Test description",
            price_usd=15.00
        )
        data = await self.l.get_lesson(lesson_id)
        self.assertEqual(data['title'], "Get Test Lesson")
        self.assertEqual(data['price_usd'], 15.00)

    async def test_purchase(self):
        # Create test lesson
        lesson_id = await self.l.create_lesson(
            title="Purchase Test Lesson",
            description="Test description",
            price_usd=20.00
        )
        # Create purchase
        await self.p.create_purchase(
            user_id=1,
            lesson_id=lesson_id,
            price_paid_usd=20.00,
            price_paid_stars=4000
        )
        # Check ownership
        has = await self.p.check_user_has_lesson(1, lesson_id)
        self.assertTrue(has)

if __name__ == '__main__':
    import asyncio
    asyncio.run(unittest.main())