#!/usr/bin/env python3
"""
Model preparation script for SKYNET-SAFE.
This script prepares a local open source LLM by loading it and applying 
appropriate quantization for efficient operation.
"""

import os
import sys
import argparse
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ModelPreparation")

def prepare_model(model_path, output_path, quantization="4bit"):
    """
    Prepare a local open source language model for use with SKYNET-SAFE.
    
    Parameters:
    -----------
    model_path : str
        Path to the local model directory
    output_path : str
        Path where the prepared model should be saved
    quantization : str
        Quantization method to use (None, "4bit", "8bit")
    """
    logger.info(f"Preparing model from {model_path}")
    logger.info(f"Output path: {output_path}")
    logger.info(f"Quantization: {quantization}")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    try:
        # Load and prepare tokenizer
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path, 
            use_local_files_only=True
        )
        tokenizer.save_pretrained(output_path)
        logger.info("Tokenizer saved successfully")
        
        # Prepare model loading parameters
        model_kwargs = {
            "device_map": "auto",
            "use_local_files_only": True,
        }
        
        # Add quantization parameters
        if quantization == "4bit":
            model_kwargs["load_in_4bit"] = True
            logger.info("Using 4-bit quantization")
        elif quantization == "8bit":
            model_kwargs["load_in_8bit"] = True
            logger.info("Using 8-bit quantization")
        
        # Load and quantize model
        logger.info("Loading model (this may take several minutes)...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path, 
            **model_kwargs
        )
        
        # Save model
        logger.info("Saving prepared model...")
        model.save_pretrained(output_path)
        logger.info("Model prepared and saved successfully")
        
    except Exception as e:
        logger.error(f"Error preparing model: {e}")
        return False
    
    return True

def main():
    """Parse command line arguments and prepare the model."""
    parser = argparse.ArgumentParser(description="Prepare a local LLM for SKYNET-SAFE")
    parser.add_argument("--model-path", type=str, required=True,
                      help="Path to the local model directory")
    parser.add_argument("--output-path", type=str, default="./data/model",
                      help="Path where the prepared model should be saved")
    parser.add_argument("--quantization", type=str, choices=[None, "4bit", "8bit"], 
                      default="4bit",
                      help="Quantization method (None, 4bit, 8bit)")
    
    args = parser.parse_args()
    
    # Print CUDA information
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"CUDA device count: {torch.cuda.device_count()}")
        logger.info(f"CUDA current device: {torch.cuda.current_device()}")
        logger.info(f"CUDA device name: {torch.cuda.get_device_name(0)}")
    
    # Prepare the model
    success = prepare_model(
        args.model_path,
        args.output_path,
        args.quantization
    )
    
    if success:
        logger.info("Model preparation completed successfully")
        # Log model size info
        model_size = sum(os.path.getsize(os.path.join(args.output_path, f)) 
                        for f in os.listdir(args.output_path) 
                        if os.path.isfile(os.path.join(args.output_path, f)))
        logger.info(f"Total model size: {model_size / (1024**3):.2f} GB")
        sys.exit(0)
    else:
        logger.error("Model preparation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()