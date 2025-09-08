import unittest
import json
from unittest.mock import patch, MagicMock
import logging
import utils

class TestInterfaceTextsValidation(unittest.TestCase):
    def setUp(self):
        # Suppress logging during tests
        logging.getLogger().setLevel(logging.CRITICAL)

    def test_valid_json(self):
        """Test with valid JSON where all values are strings"""
        valid_data = {
            "buttons": {"back": "🔙 Назад"},
            "messages": {"welcome": "Добро пожаловать!"}
        }
        
        with patch('builtins.open', new_callable=MagicMock) as mock_open:
            mock_file = MagicMock()
            mock_file.__enter__.return_value.read.return_value = '{"buttons": {"back": "🔙 Назад"}, "messages": {"welcome": "Добро пожаловать!"}}'
            mock_open.return_value.__enter__.return_value = mock_file
            
            with patch('json.load', return_value=valid_data):
                result = utils.get_interface_texts()
                self.assertEqual(result, valid_data)

    def test_invalid_non_string_value(self):
        """Test with JSON containing non-string value, should log error and return fallback"""
        invalid_data = {
            "buttons": {"back": "🔙 Назад"},
            "messages": {"welcome": {"not_a_string": "dict"}}
        }
        
        with patch('json.load', return_value=invalid_data):
            with self.assertLogs('root', level='ERROR') as log:
                result = utils.get_interface_texts()
                self.assertIn("Invalid type", log.output[0])
                self.assertEqual(result, {
                    "buttons": {"back": "🔙 Назад"},
                    "messages": {"welcome": "Добро пожаловать!"},
                    "admin": {"messages": {"lesson_management": "Управление уроками"}}
                })

    def test_fallback_on_json_decode_error(self):
        """Test fallback on JSON decode error"""
        with patch('builtins.open', new_callable=MagicMock) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            with patch('json.load', side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
                with self.assertLogs('root', level='ERROR') as log:
                    result = utils.get_interface_texts()
                    self.assertIn("JSON decode error", log.output[0])
                    self.assertEqual(result, {
                        "buttons": {"back": "🔙 Назад"},
                        "messages": {"welcome": "Добро пожаловать!"},
                        "admin": {"messages": {"lesson_management": "Управление уроками"}}
                    })

    def test_fallback_on_file_not_found(self):
        """Test fallback on file not found"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            with self.assertLogs('root', level='WARNING') as log:
                result = utils.get_interface_texts()
                self.assertIn("file not found", log.output[0])
                self.assertEqual(result, {
                    "buttons": {"back": "🔙 Назад"},
                    "messages": {"welcome": "Добро пожаловать!"},
                    "admin": {"messages": {"lesson_management": "Управление уроками"}}
                })

if __name__ == '__main__':
    unittest.main()