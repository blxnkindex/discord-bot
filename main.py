
import os
import sys
import asyncio
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord.ext.commands import Bot

if not os.path.isfile('.env'):
    sys.exit('.env file not found')
else:
    load_dotenv()

# Intents - Bot perms (TODO: Change from all (administrator?) to necessary intents/perms)

intents = discord.Intents.all()

bot = Bot(
    command_prefix = commands.when_mentioned_or('!'), 
    intents = intents, help_command = None
)

@bot.event
async def on_ready():
    print(f">>> Logged into {bot.user}")
    print("-------------------")
    await bot.change_presence(activity = discord.Game('Misaka Bot Beta: !help to start'))

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return
    await bot.process_commands(message)

async def load_extensions():
    for file in os.listdir('./'):
        if file.endswith('.py') and not file == 'main.py':
            await bot.load_extension(str(file[:-3]))
            print(f'>>> Loaded Extension: {str(file[:-3])}')
            print("-------------------")

asyncio.run(load_extensions())
bot.run(os.getenv('TOKEN'))