import os

import discord

from amongus.emoji import get_emoji, get_emoji_dead
from db.DbConnection import DbConnection


class SelectUserNameOptions(discord.ui.Select):
    def __init__(self, options: list, db_connection: DbConnection, code: str):
        super().__init__(placeholder="Select your in-game name", min_values=1, max_values=1, options=options)
        self.db_connection = db_connection
        self.code = code

    async def callback(self, interaction):
        if self.values[0] == "unlink":
            msg = await addConnection(self.db_connection, interaction, self.values[0], self.code, is_unlink=True)
        else:
            msg = await addConnection(self.db_connection, interaction, self.values[0], self.code)
        await interaction.response.send_message(content=msg, ephemeral=True, delete_after=10)


def create_user_options(db_connection: DbConnection, roomcode: str):
    sql = f"SELECT username, color_id FROM players WHERE roomcode = '{roomcode}' and discord_user_id IS NULL"
    result = db_connection.execute_list(sql)

    options: list = list()
    for username in result:
        select_option = discord.SelectOption(label=username[0], emoji=get_emoji(username[1]))
        options.append(select_option)
    options.append(discord.SelectOption(label="unlink", emoji="❌"))
    return options


def create_embed(all_players, connected_players, code: str, host_channel: discord.VoiceChannel,
                 host_member: discord.Member, game_state: int = 0):
    if game_state == 0:
        embed = discord.Embed(title="LOBBY", color=discord.Color.green())
    if game_state == 1:
        embed = discord.Embed(title="TASKS", color=discord.Color.blurple())
    if game_state == 2:
        embed = discord.Embed(title="DISCUSSION", color=discord.Color.nitro_pink())

    embed.add_field(name="Host", value=host_member.mention, inline=True)
    embed.add_field(name="Channel", value=host_channel.mention, inline=True)
    embed.add_field(name="Players Linked", value=f"{len(connected_players)}/{len(all_players)}", inline=True)
    embed.add_field(name="🔒 Code", value=f"{code}", inline=False)

    for row in all_players:
        if len(row) > 1 and row[1] is None and row[2] is not None:
            if row[3] == 0:
                embed.add_field(name=f"{get_emoji(row[2])} {row[0]}", value="unlinked")
            else:
                embed.add_field(name=f"{get_emoji_dead(row[2])} {row[0]}", value="unlinked")
            continue

        if len(row) > 1 and row[1] is None:
            embed.add_field(name=row[0], value="unlinked")
            continue

        member: discord.Member = host_channel.guild.get_member(row[1])
        if row[3] == 0:
            embed.add_field(name=f"{get_emoji(row[2])} {row[0]}", value=f"{member.mention}")
        else:
            embed.add_field(name=f"{get_emoji_dead(row[2])} {row[0]}", value=member.mention)

    return embed


async def updateEmbed(db_conenction: DbConnection, message: discord.Message, code: str, username: str = None, game_state: int = 0):
    sql = f"SELECT username, discord_user_id, discord_voice_id FROM players WHERE roomcode = '{code}' and is_host = TRUE"
    result = db_conenction.execute_list(sql)

    if len(result) < 1:
        await message.edit(view=None)
        await message.delete(delay=5)
        sql = f"UPDATE players SET discord_message_id = NULL WHERE roomcode = '{code}'"
        db_conenction.execute(sql)
        return f"Host leaved"

    host_channel: discord.VoiceChannel = message.guild.get_channel(result[0][2])
    host_member: discord.Member = message.guild.get_member(result[0][1])

    if host_channel is None:
        await message.edit(view=None)
        await message.delete(delay=5)
        sql = f"UPDATE players SET discord_message_id = NULL, is_host = FALSE WHERE roomcode = '{code}'"
        db_conenction.execute(sql)
        return f"Host leaved"

    sql = f"SELECT username, discord_user_id, color_id, is_ghost FROM players WHERE roomcode = '{code}'"
    result = db_conenction.execute_list(sql)
    sql = f"SELECT username, discord_user_id, color_id, is_ghost FROM players WHERE roomcode = '{code}' and discord_user_id IS NOT NULL"
    result2 = db_conenction.execute_list(sql)

    if len(result) < 1:
        await message.edit(view=None)
        await message.delete(delay=5)
        return f"No Lobby with room code {code} found!"

    embed: discord.Embed = create_embed(result, result2, code, host_channel, host_member, game_state=game_state)
    view_buttons = discord.ui.View(timeout=None)
    options = create_user_options(db_connection=db_conenction, roomcode=code)
    view_buttons.add_item(SelectUserNameOptions(options, db_conenction, code))

    if username is not None:
        sql = f"UPDATE players SET discord_message_id = {message.id} WHERE roomcode = '{code}' and username = '{username}'"
        db_conenction.execute(sql)

    if len(message.embeds) > 0 and message.embeds[0].to_dict() == embed.to_dict():
        return

    await message.edit(embed=embed, view=view_buttons)


