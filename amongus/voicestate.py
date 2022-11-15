import discord
import socketio

from db.DbConnection import DbConnection

# rate = RequestRate(5, Duration.SECOND * 10)
# limiter = Limiter(rate)


async def mute_deafen(bot: discord.Bot, db_connection: DbConnection, sio: socketio.AsyncClient, sql_query: str, calls: int = 0):
    result = db_connection.execute_list(sql_query)
    if len(result) < 1:
        return 0

    count = calls
    channel: discord.VoiceChannel = bot.get_channel(result[0][1])

    for i, user in enumerate(result):
        member: discord.Member = channel.guild.get_member(user[0])
        if member.voice is None:
            continue

        if (i + count) > 6:
            await sio.emit("on_mute_deafen", {"guild_id": str(member.guild.id), "member_id": str(member.id)})
            print(f"SECOND: {member.name} muted and deafed")
            continue

        print(f"MAIN: {member.name} muted and deafed")
        await member.edit(mute=True, deafen=True)

    return len(result) + count


async def unmute_undeafen(bot: discord.Bot, db_connection: DbConnection, sio: socketio.AsyncClient, sql_query: str, calls: int = 0):
    result = db_connection.execute_list(sql_query)
    if len(result) < 1:
        return 0

    count = calls
    channel: discord.VoiceChannel = bot.get_channel(result[0][1])
    for i, user in enumerate(result):
        member: discord.Member = channel.guild.get_member(user[0])
        if member.voice is None:
            continue

        if (i + count) > 6:
            await sio.emit("on_unmute_undeafen", {"guild_id": str(member.guild.id), "member_id": str(member.id)})
            print(f"SECOND: {member.name} unmuted and undeafed")
            continue

        await member.edit(mute=False, deafen=False)
        print(f"MAIN: {member.name} unmuted and undeafed")

    return len(result) + count


async def mute(bot: discord.Bot, db_connection: DbConnection, sio: socketio.AsyncClient, sql_query: str, calls: int = 0):
    result = db_connection.execute_list(sql_query)
    if len(result) < 1:
        return 0

    count = calls
    channel: discord.VoiceChannel = bot.get_channel(result[0][1])
    for i, user in enumerate(result):
        member: discord.Member = channel.guild.get_member(user[0])
        if member.voice is None:
            continue

        if (i + count) > 6:
            await sio.emit("on_mute", {"guild_id": str(member.guild.id), "member_id": str(member.id)})
            print(f"SECOND: {member.name} muted")
            continue

        await member.edit(mute=True, deafen=False)
        print(f"MAIN: {member.name} muted")

    return len(result) + count