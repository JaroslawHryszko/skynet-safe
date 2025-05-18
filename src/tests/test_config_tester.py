"""Unit tests for configuration testing module."""

import pytest
import os
import json
import time
from unittest.mock import MagicMock, patch, mock_open

from src.utils.config_tester import ConfigTester


@pytest.fixture
def test_config():
    """Fixture with test configuration."""
    return {
        "MODEL": {
            "base_model": "test-model",
            "max_length": 100,
            "temperature": 0.7,
            "do_sample": True,
            "quantization": "4bit"
        },
        "MEMORY": {
            "vector_db_type": "chroma",
            "embedding_model": "test-embedding-model",
            "memory_path": "./data/memory"
        },
        "COMMUNICATION": {
            "platform": "telegram",
            "check_interval": 10,
            "response_delay": 1.5,
            "telegram_bot_token": "test-token",
            "telegram_polling_timeout": 30,
            "telegram_allowed_users": "",
            "telegram_chat_state_file": "./data/telegram/chat_state.json",
            "telegram_test_chat_id": "test-chat-id",
            "signal_phone_number": "",
            "signal_config_path": ""
        },
        "EXTERNAL_EVALUATION": {
            "api_key": "test-api-key",
            "evaluation_frequency": 86400,
            "evaluation_prompts": [
                "Test prompt 1",
                "Test prompt 2"
            ],
            "evaluation_criteria": ["accuracy", "coherence"],
            "evaluation_scale": {
                "min": 1,
                "max": 10,
                "threshold": 7
            },
            "history_file": "./data/metawareness/evaluation_history.json",
            "test_cases_file": "./data/metawareness/test_cases.json"
        }
    }


@pytest.mark.pikachu(name="config_tester_init", description="Test ConfigTester initialization")
def test_config_tester_initialization(test_config):
    """Test initialization of the ConfigTester class."""
    tester = ConfigTester(test_config)
    
    # Verify that tester was initialized correctly
    assert tester.config == test_config
    assert isinstance(tester.test_results, dict)
    assert "local_model" in tester.test_results
    assert "telegram" in tester.test_results
    assert "external_llm" in tester.test_results
    assert "system_requirements" in tester.test_results
    
    # Verify initial statuses
    for component, result in tester.test_results.items():
        assert result["status"] == "not_tested"


@pytest.mark.pikachu(name="test_local_model", description="Test local model test functionality")
@patch("src.utils.config_tester.ModelManager")
@patch("src.utils.config_tester.torch")
def test_local_model_test(mock_torch, mock_model_manager, test_config):
    """Test the local model testing functionality."""
    # Mock CUDA and model responses
    mock_torch.cuda.is_available.return_value = True
    mock_torch.cuda.device_count.return_value = 1
    mock_device = MagicMock()
    mock_device.name = "Test GPU"
    mock_torch.cuda.get_device_properties.return_value = mock_device
    mock_device.total_memory = 10 * 1024 * 1024 * 1024  # 10GB
    
    # Mock model responses
    mock_model_instance = MagicMock()
    mock_model_manager.return_value = mock_model_instance
    mock_model_instance.generate_response.return_value = "This is a test response from the model."
    
    # Mock model parameters for device check
    mock_param = MagicMock()
    mock_param.device.type = "cuda"
    mock_model_instance.model.parameters.return_value = [mock_param]
    
    # Create tester and run test
    tester = ConfigTester(test_config)
    result = tester.test_local_model()
    
    # Check result
    assert result["status"] == "success"
    assert "Model responded successfully" in result["message"]
    assert "response_time" in result
    assert "response" in result
    assert result["gpu_utilization"] is True
    
    # Verify that the model manager was called with correct config
    mock_model_manager.assert_called_once_with(test_config["MODEL"])
    # Verify that generate_response was called
    mock_model_instance.generate_response.assert_called_once()


