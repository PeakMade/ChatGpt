#!/usr/bin/env python3
"""
Test script to verify model switching functionality
"""

from app_flask import select_optimal_model
from config.config import get_model_for_task, is_intelligent_selection_enabled, get_complexity_threshold

def test_model_switching():
    print('=== MODEL SWITCHING TEST ===')
    print(f'Intelligent Selection Enabled: {is_intelligent_selection_enabled()}')
    print(f'Complexity Threshold: {get_complexity_threshold()}')
    print()
    print('Available Models:')
    print(f'  Simple: {get_model_for_task("simple")}')
    print(f'  Complex: {get_model_for_task("complex")}')
    print(f'  Web Search: {get_model_for_task("web_search")}')
    print(f'  Fallback: {get_model_for_task("fallback")}')
    print()

    # Test cases
    test_cases = [
        'Hello, how are you?',
        'Can you analyze the current real estate market trends and provide a comprehensive evaluation of investment opportunities?',
        'What are the pros and cons of using Python vs JavaScript for web development?',
        'Please compare and evaluate the advantages and disadvantages of different programming languages',
        'Calculate 2+2',
        'Write a simple hello world program',
        'This is a very long message that should exceed the complexity threshold because it contains many words and should trigger the complex model selection based on length alone without needing any specific keywords',
        'analyze the market trends',
        'research the best practices',
        'explain how neural networks work step by step'
    ]

    for i, message in enumerate(test_cases, 1):
        selected = select_optimal_model(message)
        short_msg = message[:80] + '...' if len(message) > 80 else message
        print(f'Test {i}: {short_msg}')
        print(f'  Length: {len(message)} chars')
        print(f'  Selected Model: {selected}')
        print()

if __name__ == '__main__':
    test_model_switching()