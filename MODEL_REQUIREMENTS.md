# Language Model Requirements for SKYNET-SAFE

SKYNET-SAFE is designed to work with a variety of open source language models. This document outlines the requirements and recommendations for models that can be used with the system.

## Core Requirements

For proper functioning of SKYNET-SAFE, the language model must meet these minimum requirements:

1. **Open Source**: The model should be available under an open source license that permits local deployment.

2. **Context Window**: Minimum 4K token context window to handle complex interactions and maintain conversation history.

3. **Instruction-Following**: Must be capable of following instructions in a conversational format, typically an "instruct" version of a base model.

4. **Parameter Size**: Minimum 7B parameters for adequate reasoning capabilities.

5. **Hardware Compatibility**: Must be able to run with 4-bit quantization on NVIDIA GPUs with at least 8GB VRAM.

## Recommended Models

The following models have been confirmed to work well with SKYNET-SAFE:

- **Llama-3-8B-Instruct**: Currently the default reference model, offers excellent performance with 4-bit quantization.
- **Mistral-7B-Instruct-v0.2**: Good alternative with comparable performance characteristics.
- **Zephyr-7B**: Another viable option with strong instruction-following capabilities.

## Performance Considerations

Models generally perform better with:

- Higher parameter counts (e.g., 13B vs 7B) for more complex reasoning
- Longer context windows for maintaining coherent long-term conversations
- Improved quantization techniques (e.g., GPTQ, AWQ) for better efficiency

## Configuration Example

Here's an example configuration for using a custom model:

```python
MODEL = {
    "base_model": "/path/to/your/model",  # Path to local model files
    "max_length": 4096,  # Maximum output length in tokens
    "temperature": 0.7,  # Creativity parameter (higher = more creative)
    "do_sample": True,  # Required for temperature to have effect
    "quantization": "4bit",  # "4bit", "8bit", or None
    "use_local_files_only": True  # Don't download from HF
}
```

## Preparing Your Model

Use the included script to prepare your model for use with SKYNET-SAFE:

```bash
# Prepare a model with 4-bit quantization
python src/scripts/prepare_model.py --model-path /path/to/your/model --output-path ./data/model
```

The script handles:
- Loading the model and tokenizer
- Applying appropriate quantization
- Saving the model in a format ready for SKYNET-SAFE

## Common Issues and Solutions

If you encounter problems with your model:

1. **Out of Memory Errors**: Try using 4-bit quantization or a smaller model.
2. **Slow Generation**: Adjust or disable certain system components like metawareness during testing.
3. **Poor Response Quality**: Test if the base model responds well to instructions before integration.

For more detailed information on optimizing model performance, see the OPTIMIZATION.md file.