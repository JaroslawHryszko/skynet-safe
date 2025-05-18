"""Unit tests for Telegram Handler module."""

import pytest
import os
import json
import time
from unittest.mock import MagicMock, patch, mock_open

from src.modules.communication.handlers.telegram_handler import TelegramHandler


@pytest.fixture
def test_config():
    """Fixture with test configuration for telegram handler."""
    return {
        "telegram_bot_token": "test_token_123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "telegram_polling_timeout": 10,
        "telegram_allowed_users": ["123456789"],
        "telegram_chat_state_file": "./data/telegram/test_chat_state.json"
    }


@pytest.mark.parametrize("test_content,expected_content", [
    ("Hello world!", "Hello world!"),  # Basic ASCII
    ("Cześć świecie! Jak się masz?", "Cześć świecie! Jak się masz?"),  # Polish diacritics
    ("Zażółć gęślą jaźń", "Zażółć gęślą jaźń"),  # More Polish diacritics
    ("Spécial caractères: äöüß", "Spécial caractères: äöüß"),  # Other special characters
    ("Эй, привет! как дела?", "Эй, привет! как дела?"),  # Cyrillic
    ("日本語も大丈夫", "日本語も大丈夫"),  # Asian characters
    ("💻 🌍 📱", "💻 🌍 📱"),  # Emojis
])
def test_send_message_preserves_special_characters(test_config, test_content, expected_content):
    """Test if the telegram handler preserves special characters when sending messages."""
    with patch("requests.get") as mock_get, \
         patch("requests.post") as mock_post, \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=False), \
         patch("builtins.open", mock_open()):
        
        # Mock the API response for initialization
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"ok": True, "result": {"username": "test_bot"}}
        
        # Mock the API response for sending message
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"ok": True}
        
        # Initialize handler
        handler = TelegramHandler(test_config)
        
        # Call the method being tested
        result = handler.send_message("123456789", test_content)
        
        # Verify result
        assert result is True
        
        # Verify post request was made with correct content
        mock_post.assert_called_once()
        called_args = mock_post.call_args.kwargs["json"]
        assert called_args["chat_id"] == "123456789"
        assert called_args["text"] == expected_content  # Content should be preserved


def test_sanitize_content_preserves_unicode(test_config):
    """Test that the content sanitization preserves Unicode characters."""
    with patch("requests.get") as mock_get, \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=False), \
         patch("builtins.open", mock_open()):
        
        # Mock the API response for initialization
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"ok": True, "result": {"username": "test_bot"}}
        
        # Initialize handler
        handler = TelegramHandler(test_config)
        
        # Directly test the private method that sanitizes content
        # We need to test this without involving the public API
        original_content = "Zażółć gęślą jaźń 😊 💻"
        
        # Manually call the send_message method but mock the _send_single_message
        with patch.object(handler, "_send_single_message") as mock_send:
            mock_send.return_value = True
            handler.send_message("123456789", original_content)
            
            # Verify the sanitized content was passed to _send_single_message
            mock_send.assert_called_once()
            assert mock_send.call_args[0][1] == original_content


def test_get_new_messages(test_config):
    """Test receiving new messages with special characters."""
    with patch("requests.get") as mock_get, \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=False), \
         patch("builtins.open", mock_open()):
        
        # Mock the API response for initialization
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "ok": True, 
            "result": {
                "username": "test_bot"
            }
        }
        
        # Mock the API response for getUpdates
        mock_get.return_value.json.side_effect = [
            # First call - initialization
            {"ok": True, "result": {"username": "test_bot"}},
            # Second call - get updates
            {
                "ok": True,
                "result": [
                    {
                        "update_id": 123456789,
                        "message": {
                            "message_id": 1,
                            "from": {
                                "id": 123456789,
                                "first_name": "Test",
                                "last_name": "User",
                                "username": "testuser"
                            },
                            "chat": {
                                "id": 123456789,
                                "type": "private"
                            },
                            "date": int(time.time()),
                            "text": "Cześć! Jak się masz? 😊"
                        }
                    }
                ]
            }
        ]
        
        # Initialize handler
        handler = TelegramHandler(test_config)
        
        # Reset mock to clear initialization call
        mock_get.reset_mock()
        
        # Call the method being tested
        messages = handler.get_new_messages()
        
        # Verify messages
        assert len(messages) == 1
        assert messages[0]["sender"] == "123456789"
        assert messages[0]["content"] == "Cześć! Jak się masz? 😊"
        assert "timestamp" in messages[0]
        assert "metadata" in messages[0]
        assert messages[0]["metadata"]["username"] == "testuser"


def test_error_handling_in_send_message(test_config):
    """Test error handling in send_message method."""
    with patch("requests.get") as mock_get, \
         patch("requests.post") as mock_post, \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=False), \
         patch("builtins.open", mock_open()):
        
        # Mock the API response for initialization
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"ok": True, "result": {"username": "test_bot"}}
        
        # Mock the API response for sending message to fail
        mock_post.return_value.status_code = 400
        
        # Initialize handler
        handler = TelegramHandler(test_config)
        
        # Call the method being tested with complex content
        result = handler.send_message("123456789", "Złożona wiadomość z polskimi znakami: ąęćńóśźż")
        
        # Verify result
        assert result is False