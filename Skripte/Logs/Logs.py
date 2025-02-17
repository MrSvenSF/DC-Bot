import discord
from discord.ext import commands
import json
from datetime import datetime
import os

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        config_path = os.path.join(os.path.dirname(__file__), 'Logs.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.log_channel_id = int(self.config['log_channel'])
        self.excluded_channels = self.config['excluded_channels']
        self.log_format = self.config['log_format']

    def format_description(self, description, user, channel, content, author=None, before_content=None, after_content=None, before_channel=None, after_channel=None):
        timestamp = datetime.now().strftime("%d.%m.%Y um %H:%M Uhr")
        description = description.replace("(User)", user.mention)
        description = description.replace("(Channel)", channel.mention if channel else "")
        description = description.replace("(Datum Zeit)", timestamp)
        description = description.replace("(Bot)", self.bot.user.mention)
        description = description.replace("{content}", content)
        description = description.replace("{before_content}", before_content or "")
        description = description.replace("{after_content}", after_content or "")
        description = description.replace("{before_channel}", before_channel.mention if before_channel else "")
        description = description.replace("{after_channel}", after_channel.mention if after_channel else "")
        description = description.replace("(Author)", author.mention if author else "")
        description = description.replace("/", "\n")
        description = description.replace("**", "**")
        return description

    async def log_event(self, event_type, user, channel=None, content="", author=None, before_content=None, after_content=None, before_channel=None, after_channel=None):
        print(f"Logging event: {event_type}, User: {user}, Channel: {channel}, Content: {content}")
        if channel and channel.id in self.excluded_channels:
            print(f"Channel {channel.id} is excluded from logging.")
            return

        channel_obj = self.bot.get_channel(self.log_channel_id)
        if channel_obj:
            log_config = self.log_format[event_type]
            description = self.format_description(
                log_config['description'],
                user,
                channel,
                content,
                author,
                before_content,
                after_content,
                before_channel,
                after_channel
            )
            title = log_config['title']
            color = discord.Color(int(log_config['color'], 16))
            embed = discord.Embed(title=title, description=description, color=color)
            try:
                await channel_obj.send(embed=embed)
                print(f"Logged event: {event_type} successfully.")
            except discord.errors.Forbidden:
                await channel_obj.send("Ich habe keine Berechtigung, Nachrichten in diesem Kanal zu senden.")
                print(f"Failed to log event: {event_type} due to missing permissions.")
        else:
            print(f"Log channel {self.log_channel_id} not found.")

    def is_logging_enabled(self, channel_id):
        return channel_id not in self.excluded_channels

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        print(f"Message deleted in channel {message.channel.id} by {message.author}")
        if self.is_logging_enabled(message.channel.id):
            await self.log_event(
                event_type="message_deletions",
                user=message.author,
                channel=message.channel,
                content=f"{message.content}",
                author=message.author
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        print(f"Message edited in channel {before.channel.id} by {before.author}")
        if self.is_logging_enabled(before.channel.id):
            await self.log_event(
                event_type="message_edits",
                user=before.author,
                channel=before.channel,
                content="",
                author=before.author,
                before_content=before.content,
                after_content=after.content
            )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if self.is_logging_enabled(channel.id):
            await self.log_event(
                event_type="channel_creations",
                user=channel.guild.me,
                channel=channel,
                content=f"{channel.mention} ({channel.type})"
            )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if self.is_logging_enabled(channel.id):
            await self.log_event(
                event_type="channel_deletions",
                user=channel.guild.me,
                channel=channel,
                content=f"{channel.name} ({channel.type})"
            )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if self.is_logging_enabled(before.id):
            await self.log_event(
                event_type="channel_updates",
                user=before.guild.me,
                channel=before,
                content="",
                before_content=before.name,
                after_content=after.name
            )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if self.is_logging_enabled(before.channel.id if before.channel else after.channel.id):
            if before.channel != after.channel:
                if before.channel is None:
                    await self.log_event(
                        event_type="voice_chat_joins",
                        user=member,
                        channel=after.channel,
                        content=f"{after.channel}"
                    )
                elif after.channel is None:
                    await self.log_event(
                        event_type="voice_chat_leaves",
                        user=member,
                        channel=before.channel,
                        content=f"{before.channel}"
                    )
                else:
                    await self.log_event(
                        event_type="voice_chat_switches",
                        user=member,
                        channel=before.channel,
                        content="",
                        before_channel=before.channel,
                        after_channel=after.channel
                    )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.log_event(
            event_type="server_joins",
            user=member
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.log_event(
            event_type="server_leaves",
            user=member
        )

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def enable_logging(self, ctx, channel_id: int):
        if channel_id in self.excluded_channels:
            self.excluded_channels.remove(channel_id)
            with open('Skripte/Logs/Logs.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            await ctx.send(f"Logging für Kanal {channel_id} aktiviert")
        else:
            await ctx.send(f"Kanal {channel_id} war nicht ausgeschlossen")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def disable_logging(self, ctx, channel_id: int):
        if channel_id not in self.excluded_channels:
            self.excluded_channels.append(channel_id)
            with open('Skripte/Logs/Logs.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            await ctx.send(f"Logging für Kanal {channel_id} deaktiviert")
        else:
            await ctx.send(f"Kanal {channel_id} war bereits ausgeschlossen")

def setup(bot):
    bot.add_cog(Logger(bot))
