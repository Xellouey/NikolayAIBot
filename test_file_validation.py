"""
🧪 Test Enhanced File Validation System
Tests the new file_id validation and error handling system
"""

import asyncio
import sys
import os

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from error_handling import validate_telegram_file_id, TelegramErrorHandler
from handlers.client import validate_file_id

async def test_file_validation_system():
    """Test the enhanced file validation system"""
    print("🧪 Testing Enhanced File Validation System...")
    
    # Test 1: Valid file_id validation
    print("\n1️⃣ Testing valid file_id validation...")
    
    valid_file_ids = [
        "BAADBAADqwADBRMAAf8j09n1i5GmFgQ",  # Typical Telegram file_id
        "AwACAgIAAxkDAAICPGdCYi9w8i8jdh8j3hd93jfDjgAB",  # Another format
        "CAADBAADqwADBRMAAf8j09n1i5GmFgQ123456789"  # Long format
    ]
    
    for file_id in valid_file_ids:
        result = validate_telegram_file_id(file_id)
        assert result == True, f"Expected True for valid file_id: {file_id}"
        
        result2 = validate_file_id(file_id, "video")
        assert result2 == True, f"Expected True for valid file_id in validate_file_id: {file_id}"
    
    print("✅ Valid file_id validation working correctly")
    
    # Test 2: Invalid file_id validation  
    print("\n2️⃣ Testing invalid file_id validation...")
    
    invalid_file_ids = [
        None,
        "",
        "None",
        "null", 
        "undefined",
        "false",
        "0",
        "short",  # Too short
        "123",    # Numbers only and too short
    ]
    
    for file_id in invalid_file_ids:
        result = validate_telegram_file_id(file_id)
        assert result == False, f"Expected False for invalid file_id: {file_id}"
        
        result2 = validate_file_id(file_id, "video") 
        assert result2 == False, f"Expected False for invalid file_id in validate_file_id: {file_id}"
    
    print("✅ Invalid file_id validation working correctly")
    
    # Test 3: TelegramErrorHandler classification
    print("\n3️⃣ Testing TelegramErrorHandler error classification...")
    
    # File identifier error
    file_error = Exception("Telegram server says - Bad Request: wrong file identifier/HTTP URL specified")
    file_result = await TelegramErrorHandler.handle_telegram_error(file_error)
    assert file_result['error_type'] == 'file_error'
    assert file_result['action'] == 'use_fallback'
    print("✅ File identifier error classification working")
    
    # Rate limit error
    rate_error = Exception("Too many requests: retry after 30")
    rate_result = await TelegramErrorHandler.handle_telegram_error(rate_error)
    assert rate_result['error_type'] == 'rate_limit'
    assert rate_result['action'] == 'retry_later'
    print("✅ Rate limit error classification working")
    
    # Network error
    network_error = Exception("Connection timeout occurred")
    network_result = await TelegramErrorHandler.handle_telegram_error(network_error)
    assert network_result['error_type'] == 'network_error'
    assert network_result['action'] == 'retry'
    print("✅ Network error classification working")
    
    # Unknown error
    unknown_error = Exception("Some random error")
    unknown_result = await TelegramErrorHandler.handle_telegram_error(unknown_error)
    assert unknown_result['error_type'] == 'unknown'
    assert unknown_result['action'] == 'generic_fallback'
    print("✅ Unknown error classification working")
    
    print("\n🎯 All file validation tests passed successfully!")
    print("💡 Enhanced file validation system is working correctly")
    print("🛡️ Bot should no longer experience file identifier errors")

if __name__ == '__main__':
    asyncio.run(test_file_validation_system())