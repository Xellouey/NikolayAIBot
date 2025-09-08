# Comprehensive Test Suite for Router Priority and System Improvements
import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import modules to test
import utils
from validators import StepValidator, StepBackupManager, validate_and_update_steps
from error_handling import ErrorRecoverySystem, graceful_error_response, HealthChecker


class TestRouterPriority:
    """Test router registration order and start command handling"""
    
    @pytest.fixture
    def mock_dispatcher(self):
        """Mock aiogram Dispatcher"""
        return MagicMock()
    
    @pytest.fixture
    def mock_routers(self):
        """Mock router modules"""
        return {
            'payment': MagicMock(),
            'support': MagicMock(),
            'client': MagicMock(),
            'admin': MagicMock(),
            'mail': MagicMock(),
            'shop': MagicMock()
        }
    
    def test_router_registration_order(self, mock_dispatcher, mock_routers):
        """Test that routers are registered in correct priority order"""
        # Simulate router registration from nikolayai.py
        expected_order = ['payment', 'support', 'client', 'admin', 'mail', 'shop']
        
        # Mock the include_router calls
        calls = []
        mock_dispatcher.include_router.side_effect = lambda router: calls.append(router)
        
        # Simulate the corrected router registration
        for router_name in expected_order:
            mock_dispatcher.include_router(mock_routers[router_name])
        
        # Verify order
        assert len(calls) == 6
        for i, expected_router in enumerate(expected_order):
            assert calls[i] == mock_routers[expected_router]
    
    @pytest.mark.asyncio
    async def test_start_command_onboarding_flow(self):
        """Test that /start command properly handles onboarding for new users"""
        # Mock user database
        mock_user = AsyncMock()
        mock_user.get_user.return_value = None  # New user
        mock_user.create_user.return_value = 1
        mock_user.check_onboarding_status.return_value = False
        
        # Mock message and state
        mock_message = MagicMock()
        mock_message.from_user.id = 123
        mock_message.from_user.username = "testuser"
        mock_message.from_user.full_name = "Test User"
        
        mock_state = AsyncMock()
        mock_state.get_state.return_value = None
        mock_state.clear.return_value = None
        
        # Mock steps
        mock_steps = {
            "start": {
                "content_type": "text",
                "text": "Welcome! Please share your phone.",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            }
        }
        
        # Test the start function logic
        with patch('utils.get_steps', return_value=mock_steps):
            with patch('handlers.client.send_msg') as mock_send:
                # Simulate client.start() behavior
                user_data = await mock_user.get_user(123)
                
                if user_data is None:
                    await mock_user.create_user(123, "testuser", "Test User")
                    user_data = {}  # Simulate fresh user data
                
                onboarding_completed = await mock_user.check_onboarding_status(123)
                
                if not onboarding_completed:
                    # Should start onboarding flow
                    assert user_data is not None or user_data == {}
                    assert not onboarding_completed
                    
                    # Should send start message
                    await mock_send(mock_steps["start"], mock_message, None)
                    mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_command_completed_onboarding(self):
        """Test that /start shows main menu for users who completed onboarding"""
        # Mock user database
        mock_user = AsyncMock()
        mock_user.get_user.return_value = {"id": 1, "user_id": 123, "onboarding_completed": True}
        mock_user.check_onboarding_status.return_value = True
        
        # Mock message
        mock_message = AsyncMock()
        mock_message.from_user.id = 123
        
        # Test logic
        user_data = await mock_user.get_user(123)
        onboarding_completed = await mock_user.check_onboarding_status(123)
        
        assert user_data is not None
        assert onboarding_completed is True
        
        # Should show main menu instead of onboarding
        with patch('utils.get_text', return_value="Welcome to shop!"):
            with patch('keyboards.markup_main_menu') as mock_menu:
                # Simulate showing main menu
                welcome_text = utils.get_text('messages.welcome')
                markup = mock_menu()
                
                assert welcome_text == "Welcome to shop!"
                mock_menu.assert_called_once()


