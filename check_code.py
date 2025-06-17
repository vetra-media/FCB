#!/usr/bin/env python3
"""
Diagnostic script to check handlers directory structure
Run this to see what files exist and diagnose import issues
"""

import os
import sys

def check_handlers_directory():
    """Check the handlers directory structure"""
    
    print("🔍 CHECKING HANDLERS DIRECTORY STRUCTURE")
    print("=" * 50)
    
    # Check if handlers directory exists
    handlers_path = "handlers"
    if not os.path.exists(handlers_path):
        print(f"❌ ERROR: {handlers_path} directory does not exist!")
        return False
    
    print(f"✅ {handlers_path} directory exists")
    
    # List all files in handlers directory
    print(f"\n📁 Files in {handlers_path}:")
    try:
        files = os.listdir(handlers_path)
        for file in sorted(files):
            file_path = os.path.join(handlers_path, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"  📄 {file} ({size} bytes)")
            else:
                print(f"  📁 {file}/ (directory)")
    except Exception as e:
        print(f"❌ Error listing files: {e}")
        return False
    
    # Check for required files
    required_files = [
        '__init__.py',
        'core.py', 
        'commands.py',
        'callbacks.py',
        'discovery.py',
        'navigation.py',
        'payments.py',
        'utils.py',
        'campaigns.py',
        'errors.py'
    ]
    
    print(f"\n🔍 Checking for required files:")
    missing_files = []
    for file in required_files:
        file_path = os.path.join(handlers_path, file)
        if os.path.exists(file_path):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING!")
            missing_files.append(file)
    
    # Check Python syntax of existing files
    print(f"\n🐍 Checking Python syntax:")
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(handlers_path, file)
            try:
                with open(file_path, 'r') as f:
                    compile(f.read(), file_path, 'exec')
                print(f"  ✅ {file} - syntax OK")
            except SyntaxError as e:
                print(f"  ❌ {file} - syntax error: {e}")
            except Exception as e:
                print(f"  ⚠️  {file} - could not check: {e}")
    
    # Try importing handlers
    print(f"\n🔄 Testing imports:")
    sys.path.insert(0, '.')
    
    try:
        import handlers
        print("  ✅ import handlers - SUCCESS")
    except Exception as e:
        print(f"  ❌ import handlers - FAILED: {e}")
    
    try:
        from handlers import setup_handlers
        print("  ✅ from handlers import setup_handlers - SUCCESS")
    except Exception as e:
        print(f"  ❌ from handlers import setup_handlers - FAILED: {e}")
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"  Total files: {len(files)}")
    print(f"  Missing required files: {len(missing_files)}")
    if missing_files:
        print(f"  Missing: {', '.join(missing_files)}")
    
    return len(missing_files) == 0

if __name__ == "__main__":
    success = check_handlers_directory()
    if success:
        print("\n🎉 All checks passed!")
    else:
        print("\n❌ Issues found - see above for details")
    
    print("\n💡 Next steps:")
    print("1. Make sure all required .py files exist in handlers/")
    print("2. Check that each file has valid Python syntax")
    print("3. Try running main.py again")