async def addConnection(db_connection: DbConnection, interaction: discord.Interaction, username: str, code: str, is_unlink: bool = False):
    user: discord.User = interaction.user

    if user.voice is None:
        return "You are not in a voice Channel"

    channel: discord.VoiceChannel = user.voice.channel

    sql = f"SELECT discord_voice_id, discord_user_id FROM players WHERE is_host = TRUE and roomcode = '{code}'"
    result = db_connection.execute_list(sql)

    if len(result) < 1:
        await interaction.message.edit(view=None)
        await interaction.message.delete(delay=5)
        return "No Host found"

    host_channel: discord.VoiceChannel = interaction.guild.get_channel(result[0][0])
    host_member: discord.Member = interaction.guild.get_member(result[0][1])

    if is_unlink:
        if user.id == host_member.id:
            await interaction.message.edit(view=None)
            await interaction.message.delete(delay=5)
            sql = f"UPDATE players SET discord_message_id = NULL, is_host = FALSE WHERE roomcode = '{code}'"
            db_connection.execute(sql)
            return "Host Unlinked"
        sql = f"SELECT username FROM players WHERE discord_user_id = {user.id}"
        result = db_connection.execute_list(sql)
        if len(result) < 1:
            return f"{user.mention} not linked"

        sql = f"UPDATE players SET discord_user_id = NULL, discord_voice_id = NULL WHERE discord_user_id = {user.id}"
        db_connection.execute(sql)

        sql = f"SELECT username, discord_user_id, color_id, is_ghost FROM players WHERE roomcode = '{code}'"
        result = db_connection.execute_list(sql)
        sql = f"SELECT username, discord_user_id, color_id, is_ghost FROM players WHERE roomcode = '{code}' and discord_user_id IS NOT NULL"
        result2 = db_connection.execute_list(sql)

        if len(result) < 1:
            return f"No Lobby with room code {code} found!"

        embed = create_embed(result, result2, code, host_channel, host_member)
        view = discord.ui.View(timeout=None)
        options = create_user_options(db_connection, code)
        view.add_item(SelectUserNameOptions(options, db_connection, code))

        await interaction.message.edit(embed=embed, view=view)

        return f"{user.mention} unlinked"

    if channel.id != host_channel.id:
        return f"You must be in this voice Channel {host_channel.mention}"

    sql = f"SELECT is_host FROM players WHERE discord_user_id = {user.id}"
    result = db_connection.execute_list(sql)
    if len(result) > 0 and result[0][0] == 1:
        sql = f"UPDATE players SET discord_user_id = NULL, discord_voice_id = NULL, is_host = FALSE WHERE discord_user_id = {user.id}"
        db_connection.execute(sql)
        sql = f"UPDATE players SET discord_user_id = {user.id}, discord_voice_id = {channel.id}, is_host = TRUE WHERE roomcode = '{code}' and username = '{username}'"
        db_connection.execute(sql)
    else:
        sql = f"UPDATE players SET discord_user_id = NULL, discord_voice_id = NULL WHERE discord_user_id = {user.id}"
        db_connection.execute(sql)
        sql = f"UPDATE players SET discord_user_id = {user.id}, discord_voice_id = {channel.id} WHERE roomcode = '{code}' and username = '{username}'"
        db_connection.execute(sql)

    sql = f"SELECT username, discord_user_id, color_id, is_ghost FROM players WHERE roomcode = '{code}'"
    result = db_connection.execute_list(sql)
    sql = f"SELECT username, discord_user_id, color_id, is_ghost FROM players WHERE roomcode = '{code}' and discord_user_id IS NOT NULL"
    result2 = db_connection.execute_list(sql)

    if len(result) < 1:
        return f"No Lobby with room code {code} found!"

    embed = create_embed(result, result2, code, host_channel, host_member)
    view = discord.ui.View(timeout=None)
    options = create_user_options(db_connection, code)
    view.add_item(SelectUserNameOptions(options, db_connection, code))

    await interaction.message.edit(embed=embed, view=view)
    return f"{interaction.user.mention} connected to the Among Us User {username}"
