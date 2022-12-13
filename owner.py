from discord.ext import commands

class Owner(commands.Cog, name = 'owner'):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, *, cog: str):
        try:
            await self.bot.unload_extension(cog)
            await self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(e)
        else:
            await ctx.send(f'Extension {cog} successfully restarted', delete_after=5)
            await ctx.message.delete()

    @commands.command(name='botleave', hidden=True)
    @commands.is_owner()
    async def botleave(self, ctx):
        print(f'Leaving server {ctx.guild.name}')
        await ctx.guild.leave()

async def setup(bot):
    await bot.add_cog(Owner(bot))
