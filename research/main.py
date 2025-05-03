import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://omkars-telegram-bot.onrender.com")
WEBHOOK_PATH = f"/webhook/{TELEGRAM_BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.environ.get("PORT", 8000))

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Configure the model
model_name = "gpt-4o-mini"

# Class to store previous response
class Reference:
    def __init__(self) -> None:
        self.responses = {}  # Using dict to track conversations per user

reference = Reference()

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command(commands=["start"]))
async def command_start_handler(message: types.Message):
    """
    This handler receives messages with '/start'
    """
    await message.reply("Hi\nI am Echo Bot! Powered by OpenAI and aiogram.")

def clear_past(user_id):
    if user_id in reference.responses:
        del reference.responses[user_id]

@dp.message(Command(commands=['clear']))
async def clear(message: types.Message):
    clear_past(message.from_user.id)
    await message.reply("I have cleared the past conversation.")

@dp.message(Command(commands=["help"]))
async def helper(message: types.Message):
    help_command = """
    Available Commands:
    /start - Start the bot and get a welcome message.
    /help - Show this help message.
    /clear - Clear all messages or chat history.
    """
    await message.reply(help_command)

@dp.message()
async def chatgpt(message: types.Message):
    user_id = message.from_user.id
    print(f">>> USER {user_id}: \n\t{message.text}")
    
    messages_list = []
    
    # Add previous response if it exists
    if user_id in reference.responses and reference.responses[user_id]:
        messages_list.append({"role": "assistant", "content": reference.responses[user_id]})
    
    # Add current user message
    messages_list.append({"role": "user", "content": message.text})
    
    try:
        # Send "typing" action to show the bot is processing
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        # Create client using modern OpenAI client
        response = openai.chat.completions.create(
            model=model_name,
            messages=messages_list
        )
        
        # Store response by user ID
        reference.responses[user_id] = response.choices[0].message.content
        print(f">>> ChatGPT to {user_id}:\n\t{reference.responses[user_id]}")
        
        await bot.send_message(chat_id=message.chat.id, text=reference.responses[user_id])
    
    except openai.RateLimitError as e:
        print(f"Rate limit error: {e}")
        await bot.send_message(
            chat_id=message.chat.id, 
            text="❌ Error: You have exceeded your OpenAI API quota. Please check your plan and billing details."
        )
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        await bot.send_message(
            chat_id=message.chat.id, 
            text="⚠️ An unexpected error occurred. Please try again later."
        )

async def on_startup(bot: Bot) -> None:
    # Set webhook
    await bot.set_webhook(url=WEBHOOK_URL)
    print(f"Webhook set to: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot) -> None:
    # Remove webhook
    await bot.delete_webhook()
    print("Webhook removed")

def main():
    # Create web application
    app = web.Application()
    
    # Configure webhook route
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Setup handlers for startup and shutdown
    setup_application(app, dp, bot=bot, on_startup=on_startup, on_shutdown=on_shutdown)
    
    # Start web server
    web.run_app(app, host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()