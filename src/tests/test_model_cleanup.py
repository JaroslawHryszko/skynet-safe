"""Unit tests for model output cleanup functions."""

import pytest
from unittest.mock import MagicMock, patch
import re

from src.modules.model.model_manager import ModelManager


@pytest.fixture
def model_config():
    """Fixture with test configuration for model."""
    return {
        "base_model": "test-model",
        "max_length": 100,
        "temperature": 0.7,
        "do_sample": True,
        "quantization": "4bit"
    }


@pytest.fixture
def model_manager(model_config):
    """Fixture that returns a ModelManager instance with mocked components."""
    with patch("src.modules.model.model_manager.AutoModelForCausalLM"):
        with patch("src.modules.model.model_manager.AutoTokenizer"):
            manager = ModelManager(model_config)
            # Mock the model and tokenizer
            manager.model = MagicMock()
            manager.tokenizer = MagicMock()
            return manager


@pytest.mark.pikachu(name="test_corrupted_detection", description="Test corrupted output detection")
def test_is_corrupted_output(model_manager):
    """Test that corrupted outputs are correctly identified."""
    # Test cases with clean outputs
    clean_texts = [
        "This is a normal response with no corruption.",
        "Hello, I am Lira. How can I help you today?",
        "The weather today is sunny with a high of 75°F.",
        "I think that's an interesting question. Let me think about it.",
        "Here's a list of items: 1) Apples, 2) Bananas, 3) Oranges."
    ]
    
    # Test cases with corrupted outputs
    corrupted_texts = [
        # Code blocks with content
        "```\nHello\n```",
        # Multiple backticks
        "````````",
        # HTML-like tags
        "<lira>Hello</lira>",
        "<assistant>This is a response</assistant>",
        # Path-like patterns
        "/usr/local/bin/lira",
        "/LIRA/system/response/",
        # Multiple parens/braces
        "Hello ))))))",
        "Something }}}}",
        # Special markers
        "(*)(*)",
        "====",
        # High ratio of special chars
        "}} }} ]] )) ** // \\ {{ (( ]] {{",
        # Pipe separators
        "| | | | | |",
        # Complex mixed corruption
        "```}\n```/lira/\n(*) (*) (*)"
    ]
    
    # Test clean texts - should not detect corruption
    for text in clean_texts:
        assert model_manager._is_corrupted_output(text) == False, f"False positive: {text}"
    
    # Test corrupted texts - should detect corruption
    for text in corrupted_texts:
        assert model_manager._is_corrupted_output(text) == True, f"False negative: {text}"


@pytest.mark.pikachu(name="test_cleanup", description="Test cleanup of corrupted output")
def test_cleanup_response(model_manager):
    """Test that corrupted outputs are cleaned correctly."""
    # Test cases with corrupted outputs and expected cleaned results
    test_cases = [
        # Simple markdown code block
        (
            "This is a ```code block``` with some text.",
            "This is a with some text."
        ),
        # HTML-like tags
        (
            "Welcome <lira>back</lira> to the conversation.",
            "Welcome to the conversation."
        ),
        # Path patterns
        (
            "Check out /usr/local/bin/file and /another/path/here",
            "Check out and"
        ),
        # Multiple special characters
        (
            "Hello )))))) and {{{{{{ world",
            "Hello and world"
        ),
        # Complex mixed corruption with good content
        (
            "Lira here! Hello again. I'm glad we could connect like this. ```}\n```/lira/\n(*) (*) (*) What's been going through your mind lately?",
            "Lira here! Hello again. I'm glad we could connect like this. What's been going through your mind lately?"
        ),
        # Good sentences with corruption between
        (
            "This is a good sentence. ```}}}``` This is another good sentence.",
            "This is a good sentence. This is another good sentence."
        ),
        # Extremely corrupted output
        (
            "`````` (*) (*) /LIRA/ ======= ````` ))))))) }}}}}",
            "I'm sorry, but I couldn't generate a clear response. Could you please ask your question again?"
        )
    ]
    
    # Test each case
    for corrupted, expected in test_cases:
        cleaned = model_manager._cleanup_response(corrupted)
        # Strip any potential whitespace for comparison
        cleaned = cleaned.strip()
        expected = expected.strip()
        assert cleaned == expected, f"Cleanup failed:\nInput: {corrupted}\nExpected: {expected}\nGot: {cleaned}"


@pytest.mark.pikachu(name="test_cleanup_real", description="Test cleanup of real corrupted outputs")
def test_cleanup_real_examples(model_manager):
    """Test cleanup with real examples from logs."""
    # Real example of corrupted output from logs
    real_corrupted = """Lira
</|>

````
````/````

(Looking forward)
```
Enter text here...
```
) ) ) ) )
```
)/)</|>

( ( ( ( ) ) )

(Courtesy of CACOM )
```

(  ` ```)

(Fresh Start :) :)"""

    # Clean the real corrupted output
    cleaned = model_manager._cleanup_response(real_corrupted)
    
    # Check that cleaned output is reasonable
    assert len(cleaned) > 0
    assert '```' not in cleaned
    assert ')))' not in cleaned
    assert '(//)' not in cleaned
    assert '/LIRA/' not in cleaned
    assert '</|>' not in cleaned


@pytest.mark.pikachu(name="test_llama3_response_extraction", description="Test Llama-3 response extraction")
def test_extract_response_llama3(model_manager):
    """Test extracting responses from Llama-3 format with cleanup for corrupted outputs."""
    # Mock config to be a Llama-3 model
    with patch.dict(model_manager.config, {"base_model": "llama-3-test"}):
        # Test clean Llama-3 format
        clean_generated = "<|begin_of_text|><|system|>\nSystem prompt\n<|user|>\nUser query\n<|assistant|>\nThis is a clean response."
        response = model_manager._extract_response(clean_generated, "any prompt")
        assert response == "This is a clean response."
        
        # Test corrupted Llama-3 format
        corrupted_generated = "<|begin_of_text|><|system|>\nSystem prompt\n<|user|>\nUser query\n<|assistant|>\nThis is ```}}}\n```/lira/\n(*) (*) a corrupted response."
        
        # Patch the _is_corrupted_output and _cleanup_response methods
        with patch.object(model_manager, '_is_corrupted_output', return_value=True):
            with patch.object(model_manager, '_cleanup_response', return_value="This is a cleaned response."):
                response = model_manager._extract_response(corrupted_generated, "any prompt")
                assert response == "This is a cleaned response."


@pytest.mark.pikachu(name="test_generate_response_cleanup", description="Test response cleanup during generation")
def test_generate_response_with_cleanup(model_manager):
    """Test that generate_response applies cleanup when needed."""
    # Mock generate to return a corrupted response
    encode_return = MagicMock()
    encode_return.to.return_value = encode_return
    model_manager.tokenizer.encode.return_value = encode_return
    model_manager.tokenizer.decode.return_value = "This is ```}}}```/lira/ a corrupted response."
    
    # Patch the _is_corrupted_output and _cleanup_response methods
    with patch.object(model_manager, '_is_corrupted_output', return_value=True):
        with patch.object(model_manager, '_cleanup_response', return_value="This is a cleaned response."):
            # Test generation with cleanup
            response = model_manager.generate_response("Test query")
            assert response == "This is a cleaned response."