import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
    PreCheckoutQueryHandler,
)
from config import Config
from database import Database
from metrics import MetricsTracker
from daily_picks import setup_daily_picks
from admin import setup_admin_commands

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# States
GOAL, SPORT, STAKE_RANGE, CONFIRMED = range(4)
PAYMENT_PENDING = 5

# Initialize database and metrics
db = Database()
metrics = MetricsTracker()

GOAL_OPTIONS = [
    [InlineKeyboardButton("💰 Make consistent profit", callback_data="goal_profit")],
    [InlineKeyboardButton("📈 Grow a betting bank", callback_data="goal_grow")],
    [InlineKeyboardButton("🎯 Improve win rate", callback_data="goal_winrate")],
    [InlineKeyboardButton("🎲 Just enjoy it more", callback_data="goal_enjoy")],
]

SPORT_OPTIONS = [
    [InlineKeyboardButton("⚽ Football", callback_data="sport_football")],
    [InlineKeyboardButton("🏀 Basketball", callback_data="sport_basketball")],
    [InlineKeyboardButton("🎾 Tennis", callback_data="sport_tennis")],
    [InlineKeyboardButton("📊 Mixed", callback_data="sport_mixed")],
]

STAKE_OPTIONS = [
    [InlineKeyboardButton("🔵 $5-$25", callback_data="stake_low")],
    [InlineKeyboardButton("🟡 $25-$100", callback_data="stake_medium")],
    [InlineKeyboardButton("🔴 $100+", callback_data="stake_high")],
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command - Begin onboarding"""
    user = update.effective_user
    user_data = context.user_data
    user_data["name"] = user.first_name or "User"
    user_data["user_id"] = user.id
    user_data["username"] = user.username or "unknown"

    # Track user start
    metrics.track_user_start(user.id)
    logger.info(f"👋 User started: {user.first_name} ({user.id})")

    await update.message.reply_text(
        f"👋 Hey {user_data['name']}! Welcome to OddsLab. Before anything, 4 quick questions to personalise your experience...\n\n"
        "🎯 What's your main betting goal?",
        reply_markup=InlineKeyboardMarkup(GOAL_OPTIONS),
    )
    return GOAL


async def goal_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle goal selection"""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data
    goal_map = {
        "goal_profit": "💰 Make consistent profit",
        "goal_grow": "📈 Grow a betting bank",
        "goal_winrate": "🎯 Improve win rate",
        "goal_enjoy": "🎲 Just enjoy it more",
    }

    user_data["goal"] = goal_map.get(query.data, "Unknown")

    await query.edit_message_text(
        f"✅ Got it {user_data['name']}! {user_data['goal']}\n\n"
        "🏟 Which sport do you bet on most?",
        reply_markup=InlineKeyboardMarkup(SPORT_OPTIONS),
    )
    return SPORT


async def sport_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle sport selection"""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data
    sport_map = {
        "sport_football": "⚽ Football",
        "sport_basketball": "🏀 Basketball",
        "sport_tennis": "🎾 Tennis",
        "sport_mixed": "📊 Mixed",
    }

    user_data["sport"] = sport_map.get(query.data, "Unknown")

    await query.edit_message_text(
        "💰 What's your typical stake range per bet?",
        reply_markup=InlineKeyboardMarkup(STAKE_OPTIONS),
    )
    return STAKE_RANGE


async def stake_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle stake selection and show personalized pitch"""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data
    stake_map = {
        "stake_low": "$5-$25",
        "stake_medium": "$25-$100",
        "stake_high": "$100+",
    }

    user_data["stake"] = stake_map.get(query.data, "Unknown")

    # Generate personalized pitch
    sport = user_data.get("sport", "").split()[-1].lower()

    pitch = (
        f"✅ Got it {user_data['name']}. Based on your profile we'll focus on "
        f"{sport} value bets sized around your stake range.\n\n"
        "🔬 <b>OddsLab Premium</b>\n"
        "💰 €19/month or €49/3 months\n\n"
    )

    pricing_keyboard = [
        [InlineKeyboardButton("🔓 Join OddsLab (€19/mo)", callback_data="plan_monthly")],
        [InlineKeyboardButton("🔓 Join OddsLab (€49/3mo)", callback_data="plan_quarterly")],
        [InlineKeyboardButton("👀 See free tips first", callback_data="free_tips")],
        [InlineKeyboardButton("📊 View our record", callback_data="view_record")],
    ]

    # Track onboarding progress
    metrics.track_onboarding_complete(user_data["user_id"])
    logger.info(f"✅ Onboarding completed: {user_data['name']} - Goal: {user_data['goal']}, Sport: {user_data['sport']}")

    await query.edit_message_text(pitch, reply_markup=InlineKeyboardMarkup(pricing_keyboard), parse_mode="HTML")
    return CONFIRMED


async def free_tips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send free tips preview"""
    query = update.callback_query
    await query.answer()

    # Track free tips view
    metrics.track_free_tips_view(query.from_user.id)
    logger.info(f"👀 Free tips viewed by user {query.from_user.id}")

    await query.edit_message_text(
        "📊 <b>Today's Free Picks</b>\n\n"
        "⚽ <b>Liverpool vs Man City</b> - 18:00 GMT\n"
        "   📌 Over 2.5 Goals @ 1.85\n"
        "   🎯 Confidence: 75%\n\n"
        "🏀 <b>Lakers vs Celtics</b> - 23:30 GMT\n"
        "   📌 Lakers -5.5 @ 1.90\n"
        "   🎯 Confidence: 68%\n\n"
        "🔓 Want access to premium analysis and daily picks?\n"
        "Join OddsLab Premium today!",
        parse_mode="HTML",
    )


async def view_record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show track record"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📈 <b>OddsLab Track Record</b>\n\n"
        "Win Rate: 58.2%\n"
        "ROI: +34.5% (Last 30 days)\n"
        "Picks: 247\n"
        "Profit: +$2,340\n\n"
        "💰 Ready to join our winning community?",
        parse_mode="HTML",
    )


async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment plan selection"""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data
    plan_key = query.data.replace("plan_", "")
    plan = Config.PRICING_PLANS.get(plan_key)

    if not plan:
        await query.edit_message_text("❌ Invalid plan selected")
        return CONFIRMED

    user_data["plan"] = plan_key
    user_data["plan_name"] = plan["name"]
    user_data["plan_amount"] = plan["amount"]

    # Track payment initiation
    metrics.track_payment_initiated(query.from_user.id, plan_key)
    logger.info(f"💳 Payment initiated: {query.from_user.id} - Plan: {plan_key}")

    # Create invoice with Telegram Stars
    prices = [LabeledPrice(label=plan["name"], amount=plan["amount"])]

    await context.bot.send_invoice(
        chat_id=query.from_user.id,
        title=f"OddsLab Premium - {plan['name']}",
        description="Access to premium daily picks, analysis, and personalized recommendations for your betting strategy.",
        payload=f"oddslab_premium_{plan_key}_{query.from_user.id}_{datetime.now().timestamp()}",
        provider_token="",  # Empty for Telegram Stars
        currency=plan["currency"],
        prices=prices,
        start_parameter=f"oddslab_{plan_key}",
    )

    return PAYMENT_PENDING


async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answer precheckout query"""
    query = update.pre_checkout_query
    await query.answer(ok=True)
    logger.info(f"✅ Pre-checkout query approved for {query.from_user.id}")


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle successful payment"""
    user_data = context.user_data
    payment = update.message.successful_payment
    user = update.effective_user

    logger.info(
        f"✅ PAYMENT SUCCESSFUL: {user_data.get('name', 'Unknown')} ({user.id}) - "
        f"€{payment.total_amount/100} ({payment.currency})"
    )

    # Generate invite link for paid channel
    try:
        invite_link = await context.bot.create_chat_invite_link(
            chat_id=Config.PAID_CHANNEL_ID,
            member_limit=1,
            creates_join_request=False,
        )
        invite_url = invite_link.invite_link
        logger.info(f"✅ Invite link created: {invite_url}")
    except Exception as e:
        logger.error(f"❌ Failed to create invite link: {e}")
        invite_url = f"https://t.me/{Config.BOT_USERNAME}"

    # Save user to database
    db.add_user(
        user_id=user.id,
        username=user.username or "unknown",
        first_name=user_data.get("name", ""),
        goal=user_data.get("goal", ""),
        sport=user_data.get("sport", ""),
        stake=user_data.get("stake", ""),
        plan=user_data.get("plan", ""),
        payment_id=payment.telegram_payment_charge_id,
        amount=payment.total_amount / 100,
        currency=payment.currency,
    )

    # Track successful payment
    metrics.track_payment_successful(user.id, user_data.get("plan", ""), payment.total_amount / 100)

    # Send confirmation with invite link
    await update.message.reply_text(
        f"🎉 <b>Payment Successful!</b>\n\n"
        f"Welcome to OddsLab Premium!\n\n"
        f"👤 <b>Your Profile:</b>\n"
        f"  • Goal: {user_data.get('goal')}\n"
        f"  • Sport: {user_data.get('sport')}\n"
        f"  • Stake: {user_data.get('stake')}\n"
        f"  • Plan: {user_data.get('plan_name')}\n\n"
        f"🔗 <b>Join the channel:</b>\n"
        f"{invite_url}\n\n"
        f"✅ You'll start receiving daily picks tomorrow at 9 AM CET\n"
        f"📊 All analysis and tips will be sent directly to your DM",
        parse_mode="HTML",
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel conversation"""
    metrics.track_onboarding_cancelled(update.effective_user.id)
    logger.info(f"❌ Onboarding cancelled by user {update.effective_user.id}")
    await update.message.reply_text("❌ Onboarding cancelled. Type /start to begin again.")
    return ConversationHandler.END


def main():
    """Start the bot"""
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not TOKEN:
        raise ValueError("❌ TELEGRAM_BOT_TOKEN not set in environment")

    app = Application.builder().token(TOKEN).build()

    # Setup conversation handler for onboarding
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GOAL: [CallbackQueryHandler(goal_selected)],
            SPORT: [CallbackQueryHandler(sport_selected)],
            STAKE_RANGE: [CallbackQueryHandler(stake_selected)],
            CONFIRMED: [
                CallbackQueryHandler(plan_selected, pattern="^plan_"),
                CallbackQueryHandler(free_tips, pattern="free_tips"),
                CallbackQueryHandler(view_record, pattern="view_record"),
            ],
            PAYMENT_PENDING: [MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(PreCheckoutQueryHandler(precheckout))

    # Setup admin commands
    setup_admin_commands(app, db, metrics)

    # Setup daily picks scheduler
    setup_daily_picks(app, db)

    logger.info("🤖 OddsLab Telegram Bot started successfully!")
    app.run_polling()


if __name__ == "__main__":
    main()