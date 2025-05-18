"""Utility module for cleaning and processing text output from language models."""

import re
from typing import Optional

def cleanup_model_output(text: str, aggressive: bool = False) -> str:
    """Cleans up potentially corrupted output from language models.

    Args:
        text: Text to clean up
        aggressive: Whether to use more aggressive cleaning (removes more content)
        
    Returns:
        Cleaned text
    """
    original_text = text

    # Extract good sentences
    good_sentences = re.findall(r'[A-Z][^.!?\n]{10,}[.!?]', text)
    if good_sentences and len(' '.join(good_sentences)) > len(original_text) * 0.3:
        return ' '.join(good_sentences)

    # Remove code blocks
    text = re.sub(r'```[^`]*```', ' ', text, flags=re.DOTALL)
    text = re.sub(r'`{3,}', ' ', text)
    text = re.sub(r'`[^`\n]*`', ' ', text)
    text = re.sub(r'`{1,5}', ' ', text)

    # Remove HTML/XML style tags
    text = re.sub(r'</?[A-Za-z]+[^>]*>', ' ', text)

    # Remove path-like structures
    text = re.sub(r'/[A-Za-z/_.]+/', ' ', text)

    # Remove specific markers (conservative)
    text = re.sub(r'/LIRA/', ' ', text)
    text = re.sub(r'=====', ' ', text)

    # Remove lines with only special characters
    text = re.sub(r'^[^\w\s]*$', '', text, flags=re.MULTILINE)

    # Remove vertical bars and separators
    text = re.sub(r'\|+\s*\|+', ' ', text)
    text = re.sub(r'#+\s*#+', ' ', text)

    # Aggressive line cleanup if requested
    if aggressive:
        clean_lines = []
        for line in text.split('\n'):
            special_chars = len(re.findall(r'[^\w\s]', line))
            if len(line) > 5 and special_chars / max(1, len(line)) < 0.2:
                clean_lines.append(line)
        if clean_lines:
            text = '\n'.join(clean_lines)

    # Whitespace normalization
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = text.strip()

    # Return fallback if empty
    if not text.strip() or len(text.strip()) < 10:
        return "Sorry, the system generated corrupted output that could not be cleaned."

    return text.strip()
