import os
import logging
import asyncio
from telegram import Update, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from dhanhq import dhanhq

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DHAN_CLIENT_ID = os.getenv('DHAN_CLIENT_ID')
DHAN_ACCESS_TOKEN = os.getenv('DHAN_ACCESS_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://yourusername.github.io/your-repo-name/')

# Define conversation states
AWAITING_COMMAND = 0

# Initialize Dhan client
dhan_client = dhanhq(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)

async def start(update: Update, context):
    """Send a message with a button that opens the Web App."""
    await update.message.reply_text(
        "Welcome to the Dhan Trading Bot! Click the button below to open the Web App.",
        reply_markup={
            "keyboard": [[{"text": "Open Dhan Trading Web App", "web_app": {"url": WEBAPP_URL}}]],
            "resize_keyboard": True
        }
    )
    return AWAITING_COMMAND

async def help_command(update: Update, context):
    """Send a message when the command /help is issued."""
    help_text = """
    Available commands:
    /start - Start the bot and open the Web App
    /help - Show this help message
    /positions - View your current positions
    /balance - Check your account balance
    /tsl - Set up a Trailing Stop Loss (use the Web App for this)
    """
    await update.message.reply_text(help_text)
    return AWAITING_COMMAND

async def positions(update: Update, context):
    """Fetch and display user's positions."""
    try:
        positions = dhan_client.get_positions()
        if positions and isinstance(positions, dict) and positions.get('status') == 'success':
            positions_data = positions.get('data', [])
            if positions_data:
                response = "Your current positions:\n\n"
                for position in positions_data[:5]:  # Limit to 5 positions for brevity
                    response += f"Symbol: {position.get('tradingSymbol', 'N/A')}\n"
                    response += f"Quantity: {position.get('netQty', 'N/A')}\n"
                    response += f"Average Price: ₹{position.get('averagePrice', 'N/A')}\n"
                    response += f"LTP: ₹{position.get('lastTradedPrice', 'N/A')}\n\n"
            else:
                response = "You don't have any open positions."
        else:
            response = "Unable to fetch positions. Please try again later."
    except Exception as e:
        logger.error(f"Error fetching positions: {str(e)}")
        response = "An error occurred while fetching positions. Please try again later."
    
    await update.message.reply_text(response)
    return AWAITING_COMMAND

async def balance(update: Update, context):
    """Fetch and display user's account balance."""
    try:
        fund_limits = dhan_client.get_fund_limits()
        if fund_limits and isinstance(fund_limits, dict) and fund_limits.get('status') == 'success':
            balance_data = fund_limits.get('data', {})
            if balance_data:
                response = "Your account balance:\n\n"
                response += f"Available Balance: ₹{balance_data.get('availableBalance', 'N/A')}\n"
                response += f"Used Margin: ₹{balance_data.get('usedMargin', 'N/A')}\n"
                response += f"Available Margin: ₹{balance_data.get('availableMargin', 'N/A')}\n"
            else:
                response = "Unable to fetch balance information."
        else:
            response = "Unable to fetch balance. Please try again later."
    except Exception as e:
        logger.error(f"Error fetching balance: {str(e)}")
        response = "An error occurred while fetching balance. Please try again later."
    
    await update.message.reply_text(response)
    return AWAITING_COMMAND

async def web_app_data(update: Update, context):
    """Handle data received from the Web App."""
    data = update.effective_message.web_app_data.data
    
    if data == "get_positions":
        await positions(update, context)
    elif data == "get_balance":
        await balance(update, context)
    elif data.startswith("setup_tsl:"):
        # Example: setup_tsl:SYMBOL,QUANTITY,TRAIL_PERCENTAGE
        _, params = data.split(':', 1)
        symbol, quantity, trail_percentage = params.split(',')
        await setup_tsl(update, context, symbol, int(quantity), float(trail_percentage))
    else:
        await update.message.reply_text(f"Received unknown data: {data}")
    
    return AWAITING_COMMAND

async def setup_tsl(update: Update, context, symbol, quantity, trail_percentage):
    """Set up a Trailing Stop Loss order."""
    # This is a placeholder. Implement the actual TSL logic here using the Dhan API
    response = f"Setting up TSL for {symbol}, Quantity: {quantity}, Trail: {trail_percentage}%"
    await update.message.reply_text(response)
    # TODO: Implement actual TSL order placement and monitoring
    return AWAITING_COMMAND

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Set up conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AWAITING_COMMAND: [
                CommandHandler('help', help_command),
                CommandHandler('positions', positions),
                CommandHandler('balance', balance),
                MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data),
            ],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
