import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from config import Config
from database import Database
from metrics import MetricsTracker

logger = logging.getLogger(__name__)

db = Database()
metrics = MetricsTracker()


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin statistics"""
    if update.effective_user.id != Config.ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    conversion = metrics.get_conversion_stats()
    revenue = metrics.get_revenue_stats()
    
    stats_message = (
        "📊 <b>OddsLab Bot Statistics</b>\n\n"
        
        "<b>Onboarding Metrics:</b>\n"
        f"└ Total Starts: {conversion['total_starts']}\n"
        f"└ Onboarding Completes: {conversion['onboarding_completes']}\n"
        f"└ Onboarding Rate: {conversion['onboarding_rate']}\n\n"
        
        "<b>Payment Metrics:</b>\n"
        f"└ Successful Payments: {conversion['successful_payments']}\n"
        f"└ Conversion Rate: {conversion['conversion_rate']}\n\n"
        
        "<b>Revenue Metrics:</b>\n"
        f"└ Total Transactions: {revenue['total_transactions']}\n"
        f"└ Total Revenue: €{revenue['total_revenue']:.2f}\n"
        f"└ Average Transaction: €{revenue['avg_transaction']:.2f}\n\n"
        
        "<b>Active Subscribers:</b>\n"
        f"└ {len(db.get_active_users())} users\n"
    )
    
    await update.message.reply_text(stats_message, parse_mode="HTML")


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users"""
    if update.effective_user.id != Config.ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    users = db.get_all_users()
    
    if not users:
        await update.message.reply_text("No users found")
        return
    
    message = "👥 <b>All Users</b>\n\n"
    for user in users:
        message += (
            f"👤 {user.first_name} (@{user.username})\n"
            f"├ ID: {user.user_id}\n"
            f"├ Goal: {user.goal}\n"
            f"├ Sport: {user.sport}\n"
            f"├ Plan: {user.plan}\n"
            f"├ Amount: €{user.amount}\n"
            f"├ Status: {user.status}\n"
            f"└ Joined: {user.created_at.strftime('%Y-%m-%d')}\n\n"
        )
    
    # Split into chunks to avoid message size limit
    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="HTML")


async def admin_send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send broadcast message to all users"""
    if update.effective_user.id != Config.ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    
    broadcast_text = " ".join(context.args)
    users = db.get_active_users()
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=int(user.user_id),
                text=f"📢 <b>Announcement from OddsLab</b>\n\n{broadcast_text}",
                parse_mode="HTML"
            )
            success += 1
        except Exception as e:
            logger.error(f"Failed to send to {user.user_id}: {e}")
            failed += 1
    
    await update.message.reply_text(
        f"✅ Broadcast sent: {success} success, {failed} failed"
    )


def setup_admin_commands(app, database, metrics_tracker):
    """Setup admin commands"""
    global db, metrics
    db = database
    metrics = metrics_tracker
    
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("users", admin_users))
    app.add_handler(CommandHandler("broadcast", admin_send_broadcast))
    
    logger.info("✅ Admin commands setup complete")