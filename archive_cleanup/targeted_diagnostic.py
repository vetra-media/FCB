import os

def fix_refresh_to_back():
    files = ['formatters.py', 'handlers.py', 'main.py', 'scanner.py', 'analysis.py', 'config.py']
    
    replacements = [
        # Your existing replacements (good!)
        ('🔄 REFRESH', '⬅️ BACK'),
        ('🔄 Refresh', '⬅️ Back'), 
        ('refresh_', 'back_'),
        ('format_out_of_scans_refresh_message', 'format_out_of_scans_back_message'),
        ('build_out_of_scans_refresh_keyboard', 'build_out_of_scans_back_keyboard'),
        
        # MISSING REPLACEMENTS - Add these:
        ('🔄 REFRESH button works', '⬅️ BACK button works'),
        ('- 🔄 REFRESH button works', '- ⬅️ BACK button works'),
        ('REFRESH', 'BACK'),
        ('Refresh', 'Back'),
        ('refresh', 'back'),
        ('Instant 🔄 Refresh', 'Free ⬅️ Back'),
        ('- Instant 🔄 Refresh and 🎰 Spin buttons', '- Free ⬅️ BACK and paid 🎰 NEXT buttons'),
        ('🔄 Refresh any coin anytime', '⬅️ BACK any coin anytime (free navigation)'),
        ('Instant refresh', 'Free back navigation'),
    ]
    
    total_changes = 0
    
    for file_path in files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_changes = 0
            
            for old, new in replacements:
                before_count = content.count(old)
                content = content.replace(old, new)
                changes = before_count - content.count(old)
                file_changes += changes
                
                if changes > 0:
                    print(f"  ✅ {file_path}: '{old}' → '{new}' ({changes}x)")
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Updated {file_path} ({file_changes} total changes)")
                total_changes += file_changes
            else:
                print(f"⚪ No changes in {file_path}")
        else:
            print(f"❌ File not found: {file_path}")
    
    print(f"\n🎯 Total changes made: {total_changes}")
    return total_changes

# Run it
fix_refresh_to_back()

# After running, you still need to manually check:
print("\n📋 MANUAL CHECKS STILL NEEDED:")
print("1. handlers.py - Remove any remaining refresh callback handling")
print("2. formatters.py - Make sure function definitions match the new names")
print("3. Test the ⬅️ BACK button works (free navigation)")
print("4. Test the 🎰 NEXT button costs tokens")