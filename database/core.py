import config
import peewee
import sqlite3
from peewee import *
import asyncio
import threading

# Use SQLite for development/testing with thread safety
# check_same_thread=False позволяет использовать соединение в разных потоках
con = SqliteDatabase(
    'shop_bot.db',
    pragmas={
        'journal_mode': 'wal',  # Write-Ahead Logging для лучшей конкурентности
        'foreign_keys': 1,
        'synchronous': 'normal',
        'cache_size': -64000,  # 64MB кеш
    },
    check_same_thread=False  # Разрешаем использование в разных потоках
)

# For async compatibility, create a thread-safe wrapper
class AsyncManager:
    def __init__(self, database):
        self.database = database
        self._local = threading.local()
    
    def _ensure_connection(self):
        """Убеждаемся, что у текущего потока есть соединение"""
        # Проверяем, есть ли у текущего потока соединение
        if not hasattr(self._local, 'connected') or not self._local.connected:
            # Создаем новое соединение для этого потока
            if self.database.is_closed():
                self.database.connect(reuse_if_open=True)
            self._local.connected = True
    
    async def create(self, model_class, **kwargs):
        loop = asyncio.get_event_loop()
        def _create():
            self._ensure_connection()
            return model_class.create(**kwargs)
        return await loop.run_in_executor(None, _create)
    
    async def get(self, query):
        loop = asyncio.get_event_loop()
        def _get():
            self._ensure_connection()
            return query.get()
        return await loop.run_in_executor(None, _get)
    
    async def execute(self, query):
        """
        Универсальный исполнятель Peewee-запросов с thread-safety.
        - Для SELECT (QueryResultWrapper, .dicts(), .objects()) — просто итерируем и приводим к list.
        - Для UPDATE/INSERT/DELETE — вызываем query.execute().
        Это устраняет падение 'NoneType is not iterable' на UpdateQuery.
        """
        loop = asyncio.get_event_loop()
        def run():
            self._ensure_connection()
            # Если это обёртка результата (iterable), просто материализуем список
            try:
                if not hasattr(query, 'execute'):
                    return list(query)
            except TypeError:
                # Не итерируемый объект — перейдем к execute()
                pass
            # Для всех остальных случаев используем execute()
            if hasattr(query, 'execute'):
                return query.execute()
            # Fallback: попробуем просто материализовать
            return list(query)
        return await loop.run_in_executor(None, run)

orm = AsyncManager(con)
