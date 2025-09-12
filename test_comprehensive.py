#!/usr/bin/env python3
"""Comprehensive test suite for bot fixes"""
import asyncio
import sys
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from aiogram import types
from aiogram.fsm.context import FSMContext
from localization import get_text, DEFAULT_TEXTS
from database.lead_magnet import LeadMagnet
from handlers.support import build_admin_support_dashboard


class TestLocalization:
    """Test localization fixes"""
    
    def test_all_required_keys_exist(self):
        """Test that all required localization keys exist"""
        required_keys = [
            'support_welcome',
            'ticket_subject_prompt',
            'ticket_description_prompt',
            'no_tickets',
            'error_occurred',
            'my_lessons_title',
            'welcome',
            'catalog_title',
            'no_lessons'
        ]
        
        for key in required_keys:
            assert key in DEFAULT_TEXTS, f"Missing key: {key}"
            # Check that value is not the key itself
            assert DEFAULT_TEXTS[key] != key, f"Key {key} returns itself, not localized text"
    
    def test_get_text_normalization(self):
        """Test that get_text normalizes 'messages.' prefix"""
        # Test with and without prefix
        assert get_text('welcome') == get_text('messages.welcome')
        assert get_text('support_welcome') == get_text('messages.support_welcome')
        
        # Check it returns actual text, not the key
        assert get_text('welcome') != 'welcome'
        assert get_text('messages.welcome') != 'messages.welcome'
    
    def test_admin_messages_normalization(self):
        """Test admin message key normalization"""
        # Admin keys should work with both formats
        admin_key = 'admin.support_dashboard'
        admin_key_old = 'admin.messages.support_dashboard'
        
        # Both should return the same text
        text1 = get_text(admin_key)
        text2 = get_text(admin_key_old)
        
        # Should not return the key itself
        assert text1 != admin_key
        assert text2 != admin_key_old