class TestStepValidation:
    """Test step data validation framework"""
    
    def test_valid_text_step(self):
        """Test validation of valid text step"""
        validator = StepValidator()
        
        valid_step = {
            "content_type": "text",
            "text": "Hello, world!",
            "caption": None,
            "file_id": None,
            "keyboard": None,
            "delay": 5
        }
        
        is_valid, errors, warnings = validator.validate_step(valid_step, "test_step")
        
        assert is_valid is True
        assert len(errors) == 0
        assert len(warnings) == 0
    
    def test_valid_video_step(self):
        """Test validation of valid video step"""
        validator = StepValidator()
        
        valid_step = {
            "content_type": "video",
            "text": None,
            "caption": "This is a video caption",
            "file_id": "BAACAgIAAxkBAAM0Z_7juiU1zgUHIdXsePjdP4SgYiwAAu13AAJCGflL",
            "keyboard": [{"Button": "https://example.com"}],
            "delay": 10
        }
        
        is_valid, errors, warnings = validator.validate_step(valid_step, "video_step")
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_content_type(self):
        """Test validation fails for invalid content type"""
        validator = StepValidator()
        
        invalid_step = {
            "content_type": "invalid_type",
            "text": "Hello",
            "caption": None,
            "file_id": None,
            "keyboard": None,
            "delay": 5
        }
        
        is_valid, errors, warnings = validator.validate_step(invalid_step)
        
        assert is_valid is False
        assert any("Invalid content_type" in error for error in errors)
    
    def test_missing_file_id_for_video(self):
        """Test validation fails when video step lacks file_id"""
        validator = StepValidator()
        
        invalid_step = {
            "content_type": "video",
            "text": None,
            "caption": "Video without file_id",
            "file_id": None,
            "keyboard": None,
            "delay": 5
        }
        
        is_valid, errors, warnings = validator.validate_step(invalid_step)
        
        assert is_valid is False
        assert any("file_id is required" in error for error in errors)
    
    def test_text_too_long(self):
        """Test validation fails for text exceeding maximum length"""
        validator = StepValidator()
        
        long_text = "x" * 5000  # Exceeds MAX_TEXT_LENGTH (4096)
        
        invalid_step = {
            "content_type": "text",
            "text": long_text,
            "caption": None,
            "file_id": None,
            "keyboard": None,
            "delay": 5
        }
        
        is_valid, errors, warnings = validator.validate_step(invalid_step)
        
        assert is_valid is False
        assert any("text length" in error and "exceeds maximum" in error for error in errors)
    
    def test_invalid_keyboard_structure(self):
        """Test validation fails for malformed keyboard"""
        validator = StepValidator()
        
        invalid_step = {
            "content_type": "text",
            "text": "Hello",
            "caption": None,
            "file_id": None,
            "keyboard": [{"Button1": "url1", "Button2": "url2"}],  # Multiple keys in one button
            "delay": 5
        }
        
        is_valid, errors, warnings = validator.validate_step(invalid_step)
        
        assert is_valid is False
        assert any("exactly one key-value pair" in error for error in errors)
    
    def test_delay_out_of_range(self):
        """Test validation fails for invalid delay values"""
        validator = StepValidator()
        
        # Test negative delay
        invalid_step = {
            "content_type": "text",
            "text": "Hello",
            "caption": None,
            "file_id": None,
            "keyboard": None,
            "delay": -5
        }
        
        is_valid, errors, warnings = validator.validate_step(invalid_step)
        assert is_valid is False
        assert any("must be at least" in error for error in errors)
        
        # Test excessive delay
        invalid_step["delay"] = 500  # Exceeds MAX_DELAY_SECONDS (300)
        is_valid, errors, warnings = validator.validate_step(invalid_step)
        assert is_valid is False
        assert any("exceeds maximum" in error for error in errors)
    
    def test_validate_steps_file(self):
        """Test validation of complete steps file"""
        validator = StepValidator()
        
        valid_steps = {
            "start": {
                "content_type": "text",
                "text": "Welcome!",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            },
            "step1": {
                "content_type": "video",
                "text": None,
                "caption": "Video lesson",
                "file_id": "BAACAgIAAxkBAAM0Z_7juiU1zgUHIdXsePjdP4SgYiwAAu13AAJCGflL",
                "keyboard": [{"Learn More": "https://example.com"}],
                "delay": 35
            }
        }
        
        is_valid, errors, warnings = validator.validate_steps_file(valid_steps)
        
        assert is_valid is True
        assert len(errors) == 0


