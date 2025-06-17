"""
handlers/campaigns.py - Admin Campaign Commands
Campaign link generation and analytics for administrators
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

# Campaign imports
from campaign_manager import campaign_manager

# =============================================================================
# ADMIN CAMPAIGN COMMANDS
# =============================================================================

async def campaign_links_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command: Get all campaign links"""
    user_id = update.effective_user.id
    
    # Import here to avoid circular imports
    try:
        from config import ADMIN_USER_IDS
    except ImportError:
        ADMIN_USER_IDS = []
    
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("🚫 Admin access required")
        return
    
    links_text = campaign_manager.generate_all_links()
    await update.message.reply_text(links_text, parse_mode='Markdown')

async def campaign_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command: View campaign analytics"""
    user_id = update.effective_user.id
    
    # Import here to avoid circular imports
    try:
        from config import ADMIN_USER_IDS, ANALYTICS_ENABLED
    except ImportError:
        ADMIN_USER_IDS = []
        ANALYTICS_ENABLED = True
    
    if user_id not in ADMIN_USER_IDS:
        await update.message.reply_text("🚫 Admin access required")
        return
    
    if not ANALYTICS_ENABLED:
        await update.message.reply_text("📊 Analytics disabled in config")
        return
    
    report = campaign_manager.get_analytics_report()
    await update.message.reply_text(report, parse_mode='Markdown')