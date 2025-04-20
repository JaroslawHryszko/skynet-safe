"""Configuration testing module for SKYNET-SAFE system.

This module provides functionality to test various components of the system configuration:
- Local model verification
- Communication platform testing (Telegram, Signal)
- External LLM connectivity testing
"""

import logging
import json
import time
import sys
import os
from typing import Dict, Any, Tuple, List
import requests

# Ensure the module can import from the src directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.modules.model.model_manager import ModelManager
from src.modules.communication.handlers.telegram_handler import TelegramHandler
from src.modules.communication.handlers.signal_handler import SignalHandler
from src.modules.communication.handlers.console_handler import ConsoleHandler
from src.modules.metawareness.external_evaluation_manager import ExternalEvaluationManager

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("config_test.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("CONFIG-TESTER")


class ConfigTester:
    """Configuration testing class for SKYNET-SAFE components."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the configuration tester with system config.
        
        Args:
            config: Full system configuration dictionary
        """
        self.config = config
        self.test_results = {
            "local_model": {
                "status": "not_tested",
                "message": "",
                "response_time": 0
            },
            "telegram": {
                "status": "not_tested",
                "message": "",
                "details": {}
            },
            "external_llm": {
                "status": "not_tested",
                "message": "",
                "details": {}
            },
            "system_requirements": {
                "status": "not_tested",
                "message": "",
                "details": {}
            }
        }
        logger.info("Configuration tester initialized")

    def test_local_model(self) -> Dict[str, Any]:
        """Test if the local language model is working correctly.
        
        Returns:
            Dictionary with test results
        """
        logger.info("Testing local model...")
        result = {
            "status": "failed",
            "message": "Model test failed",
            "response_time": 0,
            "gpu_utilization": False,
            "device_info": ""
        }
        
        try:
            import torch
            
            # Check CUDA availability before model initialization
            cuda_available = torch.cuda.is_available()
            result["cuda_available"] = cuda_available
            
            if cuda_available:
                # Get GPU info before model load
                gpu_count = torch.cuda.device_count()
                result["gpu_count"] = gpu_count
                result["device_info"] = []
                
                for i in range(gpu_count):
                    device_name = torch.cuda.get_device_name(i)
                    total_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)  # GB
                    result["device_info"].append({
                        "index": i,
                        "name": device_name,
                        "total_memory_gb": round(total_memory, 2)
                    })
                    logger.info(f"Found GPU {i}: {device_name} with {round(total_memory, 2)}GB VRAM")
            
            # Initialize model manager with configuration
            model_manager = ModelManager(self.config["MODEL"])
            
            # Check if model is actually on GPU
            if hasattr(model_manager, 'model'):
                if cuda_available:
                    model_device = next(model_manager.model.parameters()).device
                    is_on_gpu = model_device.type == 'cuda'
                    result["model_device"] = str(model_device)
                    result["gpu_utilization"] = is_on_gpu
                    
                    # Check GPU memory usage after model load
                    if is_on_gpu:
                        for i in range(gpu_count):
                            reserved_memory = torch.cuda.memory_reserved(i) / (1024**3)  # GB
                            allocated_memory = torch.cuda.memory_allocated(i) / (1024**3)  # GB
                            if len(result["device_info"]) > i:
                                result["device_info"][i]["reserved_memory_gb"] = round(reserved_memory, 2)
                                result["device_info"][i]["allocated_memory_gb"] = round(allocated_memory, 2)
                                logger.info(f"GPU {i} memory: {round(allocated_memory, 2)}GB allocated / {round(reserved_memory, 2)}GB reserved")
                
            # Generate a test prompt
            test_prompt = "Please respond with a short confirmation that you are working correctly."
            
            # Measure response time
            start_time = time.time()
            response = model_manager.generate_response(test_prompt)
            response_time = time.time() - start_time
            
            # Check if response is valid
            if response and len(response) > 10:
                # Verify GPU utilization if CUDA is available
                if cuda_available and not result.get("gpu_utilization", False):
                    result["status"] = "partial_success"
                    result["message"] = f"Model responded successfully in {response_time:.2f} seconds, but is NOT utilizing GPU!"
                else:
                    result["status"] = "success"
                    result["message"] = f"Model responded successfully in {response_time:.2f} seconds" + \
                                      (f" and is properly utilizing GPU" if result.get("gpu_utilization", False) else "")
                
                result["response"] = response[:100] + "..." if len(response) > 100 else response
                result["response_time"] = response_time
                logger.info(f"Local model test successful: {response[:50]}...")
            else:
                result["message"] = "Model response too short or empty"
                logger.error(f"Local model test failed: {result['message']}")
            
        except Exception as e:
            result["message"] = f"Error testing model: {str(e)}"
            logger.error(f"Local model test error: {str(e)}", exc_info=True)
        
        self.test_results["local_model"] = result
        return result

    def test_telegram(self) -> Dict[str, Any]:
        """Test Telegram communication functionality.
        
        Returns:
            Dictionary with test results
        """
        logger.info("Testing Telegram communication...")
        result = {
            "status": "failed",
            "message": "Telegram test failed",
            "details": {}
        }
        
        # Check if Telegram is configured
        if "telegram" not in self.config["COMMUNICATION"].get("platform", []):
            result["message"] = "Telegram is not configured in platforms list"
            logger.warning(result["message"])
            self.test_results["telegram"] = result
            return result
            
        try:
            # Extract Telegram configuration from the main config
            telegram_config = {
                "bot_token": self.config["COMMUNICATION"].get("telegram_bot_token"),
                "polling_timeout": self.config["COMMUNICATION"].get("telegram_polling_timeout"),
                "allowed_users": self.config["COMMUNICATION"].get("telegram_allowed_users"),
                "chat_state_file": self.config["COMMUNICATION"].get("telegram_chat_state_file"),
		"test_chat_id": self.config["COMMUNICATION"].get("telegram_test_chat_id")
            }
            
            # Check required configuration parameters
            required_params = ["bot_token"]
            missing_params = [param for param in required_params if not telegram_config.get(param)]
            
            if missing_params:
                result["message"] = f"Missing Telegram configuration parameters: {', '.join(missing_params)}"
                result["details"]["missing_params"] = missing_params
                logger.warning(result["message"])
                self.test_results["telegram"] = result
                return result
            
            # Initialize the Telegram handler (this will verify API credentials)
            # Pass config parameters directly (TelegramHandler expects differently named parameters)
            telegram_handler = TelegramHandler({
                "telegram_bot_token": telegram_config["bot_token"],
                "telegram_polling_timeout": telegram_config["polling_timeout"],
                "telegram_allowed_users": telegram_config["allowed_users"],
                "telegram_chat_state_file": telegram_config["chat_state_file"],
		"telegram_test_chat_id": telegram_config["test_chat_id"]
            })
            
            # We can't get bot info directly, but the handler initialization 
            # checks if the bot is working in __init__
            # So if we get here, it means the bot token is valid
            
            # Use API to get bot info manually
            try:
                api_url = f"https://api.telegram.org/bot{telegram_config['bot_token']}/getMe"
                response = requests.get(api_url)
                if response.status_code == 200:
                    bot_info = response.json()
                    if bot_info.get("ok"):
                        result["details"]["bot_info"] = bot_info.get("result", {})
                    else:
                        result["message"] = f"Failed to retrieve bot information: {bot_info.get('description')}"
                        logger.error(result["message"])
                        self.test_results["telegram"] = result
                        return result
                else:
                    result["message"] = f"Failed to retrieve bot information: HTTP {response.status_code}"
                    logger.error(result["message"])
                    self.test_results["telegram"] = result
                    return result
            except Exception as e:
                result["message"] = f"Error retrieving bot information: {str(e)}"
                logger.error(result["message"])
                self.test_results["telegram"] = result
                return result
            
            # Try sending a test message to self (bot)
            test_message = "Telegram configuration test message"
            
            # Only proceed if we have a test chat ID configured
            test_chat_id = telegram_config.get("test_chat_id")
            if not test_chat_id:
                result["status"] = "partial_success"
                result["message"] = "Telegram credentials verified, but no test_chat_id configured for message test"
                logger.info(result["message"])
                self.test_results["telegram"] = result
                return result
                
            # Send test message
            message_sent = telegram_handler.send_message(test_chat_id, test_message)
            if not message_sent:
                result["status"] = "partial_success"
                result["message"] = "Telegram credentials verified, but failed to send test message"
                logger.warning(result["message"])
                self.test_results["telegram"] = result
                return result
                
            # Try receiving messages (this will mostly work if we can receive updates)
            result["status"] = "success"
            result["message"] = "Telegram fully operational - credentials verified and test message sent"
            result["details"]["test_message_sent"] = True
            logger.info(result["message"])
            
        except Exception as e:
            result["message"] = f"Error testing Telegram: {str(e)}"
            logger.error(f"Telegram test error: {str(e)}", exc_info=True)
        
        self.test_results["telegram"] = result
        return result

    def test_external_llm(self) -> Dict[str, Any]:
        """Test connection to external LLM (Claude).
        
        Returns:
            Dictionary with test results
        """
        logger.info("Testing external LLM connection...")
        result = {
            "status": "failed",
            "message": "External LLM test failed",
            "details": {}
        }
        
        try:
            # Initialize external evaluation manager (which uses Claude)
            ext_eval_manager = ExternalEvaluationManager(self.config["EXTERNAL_EVALUATION"])
            
            # Check if API key is configured
            api_key = self.config["EXTERNAL_EVALUATION"].get("api_key")
            if not api_key:
                result["message"] = "No external LLM API key configured"
                logger.warning(result["message"])
                self.test_results["external_llm"] = result
                return result
            
            # Simple test prompt for Claude
            test_prompt = "Please respond with a short confirmation message."
            
            # Test the connection to Claude
            start_time = time.time()
            claude_response = ext_eval_manager.get_claude_evaluation(test_prompt)
            response_time = time.time() - start_time
            
            if claude_response:
                result["status"] = "success"
                result["message"] = f"External LLM responded successfully in {response_time:.2f} seconds"
                result["details"]["response"] = claude_response[:100] + "..." if len(claude_response) > 100 else claude_response
                result["details"]["response_time"] = response_time
                logger.info(f"External LLM test successful: {claude_response[:50]}...")
            else:
                result["message"] = "External LLM response empty"
                logger.error(result["message"])
            
        except Exception as e:
            result["message"] = f"Error testing external LLM: {str(e)}"
            logger.error(f"External LLM test error: {str(e)}", exc_info=True)
        
        self.test_results["external_llm"] = result
        return result

    def test_system_requirements(self) -> Dict[str, Any]:
        """Test if the system meets minimum requirements.
        
        Returns:
            Dictionary with test results
        """
        logger.info("Testing system requirements...")
        result = {
            "status": "failed",
            "message": "System requirements test failed",
            "details": {}
        }
        
        try:
            import torch
            import psutil
            
            # Check Python version
            python_version = sys.version_info
            result["details"]["python_version"] = f"{python_version.major}.{python_version.minor}.{python_version.micro}"
            python_ok = python_version.major >= 3 and python_version.minor >= 9
            result["details"]["python_ok"] = python_ok
            
            # Check CUDA availability
            cuda_available = torch.cuda.is_available()
            result["details"]["cuda_available"] = cuda_available
            
            # Check GPU count
            gpu_count = torch.cuda.device_count() if cuda_available else 0
            result["details"]["gpu_count"] = gpu_count
            
            # Check GPU memory (if available)
            if cuda_available and gpu_count > 0:
                gpu_memory = []
                for i in range(gpu_count):
                    device = torch.cuda.get_device_properties(i)
                    memory_gb = device.total_memory / (1024 ** 3)
                    gpu_memory.append({
                        "device": i,
                        "name": device.name,
                        "memory_gb": round(memory_gb, 2)
                    })
                result["details"]["gpu_memory"] = gpu_memory
            
            # Check RAM
            ram = psutil.virtual_memory()
            ram_gb = ram.total / (1024 ** 3)
            result["details"]["ram_gb"] = round(ram_gb, 2)
            ram_ok = ram_gb >= 16  # Minimum 16GB
            result["details"]["ram_ok"] = ram_ok
            
            # Check disk space
            disk = psutil.disk_usage('/')
            disk_gb = disk.total / (1024 ** 3)
            free_disk_gb = disk.free / (1024 ** 3)
            result["details"]["disk_gb"] = round(disk_gb, 2)
            result["details"]["free_disk_gb"] = round(free_disk_gb, 2)
            disk_ok = free_disk_gb >= 20  # Minimum 20GB free
            result["details"]["disk_ok"] = disk_ok
            
            # Check internet connection
            internet_ok = self._check_internet_connection()
            result["details"]["internet_ok"] = internet_ok
            
            # Overall status
            requirements_ok = python_ok and ram_ok and disk_ok and internet_ok
            
            if cuda_available and gpu_count > 0:
                requirements_ok = requirements_ok and True
                result["details"]["gpu_ok"] = True
            else:
                result["details"]["gpu_ok"] = False
                requirements_ok = False
            
            if requirements_ok:
                result["status"] = "success"
                result["message"] = "System meets all requirements"
            else:
                result["status"] = "failed"
                failed_reqs = []
                if not python_ok:
                    failed_reqs.append("Python version")
                if not ram_ok:
                    failed_reqs.append("RAM")
                if not disk_ok:
                    failed_reqs.append("Disk space")
                if not internet_ok:
                    failed_reqs.append("Internet connection")
                if not (cuda_available and gpu_count > 0):
                    failed_reqs.append("GPU/CUDA")
                
                result["message"] = f"System does not meet requirements: {', '.join(failed_reqs)}"
            
            logger.info(f"System requirements test: {result['status']}")
            
        except Exception as e:
            result["message"] = f"Error testing system requirements: {str(e)}"
            logger.error(f"System requirements test error: {str(e)}", exc_info=True)
        
        self.test_results["system_requirements"] = result
        return result

    def _check_internet_connection(self) -> bool:
        """Check if there is an active internet connection.
        
        Returns:
            Boolean indicating if internet connection is available
        """
        try:
            # Try to connect to a reliable website
            response = requests.get("https://www.google.com", timeout=5)
            return response.status_code == 200
        except:
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all configuration tests.
        
        Returns:
            Dictionary with all test results
        """
        logger.info("Running all configuration tests...")
        
        # Test system requirements first
        self.test_system_requirements()
        
        # Test local model
        self.test_local_model()
        
        # Test Telegram communication
        self.test_telegram()
        
        # Test external LLM
        self.test_external_llm()
        
        # Compile overall results
        overall_status = "success"
        for component, result in self.test_results.items():
            if result["status"] == "failed":
                overall_status = "failed"
                break
            elif result["status"] == "partial_success" and overall_status != "failed":
                overall_status = "partial_success"
        
        # Create final result with summary
        final_result = {
            "timestamp": time.time(),
            "overall_status": overall_status,
            "components": self.test_results,
            "summary": self._generate_summary()
        }
        
        # Log and return results
        logger.info(f"Configuration testing completed with status: {overall_status}")
        return final_result
    
    def _generate_summary(self) -> str:
        """Generate a human-readable summary of test results.
        
        Returns:
            String containing test summary
        """
        summary_lines = ["SKYNET-SAFE Configuration Test Results:"]
        
        # System requirements
        sys_req = self.test_results["system_requirements"]
        summary_lines.append(f"\n1. System Requirements: {sys_req['status'].upper()}")
        summary_lines.append(f"   {sys_req['message']}")
        if sys_req["details"]:
            if "python_version" in sys_req["details"]:
                summary_lines.append(f"   - Python: v{sys_req['details']['python_version']} ({'OK' if sys_req['details'].get('python_ok', False) else 'NOT OK'})")
            if "ram_gb" in sys_req["details"]:
                summary_lines.append(f"   - RAM: {sys_req['details']['ram_gb']} GB ({'OK' if sys_req['details'].get('ram_ok', False) else 'NOT OK'})")
            if "free_disk_gb" in sys_req["details"]:
                summary_lines.append(f"   - Free Disk: {sys_req['details']['free_disk_gb']} GB ({'OK' if sys_req['details'].get('disk_ok', False) else 'NOT OK'})")
            if "gpu_count" in sys_req["details"]:
                gpu_info = f"{sys_req['details']['gpu_count']} GPU(s)"
                if sys_req['details'].get('gpu_memory'):
                    gpu_names = [f"{g['name']} ({g['memory_gb']} GB)" for g in sys_req['details']['gpu_memory']]
                    gpu_info += f": {', '.join(gpu_names)}"
                summary_lines.append(f"   - GPU: {gpu_info} ({'OK' if sys_req['details'].get('gpu_ok', False) else 'NOT OK'})")
            if "internet_ok" in sys_req["details"]:
                summary_lines.append(f"   - Internet: {'Connected' if sys_req['details']['internet_ok'] else 'Not connected'}")
        
        # Local model
        local_model = self.test_results["local_model"]
        summary_lines.append(f"\n2. Local Model: {local_model['status'].upper()}")
        summary_lines.append(f"   {local_model['message']}")
        if local_model.get("response_time"):
            summary_lines.append(f"   - Response time: {local_model['response_time']:.2f} seconds")
        if local_model.get("response"):
            summary_lines.append(f"   - Sample response: \"{local_model['response'][:50]}...\"")
        
        # Add GPU utilization details
        if local_model.get("cuda_available"):
            if local_model.get("gpu_utilization"):
                summary_lines.append(f"   - GPU utilization: ✅ Model is on {local_model.get('model_device', 'unknown device')}")
            else:
                summary_lines.append(f"   - GPU utilization: ❌ Model is NOT using GPU!")
                
            # Add memory usage details if available
            if local_model.get("device_info") and isinstance(local_model["device_info"], list):
                for i, gpu_info in enumerate(local_model["device_info"]):
                    if "allocated_memory_gb" in gpu_info:
                        usage_percent = (gpu_info["allocated_memory_gb"] / gpu_info["total_memory_gb"]) * 100
                        summary_lines.append(f"   - GPU {i} ({gpu_info['name']}): " +
                                            f"{gpu_info['allocated_memory_gb']:.2f}GB / {gpu_info['total_memory_gb']:.2f}GB " +
                                            f"({usage_percent:.1f}% utilized)")
        
        # Telegram
        telegram = self.test_results["telegram"]
        summary_lines.append(f"\n3. Telegram: {telegram['status'].upper()}")
        summary_lines.append(f"   {telegram['message']}")
        if telegram.get("details", {}).get("bot_info"):
            bot_info = telegram["details"]["bot_info"]
            summary_lines.append(f"   - Bot: @{bot_info.get('username')} ({bot_info.get('first_name', 'Unknown')})")
        if telegram.get("details", {}).get("test_message_sent"):
            summary_lines.append(f"   - Test message: Successfully sent")
        
        # External LLM
        ext_llm = self.test_results["external_llm"]
        summary_lines.append(f"\n4. External LLM: {ext_llm['status'].upper()}")
        summary_lines.append(f"   {ext_llm['message']}")
        if ext_llm.get("details", {}).get("response_time"):
            summary_lines.append(f"   - Response time: {ext_llm['details']['response_time']:.2f} seconds")
        if ext_llm.get("details", {}).get("response"):
            summary_lines.append(f"   - Sample response: \"{ext_llm['details']['response'][:50]}...\"")
        
        # Overall result
        overall_status = "success"
        for component, result in self.test_results.items():
            if result["status"] == "failed":
                overall_status = "failed"
                break
            elif result["status"] == "partial_success" and overall_status != "failed":
                overall_status = "partial_success"
        
        status_text = {
            "success": "ALL TESTS PASSED",
            "partial_success": "SOME TESTS PASSED WITH WARNINGS",
            "failed": "SOME TESTS FAILED"
        }
        
        summary_lines.append(f"\nOVERALL RESULT: {status_text.get(overall_status, 'UNKNOWN')}")
        
        return "\n".join(summary_lines)

    def save_results(self, filename: str = "config_test_results.json") -> str:
        """Save test results to a JSON file.
        
        Args:
            filename: Name of the file to save results to
            
        Returns:
            Path to the saved file
        """
        final_result = {
            "timestamp": time.time(),
            "overall_status": "unknown",
            "components": self.test_results,
            "summary": self._generate_summary()
        }
        
        # Determine overall status
        overall_status = "success"
        for component, result in self.test_results.items():
            if result["status"] == "failed":
                overall_status = "failed"
                break
            elif result["status"] == "partial_success" and overall_status != "failed":
                overall_status = "partial_success"
        
        final_result["overall_status"] = overall_status
        
        # Save to file
        with open(filename, "w") as f:
            json.dump(final_result, f, indent=2)
        
        logger.info(f"Test results saved to {filename}")
        return filename


def main():
    """Run the configuration tests as a standalone script."""
    import argparse
    from src.config import config
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test SKYNET-SAFE configuration")
    parser.add_argument("--component", choices=["all", "model", "telegram", "external_llm", "system"], 
                      default="all", help="Which component to test")
    parser.add_argument("--output", default="config_test_results.json", help="Output file for test results")
    args = parser.parse_args()
    
    # Build configuration dictionary
    system_config = {
        "MODEL": config.MODEL_CONFIG,
        "MEMORY": config.MEMORY_CONFIG,
        "COMMUNICATION": config.COMMUNICATION_CONFIG,
        "PLATFORM_CONFIG": config.PLATFORM_CONFIG,
        "EXTERNAL_EVALUATION": config.EXTERNAL_EVALUATION_CONFIG
    }
    
    # Create tester instance
    tester = ConfigTester(system_config)
    
    # Run tests based on selected component
    if args.component == "all":
        results = tester.run_all_tests()
    elif args.component == "model":
        results = tester.test_local_model()
    elif args.component == "telegram":
        results = tester.test_telegram()
    elif args.component == "external_llm":
        results = tester.test_external_llm()
    elif args.component == "system":
        results = tester.test_system_requirements()
    
    # Save results if full test or if requested
    if args.output:
        tester.save_results(args.output)
    
    # Print human-readable summary
    print(tester._generate_summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
