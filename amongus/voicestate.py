import discord
import socketio
from pyrate_limiter import RequestRate, Limiter, Duration, BucketFullException

from db.DbConnection import DbConnection

rate = RequestRate(5, Duration.SECOND * 10)
limiter = Limiter(rate)


async def mute_deafen(bot: discord.Bot, db_connection: DbConnection, sio: socketio.AsyncClient, sql_query: str):
    result = db_connection.execute_list(sql_query)
    print(result)
    print(len(result))
    if len(result) < 1:
        return

    channel: discord.VoiceChannel = bot.get_channel(result[0][1])
    for i, user in enumerate(result):
        member: discord.Member = channel.guild.get_member(user[0])
        if member.voice is None:
            continue

        print(f"{member.name} muted and deafed")
        if i > 6:
            await sio.emit("on_mute_deafen", {"guild_id": str(member.guild.id), "member_id": str(member.id)})
            continue

        await member.edit(mute=True, deafen=True)


async def unmute_undeafen(bot: discord.Bot, db_connection: DbConnection, sio: socketio.AsyncClient, sql_query: str):
    result = db_connection.execute_list(sql_query)
    if len(result) < 1:
        return

    channel: discord.VoiceChannel = bot.get_channel(result[0][1])
    for i, user in enumerate(result):
        member: discord.Member = channel.guild.get_member(user[0])
        if member.voice is None:
            continue

        print(f"{member.name} unmuted and undeafed")
        if i > 6:
            await sio.emit("on_unmute_undeafen", {"guild_id": str(member.guild.id), "member_id": str(member.id)})
            continue

        await member.edit(mute=False, deafen=False)


async def mute(bot: discord.Bot, db_connection: DbConnection, sio: socketio.AsyncClient, sql_query: str):
    result = db_connection.execute_list(sql_query)
    if len(result) < 1:
        return

    channel: discord.VoiceChannel = bot.get_channel(result[0][1])
    for i, user in enumerate(result):
        member: discord.Member = channel.guild.get_member(user[0])
        if member.voice is None:
            continue

        print(f"{member.name} muted and deafed")
        if i > 6:
            await sio.emit("on_mute", {"guild_id": str(member.guild.id), "member_id": str(member.id)})
            continue

        await member.edit(mute=True, deafen=False)
