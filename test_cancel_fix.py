#!/usr/bin/env python3
"""Test that cancel in support returns users to main menu, not admin panel"""
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from aiogram import types
from aiogram.fsm.context import FSMContext
from handlers.support import cancel_support_inline

async def test_cancel_returns_to_main_menu():
    """Test that regular users return to main menu when canceling ticket creation"""
    
    # Mock user (not admin)
    mock_user = Mock()
    mock_user.id = 123456  # Regular user ID
    
    # Mock callback query
    mock_call = Mock(spec=types.CallbackQuery)
    mock_call.from_user = mock_user
    mock_call.answer = AsyncMock()
    mock_call.message = Mock()
    mock_call.message.edit_text = AsyncMock()
    
    # Mock FSM state
    mock_state = Mock(spec=FSMContext)
    mock_state.get_state = AsyncMock(return_value='FSMSupport:waiting_subject')
    mock_state.clear = AsyncMock()
    
    # Mock config and utils to ensure user is NOT admin
    with patch('handlers.support.config.ADMINS', [999999]):  # Different ID
        with patch('handlers.support.utils.get_admins', return_value=[]):
            # Call the handler
            await cancel_support_inline(mock_call, mock_state)
    
    # Verify state was cleared
    mock_state.clear.assert_called_once()
    
    # Verify answer was called
    mock_call.answer.assert_called_once_with("❌ Отменено")
    
    # Verify message was edited
    mock_call.message.edit_text.assert_called_once()
    
    # Get the actual call arguments
    call_args = mock_call.message.edit_text.call_args
    text_arg = call_args[0][0] if call_args[0] else call_args.kwargs.get('text', '')
    
    # Check that it's NOT the admin panel
    assert 'Панель поддержки' not in text_arg, f"User should not see admin panel! Got: {text_arg}"
    
    # It should be the welcome message
    print(f"✅ Text shown to user: {text_arg[:50]}...")
    
    # Check the keyboard
    markup_arg = call_args.kwargs.get('reply_markup')
    if markup_arg:
        markup_str = str(markup_arg)
        # Should have main menu buttons, not support dashboard
        assert 'catalog' in markup_str or 'my_lessons' in markup_str, "Should show main menu"
        assert 'tickets_open' not in markup_str, "Should NOT show admin tickets"
    
    print("✅ Test passed: Regular users return to main menu on cancel")
    return True


async def test_admin_gets_dashboard():
    """Test that admins get dashboard when canceling"""
    
    # Mock admin user
    mock_admin = Mock()
    mock_admin.id = 999999  # Admin ID
    
    # Mock callback query
    mock_call = Mock(spec=types.CallbackQuery)
    mock_call.from_user = mock_admin
    mock_call.answer = AsyncMock()
    mock_call.message = Mock()
    mock_call.message.edit_text = AsyncMock()
    
    # Mock FSM state
    mock_state = Mock(spec=FSMContext)
    mock_state.get_state = AsyncMock(return_value='FSMSupport:admin_responding')
    mock_state.clear = AsyncMock()
    
    # Mock support_ticket for dashboard
    with patch('handlers.support.support_ticket') as mock_ticket:
        mock_ticket.get_tickets_count_by_status = AsyncMock(return_value={
            'total': 5, 'open': 2, 'in_progress': 2, 'closed': 1
        })
        
        # Mock config to make user admin
        with patch('handlers.support.config.ADMINS', [999999]):
            # Call the handler
            await cancel_support_inline(mock_call, mock_state)
    
    # Get the actual call arguments
    call_args = mock_call.message.edit_text.call_args
    text_arg = call_args[0][0] if call_args[0] else call_args.kwargs.get('text', '')
    
    # Admin should see the dashboard
    assert 'Панель поддержки' in text_arg or 'total' in text_arg or '5' in text_arg, \
        f"Admin should see dashboard! Got: {text_arg[:100]}..."
    
    print("✅ Test passed: Admins get dashboard on cancel")
    return True


async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Testing Cancel Fix: Users → Main Menu, Not Admin Panel")
    print("=" * 60)
    
    results = []
    
    # Test 1: Regular user cancels
    try:
        result = await test_cancel_returns_to_main_menu()
        results.append(("Regular user → Main menu", result))
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        results.append(("Regular user → Main menu", False))
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        results.append(("Regular user → Main menu", False))
    
    # Test 2: Admin cancels
    try:
        result = await test_admin_gets_dashboard()
        results.append(("Admin → Dashboard", result))
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        results.append(("Admin → Dashboard", False))
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        results.append(("Admin → Dashboard", False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ FIX VERIFIED: Regular users now return to main menu!")
    else:
        print("\n❌ Some tests failed. Please review the implementation.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
