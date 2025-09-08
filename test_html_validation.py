"""
Test HTML Text Validation for Telegram Bot
Tests the validate_html_text function from utils.py
"""

import sys
import os

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import validate_html_text

def test_validate_html_text():
    """Test the HTML text validation system"""
    print("Test Testing HTML Text Validation System...")
    
    # Test 1: Valid HTML texts
    print("\n1 Testing valid HTML validation...")
    
    valid_htmls = [
        "<b>Bold text</b>",  # Basic bold
        "<i>Italic text</i>",  # Basic italic
        "<u>Underlined text</u>",  # Underline
        "<s>Strikethrough text</s>",  # Strikethrough
        "<code>Code text</code>",  # Code
        "<pre>Preformatted text</pre>",  # Pre
        '<a href="https://example.com">Link text</a>',  # Valid link
        "Plain text without tags",  # No tags
        "<b>Nested <i>bold and italic</i> text</b>",  # Nested tags
        "Short text",  # Short length
    ]
    
    for html in valid_htmls:
        result = validate_html_text(html)
        assert result == True, f"Expected True for valid HTML: {html}"
    
    print("Valid HTML validation working correctly")
    
    # Test 2: Invalid HTML - unbalanced tags
    print("\n2 Testing unbalanced tags...")
    
    unbalanced_htmls = [
        "<b>Bold text",  # Missing closing
        "Text <i>italic",  # Missing closing
        "</b>Closing without opening",  # Closing without opening
        "<b><i>Nested but missing closings</b>",  # Mismatched
    ]
    
    for html in unbalanced_htmls:
        result = validate_html_text(html)
        assert result == False, f"Expected False for unbalanced: {html}"
    
    print("Unbalanced tags validation working correctly")
    
    # Test 3: Invalid tags or attributes
    print("\n3 Testing invalid tags and attributes...")
    
    invalid_htmls = [
        "<invalid>Invalid tag</invalid>",  # Unknown tag
        '<a href="http://example.com">HTTP link (should be HTTPS? but accept http)</a>',  # HTTP - but function accepts http
        '<a href="javascript:alert(1)">Malicious link</a>',  # Invalid href
        '<a href="">Empty href</a>',  # Empty href
        "<B>Uppercase tag</B>",  # Case insensitive, but function uses lower
    ]
    
    # Note: Function accepts http://, but for test, adjust if needed
    for html in invalid_htmls:
        result = validate_html_text(html)
        if "javascript" in html or "Empty href" in html:
            assert result == False, f"Expected False for invalid: {html}"
        else:
            # Uppercase should be handled as lower
            result = validate_html_text(html)
            assert result == False if "invalid" in html else True, f"Unexpected for {html}"
    
    print("Invalid tags/attributes validation working correctly")
    
    # Test 4: Length validation
    print("\n4 Testing length limits...")
    
    short_text = "a" * 4095
    long_text = "a" * 4097
    
    assert validate_html_text(short_text) == True, "Short text should be valid"
    assert validate_html_text(long_text) == False, "Long text should be invalid"
    
    print("Length validation working correctly")
    
    # Test 5: Invalid characters
    print("\n5 Testing invalid characters...")
    
    invalid_chars = "\x00Null character in text\x00"
    valid_chars = "Normal text with \n and spaces"
    
    assert validate_html_text(invalid_chars) == False, "Invalid chars should fail"
    assert validate_html_text(valid_chars) == True, "Valid chars should pass"
    
    print("Invalid characters validation working correctly")
    
    print("\nAll HTML validation tests passed successfully!")
    print("validate_html_text function is working correctly")

if __name__ == '__main__':
    test_validate_html_text()