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

    def format_description(self, description, user, writer, channel, content, before_content=None, after_content=None, before_channel=None, after_channel=None, message_link=None):
        timestamp = datetime.now().strftime("%d.%m.%Y um %H:%M Uhr")
        description = description.replace("(User)", user.mention if user else "")
        description = description.replace("(Writer)", writer.mention if writer else "")
        description = description.replace("(Channel)", channel.mention if channel else "")
        description = description.replace("(Datum Zeit)", timestamp)
        description = description.replace("(Bot)", self.bot.user.mention)
        description = description.replace("{content}", content)
        description = description.replace("{before_content}", before_content or "")
        description = description.replace("{after_content}", after_content or "")
        description = description.replace("{before_channel}", before_channel.mention if before_channel else "")
        description = description.replace("{after_channel}", after_channel.mention if after_channel else "")
        description = description.replace("{message_link}", message_link or "")
        description = description.replace("|", "\n")
        description = description.replace("**", "**")
        return description

    async def log_event(self, event_type, user, writer, channel=None, content="", before_content=None, after_content=None, before_channel=None, after_channel=None, message_link=None):
        print(f"Logging event: {event_type}, User: {user}, Writer: {writer}, Channel: {channel}, Content: {content}")
        if channel and channel.id in self.excluded_channels:
            print(f"Channel {channel.id} is excluded from logging.")
            return

        channel_obj = self.bot.get_channel(self.log_channel_id)
        if channel_obj:
            log_config = self.log_format[event_type]
            description = self.format_description(
                log_config['description'],
                user,
                writer,
                channel,
                content,
                before_content,
                after_content,
                before_channel,
                after_channel,
                message_link
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

    def get_user_and_writer(self, message, action_user=None):
        # Determine the user who performed the action and the writer
        writer = message.author
        user = action_user if action_user else ""
        return user, writer

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        user = message.guild.get_member(message.user.id)  # Get the user who deleted the message
        writer = message.author
        print(f"Message deleted in channel {message.channel.id} by {user}")
        if self.is_logging_enabled(message.channel.id):
            message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
            await self.log_event(
                event_type="message_deletions",
                user=user,
                writer=writer,
                channel=message.channel,
                content=f"{message.content}",
                message_link=message_link
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        user = before.guild.get_member(before.author.id)  # Get the user who edited the message
        writer = before.author
        print(f"Message edited in channel {before.channel.id} by {user}")
        if self.is_logging_enabled(before.channel.id):
            message_link = f"https://discord.com/channels/{before.guild.id}/{before.channel.id}/{before.id}"
            await self.log_event(
                event_type="message_edits",
                user=user,
                writer=writer,
                channel=before.channel,
                content="",
                before_content=before.content,
                after_content=after.content,
                message_link=message_link
            )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        user, writer = channel.guild.me, channel.guild.me
        if self.is_logging_enabled(channel.id):
            await self.log_event(
                event_type="channel_creations",
                user=user,
                writer=writer,
                channel=channel,
                content=f"{channel.mention} ({channel.type})"
            )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        user, writer = channel.guild.me, channel.guild.me
        if self.is_logging_enabled(channel.id):
            await self.log_event(
                event_type="channel_deletions",
                user=user,
                writer=writer,
                channel=channel,
                content=f"{channel.name} ({channel.type})"
            )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        user, writer = before.guild.me, before.guild.me
        if self.is_logging_enabled(before.id):
            changed_permissions = []
            for perm, value in before.overwrites.items():
                if perm not in after.overwrites or after.overwrites[perm] != value:
                    changed_permissions.append(f"{perm}: {value} -> {after.overwrites.get(perm, 'None')}")
            if changed_permissions:
                await self.log_event(
                    event_type="channel_updates",
                    user=user,
                    writer=writer,
                    channel=before,
                    content="\n".join(changed_permissions),
                    before_content=before.name,
                    after_content=after.name
                )

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        user, writer = before.guild.me, before.guild.me
        changed_permissions = []
        for perm, value in before.permissions:
            if getattr(after.permissions, perm) != value:
                emoji = ":white_check_mark:" if getattr(after.permissions, perm) else ":x:"
                changed_permissions.append(f"{emoji} {perm}")
        if changed_permissions:
            await self.log_event(
                event_type="role_updates",
                user=user,
                writer=writer,
                channel=None,
                content="\n".join(changed_permissions),
                before_content=before.name,
                after_content=after.name
            )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        writer = reaction.message.author
        print(f"Reaction added in channel {reaction.message.channel.id} by {user}")
        if self.is_logging_enabled(reaction.message.channel.id):
            message_link = f"https://discord.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{reaction.message.id}"
            await self.log_event(
                event_type="reaction_add",
                user=user,
                writer=writer,
                channel=reaction.message.channel,
                content=f"Reaction: {reaction.emoji} to message: {reaction.message.content}",
                message_link=message_link
            )

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        writer = reaction.message.author
        print(f"Reaction removed in channel {reaction.message.channel.id} by {user}")
        if self.is_logging_enabled(reaction.message.channel.id):
            message_link = f"https://discord.com/channels/{reaction.message.guild.id}/{reaction.message.channel.id}/{reaction.message.id}"
            await self.log_event(
                event_type="reaction_remove",
                user=user,
                writer=writer,
                channel=reaction.message.channel,
                content=f"Reaction: {reaction.emoji} from message: {reaction.message.content}",
                message_link=message_link
            )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        user, writer = member, member
        if self.is_logging_enabled(before.channel.id if before.channel else after.channel.id):
            if before.channel != after.channel:
                if before.channel is None:
                    await self.log_event(
                        event_type="voice_chat_joins",
                        user=user,
                        writer=writer,
                        channel=after.channel,
                        content=f"{after.channel}"
                    )
                elif after.channel is None:
                    await self.log_event(
                        event_type="voice_chat_leaves",
                        user=user,
                        writer=writer,
                        channel=before.channel,
                        content=f"{before.channel}"
                    )
                else:
                    await self.log_event(
                        event_type="voice_chat_switches",
                        user=user,
                        writer=writer,
                        channel=before.channel,
                        content="",
                        before_channel=before.channel,
                        after_channel=after.channel
                    )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.log_event(
            event_type="server_joins",
            user=member,
            writer=member
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.log_event(
            event_type="server_leaves",
            user=member,
            writer=member
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