@pytest.mark.pikachu(name="test_telegram", description="Test Telegram testing functionality")
@patch("src.utils.config_tester.TelegramHandler")
@patch("src.utils.config_tester.requests.get")
def test_telegram_test_successful(mock_requests_get, mock_telegram_handler, test_config):
    """Test the Telegram testing functionality when successful."""
    # Mock HTTP responses
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ok": True,
        "result": {
            "id": 123456789,
            "is_bot": True,
            "first_name": "Test Bot",
            "username": "test_bot"
        }
    }
    mock_requests_get.return_value = mock_response
    
    # Mock Telegram handler
    mock_handler_instance = MagicMock()
    mock_telegram_handler.return_value = mock_handler_instance
    mock_handler_instance.send_message.return_value = True
    
    # Create tester and run test
    tester = ConfigTester(test_config)
    result = tester.test_telegram()
    
    # Check result
    assert result["status"] == "success"
    assert "Telegram fully operational" in result["message"]
    assert "details" in result
    assert "bot_info" in result["details"]
    assert result["details"]["test_message_sent"] is True
    
    # Verify that the handler was initialized with correct config
    mock_telegram_handler.assert_called_once()
    # Verify that send_message was called with the test chat ID
    mock_handler_instance.send_message.assert_called_once_with(
        test_config["COMMUNICATION"]["telegram_test_chat_id"], 
        "Telegram configuration test message"
    )


@pytest.mark.pikachu(name="test_external_llm", description="Test external LLM test functionality")
@patch("src.utils.config_tester.ExternalEvaluationManager")
def test_external_llm_test(mock_external_eval_manager, test_config):
    """Test the external LLM testing functionality."""
    # Mock external evaluation manager
    mock_manager_instance = MagicMock()
    mock_external_eval_manager.return_value = mock_manager_instance
    mock_manager_instance.get_claude_evaluation.return_value = "This is a test response from Claude."
    
    # Create tester and run test
    tester = ConfigTester(test_config)
    result = tester.test_external_llm()
    
    # Check result
    assert result["status"] == "success"
    assert "External LLM responded successfully" in result["message"]
    assert "details" in result
    assert "response" in result["details"]
    assert "response_time" in result["details"]
    
    # Verify that the external evaluation manager was called with correct config
    mock_external_eval_manager.assert_called_once_with(test_config["EXTERNAL_EVALUATION"])
    # Verify that get_claude_evaluation was called
    mock_manager_instance.get_claude_evaluation.assert_called_once()


@pytest.mark.pikachu(name="test_system_requirements", description="Test system requirements check")
@patch("src.utils.config_tester.requests.get")
@patch("src.utils.config_tester.psutil")
@patch("src.utils.config_tester.torch")
@patch("src.utils.config_tester.sys")
def test_system_requirements_check(mock_sys, mock_torch, mock_psutil, mock_requests_get, test_config):
    """Test the system requirements check functionality."""
    # Mock Python version
    mock_sys.version_info.major = 3
    mock_sys.version_info.minor = 10
    mock_sys.version_info.micro = 0
    
    # Mock CUDA availability
    mock_torch.cuda.is_available.return_value = True
    mock_torch.cuda.device_count.return_value = 1
    
    # Mock GPU properties
    mock_device = MagicMock()
    mock_device.name = "Test GPU"
    mock_device.total_memory = 16 * 1024 * 1024 * 1024  # 16GB
    mock_torch.cuda.get_device_properties.return_value = mock_device
    
    # Mock system memory
    mock_memory = MagicMock()
    mock_memory.total = 32 * 1024 * 1024 * 1024  # 32GB
    mock_psutil.virtual_memory.return_value = mock_memory
    
    # Mock disk usage
    mock_disk = MagicMock()
    mock_disk.total = 500 * 1024 * 1024 * 1024  # 500GB
    mock_disk.free = 100 * 1024 * 1024 * 1024  # 100GB
    mock_psutil.disk_usage.return_value = mock_disk
    
    # Mock internet connection
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_requests_get.return_value = mock_response
    
    # Create tester and run test
    tester = ConfigTester(test_config)
    result = tester.test_system_requirements()
    
    # Check result
    assert result["status"] == "success"
    assert "System meets all requirements" in result["message"]
    assert "details" in result
    assert result["details"]["python_ok"] is True
    assert result["details"]["ram_ok"] is True
    assert result["details"]["disk_ok"] is True
    assert result["details"]["internet_ok"] is True
    assert result["details"]["gpu_ok"] is True


