# Step Data Validation Framework
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StepValidationError(Exception):
    """Custom exception for step validation errors"""
    pass


class StepValidator:
    """Comprehensive step data validation framework"""
    
    VALID_CONTENT_TYPES = {'text', 'photo', 'video', 'audio', 'document', 'animation', 'voice', 'video_note'}
    MAX_TEXT_LENGTH = 4096
    MAX_CAPTION_LENGTH = 1024
    MAX_DELAY_SECONDS = 300
    MIN_DELAY_SECONDS = 0
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_step(self, step_data: Dict[str, Any], step_key: str = None) -> Tuple[bool, List[str], List[str]]:
        """
        Validate a single step data structure
        
        Args:
            step_data: Dictionary containing step information
            step_key: Optional step key for context in error messages
            
        Returns:
            Tuple of (is_valid, error_list, warning_list)
        """
        self.errors = []
        self.warnings = []
        
        context = f"Step '{step_key}'" if step_key else "Step"
        
        # Check required fields
        self._validate_required_fields(step_data, context)
        
        # Validate content type
        self._validate_content_type(step_data, context)
        
        # Validate text content
        self._validate_text_content(step_data, context)
        
        # Validate file_id for media types
        self._validate_file_id(step_data, context)
        
        # Validate caption
        self._validate_caption(step_data, context)
        
        # Validate keyboard structure
        self._validate_keyboard(step_data, context)
        
        # Validate delay
        self._validate_delay(step_data, context)
        
        return len(self.errors) == 0, self.errors.copy(), self.warnings.copy()
    
    def _validate_required_fields(self, step_data: Dict[str, Any], context: str):
        """Validate required fields are present"""
        required_fields = ['content_type', 'text', 'caption', 'file_id', 'keyboard', 'delay']
        
        for field in required_fields:
            if field not in step_data:
                self.errors.append(f"{context}: Missing required field '{field}'")
    
    def _validate_content_type(self, step_data: Dict[str, Any], context: str):
        """Validate content type"""
        content_type = step_data.get('content_type')
        
        if not content_type:
            self.errors.append(f"{context}: content_type is required")
            return
            
        if content_type not in self.VALID_CONTENT_TYPES:
            self.errors.append(
                f"{context}: Invalid content_type '{content_type}'. "
                f"Must be one of: {', '.join(self.VALID_CONTENT_TYPES)}"
            )
    
    def _validate_text_content(self, step_data: Dict[str, Any], context: str):
        """Validate text content"""
        text = step_data.get('text')
        
        # Text is required for all content types
        if text is None and step_data.get('content_type') == 'text':
            self.errors.append(f"{context}: text field is required for text content type")
            return
        
        if text is not None:
            if not isinstance(text, str):
                self.errors.append(f"{context}: text must be a string")
                return
                
            if len(text) > self.MAX_TEXT_LENGTH:
                self.errors.append(
                    f"{context}: text length ({len(text)}) exceeds maximum allowed "
                    f"({self.MAX_TEXT_LENGTH} characters)"
                )
    
    def _validate_file_id(self, step_data: Dict[str, Any], context: str):
        """Validate file_id for media types"""
        content_type = step_data.get('content_type')
        file_id = step_data.get('file_id')
        
        # Media types require file_id
        media_types = {'photo', 'video', 'audio', 'document', 'animation', 'voice', 'video_note'}
        
        if content_type in media_types:
            if not file_id or file_id == 'None' or file_id == '':
                self.errors.append(
                    f"{context}: file_id is required for content_type '{content_type}'"
                )
            elif not isinstance(file_id, str):
                self.errors.append(f"{context}: file_id must be a string")
        
        # Text type should not have file_id
        elif content_type == 'text' and file_id:
            self.warnings.append(
                f"{context}: file_id is not needed for text content type"
            )
    
    def _validate_caption(self, step_data: Dict[str, Any], context: str):
        """Validate caption field"""
        caption = step_data.get('caption')
        
        if caption is not None:
            if not isinstance(caption, str):
                self.errors.append(f"{context}: caption must be a string or null")
                return
                
            if len(caption) > self.MAX_CAPTION_LENGTH:
                self.errors.append(
                    f"{context}: caption length ({len(caption)}) exceeds maximum allowed "
                    f"({self.MAX_CAPTION_LENGTH} characters)"
                )
    
    def _validate_keyboard(self, step_data: Dict[str, Any], context: str):
        """Validate keyboard structure"""
        keyboard = step_data.get('keyboard')
        
        if keyboard is None:
            return  # null is valid
        
        if not isinstance(keyboard, list):
            self.errors.append(f"{context}: keyboard must be a list or null")
            return
        
        for i, button in enumerate(keyboard):
            if not isinstance(button, dict):
                self.errors.append(
                    f"{context}: keyboard button {i} must be an object"
                )
                continue
            
            if len(button) != 1:
                self.errors.append(
                    f"{context}: keyboard button {i} must have exactly one key-value pair"
                )
                continue
            
            for button_text, url in button.items():
                if not isinstance(button_text, str) or not button_text.strip():
                    self.errors.append(
                        f"{context}: keyboard button {i} text must be a non-empty string"
                    )
                
                if not isinstance(url, str) or not url.strip():
                    self.errors.append(
                        f"{context}: keyboard button {i} URL must be a non-empty string"
                    )
                elif not (url.startswith('http://') or url.startswith('https://')):
                    self.warnings.append(
                        f"{context}: keyboard button {i} URL should start with http:// or https://"
                    )
    
    def _validate_delay(self, step_data: Dict[str, Any], context: str):
        """Validate delay field"""
        delay = step_data.get('delay')
        
        if delay is None:
            self.errors.append(f"{context}: delay field is required")
            return
        
        if not isinstance(delay, (int, float)):
            self.errors.append(f"{context}: delay must be a number")
            return
        
        if delay < self.MIN_DELAY_SECONDS:
            self.errors.append(
                f"{context}: delay ({delay}) must be at least {self.MIN_DELAY_SECONDS} seconds"
            )
        
        if delay > self.MAX_DELAY_SECONDS:
            self.errors.append(
                f"{context}: delay ({delay}) exceeds maximum allowed "
                f"({self.MAX_DELAY_SECONDS} seconds)"
            )
    
    def validate_steps_file(self, steps_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate entire steps file structure
        
        Args:
            steps_data: Complete steps dictionary
            
        Returns:
            Tuple of (is_valid, error_list, warning_list)
        """
        all_errors = []
        all_warnings = []
        
        if not isinstance(steps_data, dict):
            return False, ["Steps data must be a dictionary"], []
        
        if not steps_data:
            return False, ["Steps data cannot be empty"], []
        
        # Validate each step
        for step_key, step_data in steps_data.items():
            if not isinstance(step_data, dict):
                all_errors.append(f"Step '{step_key}' must be a dictionary")
                continue
            
            is_valid, errors, warnings = self.validate_step(step_data, step_key)
            all_errors.extend(errors)
            all_warnings.extend(warnings)
        
        return len(all_errors) == 0, all_errors, all_warnings


class StepBackupManager:
    """Manages step file backups for recovery"""
    
    def __init__(self, steps_file: str = "json/steps.json"):
        self.steps_file = steps_file
        self.backup_dir = "json/backups"
        
    def create_backup(self) -> str:
        """
        Create a backup of current steps file
        
        Returns:
            Path to backup file
        """
        import os
        import shutil
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"steps_backup_{timestamp}.json"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            shutil.copy2(self.steps_file, backup_path)
            logger.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        Restore steps from backup file
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if restore successful
        """
        import shutil
        
        try:
            # Validate backup file before restoring
            validator = StepValidator()
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            is_valid, errors, warnings = validator.validate_steps_file(backup_data)
            
            if not is_valid:
                logger.error(f"Backup file is invalid: {errors}")
                return False
            
            # Create backup of current file before restoring
            current_backup = self.create_backup()
            logger.info(f"Current file backed up to: {current_backup}")
            
            # Restore from backup
            shutil.copy2(backup_path, self.steps_file)
            logger.info(f"Steps restored from backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> List[str]:
        """
        List available backup files
        
        Returns:
            List of backup file paths
        """
        import os
        import glob
        
        if not os.path.exists(self.backup_dir):
            return []
        
        pattern = os.path.join(self.backup_dir, "steps_backup_*.json")
        backups = glob.glob(pattern)
        backups.sort(reverse=True)  # Latest first
        return backups


def validate_and_update_steps(new_steps: Dict[str, Any], backup_on_error: bool = True) -> Tuple[bool, str]:
    """
    Validate and update steps file with comprehensive error handling
    
    Args:
        new_steps: New steps data to validate and save
        backup_on_error: Whether to create backup before attempting update
        
    Returns:
        Tuple of (success, message)
    """
    import utils
    
    validator = StepValidator()
    backup_manager = StepBackupManager()
    
    try:
        # Validate new steps
        is_valid, errors, warnings = validator.validate_steps_file(new_steps)
        
        if not is_valid:
            error_msg = "Validation failed:\n" + "\n".join(errors)
            logger.error(error_msg)
            return False, error_msg
        
        # Log warnings if any
        if warnings:
            warning_msg = "Validation warnings:\n" + "\n".join(warnings)
            logger.warning(warning_msg)
        
        # Create backup before updating
        if backup_on_error:
            backup_path = backup_manager.create_backup()
            logger.info(f"Backup created before update: {backup_path}")
        
        # Update steps file
        utils.update_steps(new_steps)
        
        success_msg = "Steps updated successfully"
        if warnings:
            success_msg += f" (with {len(warnings)} warnings)"
        
        logger.info(success_msg)
        return True, success_msg
        
    except Exception as e:
        error_msg = f"Failed to update steps: {e}"
        logger.error(error_msg)
        return False, error_msg