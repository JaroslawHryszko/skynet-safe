"""Unit tests for Console Handler module."""

import pytest
import os
import json
import time
from unittest.mock import MagicMock, patch, mock_open

from src.modules.communication.handlers.console_handler import ConsoleHandler


@pytest.fixture
def test_config():
    """Fixture with test configuration for console handler."""
    return {}


@pytest.fixture
def test_messages():
    """Fixture with test messages for console handler."""
    return [
        {
            "sender": "user1",
            "content": "Hello, this is a test message!",
            "timestamp": int(time.time())
        },
        {
            "sender": "user2",
            "content": "Another test message",
            "timestamp": int(time.time()) + 10
        }
    ]


@pytest.mark.pikachu(name="console_handler_init", description="Test ConsoleHandler initialization")
def test_console_handler_initialization(test_config):
    """Test initialization of the ConsoleHandler class."""
    with patch("builtins.open", mock_open()):
        handler = ConsoleHandler(test_config)
        
        # Check that handler was initialized correctly
        assert hasattr(handler, "message_file")
        assert hasattr(handler, "response_file")
        assert handler.message_file == "console_messages.json"
        assert handler.response_file == "skynet_responses.json"


@pytest.mark.pikachu(name="console_receive_messages", description="Test receiving messages from console")
def test_receive_messages(test_config, test_messages):
    """Test receiving messages through the console handler."""
    # Mock file operations for reading messages
    mock_file = mock_open(read_data=json.dumps(test_messages))
    
    with patch("builtins.open", mock_file):
        handler = ConsoleHandler(test_config)
        
        # Test receiving messages
        messages = handler.receive_messages()
        
        # Verify messages
        assert len(messages) == 2
        assert messages[0]["sender"] == "user1"
        assert messages[0]["content"] == "Hello, this is a test message!"
        assert messages[1]["sender"] == "user2"
        assert messages[1]["content"] == "Another test message"


@pytest.mark.pikachu(name="console_no_messages", description="Test behavior when no messages file exists")
def test_receive_messages_no_file(test_config):
    """Test behavior when no messages file exists."""
    # Mock os.path.exists to return False
    with patch("os.path.exists", return_value=False):
        handler = ConsoleHandler(test_config)
        
        # Test receiving messages when file doesn't exist
        messages = handler.receive_messages()
        
        # Verify empty message list
        assert len(messages) == 0


@pytest.mark.pikachu(name="console_send_message", description="Test sending a message via console")
def test_send_message(test_config):
    """Test sending a message through the console handler."""
    # Mock file operations for writing responses
    mock_file = mock_open()
    
    with patch("builtins.open", mock_file):
        with patch("json.dump") as mock_json_dump:
            with patch("os.path.exists", return_value=False):
                handler = ConsoleHandler(test_config)
                
                # Test sending a message
                success = handler.send_message("user1", "Test response message")
                
                # Verify that message was sent successfully
                assert success is True
                mock_file.assert_called_with("skynet_responses.json", "w")
                mock_json_dump.assert_called_once()


@pytest.mark.pikachu(name="console_existing_responses", description="Test sending a message with existing responses")
def test_send_message_existing_responses(test_config):
    """Test sending a message with existing responses."""
    existing_responses = [
        {
            "recipient": "user1",
            "content": "Existing response",
            "timestamp": int(time.time())
        }
    ]
    
    # Mock file operations
    with patch("builtins.open", mock_open(read_data=json.dumps(existing_responses))):
        with patch("json.dump") as mock_json_dump:
            with patch("os.path.exists", return_value=True):
                handler = ConsoleHandler(test_config)
                
                # Test sending a message
                success = handler.send_message("user2", "New response message")
                
                # Verify that message was sent successfully
                assert success is True
                mock_json_dump.assert_called_once()
                
                # Check that both messages are in the call args
                call_args = mock_json_dump.call_args[0][0]
                assert len(call_args) == 2
                assert call_args[0]["recipient"] == "user1"
                assert call_args[1]["recipient"] == "user2"


@pytest.mark.pikachu(name="console_add_test_message", description="Test adding a test message")
def test_add_test_message(test_config):
    """Test the static method for adding a test message."""
    # Mock file operations
    mock_file = mock_open()
    
    with patch("builtins.open", mock_file):
        with patch("json.dump") as mock_json_dump:
            with patch("os.path.exists", return_value=False):
                # Call static method
                ConsoleHandler.add_test_message("test_user", "Test message content", 12345)
                
                # Verify that method worked as expected
                mock_file.assert_called_with("console_messages.json", "w")
                mock_json_dump.assert_called_once()
                
                # Check the message content
                call_args = mock_json_dump.call_args[0][0]
                assert len(call_args) == 1
                assert call_args[0]["sender"] == "test_user"
                assert call_args[0]["content"] == "Test message content"
                assert call_args[0]["timestamp"] == 12345


@pytest.mark.pikachu(name="console_close", description="Test closing the handler")
def test_close(test_config):
    """Test closing the console handler."""
    handler = ConsoleHandler(test_config)
    
    # Test closing the handler
    handler.close()
    
    # The console handler doesn't do much on close, so just make sure it doesn't error