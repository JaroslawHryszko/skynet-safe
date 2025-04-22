"""Utility module for cleaning and processing text output from language models."""

import re
from typing import Optional

def cleanup_model_output(text: str, aggressive: bool = False) -> str:
    """Cleans up potentially corrupted output from language models.
    
    This consolidated function combines multiple cleanup strategies to handle
    various forms of corruption or unwanted artifacts in model outputs.
    
    Args:
        text: Text to clean up
        aggressive: Whether to use more aggressive cleaning (removes more content)
        
    Returns:
        Cleaned text
    """
    # Keep original for comparison
    original_text = text
    
    # First try to extract good sentences if they exist
    good_sentences = re.findall(r'[A-Z][^.!?\n]{10,}[.!?]', text)
    
    # If we found a reasonable amount of good sentences, just use those
    if good_sentences and len(' '.join(good_sentences)) > len(original_text) * 0.3:
        return ' '.join(good_sentences)
    
    # Clean up code blocks and their content
    text = re.sub(r'```[^`]*```', ' ', text, flags=re.DOTALL)
    text = re.sub(r'`{3,}', ' ', text)
    
    # Clean up individual code ticks
    text = re.sub(r'`[^`\n]*`', ' ', text)
    text = re.sub(r'`{1,5}', ' ', text)
    
    # Remove HTML/XML style tags
    text = re.sub(r'</?[A-Za-z]+[^>]*>', ' ', text)
    
    # Remove path-like structures
    text = re.sub(r'/[A-Za-z/_.]+/', ' ', text)
    
    # Remove markers like (Lira:) 
    text = re.sub(r'\([A-Za-z]+:?\)', ' ', text)
    
    # Remove other special markers
    text = re.sub(r'\(\*\)', ' ', text)
    text = re.sub(r'/LIRA/', ' ', text)
    text = re.sub(r'=====', ' ', text)
    
    # Remove lines with only special characters
    text = re.sub(r'^[^\w\s]*$', '', text, flags=re.MULTILINE)
    
    # Remove multiple brackets, braces, etc.
    #text = re.sub(r'[\)\}\(\{\[\]\/\\]{2,}', ' ', text)
    #text = re.sub(r'[\)\}\(\{\[\]\/\\]+$', '', text, flags=re.MULTILINE)
    
    # Remove vertical bars and other separators
    text = re.sub(r'\|+\s*\|+', ' ', text)
    text = re.sub(r'#+\s*#+', ' ', text)
    
    # If aggressive mode, do more cleanup
    if aggressive:
        # Try to extract only text that looks reasonably clean
        clean_lines = []
        for line in text.split('\n'):
            # Calculate the ratio of special characters to line length
            special_chars = len(re.findall(r'[^\w\s]', line))
            if len(line) > 5 and special_chars / max(1, len(line)) < 0.2:
                clean_lines.append(line)
        
        if clean_lines:
            text = '\n'.join(clean_lines)
    
    # Clean up whitespace - multiple spaces, newlines, etc.
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = text.strip()
    
    # If text is still heavily corrupted, fall back to more aggressive extraction
    if len(re.findall(r'[^\w\s]', text)) > len(text) / 4:
        # Try to extract sentence fragments that look reasonable
        sentence_fragments = re.findall(r'[A-Z][a-z]{2,}[^.!?\n]{5,}[.!?]', text)
        if sentence_fragments:
            text = ' '.join(sentence_fragments)
    
    # If we still have nothing useful, return a message
    if not text.strip() or len(text.strip()) < 10:
        return "Sorry, the system generated corrupted output that could not be cleaned."
    
    return text.strip()