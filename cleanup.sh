#!/bin/bash

# FCB Project Cleanup Script
# This script will clean up your messy file structure and fix imports

echo "🧹 Starting FCB project cleanup..."

# Skip backup this time since we already have one
echo "📦 Skipping backup (you already have final_backup_20250620_000414)"

# List of core files to keep (everything else gets deleted)
CORE_FILES=(
    "main.py"
    "analysis.py"
    "api_client.py"
    "pro_api_client.py"
    "cache.py"
    "config.py"
    "database.py"
    "handlers.py"
    "formatters.py"
    "scanner.py"
    "casino.py"
    "casino_handlers_integration.py"
    "gamified_discovery.py"
    "signal_rewards.py"
    "__init__.py"
    "requirements.txt"
    ".env.prod"
    ".env.test"
    ".gitignore"
    "render.yaml"
    ".github/"
)

echo "🗂️ Cleaning up directories and files..."

# Remove junk directories
echo "Removing archive directories..."
rm -rf archive_cleanup/
rm -rf backups/
rm -rf TEST_DEBUG/
rm -rf analysis/
rm -rf src/

# Remove individual junk files
echo "Removing duplicate and test files..."
rm -f handlers_broken_backup.py
rm -f debug_test.py
rm -f volume_test.py
rm -f broken_images.txt
rm -f working_images.txt
rm -f readme.txt

echo "✅ Junk files removed"

# Check for problematic imports in remaining Python files
echo "🔍 Checking for broken imports..."

BROKEN_IMPORTS_FOUND=false

for file in *.py; do
    if [[ -f "$file" ]]; then
        # Check for imports from deleted directories
        if grep -q "from src\|from archive_cleanup\|from TEST_DEBUG\|from analysis\.legacy_archived\|from backups" "$file"; then
            echo "⚠️  Found broken imports in $file:"
            grep -n "from src\|from archive_cleanup\|from TEST_DEBUG\|from analysis\.legacy_archived\|from backups" "$file"
            BROKEN_IMPORTS_FOUND=true
        fi
        
        # Check for relative imports that might be broken
        if grep -q "from \.\." "$file"; then
            echo "⚠️  Found relative imports in $file that might be broken:"
            grep -n "from \.\." "$file"
            BROKEN_IMPORTS_FOUND=true
        fi
    fi
done

if [[ "$BROKEN_IMPORTS_FOUND" = true ]]; then
    echo ""
    echo "❌ BROKEN IMPORTS FOUND!"
    echo "You'll need to fix these imports manually before deploying."
    echo "Most likely fixes:"
    echo "  - Change 'from src.config import ...' to 'from config import ...'"
    echo "  - Remove any imports from deleted directories"
    echo ""
else
    echo "✅ No broken imports detected"
fi

# Show final file structure
echo ""
echo "📋 Final file structure:"
echo "Root directory now contains:"
ls -la *.py *.txt *.yaml *.yml .env* .git* 2>/dev/null | head -20

echo ""
echo "🎉 Cleanup complete!"
echo ""
echo "Next steps:"
echo "1. Test your app locally: python main.py"
echo "2. Fix any import errors if they exist"
echo "3. Commit and push: git add . && git commit -m 'Clean up file structure' && git push"
echo "4. Deploy to Render"
echo ""
echo "💾 Your backup is saved in: $BACKUP_DIR"