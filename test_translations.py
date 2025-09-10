import pytest
from unittest.mock import Mock, patch
from database.lesson import Translations

@pytest.mark.asyncio
async def test_create_translation():
    """Test creating a translation"""
    t = Translations()
    translation = await t.create_translation('test_step', 'en', 'text', 'Test value')
    assert translation is not None
    assert translation.step_id == 'test_step'
    assert translation.language == 'en'
    assert translation.value == 'Test value'

@pytest.mark.asyncio
async def test_get_translation():
    """Test getting a translation"""
    t = Translations()
    await t.create_translation('test_step', 'en', 'text', 'Test value')
    translation = await t.get_translation('test_step', 'en', 'text')
    assert translation == 'Test value'

@pytest.mark.asyncio
async def test_update_translation():
    """Test updating a translation"""
    t = Translations()
    await t.create_translation('test_step', 'en', 'text', 'Old value')
    await t.update_translation('test_step', 'en', 'text', 'New value')
    translation = await t.get_translation('test_step', 'en', 'text')
    assert translation == 'New value'

@pytest.mark.asyncio
async def test_get_all_translations():
    """Test getting all translations"""
    t = Translations()
    await t.create_translation('test_step1', 'en', 'text', 'Value1')
    await t.create_translation('test_step2', 'es', 'caption', 'Value2')
    translations = await t.get_all_translations()
    assert len(translations) >= 2
    assert any(t['value'] == 'Value1' for t in translations)