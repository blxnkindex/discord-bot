import discord
import os
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.all()

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message):
        # Ensures bot does not respond to itself
        if message.author == client.user:
            return
            
        if message.content == '$test':
            await message.channel.send('test')

client = MyClient(intents=discord.Intents.all())
client.run(os.getenv('TOKEN'))
