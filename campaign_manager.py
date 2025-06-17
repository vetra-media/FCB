# campaign_manager.py - Centralized campaign management
from config import CAMPAIGNS, CAMPAIGN_LINKS, BOT_USERNAME, CAMPAIGN_TRACKING_ENABLED
from database import track_user_campaign, get_campaign_analytics

def format_campaign_welcome(campaign_data: dict):
    """Format welcome message based on campaign source"""
    
    if campaign_data['is_campaign_user']:
        source = campaign_data['source']
        platform_emoji = {
            'twitter': '🐦',
            'reddit': '🟠', 
            'instagram': '📸',
            'tiktok': '🎵',
            'youtube': '📺',
            'telegram': '✈️',
            'referral': '👥',
            'affiliate': '🤝'
        }
        
        emoji = platform_emoji.get(source, '🎯')
        welcome_text = f"{emoji} **Welcome from {source.title()}!** Thanks for discovering FOMO Crypto Bot!\n\n"
    else:
        welcome_text = "🎉 **Welcome to FOMO Crypto Bot!**\n\n"
    
    welcome_text += """🚀 **Your Crypto FOMO Discovery Tool**

🆓 **You get 5 FREE scans daily** + 3 bonus starter scans!
💎 **Find early opportunities** before they pump  
⚡ **Real-time alerts** with actionable insights

Ready to discover your next crypto gem?"""

    return welcome_text

def format_analytics_report(analytics_data: dict):
    """Format campaign analytics for admin view"""
    if not analytics_data:
        return "📊 No campaign data available yet."
    
    report = "📈 **Campaign Performance Report**\n\n"
    
    # User acquisition by source
    sources = analytics_data.get('sources', {})
    if sources:
        report += "👥 **User Acquisition:**\n"
        total_users = sum(sources.values())
        for source, count in sources.items():
            percentage = (count / total_users * 100) if total_users > 0 else 0
            report += f"• {source}: {count} users ({percentage:.1f}%)\n"
    
    # Conversion rates
    conversions = analytics_data.get('conversions', [])
    if conversions:
        report += "\n💰 **Purchase Conversion Rates:**\n"
        for source, total, buyers, rate in conversions:
            report += f"• {source}: {rate}% ({buyers}/{total} users)\n"
    
    report += f"\n📊 *Total tracked users: {sum(sources.values()) if sources else 0}*"
    
    return report

class CampaignManager:
    """Centralized campaign management that integrates with your existing architecture"""
    
    @staticmethod
    def get_active_campaigns():
        """Get all active campaign links from config"""
        return CAMPAIGN_LINKS
    
    @staticmethod
    def get_campaign_link(platform: str):
        """Get specific campaign link"""
        return CAMPAIGN_LINKS.get(platform, f"https://t.me/{BOT_USERNAME}")
    
    @staticmethod
    def process_start_command(user_id: int, args: list):
        """Process /start command with campaign tracking"""
        campaign_code = args[0] if args else None
        source = track_user_campaign(user_id, campaign_code)
        
        return {
            'campaign_code': campaign_code,
            'source': source,
            'is_campaign_user': bool(campaign_code),
            'welcome_type': 'campaign' if campaign_code else 'organic'
        }
    
    @staticmethod
    def get_analytics_report():
        """Get formatted analytics report"""
        if not CAMPAIGN_TRACKING_ENABLED:
            return "📊 Campaign tracking is disabled in configuration."
        
        data = get_campaign_analytics()
        return format_analytics_report(data)
    
    @staticmethod
    def generate_all_links():
        """Generate all campaign links for easy copying"""
        links_text = "🔗 **Active Campaign Links**\n\n"
        
        for platform, link in CAMPAIGN_LINKS.items():
            links_text += f"**{platform.title()}:**\n`{link}`\n\n"
        
        links_text += "💡 *Update campaigns in .env file to change all links instantly*"
        return links_text

# Global instance
campaign_manager = CampaignManager()