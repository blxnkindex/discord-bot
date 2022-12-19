import os
import sys
import asyncio
import random
from dotenv import load_dotenv

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context

if not os.path.isfile('.env'):
    sys.exit('.env file not found')
else:
    load_dotenv()

# Bot Perms
intents = discord.Intents.default()
intents.message_content=True


bot = Bot(
    command_prefix = commands.when_mentioned_or('>'), 
    intents = intents, help_command = None
)

@bot.event
async def on_ready():
    print(f">>> Logged into {bot.user}")
    print("-------------------")
    # Syncs to test server
    await bot.tree.sync(guild = discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    await bot.change_presence(activity = discord.Game('Available commands: \'>help\''))
    # presence_randomiser.start()


@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx: Context, error):
    await ctx.reply(error, ephemeral = True)

@tasks.loop(minutes=.5)
async def presence_randomiser():
    status = ['complaining about katarina items', 'why is sivir -15% damage', 'complaining about aram ziggs',
    'complaining about twitch ult', 'complaining about camille (sunderer is really bad)', 'going gym', 'watching world cup',
    'writing the source code', 'failing uni', 'not having internship', 'being doomer', 'retail therapy',
    'listening to rach (we\'re first name basis)', 'the slow lee sin ward hop']
    await bot.change_presence(activity=discord.Game(name = random.choice(status)))

async def load_extensions():
    for file in os.listdir('./'):
        if file.endswith('.py') and not file == 'main.py':
            await bot.load_extension(str(file[:-3]))
            print(f'>>> Loaded Extension: {str(file[:-3])}')
            print("-------------------")

asyncio.run(load_extensions())

# Run with log_handler=None to disable discord output.
bot.run(os.getenv('TOKEN'))