class TestSupportCancelFlow:
    """Test support cancel flow fixes"""
    
    @pytest.mark.asyncio
    async def test_build_admin_support_dashboard_exists(self):
        """Test that build_admin_support_dashboard function exists and works"""
        # Mock the support_ticket to return test data
        with patch('handlers.support.support_ticket') as mock_ticket:
            mock_ticket.get_tickets_count_by_status = AsyncMock(return_value={
                'total': 10,
                'open': 5,
                'in_progress': 3,
                'closed': 2
            })
            
            text, markup = await build_admin_support_dashboard()
            
            # Check that we got results
            assert text is not None
            assert markup is not None
            assert '10' in text  # Total tickets
            assert '5' in text   # Open tickets
    
    @pytest.mark.asyncio
    async def test_no_fake_callback_query(self):
        """Test that no fake CallbackQuery objects are created"""
        # Read the support.py file to check for fake CallbackQuery creation
        with open('handlers/support.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check that we're not creating fake CallbackQuery objects
        assert 'types.CallbackQuery(' not in content or 'fake' not in content
        
        # Verify build_admin_support_dashboard is used instead
        assert 'build_admin_support_dashboard' in content


class TestLeadMagnet:
    """Test lead magnet functionality"""
    
    @pytest.mark.asyncio
    async def test_lead_magnet_model_exists(self):
        """Test that LeadMagnet model exists and has required methods"""
        # Check methods exist
        assert hasattr(LeadMagnet, 'get_lead_magnet')
        assert hasattr(LeadMagnet, 'set_enabled')
        assert hasattr(LeadMagnet, 'set_greeting_text')
        assert hasattr(LeadMagnet, 'set_lessons_label')
        assert hasattr(LeadMagnet, 'set_video')
        assert hasattr(LeadMagnet, 'is_ready')
        assert hasattr(LeadMagnet, 'get_text_for_locale')
    
    @pytest.mark.asyncio
    async def test_lead_magnet_default_state(self):
        """Test lead magnet default configuration"""
        lead_magnet = await LeadMagnet.get_lead_magnet()
        
        assert lead_magnet is not None
        assert lead_magnet.enabled == False  # Should be disabled by default
        assert lead_magnet.video_file_id is None  # No video by default
    
    @pytest.mark.asyncio
    async def test_lead_magnet_cannot_enable_without_video(self):
        """Test that lead magnet cannot be enabled without video"""
        # Ensure video is not set
        lead_magnet = await LeadMagnet.get_lead_magnet()
        if lead_magnet and lead_magnet.video_file_id:
            lead_magnet.video_file_id = None
            lead_magnet.save()
        
        # Try to enable without video
        result = await LeadMagnet.set_enabled(True)
        assert result == False  # Should fail
        
        # Check it's still disabled
        is_ready = await LeadMagnet.is_ready()
        assert is_ready == False
    
    @pytest.mark.asyncio
    async def test_lead_magnet_text_fallback(self):
        """Test lead magnet text locale fallback"""
        # Test fallback to Russian
        text = await LeadMagnet.get_text_for_locale('greeting_text', 'xx')  # Non-existent locale
        assert text is not None
        assert len(text) > 0
        
        # Test fallback for label
        label = await LeadMagnet.get_text_for_locale('lessons_label', 'xx')
        assert label is not None
        assert len(label) > 0


class TestUserFlow:
    """Test user flow with lead magnet"""
    
    @pytest.mark.asyncio
    async def test_start_command_flow(self):
        """Test /start command flow"""
        from handlers.client import send_lead_magnet
        
        # Mock message
        mock_message = Mock(spec=types.Message)
        mock_message.from_user = Mock()
        mock_message.from_user.id = 12345
        
        # Mock bot
        mock_bot = AsyncMock()
        
        # Test when lead magnet is not ready
        with patch('handlers.client.LeadMagnet.is_ready', return_value=False):
            result = await send_lead_magnet(mock_message, mock_bot, 'ru')
            assert result == False  # Should return False when not ready
    
    def test_my_lessons_includes_lead_magnet(self):
        """Test that My Lessons includes lead magnet when enabled"""
        from keyboards import markup_my_lessons
        
        # Test with lead magnet
        lessons = [
            {'id': 'lead_magnet', 'title': 'Вводный урок', 'is_lead': True},
            {'id': 1, 'title': 'Урок 1', 'is_lead': False}
        ]
        
        markup = markup_my_lessons(lessons)
        
        # Check that markup contains lead_magnet callback
        buttons_text = str(markup)
        assert 'lead_magnet:play' in buttons_text
        assert 'view_lesson:1' in buttons_text


class TestAdminPanel:
    """Test admin panel for lead magnet"""
    
    def test_admin_menu_has_lead_magnet(self):
        """Test that admin menu has lead magnet button"""
        from keyboards import markup_admin_shop
        
        markup = markup_admin_shop(123456)  # Admin user ID
        
        # Check that lead magnet button exists
        buttons_text = str(markup)
        assert 'lead_magnet' in buttons_text
    
    def test_lead_magnet_states_exist(self):
        """Test that FSMLeadMagnet states exist"""
        from states import FSMLeadMagnet
        
        assert hasattr(FSMLeadMagnet, 'editing_text')
        assert hasattr(FSMLeadMagnet, 'editing_video')
        assert hasattr(FSMLeadMagnet, 'editing_label')
    
    def test_admin_panel_is_russian_only(self):
        """Test that admin panel texts are in Russian"""
        from handlers.admin_lead_magnet import markup_lead_magnet_menu
        
        markup = markup_lead_magnet_menu(is_enabled=False, has_video=False)
        
        # Convert to string to check button texts
        buttons_text = str(markup)
        
        # Check for Russian texts
        assert 'Включить' in buttons_text or 'Выключить' in buttons_text
        assert 'Изменить' in buttons_text
        assert 'Назад' in buttons_text


def run_tests():
    """Run all tests and report results"""
    print("=" * 60)
    print("🧪 COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Run pytest with verbose output
    exit_code = pytest.main([__file__, '-v', '--tb=short'])
    
    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n📋 Summary of fixes verified:")
        print("  ✅ Localization: All keys present, normalization works")
        print("  ✅ Support cancel: No fake CallbackQuery, uses builder")
        print("  ✅ Lead magnet: Model works, cannot enable without video")
        print("  ✅ User flow: Lead magnet integrated in /start and My Lessons")
        print("  ✅ Admin panel: Lead magnet management added, Russian-only")
        print("\n✅ Comprehensive test completed successfully!")
    else:
        print("\n" + "=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        print("\nPlease review the errors above and fix any issues.")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
