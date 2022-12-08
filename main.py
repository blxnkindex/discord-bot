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
    await bot.tree.sync(guild = discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    await bot.change_presence(activity = discord.Game('Music and music queue now working \'/play\''))
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
    status = ['manifesting gunblade\'s return', 'buffing camille (she\'s weak)', 'watching walking dead', 'getting unlucky',
    'picking ziggs (20th game straight)', 'making music queue', 'changing profile pictures', 'complaining about twitch ult', 'complaining about katarina damage']
    await bot.change_presence(activity=discord.Game(name = random.choice(status)))

async def load_extensions():
    for file in os.listdir('./'):
        if file.endswith('.py') and not file == 'main.py':
            await bot.load_extension(str(file[:-3]))
            print(f'>>> Loaded Extension: {str(file[:-3])}')
            print("-------------------")

asyncio.run(load_extensions())
bot.run(os.getenv('TOKEN'))