from abc import ABC

import discord
from discord.ext import commands

from amongus.embed import updateEmbed
from db.DbConnection import DbConnection


class EventsListener(commands.Bot, ABC):
    def __init__(self, db_connection: DbConnection = None):
        super().__init__(intents=discord.Intents.default())
        self.db_connection = db_connection

    async def on_ready(self):
        print(f"{self.user} is ready and online!")

    async def on_guild_join(self, guild: discord.Guild):
        print(f"{self.user} joined {self.guild.name}")

    async def on_guild_remove(self, guild: discord.Guild):
        print(f"{self.user} leaved {guild.name}")

    async def on_voice_state_update(self, member: discord.Member, voice_state_old: discord.VoiceState,
                                    voice_state_new: discord.VoiceState):
        if self.db_connection is None:
            return
        #channel_new: discord.VoiceChannel = voice_state_new.channel
        channel_old: discord.VoiceChannel = voice_state_old.channel

        if channel_old is not None:
            sql = f"SELECT discord_voice_id FROM players WHERE discord_voice_id = {channel_old.id}"
            result = self.db_connection.execute_list(sql)
            if result[0][0] is None:
                return

            sql = f"SELECT discord_message_id, roomcode FROM players WHERE discord_user_id = {member.id}"
            result = self.db_connection.execute_list(sql)
            sql = f"UPDATE players SET discord_user_id = NULL, discord_voice_id = NULL WHERE discord_user_id = {member.id}"
            self.db_connection.execute(sql)
            msg: discord.Message = self.get_message(result[0][0])
            await member.edit(mute=False, deafen=False)
            await updateEmbed(self.db_connection, msg, result[0][1])