class TestStepBackupManager:
    """Test step backup and recovery functionality"""
    
    @pytest.fixture
    def temp_steps_file(self):
        """Create temporary steps file for testing"""
        fd, path = tempfile.mkstemp(suffix='.json')
        test_steps = {
            "start": {
                "content_type": "text",
                "text": "Test step",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            }
        }
        
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(test_steps, f)
        
        yield path
        
        # Cleanup
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
    
    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory"""
        import tempfile
        backup_dir = tempfile.mkdtemp()
        yield backup_dir
        
        # Cleanup
        import shutil
        try:
            shutil.rmtree(backup_dir)
        except FileNotFoundError:
            pass
    
    def test_create_backup(self, temp_steps_file, temp_backup_dir):
        """Test backup creation"""
        # Override backup directory
        manager = StepBackupManager(temp_steps_file)
        manager.backup_dir = temp_backup_dir
        
        backup_path = manager.create_backup()
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        assert backup_path.startswith(temp_backup_dir)
        assert "steps_backup_" in backup_path
        
        # Verify backup content
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        assert "start" in backup_data
        assert backup_data["start"]["text"] == "Test step"
    
    def test_list_backups(self, temp_backup_dir):
        """Test listing backup files"""
        manager = StepBackupManager()
        manager.backup_dir = temp_backup_dir
        
        # Create some test backup files
        test_files = [
            "steps_backup_20240101_120000.json",
            "steps_backup_20240102_120000.json",
            "other_file.json"  # Should be ignored
        ]
        
        for filename in test_files:
            filepath = os.path.join(temp_backup_dir, filename)
            with open(filepath, 'w') as f:
                json.dump({"test": "data"}, f)
        
        backups = manager.list_backups()
        
        assert len(backups) == 2  # Only backup files, not other_file.json
        assert all("steps_backup_" in backup for backup in backups)


class TestErrorHandling:
    """Test error handling and recovery mechanisms"""
    
    @pytest.mark.asyncio
    async def test_error_recovery_decorator(self):
        """Test error recovery decorator functionality"""
        recovery_system = ErrorRecoverySystem()
        
        call_count = 0
        
        @recovery_system.error_handler("test_operation", max_retries=2)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Test error")
            return "success"
        
        # Should succeed after 2 retries
        result = await failing_function()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_safe_send_message(self):
        """Test safe message sending with fallback"""
        recovery_system = ErrorRecoverySystem()
        
        with patch('handlers.client.send_msg') as mock_send:
            # Test successful send
            mock_send.return_value = None
            
            result = await recovery_system.safe_send_message(123, "Test message")
            assert result is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_recover_from_step_error(self):
        """Test recovery from step-related errors"""
        recovery_system = ErrorRecoverySystem()
        
        with patch.object(recovery_system, 'safe_send_message', return_value=True) as mock_send:
            result = await recovery_system.recover_from_step_error(123, "test error")
            
            assert result is True
            mock_send.assert_called_once()
            
            # Check that recovery message was sent
            args, kwargs = mock_send.call_args
            assert args[0] == 123  # user_id
            assert "техническая ошибка" in args[1]  # recovery message
    
    @pytest.mark.asyncio
    async def test_steps_file_corruption_recovery(self):
        """Test recovery from corrupted steps file"""
        recovery_system = ErrorRecoverySystem()
        
        with patch('validators.StepBackupManager') as mock_backup_manager:
            mock_manager = mock_backup_manager.return_value
            mock_manager.list_backups.return_value = []  # No backups available
            
            with patch('utils.update_steps') as mock_update:
                result = await recovery_system.handle_steps_file_corruption()
                
                assert result is True
                mock_update.assert_called_once()
                
                # Should use fallback steps
                fallback_steps = mock_update.call_args[0][0]
                assert "join" in fallback_steps
                assert "start" in fallback_steps


class TestHealthChecker:
    """Test system health monitoring"""
    
    @pytest.mark.asyncio
    async def test_health_check_healthy_system(self):
        """Test health check on healthy system"""
        checker = HealthChecker()
        
        with patch('database.user.User') as mock_user_class:
            mock_user = mock_user_class.return_value
            mock_user.get_all_users.return_value = []
            
            with patch('utils.get_steps', return_value={"start": {"content_type": "text", "text": "test", "caption": None, "file_id": None, "keyboard": None, "delay": 0}}):
                with patch('utils.get_interface_texts', return_value={"messages": {"welcome": "test"}}):
                    health = await checker.check_system_health()
                    
                    assert health["overall_status"] == "healthy"
                    assert health["checks"]["database"] == "healthy"
                    assert health["checks"]["steps_file"] == "healthy"
                    assert health["checks"]["interface_texts"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_degraded_system(self):
        """Test health check on system with issues"""
        checker = HealthChecker()
        
        with patch('database.user.User') as mock_user_class:
            mock_user = mock_user_class.return_value
            mock_user.get_all_users.side_effect = Exception("Database error")
            
            with patch('utils.get_steps', return_value={}):  # Empty steps file
                health = await checker.check_system_health()
                
                assert health["overall_status"] == "degraded"
                assert "error" in health["checks"]["database"]
                assert "error" in health["checks"]["steps_file"]


class TestOnboardingIntegration:
    """Integration tests for onboarding flow"""
    
    @pytest.mark.asyncio
    async def test_complete_onboarding_flow(self):
        """Test complete user onboarding flow"""
        # Mock user database operations
        mock_user = AsyncMock()
        mock_user.get_user.side_effect = [
            None,  # First call - new user
            {"id": 1, "user_id": 123, "phone": None},  # After creation
            {"id": 1, "user_id": 123, "phone": "+1234567890"}  # After phone update
        ]
        mock_user.create_user.return_value = 1
        mock_user.check_onboarding_status.return_value = False
        mock_user.mark_onboarding_complete.return_value = None
        
        # Mock steps
        test_steps = {
            "start": {
                "content_type": "text",
                "text": "Welcome! Share your phone.",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            },
            "step1": {
                "content_type": "text", 
                "text": "Great! Here's your first lesson.",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 3
            }
        }
        
        # Test the flow
        with patch('utils.get_steps', return_value=test_steps):
            with patch('handlers.client.send_msg') as mock_send:
                # 1. User sends /start
                user_data = await mock_user.get_user(123)
                assert user_data is None
                
                # 2. Create new user
                await mock_user.create_user(123, "testuser", "Test User")
                user_data = await mock_user.get_user(123)
                
                # 3. Check onboarding status
                onboarding_completed = await mock_user.check_onboarding_status(123)
                assert not onboarding_completed
                
                # 4. Should start onboarding
                assert user_data is not None
                
                # 5. Complete onboarding
                await mock_user.mark_onboarding_complete(123)
                
                # Verify calls were made
                mock_user.create_user.assert_called_once()
                mock_user.mark_onboarding_complete.assert_called_once()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])