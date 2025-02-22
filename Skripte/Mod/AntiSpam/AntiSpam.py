import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime, timedelta, timezone

class AntiSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_counts = {}
        self.message_history = {}
        self.spam_warning_sent = {}
        self.load_config()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'AntiSpam.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.excluded_channels = self.config['excluded_channels']
        self.time_window = self.config['time_window']
        self.message_limit = self.config['message_limit']

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.channel.id in self.excluded_channels:
            return

        author_id = message.author.id
        now = datetime.now(timezone.utc)

        if author_id not in self.message_counts:
            self.message_counts[author_id] = []
            self.message_history[author_id] = []
            self.spam_warning_sent[author_id] = False

        self.message_counts[author_id].append(now)
        self.message_history[author_id].append(message)

        # Remove messages outside the time window
        self.message_counts[author_id] = [
            msg_time for msg_time in self.message_counts[author_id]
            if now - msg_time <= timedelta(seconds=self.time_window)
        ]
        self.message_history[author_id] = [
            msg for msg in self.message_history[author_id]
            if now - msg.created_at <= timedelta(seconds=self.time_window)
        ]

        if len(self.message_counts[author_id]) > self.message_limit:
            if not self.spam_warning_sent[author_id]:
                await message.channel.send(f'{message.author.mention}, please stop spamming!')
                self.spam_warning_sent[author_id] = True
            await asyncio.sleep(1)  # Ensure the warning message is sent before deleting
            for msg in self.message_history[author_id]:
                await msg.delete()
        else:
            self.spam_warning_sent[author_id] = False

        # Clear message history if user stops spamming
        if len(self.message_counts[author_id]) == 0:
            self.message_history[author_id] = []

def setup(bot):
    bot.add_cog(AntiSpam(bot))
