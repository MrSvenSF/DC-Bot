import discord
from discord.ext import commands

class Willkommen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = discord.utils.get(member.guild.text_channels, name='general')
        if channel:
            await channel.send(f'Willkommen {member.mention}!')

def setup(bot):
    bot.add_cog(Willkommen(bot))
