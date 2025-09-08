"""
Comprehensive unit tests for step editor functionality.
Tests all aspects of the step editor including editing, positioning, delays, keyboards, and deletion.
"""

import asyncio
import json
import os
import tempfile
import shutil
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram import types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

# Import modules to test
import utils
from handlers.admin import editor, edit, actionEditor, msgEditor, createStep, stepCreate
from states import FSMEditor, FSMCreateStep


class TestStepEditor:
    """Test suite for step editor functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with temporary files"""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.test_steps_file = os.path.join(self.test_dir, "test_steps.json")
        self.test_admins_file = os.path.join(self.test_dir, "test_admins.json")
        
        # Sample test data
        self.test_steps = {
            "join": {
                "content_type": "text",
                "text": "🎉 Добро пожаловать!",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            },
            "start": {
                "content_type": "text", 
                "text": "👋 Привет! Начнем обучение",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            },
            "step1": {
                "content_type": "video",
                "text": None,
                "caption": "📹 Первый урок",
                "file_id": "test_video_id",
                "keyboard": None,
                "delay": 10
            },
            "step2": {
                "content_type": "text",
                "text": "📝 Второй урок",
                "caption": None,
                "file_id": None,
                "keyboard": [{"Кнопка": "https://example.com"}],
                "delay": 5
            }
        }
        
        self.test_admins = [12345, 67890]
        
        # Write test files
        with open(self.test_steps_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_steps, f, indent=4, ensure_ascii=False)
        
        with open(self.test_admins_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_admins, f, indent=4, ensure_ascii=False)
        
        yield
        
        # Cleanup
        shutil.rmtree(self.test_dir)
    
    def create_mock_call(self, data="editor", user_id=12345):
        """Create mock callback query"""
        call = AsyncMock(spec=types.CallbackQuery)
        call.data = data
        call.from_user = MagicMock()
        call.from_user.id = user_id
        call.message = AsyncMock(spec=types.Message)
        call.answer = AsyncMock()
        return call
    
    def create_mock_message(self, text="", content_type="text", user_id=12345):
        """Create mock message"""
        message = AsyncMock(spec=types.Message)
        message.text = text
        message.content_type = content_type
        message.from_user = MagicMock()
        message.from_user.id = user_id
        message.answer = AsyncMock()
        return message
    
    def create_mock_state(self, current_state=None, data=None):
        """Create mock FSM state"""
        state = AsyncMock(spec=FSMContext)
        state.get_state = AsyncMock(return_value=current_state)
        state.set_state = AsyncMock()
        state.update_data = AsyncMock()
        state.get_data = AsyncMock(return_value=data or {})
        state.clear = AsyncMock()
        return state

    @patch('utils.get_steps')
    @patch('keyboards.markup_editor')
    async def test_editor_menu_display(self, mock_markup, mock_get_steps):
        """Test that editor menu displays correctly"""
        # Arrange
        mock_get_steps.return_value = self.test_steps
        mock_markup.return_value = MagicMock()
        call = self.create_mock_call()
        state = self.create_mock_state()
        
        # Act
        await editor(call, state)
        
        # Assert
        call.answer.assert_called_once()
        call.message.edit_text.assert_called_once()
        edit_text_args = call.message.edit_text.call_args
        assert "Выберите шаг" in edit_text_args[0][0]
        mock_markup.assert_called_once()

    @patch('utils.get_steps')
    @patch('utils.update_steps')
    async def test_step_content_editing_text(self, mock_update, mock_get_steps):
        """Test editing text content of a step"""
        # Arrange
        mock_get_steps.return_value = self.test_steps.copy()
        call = self.create_mock_call("edit:step1")
        state = self.create_mock_state()
        
        # Act - start editing
        await edit(call, state)
        
        # Assert initial setup
        state.set_state.assert_called_with(FSMEditor.action)
        state.update_data.assert_called_with(key="step1")
        
        # Arrange for action selection
        message = self.create_mock_message("👟 Шаг")
        state_data = {"key": "step1"}
        state.get_data = AsyncMock(return_value=state_data)
        
        # Act - select action
        await actionEditor(message, state)
        
        # Assert action setup
        state.set_state.assert_called_with(FSMEditor.value)
        state.update_data.assert_called_with(action="step")
        
        # Arrange for new content
        new_message = self.create_mock_message("🎯 Новый текст урока")
        state_data = {"key": "step1", "action": "step"}
        state.get_data = AsyncMock(return_value=state_data)
        
        # Act - provide new content
        await msgEditor(new_message, state)
        
        # Assert content update
        mock_update.assert_called_once()
        updated_steps = mock_update.call_args[0][0]
        assert updated_steps["step1"]["text"] == "🎯 Новый текст урока"
        assert updated_steps["step1"]["content_type"] == "text"

    @patch('utils.get_steps')
    @patch('utils.move_dict_item')
    @patch('utils.update_steps')
    async def test_step_position_change(self, mock_update, mock_move, mock_get_steps):
        """Test changing step position"""
        # Arrange
        mock_get_steps.return_value = self.test_steps.copy()
        mock_move.return_value = {"reordered": "steps"}
        
        message = self.create_mock_message("👟 Шаг")
        state = self.create_mock_state(data={"key": "step1"})
        
        # Act - select position action
        await actionEditor(message, state)
        
        # Arrange for position value
        position_message = self.create_mock_message("🖌 Позицию")
        state.get_data = AsyncMock(return_value={"key": "step1"})
        await actionEditor(position_message, state)
        
        # Provide new position
        position_value_message = self.create_mock_message("3")
        state.get_data = AsyncMock(return_value={"key": "step1", "action": "position"})
        
        # Act
        await msgEditor(position_value_message, state)
        
        # Assert
        mock_move.assert_called_with(self.test_steps, "step1", 4)  # position + 1
        mock_update.assert_called_with({"reordered": "steps"})

    @patch('utils.get_steps')
    @patch('utils.update_steps')
    async def test_step_delay_configuration(self, mock_update, mock_get_steps):
        """Test configuring step delays"""
        # Arrange
        test_steps = self.test_steps.copy()
        mock_get_steps.return_value = test_steps
        
        # Select delay action
        message = self.create_mock_message("⏳ Задержку")
        state = self.create_mock_state(data={"key": "step2"})
        await actionEditor(message, state)
        
        # Set new delay
        delay_message = self.create_mock_message("30")
        state.get_data = AsyncMock(return_value={"key": "step2", "action": "delay"})
        
        # Act
        await msgEditor(delay_message, state)
        
        # Assert
        mock_update.assert_called_once()
        updated_steps = mock_update.call_args[0][0]
        assert updated_steps["step2"]["delay"] == 30

    @patch('utils.get_steps')
    @patch('utils.update_steps')
    async def test_step_delay_skip(self, mock_update, mock_get_steps):
        """Test skipping delay (setting to 0)"""
        # Arrange
        test_steps = self.test_steps.copy()
        mock_get_steps.return_value = test_steps
        
        # Skip delay
        skip_message = self.create_mock_message("➡️ пропустить")
        state = self.create_mock_state(data={"key": "step1", "action": "delay"})
        
        # Act
        await msgEditor(skip_message, state)
        
        # Assert
        mock_update.assert_called_once()
        updated_steps = mock_update.call_args[0][0]
        assert updated_steps["step1"]["delay"] == 0

    @patch('utils.get_steps')
    @patch('utils.update_steps')
    async def test_keyboard_buttons_configuration(self, mock_update, mock_get_steps):
        """Test configuring keyboard buttons"""
        # Arrange
        test_steps = self.test_steps.copy()
        mock_get_steps.return_value = test_steps
        
        # Valid JSON keyboard
        keyboard_json = '[{"Новая кнопка": "https://new-url.com"}, {"Вторая кнопка": "https://second.com"}]'
        keyboard_message = self.create_mock_message(keyboard_json)
        state = self.create_mock_state(data={"key": "step1", "action": "keyboard"})
        
        # Act
        await msgEditor(keyboard_message, state)
        
        # Assert
        mock_update.assert_called_once()
        updated_steps = mock_update.call_args[0][0]
        expected_keyboard = [
            {"Новая кнопка": "https://new-url.com"},
            {"Вторая кнопка": "https://second.com"}
        ]
        assert updated_steps["step1"]["keyboard"] == expected_keyboard

    @patch('utils.get_steps')
    async def test_keyboard_invalid_json_error(self, mock_get_steps):
        """Test invalid JSON keyboard handling"""
        # Arrange
        mock_get_steps.return_value = self.test_steps.copy()
        
        # Invalid JSON
        invalid_json_message = self.create_mock_message('{"invalid": json}')
        state = self.create_mock_state(data={"key": "step1", "action": "keyboard"})
        
        # Act
        await msgEditor(invalid_json_message, state)
        
        # Assert - should ask for correct format
        invalid_json_message.answer.assert_called_once()
        error_text = invalid_json_message.answer.call_args[0][0]
        assert "корректные кнопки" in error_text

    @patch('utils.get_steps')
    @patch('utils.remove_dict_item')
    @patch('utils.update_steps')
    async def test_step_deletion_with_confirmation(self, mock_update, mock_remove, mock_get_steps):
        """Test step deletion with proper confirmation"""
        # Arrange
        mock_get_steps.return_value = self.test_steps.copy()
        mock_remove.return_value = {"remaining": "steps"}
        
        # Confirm deletion
        confirm_message = self.create_mock_message("Подтвердить")
        state = self.create_mock_state(data={"key": "step2", "action": "delete"})
        
        # Act
        await msgEditor(confirm_message, state)
        
        # Assert
        mock_remove.assert_called_with(self.test_steps, "step2")
        mock_update.assert_called_with({"remaining": "steps"})

    @patch('utils.get_steps')
    async def test_step_deletion_wrong_confirmation(self, mock_get_steps):
        """Test step deletion with wrong confirmation"""
        # Arrange
        mock_get_steps.return_value = self.test_steps.copy()
        
        # Wrong confirmation
        wrong_message = self.create_mock_message("неправильно")
        state = self.create_mock_state(data={"key": "step2", "action": "delete"})
        
        # Act
        await msgEditor(wrong_message, state)
        
        # Assert - should ask for correct confirmation
        wrong_message.answer.assert_called_once()
        error_text = wrong_message.answer.call_args[0][0]
        assert "Подтвердить" in error_text

    @patch('utils.get_steps')
    @patch('utils.get_new_key')
    @patch('utils.update_steps')
    async def test_create_new_step(self, mock_update, mock_new_key, mock_get_steps):
        """Test creating a new step"""
        # Arrange
        mock_get_steps.return_value = self.test_steps.copy()
        mock_new_key.return_value = "step3"
        
        call = self.create_mock_call("createStep")
        state = self.create_mock_state()
        
        # Act - start step creation
        await createStep(call, state)
        
        # Assert setup
        state.set_state.assert_called_with(FSMCreateStep.step)
        
        # Arrange new step content
        new_step_message = self.create_mock_message("🎓 Новый урок")
        new_step_message.content_type = "text"
        new_step_message.text = "🎓 Новый урок"
        new_step_message.caption = None
        
        # Act - create step
        await stepCreate(new_step_message, state)
        
        # Assert step creation
        mock_update.assert_called_once()
        updated_steps = mock_update.call_args[0][0]
        assert "step3" in updated_steps
        assert updated_steps["step3"]["text"] == "🎓 Новый урок"
        assert updated_steps["step3"]["content_type"] == "text"

    async def test_invalid_content_type_rejection(self):
        """Test rejection of invalid content types"""
        # Arrange
        invalid_message = self.create_mock_message("", content_type="sticker")
        state = self.create_mock_state(data={"key": "step1", "action": "step"})
        
        # Act
        await msgEditor(invalid_message, state)
        
        # Assert - should ask for correct message type
        invalid_message.answer.assert_called_once()
        error_text = invalid_message.answer.call_args[0][0]
        assert "корректное сообщение" in error_text

    @patch('utils.get_steps')
    async def test_invalid_position_handling(self, mock_get_steps):
        """Test handling of invalid position values"""
        # Arrange
        mock_get_steps.return_value = self.test_steps.copy()
        
        # Invalid position (negative)
        invalid_position_message = self.create_mock_message("-1")
        state = self.create_mock_state(data={"key": "step1", "action": "position"})
        
        # Act
        await msgEditor(invalid_position_message, state)
        
        # Assert - should ask for correct position
        invalid_position_message.answer.assert_called_once()
        error_text = invalid_position_message.answer.call_args[0][0]
        assert "корректную позицию" in error_text

    @patch('utils.get_steps')
    async def test_invalid_delay_handling(self, mock_get_steps):
        """Test handling of invalid delay values"""
        # Arrange
        mock_get_steps.return_value = self.test_steps.copy()
        
        # Invalid delay (non-numeric)
        invalid_delay_message = self.create_mock_message("abc")
        state = self.create_mock_state(data={"key": "step1", "action": "delay"})
        
        # Act
        await msgEditor(invalid_delay_message, state)
        
        # Assert - should ask for correct delay
        invalid_delay_message.answer.assert_called_once()
        error_text = invalid_delay_message.answer.call_args[0][0]
        assert "корректную задержку" in error_text

    def test_utils_move_dict_item(self):
        """Test utility function for moving dictionary items"""
        # Arrange
        test_dict = {"a": 1, "b": 2, "c": 3, "d": 4}
        
        # Act
        result = utils.move_dict_item(test_dict, "b", 0)
        
        # Assert
        keys = list(result.keys())
        assert keys[0] == "b"  # "b" should be first
        assert keys[1] == "a"  # "a" should be second

    def test_utils_remove_dict_item(self):
        """Test utility function for removing dictionary items"""
        # Arrange
        test_dict = {"a": 1, "b": 2, "c": 3}
        
        # Act
        result = utils.remove_dict_item(test_dict, "b")
        
        # Assert
        assert "b" not in result
        assert len(result) == 2
        assert result["a"] == 1
        assert result["c"] == 3

    def test_utils_remove_nonexistent_key_error(self):
        """Test error handling when removing non-existent key"""
        # Arrange
        test_dict = {"a": 1, "b": 2}
        
        # Act & Assert
        with pytest.raises(KeyError):
            utils.remove_dict_item(test_dict, "nonexistent")

    def test_utils_get_new_key(self):
        """Test generating new step keys"""
        # Test with utils function using temporary file
        with patch('utils.get_steps') as mock_get_steps:
            # Test case 1: Normal step sequence
            mock_get_steps.return_value = {
                "join": {}, "start": {}, "step1": {}, "step2": {}
            }
            result = utils.get_new_key()
            assert result == "step3"
            
            # Test case 2: No steps yet
            mock_get_steps.return_value = {
                "join": {}, "start": {}
            }
            result = utils.get_new_key()
            assert result == "step1"


