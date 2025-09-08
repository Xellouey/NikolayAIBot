import config
import peewee
import sqlite3
from peewee import *
import asyncio

# Use SQLite for development/testing
con = SqliteDatabase('shop_bot.db')

# For async compatibility, create a simple wrapper
class AsyncManager:
    def __init__(self, database):
        self.database = database
    
    async def create(self, model_class, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: model_class.create(**kwargs))
    
    async def get(self, query):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: query.get())
    
    async def execute(self, query):
        loop = asyncio.get_event_loop()
        if hasattr(query, 'dicts'):
            def sync_execute():
                return list(query.dicts())
            return await loop.run_in_executor(None, sync_execute)
        def sync_execute2():
            return query.execute()
        return await loop.run_in_executor(None, sync_execute2)

orm = AsyncManager(con)
