import os
import sys
import asyncio
from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord.ext.commands import Bot, Context

if not os.path.isfile('.env'):
    sys.exit('.env file not found')
else:
    load_dotenv()

# Intents - Bot perms (TODO: Change from all (administrator?) to necessary intents/perms)

intents = discord.Intents.all()

bot = Bot(
    command_prefix = commands.when_mentioned_or('>'), 
    intents = intents, help_command = None
)

@bot.event
async def on_ready():
    print(f">>> Logged into {bot.user}")
    print("-------------------")
    # Syncs to test server
    await bot.tree.sync(guild = discord.Object(id = 715252385269678241))
    await bot.change_presence(activity = discord.Game('Bot Online: !help to start'))


@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx: Context, error):
    await ctx.reply(error, ephemeral = True)


async def load_extensions():
    for file in os.listdir('./'):
        if file.endswith('.py') and not file == 'main.py':
            await bot.load_extension(str(file[:-3]))
            print(f'>>> Loaded Extension: {str(file[:-3])}')
            print("-------------------")

asyncio.run(load_extensions())
bot.run(os.getenv('TOKEN'))