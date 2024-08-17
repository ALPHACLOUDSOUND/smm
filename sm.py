import logging
import requests
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackContext
from telegram.helpers import escape_markdown
import uuid

# Telegram Bot Token
TELEGRAM_TOKEN = '7285921844:AAEAyjEnGs9UjaFTb6SqXWwFcuGellubuNY'

# SMM Panel API details
SMM_API_KEY = '8eaf926262340d6379291e92221039f1'
SMM_API_URL = 'https://cheapestsmmpanels.com/api/v2'

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Command handler for /start
async def start(update: Update, context: CallbackContext) -> None:
    welcome_message = (
        "Welcome to the SMM Bot! Use the commands or inline mode to interact.\n\n"
        "Here are the available commands:\n"
        "/order <service_id> <link> <quantity> - Place an order\n"
        "/status <order_id> - Check order status\n"
        "/balance - Check your balance\n"
        "/cancel <order_ids_comma_separated> - Cancel orders\n"
        "/services - List all services"
    )
    await update.message.reply_text(welcome_message)

# Function to fetch services list from the API
def fetch_services():
    try:
        response = requests.post(SMM_API_URL, data={
            'key': SMM_API_KEY,
            'action': 'services'
        })
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching services: {e}")
        return None

# Function to place an order
async def place_order(update: Update, context: CallbackContext) -> None:
    args = context.args

    if len(args) < 3:
        await update.message.reply_text('Usage: /order <service_id> <link> <quantity>')
        return

    service_id = args[0]
    link = args[1]
    quantity = args[2]

    order_data = {
        'key': SMM_API_KEY,
        'action': 'add',
        'service': service_id,
        'link': link,
        'quantity': quantity
    }

    try:
        response = requests.post(SMM_API_URL, data=order_data)
        response_data = response.json()

        if "order" in response_data:
            await update.message.reply_text(f'Order placed successfully! Order ID: {response_data["order"]}')
        else:
            await update.message.reply_text(f'Failed to place order: {response_data.get("error", "Unknown error")}')
    except Exception as e:
        logger.error(f'Error placing order: {e}')
        await update.message.reply_text('An error occurred while placing the order.')

# Function to check order status
async def check_status(update: Update, context: CallbackContext) -> None:
    args = context.args

    if len(args) < 1:
        await update.message.reply_text('Usage: /status <order_id>')
        return

    order_id = args[0]

    status_data = {
        'key': SMM_API_KEY,
        'action': 'status',
        'order': order_id
    }

    try:
        response = requests.post(SMM_API_URL, data=status_data)
        response_data = response.json()

        if "status" in response_data:
            await update.message.reply_text(
                f"Order Status: {response_data['status']}\n"
                f"Charge: {response_data['charge']}\n"
                f"Start Count: {response_data['start_count']}\n"
                f"Remains: {response_data['remains']}\n"
                f"Currency: {response_data['currency']}"
            )
        else:
            await update.message.reply_text(f'Failed to retrieve status: {response_data.get("error", "Unknown error")}')
    except Exception as e:
        logger.error(f'Error checking status: {e}')
        await update.message.reply_text('An error occurred while checking the status.')

# Function to get balance
async def check_balance(update: Update, context: CallbackContext) -> None:
    try:
        response = requests.post(SMM_API_URL, data={
            'key': SMM_API_KEY,
            'action': 'balance'
        })
        balance_info = response.json()

        if 'balance' in balance_info:
            await update.message.reply_text(f"Your balance is: ${balance_info['balance']} {balance_info['currency']}")
        else:
            await update.message.reply_text("Failed to retrieve balance.")
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        await update.message.reply_text("An error occurred while retrieving balance.")

# Function to cancel orders
async def cancel_orders(update: Update, context: CallbackContext) -> None:
    args = context.args

    if len(args) < 1:
        await update.message.reply_text('Usage: /cancel <order_ids_comma_separated>')
        return

    orders = args[0]

    cancel_data = {
        'key': SMM_API_KEY,
        'action': 'cancel',
        'orders': orders
    }

    try:
        response = requests.post(SMM_API_URL, data=cancel_data)
        cancel_response = response.json()

        results = []
        for order in cancel_response:
            if "cancel" in order:
                results.append(f"Order {order['order']}: Cancelled successfully.")
            else:
                results.append(f"Order {order['order']}: {order['cancel'].get('error', 'Unknown error')}")

        await update.message.reply_text("\n".join(results))
    except Exception as e:
        logger.error(f"Error canceling orders: {e}")
        await update.message.reply_text("An error occurred while canceling orders.")

# Inline query handler
async def inline_query(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query.lower()
    results = []

    if query.startswith("services"):
        services = fetch_services()
        if services:
            for service in services:
                service_details = (
                    f"*Service Name:* {escape_markdown(service['name'], version=2)}\n"
                    f"*Service ID:* {escape_markdown(str(service['service']), version=2)}\n"
                    f"*Category:* {escape_markdown(service['category'], version=2)}\n"
                    f"*Type:* {escape_markdown(service['type'], version=2)}\n"
                    f"*Price per 1000:* ${escape_markdown(service['rate'], version=2)}\n"
                    f"*Min Quantity:* {escape_markdown(service['min'], version=2)}\n"
                    f"*Max Quantity:* {escape_markdown(service['max'], version=2)}\n"
                    f"*Refill Available:* {'Yes' if service['refill'] else 'No'}\n"
                    f"*Cancellation Available:* {'Yes' if service['cancel'] else 'No'}"
                )

                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid.uuid4()),
                        title=service['name'],
                        input_message_content=InputTextMessageContent(
                            service_details,
                            parse_mode="MarkdownV2"
                        )
                    )
                )

    elif query.startswith("commands"):
        commands_list = (
            "/order <service_id> <link> <quantity> - Place an order\n"
            "/status <order_id> - Check order status\n"
            "/balance - Check your balance\n"
            "/cancel <order_ids_comma_separated> - Cancel orders\n"
            "/services - List all services"
        )
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="List of Commands",
                input_message_content=InputTextMessageContent(commands_list)
            )
        )

    await update.inline_query.answer(results)

def main() -> None:
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("order", place_order))
    application.add_handler(CommandHandler("status", check_status))
    application.add_handler(CommandHandler("balance", check_balance))
    application.add_handler(CommandHandler("cancel", cancel_orders))

    # Register the inline query handler
    application.add_handler(InlineQueryHandler(inline_query))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
