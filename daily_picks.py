import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from telegram.error import TelegramError
from config import Config
from database import Database

logger = logging.getLogger(__name__)
db = Database()


async def send_daily_picks(app):
    """Send daily picks to all paid subscribers"""
    
    # Get all active users
    users = db.get_active_users()
    
    if not users:
        logger.info("No active users to send picks to")
        return
    
    # Your daily picks message - replace with your data source
    picks_message = (
        "📊 <b>Today's OddsLab Premium Picks</b>\n"
        f"📅 {datetime.now().strftime('%B %d, %Y')}\n\n"
        
        "⚽ <b>Football</b>\n"
        "└ Liverpool vs Man City - 18:00 GMT\n"
        "   📌 Over 2.5 Goals @ 1.85\n"
        "   🎯 Confidence: 75%\n"
        "   💰 Suggested Stake: €20\n\n"
        
        "🏀 <b>Basketball</b>\n"
        "└ Lakers vs Celtics - 23:30 GMT\n"
        "   📌 Lakers -5.5 @ 1.90\n"
        "   🎯 Confidence: 68%\n"
        "   💰 Suggested Stake: €15\n\n"
        
        "🎾 <b>Tennis</b>\n"
        "└ Djokovic vs Alcaraz - 15:00 GMT\n"
        "   📌 Over 23.5 Games @ 1.92\n"
        "   🎯 Confidence: 72%\n"
        "   💰 Suggested Stake: €25\n\n"
        
        "⏰ All picks analysis available in the channel\n"
        "🔔 Good luck! 🍀"
    )
    
    success_count = 0
    failed_count = 0
    
    for user in users:
        try:
            await app.bot.send_message(
                chat_id=int(user.user_id),
                text=picks_message,
                parse_mode="HTML"
            )
            success_count += 1
        except TelegramError as e:
            logger.warning(f"Failed to send picks to user {user.user_id}: {e}")
            failed_count += 1
        except Exception as e:
            logger.error(f"Unexpected error sending to {user.user_id}: {e}")
            failed_count += 1
    
    logger.info(f"✅ Daily picks sent: {success_count} success, {failed_count} failed")
    db.add_metric("picks_sent", 0, metadata=f"success:{success_count},failed:{failed_count}")


def setup_daily_picks(app, database):
    """Setup daily picks scheduler"""
    global db
    db = database
    
    scheduler = AsyncIOScheduler(timezone=Config.TIMEZONE)
    
    # Schedule picks to be sent at 9 AM CET every day
    scheduler.add_job(
        send_daily_picks,
        'cron',
        hour=Config.PICKS_TIME.hour,
        minute=Config.PICKS_TIME.minute,
        timezone=Config.TIMEZONE,
        args=[app],
        id='send_daily_picks'
    )
    
    scheduler.start()
    logger.info(f"📅 Daily picks scheduler started (9 AM {Config.TIMEZONE})")