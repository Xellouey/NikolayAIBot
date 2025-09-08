# Simple Integration Test Runner
import sys
import os
import asyncio
import json
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all new modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import utils
        print("✅ utils module imported successfully")
    except Exception as e:
        print(f"❌ Failed to import utils: {e}")
        return False
    
    try:
        import validators
        print("✅ validators module imported successfully")
    except Exception as e:
        print(f"❌ Failed to import validators: {e}")
        return False
    
    try:
        import error_handling
        print("✅ error_handling module imported successfully")
    except Exception as e:
        print(f"❌ Failed to import error_handling: {e}")
        return False
    
    return True

def test_step_validation():
    """Test step validation functionality"""
    print("🧪 Testing step validation...")
    
    try:
        from validators import StepValidator
        
        validator = StepValidator()
        
        # Test valid step
        valid_step = {
            "content_type": "text",
            "text": "Hello, world!",
            "caption": None,
            "file_id": None,
            "keyboard": None,
            "delay": 5
        }
        
        is_valid, errors, warnings = validator.validate_step(valid_step, "test_step")
        
        if is_valid and len(errors) == 0:
            print("✅ Step validation working correctly")
            return True
        else:
            print(f"❌ Step validation failed: {errors}")
            return False
            
    except Exception as e:
        print(f"❌ Step validation test failed: {e}")
        return False

def test_error_recovery():
    """Test error recovery system"""
    print("🧪 Testing error recovery system...")
    
    try:
        from error_handling import ErrorRecoverySystem
        
        recovery = ErrorRecoverySystem()
        
        # Test error statistics
        stats = recovery.get_error_stats()
        
        if isinstance(stats, dict) and "error_counts" in stats:
            print("✅ Error recovery system working correctly")
            return True
        else:
            print(f"❌ Error recovery system failed: Invalid stats format")
            return False
            
    except Exception as e:
        print(f"❌ Error recovery test failed: {e}")
        return False

async def test_database_fields():
    """Test that new database fields can be accessed"""
    print("🧪 Testing database field additions...")
    
    try:
        from database.user import User
        
        # Check if new fields exist in the model
        user_model = User()
        
        # These fields should be available in the model
        required_fields = ['onboarding_completed', 'last_onboarding_step', 'onboarding_completed_at']
        
        model_fields = [field.name for field in User._meta.fields.values()]
        
        missing_fields = [field for field in required_fields if field not in model_fields]
        
        if not missing_fields:
            print("✅ Database fields added successfully")
            return True
        else:
            print(f"❌ Missing database fields: {missing_fields}")
            return False
            
    except Exception as e:
        print(f"❌ Database field test failed: {e}")
        return False

def test_router_order_fix():
    """Test that router order has been corrected"""
    print("🧪 Testing router order fix...")
    
    try:
        # Read the nikolayai.py file to check router order
        with open("nikolayai.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that client.router comes before shop.shop_router
        client_pos = content.find("dp.include_router(client.router)")
        shop_pos = content.find("dp.include_router(shop.shop_router)")
        
        if client_pos != -1 and shop_pos != -1 and client_pos < shop_pos:
            print("✅ Router order corrected successfully")
            return True
        else:
            print(f"❌ Router order not corrected (client: {client_pos}, shop: {shop_pos})")
            return False
            
    except Exception as e:
        print(f"❌ Router order test failed: {e}")
        return False

def test_shop_start_handler_removal():
    """Test that conflicting shop start handler was removed"""
    print("🧪 Testing shop start handler removal...")
    
    try:
        # Read the shop.py file to check handler removal
        with open("handlers/shop.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that the conflicting handler is removed
        if "@shop_router.message(CommandStart())" not in content:
            print("✅ Shop start handler removed successfully")
            return True
        else:
            print("❌ Shop start handler still exists")
            return False
            
    except Exception as e:
        print(f"❌ Shop handler test failed: {e}")
        return False

def test_steps_file_integrity():
    """Test that steps.json file is valid"""
    print("🧪 Testing steps file integrity...")
    
    try:
        import utils
        
        steps = utils.get_steps()
        
        if steps and isinstance(steps, dict):
            print(f"✅ Steps file loaded successfully ({len(steps)} steps)")
            return True
        else:
            print("❌ Steps file is empty or invalid")
            return False
            
    except Exception as e:
        print(f"❌ Steps file test failed: {e}")
        return False

async def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting Router Conflict Resolution Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Step Validation", test_step_validation),
        ("Error Recovery", test_error_recovery),
        ("Database Fields", test_database_fields),
        ("Router Order Fix", test_router_order_fix),
        ("Shop Handler Removal", test_shop_start_handler_removal),
        ("Steps File Integrity", test_steps_file_integrity)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Router conflict resolution implementation is successful.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_integration_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Critical error during testing: {e}")
        exit(1)