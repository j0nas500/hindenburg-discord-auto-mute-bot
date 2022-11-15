import asyncio

import discord
import socketio

from db.DbConnection import DbConnection


# rate = RequestRate(5, Duration.SECOND * 10)
# limiter = Limiter(rate)

class VoicestateClass:
    def __init__(self, bot: discord.Bot, db_connection: DbConnection, sio: socketio.AsyncClient):
        self.bot = bot
        self.db_connection = db_connection
        self.sio = sio
        self.task: asyncio.Task = None

    async def perform_tasks(self, sql_query_alive: str, game_state: int, sql_query_dead: str = None):
        result_alive = self.db_connection.execute_list(sql_query_alive)
        if sql_query_dead is not None:
            result_dead = self.db_connection.execute_list(sql_query_dead)

        if self.task is not None:
            if not self.task.cancelled():
                self.task.cancel()

        if game_state == 0:
            self.task = asyncio.create_task(self.game_start(result_alive))
            return
        if game_state == 1:
            self.task = asyncio.create_task(self.game_end(result_alive))
            return
        if game_state == 2:
            self.task = asyncio.create_task(self.meeting_start(result_alive, result_dead))
            return
        if game_state == 3:
            self.task = asyncio.create_task(self.meeting_end(result_alive, result_dead))
        if game_state == 4:
            self.task = asyncio.create_task(self.mute_only(result_alive))

    async def game_start(self, result):
        try:
            print("START OF GAME START AUTO MUTE")
            await self.mute_deafen(result)
        except asyncio.CancelledError as err:
            print("CANCELLING GAME START AUTO MUTE")
        finally:
            print("END OF GAME START AUTO MUTE")
            print()

    async def game_end(self, result):
        try:
            print("START OF GAME END AUTO MUTE")
            await self.unmute_undeafen(result)
        except asyncio.CancelledError as err:
            print("CANCELLING GAME END AUTO MUTE")
        finally:
            print("END OF GAME END AUTO MUTE")
            print()

    async def meeting_start(self, result_alive, result_dead):
        try:
            print("START OF MEETING START AUTO MUTE")
            calls = await self.mute(result_dead)
            print(calls)
            await self.unmute_undeafen(result_alive, calls=calls)
        except asyncio.CancelledError as err:
            print("CANCELLING MEETING START AUTO MUTE")
        finally:
            print("END OF MEETING START AUTO MUTE")
            print()

    async def meeting_end(self, result_alive, result_dead):
        try:
            print("START OF MEETING END AUTO MUTE")
            calls = await self.mute_deafen(result_alive)
            print(calls)
            await self.unmute_undeafen(result_dead, calls=calls)
        except asyncio.CancelledError as err:
            print("CANCELLING MEETING END AUTO MUTE")
        finally:
            print("END OF MEETING END AUTO MUTE")
            print()

    async def player_die(self, result_dead):
        try:
            print("START OF PLAYER DIE END AUTO MUTE")
            await self.mute_only(result_dead)
        except asyncio.CancelledError as err:
            print("CANCELLING PLAYER DIE END AUTO MUTE")
        finally:
            print("END OF PLAYER DIE AUTO MUTE")
            print()

    async def mute_deafen(self, result, calls: int = 0):
        if len(result) < 1:
            return 0

        count: int = calls
        channel: discord.VoiceChannel = self.bot.get_channel(result[0][1])

        for i, user in enumerate(result):
            member: discord.Member = channel.guild.get_member(user[0])
            if member.voice is None:
                continue

            if (i + count) > 6:
                await self.sio.emit("on_mute_deafen", {"guild_id": str(member.guild.id), "member_id": str(member.id)})
                print(f"SECOND: {member.name} muted and deafed")
                continue

            print(f"MAIN: {member.name} muted and deafed")
            await member.edit(mute=True, deafen=True)

        return len(result) + count

    async def unmute_undeafen(self, result, calls: int = 0):
        if len(result) < 1:
            return 0

        count = calls
        channel: discord.VoiceChannel = self.bot.get_channel(result[0][1])
        for i, user in enumerate(result):
            member: discord.Member = channel.guild.get_member(user[0])
            if member.voice is None:
                continue

            if (i + count) > 6:
                await self.sio.emit("on_unmute_undeafen",
                                    {"guild_id": str(member.guild.id), "member_id": str(member.id)})
                print(f"SECOND: {member.name} unmuted and undeafed")
                continue

            await member.edit(mute=False, deafen=False)
            print(f"MAIN: {member.name} unmuted and undeafed")

        return len(result) + count

    async def mute(self, result, calls: int = 0):
        if len(result) < 1:
            return 0

        count = calls
        channel: discord.VoiceChannel = self.bot.get_channel(result[0][1])
        for i, user in enumerate(result):
            member: discord.Member = channel.guild.get_member(user[0])
            if member.voice is None:
                continue

            if (i + count) > 6:
                await self.sio.emit("on_mute", {"guild_id": str(member.guild.id), "member_id": str(member.id)})
                print(f"SECOND: {member.name} muted")
                continue

            await member.edit(mute=True, deafen=False)
            print(f"MAIN: {member.name} muted")

        return len(result) + count

    async def mute_only(self, result, calls: int = 0):
        if len(result) < 1:
            return 0

        count = calls
        channel: discord.VoiceChannel = self.bot.get_channel(result[0][1])
        for i, user in enumerate(result):
            member: discord.Member = channel.guild.get_member(user[0])
            if member.voice is None:
                continue

            if member.voice.mute:
                continue

            await member.edit(mute=True)
            print(f"MAIN: {member.name} muted ONLY")

        return len(result) + count
