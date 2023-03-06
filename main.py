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

bot = Bot(command_prefix = commands.when_mentioned_or('>'), intents = intents, help_command = None)

@bot.event
async def on_ready():
    print(f">>> Logged into {bot.user}")
    print("-------------------")
    # Syncs to test server
    await bot.tree.sync(guild = discord.Object(id = int(os.getenv('MAIN_SERVER'))))
    await bot.change_presence(activity = discord.Game('Commands: \'>help\''))
    # presence_randomiser.start()


@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot:
        return
    await bot.process_commands(message)

@bot.event
async def on_command_error(ctx, exc):
		# If the command does not exist/is not found.
		if isinstance(exc, commands.CommandNotFound):
			await ctx.send("Command not found", delete_after=10)
		elif isinstance(exc, commands.MissingPermissions):
			pass
		elif isinstance(exc, commands.BotMissingPermissions):
			await ctx.send("I'm missing permissions!")
			# raise exc  # So we see this in the terminal.

@tasks.loop(minutes=.5)
async def presence_randomiser():
    status = ['']
    await bot.change_presence(activity=discord.Game(name = random.choice(status)))

async def load_extensions():
    for file in os.listdir('./cogs/'):
        if file.endswith('.py') and not (file == 'main.py' or file == 'utils.py'):
            await bot.load_extension(f'cogs.{str(file[:-3])}')
            print(f'>>> Loaded Extension: {str(file[:-3])}')
            print("-------------------")

if __name__ == "__main__":
    asyncio.run(load_extensions())
    if len(sys.argv) == 1:
        # Run with log_handler=None to disable discord output.
        bot.run(os.getenv('TOKEN'))
    elif len(sys.argv) == 2 and sys.argv[1] == '--nooutput':
        print(f'>>> Launched with noouput flag will NOT output any discord output')
        print("-------------------")
        bot.run(os.getenv('TOKEN'), log_handler=None)