@pytest.mark.pikachu(name="test_run_all", description="Test running all tests")
@patch.object(ConfigTester, "test_system_requirements")
@patch.object(ConfigTester, "test_local_model")
@patch.object(ConfigTester, "test_telegram")
@patch.object(ConfigTester, "test_external_llm")
def test_run_all_tests(mock_test_external_llm, mock_test_telegram, 
                       mock_test_local_model, mock_test_system_requirements, test_config):
    """Test running all configuration tests."""
    # Set up mock returns for all tests
    mock_test_system_requirements.return_value = {"status": "success", "message": "System OK"}
    mock_test_local_model.return_value = {"status": "success", "message": "Model OK"}
    mock_test_telegram.return_value = {"status": "success", "message": "Telegram OK"}
    mock_test_external_llm.return_value = {"status": "success", "message": "External LLM OK"}
    
    # Create tester and run all tests
    tester = ConfigTester(test_config)
    result = tester.run_all_tests()
    
    # Check that all tests were called
    mock_test_system_requirements.assert_called_once()
    mock_test_local_model.assert_called_once()
    mock_test_telegram.assert_called_once()
    mock_test_external_llm.assert_called_once()
    
    # Check result
    assert result["overall_status"] == "success"
    assert "components" in result
    assert "summary" in result


@pytest.mark.pikachu(name="test_summary_generation", description="Test summary generation")
def test_summary_generation(test_config):
    """Test the generation of human-readable summary."""
    tester = ConfigTester(test_config)
    
    # Set test results
    tester.test_results = {
        "system_requirements": {
            "status": "success",
            "message": "System meets all requirements",
            "details": {
                "python_version": "3.10.0",
                "python_ok": True,
                "ram_gb": 32.0,
                "ram_ok": True,
                "free_disk_gb": 100.0,
                "disk_ok": True,
                "gpu_count": 1,
                "gpu_ok": True,
                "gpu_memory": [{"device": 0, "name": "Test GPU", "memory_gb": 16.0}],
                "internet_ok": True
            }
        },
        "local_model": {
            "status": "success",
            "message": "Model responded successfully in 1.23 seconds",
            "response_time": 1.23,
            "response": "This is a test response",
            "gpu_utilization": True,
            "model_device": "cuda:0",
            "device_info": [
                {"index": 0, "name": "Test GPU", "total_memory_gb": 16.0, 
                "allocated_memory_gb": 8.0, "reserved_memory_gb": 10.0}
            ]
        },
        "telegram": {
            "status": "success",
            "message": "Telegram fully operational",
            "details": {
                "bot_info": {"username": "test_bot", "first_name": "Test Bot"},
                "test_message_sent": True
            }
        },
        "external_llm": {
            "status": "success",
            "message": "External LLM responded successfully in 2.34 seconds",
            "details": {
                "response_time": 2.34,
                "response": "This is a test response from Claude"
            }
        }
    }
    
    # Generate summary
    summary = tester._generate_summary()
    
    # Check summary content
    assert "SKYNET-SAFE Configuration Test Results:" in summary
    assert "System Requirements: SUCCESS" in summary
    assert "Local Model: SUCCESS" in summary
    assert "Telegram: SUCCESS" in summary
    assert "External LLM: SUCCESS" in summary
    assert "OVERALL RESULT: ALL TESTS PASSED" in summary


@pytest.mark.pikachu(name="test_save_results", description="Test saving results to file")
def test_save_results(test_config):
    """Test saving test results to a JSON file."""
    # Mock open function
    mock_file = mock_open()
    
    with patch("builtins.open", mock_file):
        tester = ConfigTester(test_config)
        # Set test results to something
        tester.test_results = {
            "system_requirements": {"status": "success", "message": "System OK"},
            "local_model": {"status": "success", "message": "Model OK"},
            "telegram": {"status": "success", "message": "Telegram OK"},
            "external_llm": {"status": "success", "message": "External LLM OK"}
        }
        
        # Save results
        filename = tester.save_results("test_results.json")
        
        # Check that file was opened correctly
        mock_file.assert_called_once_with("test_results.json", "w")
        # Check that json.dump was called
        handle = mock_file()
        handle.write.assert_called()  # json.dump calls write
        
        # Check returned filename
        assert filename == "test_results.json"