import os

import discord
import dotenv
from discord.ext import commands

from amongus.embed import addConnection, create_embed, create_user_options, SelectUserNameOptions, updateEmbed
from db.DbConnection import DbConnection

dotenv.load_dotenv()


class SelectUserName(discord.ui.Select):
    def __init__(self, options: list, db_connection: DbConnection, code: str, result, channel: discord.VoiceChannel,
                 member: discord.Member, origin_interaction: discord.Interaction):
        super().__init__(placeholder="Select", min_values=1, max_values=1, options=options)
        self.db_connection = db_connection
        self.code = code
        self.result = result
        self.channel = channel
        self.member = member
        self.origin_interaction = origin_interaction

    async def callback(self, interaction):
        await self.origin_interaction.edit_original_response(view=None, delete_after=5)
        await interaction.response.send_message(content=f"{self.values[0]} is your Among Us name")

        res: list = [[self.values[0], self.member.id]]
        embed = create_embed(self.result, res, self.code, self.channel, self.member)
        view_user_list = discord.ui.View(timeout=None)
        options = create_user_options(self.db_connection, self.code)
        view_user_list.add_item(SelectUserNameOptions(options, self.db_connection, self.code))

        interaction_message: discord.InteractionMessage = await interaction.edit_original_response(content=None,
                                                                                                   embed=embed,
                                                                                                   view=view_user_list)
        sql = f"UPDATE players SET discord_message_id = {interaction_message.id}, discord_voice_id = {self.channel.id}, discord_user_id = {self.member.id}, is_host = TRUE WHERE roomcode = '{self.code}' and username = '{self.values[0]}'"
        self.db_connection.execute(sql)
        sql = f"UPDATE players SET discord_message_id = {interaction_message.id}, discord_voice_id = {self.channel.id} WHERE roomcode = '{self.code}' and is_host = FALSE"
        self.db_connection.execute(sql)

        await updateEmbed(self.db_connection, interaction_message, self.code)


# class ViewUserName(discord.ui.View):
#     def __init__(self, db_connection: DbConnection, code: str):
#         super().__init__(timeout=30)


class Setup(commands.Cog):
    def __init__(self, bot: commands.Bot, db_connection: DbConnection):
        self.bot = bot
        self.db_connection = db_connection

    @commands.slash_command(name="setup", description="Setup for Auto Mute")
    @discord.default_permissions(connect=True)
    async def setup(self, ctx,
                    room_code: discord.Option(str, name="roomcode", description="Roomcode of your Among Us Lobby",
                                              max_length=6, min_length=4)):
        member: discord.Member = ctx.author
        if member.voice is None:
            await ctx.send_response(content="You are not in a voice Channel", ephemeral=True, delete_after=10)
            return

        channel: discord.VoiceChannel = member.voice.channel

        code: str = room_code
        code = code.upper()
        if ";" in code or "'" in code or "`" in code or "DROP" in code:
            await ctx.respond("Don't try it")
            return

        sql = f"SELECT username, discord_user_id FROM players WHERE roomcode = '{code}'"
        result = self.db_connection.execute_list(sql)

        if len(result) < 1:
            await ctx.send_response(content=f"No Lobby with room code {code} found!", ephemeral=True, delete_after=10)
            return

        sql = f"SELECT discord_user_id FROM players WHERE roomcode = '{code}' and is_host = TRUE"
        result2 = self.db_connection.execute_list(sql)

        if len(result2) > 0:
            if member.id != result2[0][0]:
                await ctx.send_response(content=f"You are not the Host of the Lobby", ephemeral=True, delete_after=10)
                return

            sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{code}' and is_host = TRUE"
            result2 = self.db_connection.execute_list(sql)
            msg: discord.Message = self.bot.get_message(result2[0][0])
            await msg.edit(view=None)
            await msg.delete(delay=5)

        if len(result) > 1:
            options: list = list()
            for row in result:
                select_option = discord.SelectOption(
                    label=row[0]
                )
                options.append(select_option)

            view_select = discord.ui.View(timeout=60)
            interaction: discord.Interaction = await ctx.send_response(content="Select your Among Us Username",
                                                                       ephemeral=True,
                                                                       view=view_select)

            select = SelectUserName(options, self.db_connection, code, result, channel, member, interaction)
            view_select.add_item(select)
            await interaction.edit_original_response(view=view_select)
            return

        interaction: discord.Interaction = await ctx.send_response(content=f"{result[0][0]} is your Among Us name")
        interaction_message: discord.InteractionMessage = await interaction.original_response()

        sql = f"UPDATE players SET discord_message_id = {interaction_message.id}, discord_voice_id = {channel.id}, discord_user_id = {member.id}, is_host = TRUE WHERE roomcode = '{code}' and username = '{result[0][0]}'"
        self.db_connection.execute(sql)
        sql = f"UPDATE players SET discord_message_id = {interaction_message.id}, discord_voice_id = {channel.id} WHERE roomcode = '{code}' and is_host = FALSE"
        self.db_connection.execute(sql)

        view_user_name = discord.ui.View(timeout=None)
        options = create_user_options(self.db_connection, code)
        view_user_name.add_item(SelectUserNameOptions(options, self.db_connection, code))

        res: list = [[result[0][0], member.id]]
        embed = create_embed(res, res, code, channel, member)

        await interaction.edit_original_response(content=None, embed=embed, view=view_user_name)
