#!/usr/bin/env python3
"""Test script to verify all the fixes"""
import asyncio
import sys
from localization import get_text, DEFAULT_TEXTS
from database.lead_magnet import LeadMagnet

def test_localization():
    """Test that localization keys are working correctly"""
    print("🧪 Testing localization...")
    
    # Test that all needed keys exist
    required_keys = [
        'support_welcome',
        'ticket_subject_prompt',
        'no_tickets',
        'error_occurred',
        'my_lessons_title',
        'welcome'
    ]
    
    missing = []
    for key in required_keys:
        if key not in DEFAULT_TEXTS:
            missing.append(key)
    
    if missing:
        print(f"❌ Missing keys: {missing}")
        return False
    
    # Test get_text with and without prefixes (normalization)
    test_cases = [
        ('welcome', 'welcome'),
        ('messages.welcome', 'welcome'),  # Should normalize
        ('support_welcome', 'support_welcome'),
        ('messages.support_welcome', 'support_welcome'),  # Should normalize
    ]
    
    for input_key, expected_key in test_cases:
        result = get_text(input_key)
        if result == input_key:  # If key is returned as-is, something is wrong
            print(f"❌ get_text('{input_key}') returned the key itself, not the text")
            return False
        print(f"✅ get_text('{input_key}') = '{result[:30]}...'")
    
    print("✅ Localization tests passed!")
    return True


async def test_lead_magnet():
    """Test lead magnet functionality"""
    print("\n🧪 Testing lead magnet...")
    
    # Test getting lead magnet
    lead_magnet = await LeadMagnet.get_lead_magnet()
    if not lead_magnet:
        print("❌ Failed to get lead magnet configuration")
        return False
    
    print(f"✅ Lead magnet exists: enabled={lead_magnet.enabled}, has_video={bool(lead_magnet.video_file_id)}")
    
    # Test is_ready
    is_ready = await LeadMagnet.is_ready()
    print(f"✅ Lead magnet ready status: {is_ready}")
    
    # Test getting text for locale
    greeting = await LeadMagnet.get_text_for_locale('greeting_text', 'ru')
    label = await LeadMagnet.get_text_for_locale('lessons_label', 'ru')
    
    if not greeting or not label:
        print("❌ Failed to get lead magnet texts")
        return False
    
    print(f"✅ Greeting text: '{greeting}'")
    print(f"✅ Lessons label: '{label}'")
    
    print("✅ Lead magnet tests passed!")
    return True


def test_support_dashboard_builder():
    """Test that build_admin_support_dashboard exists"""
    print("\n🧪 Testing support dashboard builder...")
    
    try:
        from handlers.support import build_admin_support_dashboard
        print("✅ build_admin_support_dashboard function exists")
        return True
    except ImportError as e:
        print(f"❌ Cannot import build_admin_support_dashboard: {e}")
        return False


async def main():
    """Run all tests"""
    print("=" * 50)
    print("🔧 Running tests for bot fixes...")
    print("=" * 50)
    
    results = []
    
    # Test localization
    results.append(("Localization", test_localization()))
    
    # Test lead magnet
    results.append(("Lead Magnet", await test_lead_magnet()))
    
    # Test support dashboard
    results.append(("Support Dashboard", test_support_dashboard_builder()))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("\n🎉 All tests passed! The fixes are working correctly.")
        print("✅ All fixes tested and working correctly!")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
