import discord
from discord.ext import commands

from amongus.embed import updateEmbed
from amongus.emoji import get_emoji
from db.DbConnection import DbConnection


class SelectUserNameLink(discord.ui.Select):
    def __init__(self, options: list, db_connection: DbConnection, code: str, channel: discord.VoiceChannel,
                 member: discord.Member, msg: discord.Message):
        super().__init__(placeholder="Select", min_values=1, max_values=1, options=options)
        self.db_connection = db_connection
        self.code = code
        self.channel = channel
        self.member = member
        self.msg = msg

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        sql = f"UPDATE players SET discord_message_id = {self.msg.id}, discord_voice_id = {self.channel.id}, discord_user_id = {self.member.id} WHERE roomcode = '{self.code}' and username = '{self.values[0]}'"
        self.db_connection.execute(sql)
        await updateEmbed(self.db_connection, self.msg, self.code)
        await interaction.response.edit_message(content=f"{self.member.mention} linked to the Among Us User {self.values[0]}", view=None)


class Link(commands.Cog):
    def __init__(self, bot: commands.Bot, db_connection: DbConnection):
        self.bot = bot
        self.db_connection = db_connection

    @commands.slash_command(name="link", description="link discord user to in-game user")
    @discord.default_permissions(connect=True)
    async def link(self, ctx: discord.ApplicationContext,
                   user: discord.Option(discord.SlashCommandOptionType.user)):

        host_member: discord.Member = ctx.author
        member: discord.Member = user

        if member.voice is None:
            if member.voice is None:
                await ctx.send_response(content=f"{member.mention} is not in a voice Channel", ephemeral=True,
                                        delete_after=10)
                return

        channel: discord.VoiceChannel = member.voice.channel

        sql = f"SELECT roomcode, discord_message_id FROM players WHERE discord_user_id = '{host_member.id}' and is_host = TRUE"
        result = self.db_connection.execute_list(sql)

        if len(result) < 1:
            await ctx.send_response(content=f"You are not the Host of the Lobby", ephemeral=True, delete_after=10)
            return

        code = result[0][0]
        msg: discord.Message = self.bot.get_message(result[0][1])

        sql = f"SELECT username, color_id FROM players WHERE roomcode = '{code}' and discord_user_id IS NULL"
        result = self.db_connection.execute_list(sql)

        options: list = list()
        for username in result:
            select_option = discord.SelectOption(label=username[0], emoji=get_emoji(username[1]))
            options.append(select_option)

        view = discord.ui.View(timeout=30)
        view.add_item(SelectUserNameLink(options, self.db_connection, code, channel, member, msg))

        await ctx.send_response(content=f"Select in-game name to link {member.mention}", ephemeral=True, view=view, delete_after=30)