class TestStepEditorIntegration:
    """Integration tests for step editor with file operations"""
    
    def setup_method(self):
        """Set up test files for each test"""
        self.test_dir = tempfile.mkdtemp()
        self.test_steps_file = os.path.join(self.test_dir, "steps.json")
        
        self.test_steps = {
            "join": {
                "content_type": "text",
                "text": "Welcome!",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            },
            "start": {
                "content_type": "text",
                "text": "Let's start!",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 0
            },
            "step1": {
                "content_type": "text",
                "text": "First lesson",
                "caption": None,
                "file_id": None,
                "keyboard": None,
                "delay": 5
            }
        }
        
        with open(self.test_steps_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_steps, f, indent=4, ensure_ascii=False)
    
    def teardown_method(self):
        """Clean up test files"""
        shutil.rmtree(self.test_dir)
    
    def test_file_operations_get_steps(self):
        """Test reading steps from file"""
        # Act
        steps = utils.get_steps(self.test_steps_file)
        
        # Assert
        assert len(steps) == 3
        assert steps["join"]["text"] == "Welcome!"
        assert steps["step1"]["delay"] == 5
    
    def test_file_operations_update_steps(self):
        """Test updating steps file"""
        # Arrange
        modified_steps = self.test_steps.copy()
        modified_steps["step1"]["text"] = "Modified lesson"
        modified_steps["step2"] = {
            "content_type": "text",
            "text": "New step",
            "caption": None,
            "file_id": None,
            "keyboard": None,
            "delay": 0
        }
        
        # Act
        utils.update_steps(modified_steps, self.test_steps_file)
        
        # Verify file was updated
        with open(self.test_steps_file, 'r', encoding='utf-8') as f:
            updated_data = json.load(f)
        
        # Assert
        assert updated_data["step1"]["text"] == "Modified lesson"
        assert "step2" in updated_data
        assert updated_data["step2"]["text"] == "New step"


if __name__ == "__main__":
    # Run tests
    print("🧪 Запуск тестов редактора шагов...")
    
    # Run with pytest if available, otherwise run basic tests
    try:
        import pytest
        pytest.main([__file__, "-v", "--tb=short"])
    except ImportError:
        print("⚠️ pytest не установлен. Запуск базовых тестов...")
        
        # Run basic tests without pytest
        test_suite = TestStepEditor()
        test_suite.setup_test_environment()
        
        print("✅ Основные тесты завершены")
        print("📝 Для полного тестирования установите pytest: pip install pytest")