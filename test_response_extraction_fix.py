#!/usr/bin/env python3
"""
Test script to verify the response extraction fix in model_manager.py
This test simulates the model response extraction process.
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import config
from src.modules.model.model_manager import ModelManager

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_response_extraction():
    """Test the response extraction with a simple query."""
    print("🔧 Testing Response Extraction Fix")
    print("=" * 50)
    
    try:
        # Initialize the model manager
        print("📦 Loading model...")
        model_manager = ModelManager(config.MODEL)
        print("✅ Model loaded successfully!")
        
        # Test with a simple query
        test_query = "Jak się dzisiaj czujesz?"
        print(f"\n🤖 Testing with query: '{test_query}'")
        
        # Generate response
        response = model_manager.generate_response(test_query)
        
        print(f"\n📤 Generated response:")
        print(f"'{response}'")
        print(f"\n📊 Response length: {len(response)} characters")
        
        # Check if the response contains the prompt (which should not happen with the fix)
        if test_query.lower() in response.lower():
            print("❌ ISSUE: Response still contains the query/prompt!")
            return False
        elif any(marker in response for marker in ["<|system|>", "<|user|>", "<|assistant|>", "<|begin_of_text|>"]):
            print("❌ ISSUE: Response contains prompt markers!")
            return False
        else:
            print("✅ SUCCESS: Response looks clean (no prompt included)")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_response_extraction()
    sys.exit(0 if success else 1)