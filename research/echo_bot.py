import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
Telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
print(f"Token loaded: {Telegram_token is not None}")

# Initialize bot and dispatcher
bot = Bot(token=Telegram_token)
dp = Dispatcher() #dispatcher to handle incoming messages and updates

# Command handler for /start and /help
@dp.message(Command(commands=["start", "help"]))
async def command_start_handler(message: types.Message):
    """
    This handler receives messages with '/start' or '/help'
    """
    await message.reply("Hi\nI am Echo Bot! Powered by aiogram")

# Optional: Echo handler for all other messages
@dp.message()
async def echo_handler(message: types.Message):
    await message.answer(message.text)

# Main function
async def main():
    # Skip pending updates
    await bot.delete_webhook(drop_pending_updates=True)  #skips pending messages and clears previous webhooks
    # Start polling
    await dp.start_polling(bot) #continuously checking for updates

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) #pythons asynchoronous library, this is event loop