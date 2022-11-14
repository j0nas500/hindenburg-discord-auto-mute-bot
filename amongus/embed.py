import os

import discord
from db.DbConnection import DbConnection


class UserButton(discord.ui.Button):
    def __init__(self, label: str, row: int, db_connection: DbConnection):
        super().__init__(label=label, row=row)
        self.db_connection = db_connection

    async def callback(self, interaction: discord.Interaction):
        msg = await addConnection(self.db_connection, int(self.label), interaction)
        await interaction.response.send_message(content=msg, ephemeral=True, delete_after=10)


def create_view_buttons(result, db_connection: DbConnection):
    view_buttons = discord.ui.View(timeout=None)
    row = 0
    for i, user in enumerate(result):
        view_buttons.add_item(UserButton(str(i + 1), row, db_connection))
        if (i + 1) % 5 == 0:
            row = row + 1

    return view_buttons


def create_embed(all_players, connected_players, code: str, host_channel: discord.VoiceChannel,
                 host_member: discord.Member):
    embed = discord.Embed(title="Among Us Auto Mute")
    embed.add_field(name="Code", value=f"`{code}`")
    embed.add_field(name="Channel", value=host_channel.mention)
    embed.add_field(name="Host", value=host_member.mention)
    embed.add_field(name="Player connected", value=f"{len(connected_players)}/{len(all_players)}", inline=False)

    for i, row in enumerate(all_players):
        if len(row) > 1 and row[1] is None:
            embed.add_field(name=i + 1, value=row[0])
            continue

        member: discord.Member = host_channel.guild.get_member(row[1])
        embed.add_field(name=i + 1, value=f"{row[0]} [{member.mention}]")

    return embed


async def updateEmbed(db_conenction: DbConnection, message: discord.Message, code: str, username: str = None):

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

    sql = f"SELECT username, discord_user_id FROM players WHERE roomcode = '{code}'"
    result = db_conenction.execute_list(sql)
    sql = f"SELECT username, discord_user_id FROM players WHERE roomcode = '{code}' and discord_user_id IS NOT NULL"
    result2 = db_conenction.execute_list(sql)

    if len(result) < 1:
        await message.edit(view=None)
        await message.delete(delay=5)
        return f"No Lobby with room code {code} found!"

    embed = create_embed(result, result2, code, host_channel, host_member)
    view_buttons = create_view_buttons(result, db_conenction)

    if username is not None:
        sql = f"UPDATE players SET discord_message_id = {message.id} WHERE roomcode = '{code}' and username = '{username}'"
        db_conenction.execute(sql)

    await message.edit(embed=embed, view=view_buttons)


async def addConnection(db_connection: DbConnection, index: int, interaction: discord.Interaction):
    user: discord.User = interaction.user
    code: str = interaction.message.embeds[0].fields[0].value
    code = code[1:-1]

    try:
        username: str = interaction.message.embeds[0].fields[index + 3].value
        username = username.split(" [")
        username = username[0]
    except IndexError as err:
        return f"No User with Number {index}"

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

    sql = f"SELECT username, discord_user_id FROM players WHERE roomcode = '{code}'"
    result = db_connection.execute_list(sql)
    sql = f"SELECT username, discord_user_id FROM players WHERE roomcode = '{code}' and discord_user_id IS NOT NULL"
    result2 = db_connection.execute_list(sql)

    if len(result) < 1:
        return f"No Lobby with room code {code} found!"

    embed = create_embed(result, result2, code, host_channel, host_member)

    await interaction.message.edit(embed=embed)
    return f"{interaction.user.mention} conencted to the Among Us User {username}"
