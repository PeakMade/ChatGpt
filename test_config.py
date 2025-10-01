#!/usr/bin/env python3
"""Test script for the external configuration system"""

import config
import os
import time

def test_configuration():
    print("Testing External Configuration System")
    print("=" * 50)
    
    # Test loading configuration
    try:
        model_config = config.load_model_config()
        print("✓ Configuration loaded successfully")
        
        print("\nModel Configuration:")
        print(f"  Simple Model: {model_config['simple_model']}")
        print(f"  Complex Model: {model_config['complex_model']}")
        print(f"  Web Search Model: {model_config['web_search_model']}")
        print(f"  Fallback Model: {model_config['fallback_model']}")
        
        print(f"\nSettings:")
        print(f"  Intelligent Selection: {model_config['enable_intelligent_selection']}")
        print(f"  Complexity Threshold: {model_config['complexity_threshold']}")
        print(f"  Model Display Name: {model_config['model_display_name']}")
        
        print(f"\nFile Info:")
        config_file = os.path.join(os.getcwd(), 'model_config.ini')
        if os.path.exists(config_file):
            mod_time = os.path.getmtime(config_file)
            print(f"  Config File: {config_file}")
            print(f"  Last Modified: {time.ctime(mod_time)}")
            print(f"  File Size: {os.path.getsize(config_file)} bytes")
        else:
            print(f"  Config File: NOT FOUND at {config_file}")
            
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False
    
    # Test dynamic reloading
    print("\nTesting Dynamic Reloading:")
    try:
        # Load twice to test caching
        config1 = config.load_model_config()
        config2 = config.load_model_config()
        
        if config1 == config2:
            print("✓ Configuration caching working correctly")
        else:
            print("✗ Configuration caching inconsistent")
            
    except Exception as e:
        print(f"✗ Dynamic reloading test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_configuration()
    print(f"\nTest Result: {'SUCCESS' if success else 'FAILED'}")