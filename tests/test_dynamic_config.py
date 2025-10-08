#!/usr/bin/env python3
"""Test script for dynamic configuration reloading"""

import config
import time
import os

def test_dynamic_reloading():
    print("Testing Dynamic Configuration Reloading")
    print("=" * 50)
    
    config_file = os.path.join(os.getcwd(), 'model_config.ini')
    backup_file = config_file + '.backup'
    
    try:
        # Create backup of original config
        with open(config_file, 'r') as f:
            original_content = f.read()
        
        with open(backup_file, 'w') as f:
            f.write(original_content)
        
        print("✓ Created backup of original configuration")
        
        # Load initial configuration
        initial_config = config.load_model_config()
        print(f"Initial simple model: {initial_config['simple_model']}")
        print(f"Initial intelligent selection: {initial_config['enable_intelligent_selection']}")
        
        # Modify the configuration file
        modified_content = original_content.replace(
            'simple_model = gpt-4o-mini', 
            'simple_model = gpt-4o'
        ).replace(
            'enable_intelligent_model_selection = true',
            'enable_intelligent_model_selection = false'
        )
        
        with open(config_file, 'w') as f:
            f.write(modified_content)
        
        print("\n✓ Modified configuration file")
        
        # Wait a moment for file system
        time.sleep(0.1)
        
        # Load configuration again
        new_config = config.load_model_config()
        print(f"New simple model: {new_config['simple_model']}")
        print(f"New intelligent selection: {new_config['enable_intelligent_selection']}")
        
        # Verify changes were detected
        if (new_config['simple_model'] != initial_config['simple_model'] and
            new_config['enable_intelligent_selection'] != initial_config['enable_intelligent_selection']):
            print("✓ Configuration changes detected successfully!")
            success = True
        else:
            print("✗ Configuration changes not detected")
            success = False
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        success = False
    
    finally:
        # Restore original configuration
        try:
            with open(backup_file, 'r') as f:
                original_content = f.read()
            
            with open(config_file, 'w') as f:
                f.write(original_content)
            
            os.remove(backup_file)
            print("✓ Restored original configuration")
        except Exception as e:
            print(f"⚠️ Failed to restore original configuration: {e}")
    
    return success

if __name__ == "__main__":
    success = test_dynamic_reloading()
    print(f"\nDynamic Reloading Test: {'SUCCESS' if success else 'FAILED'}")