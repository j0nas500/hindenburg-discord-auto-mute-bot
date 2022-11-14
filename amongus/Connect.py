import discord
from discord.ext import commands

from amongus.embed import updateEmbed
from db.DbConnection import DbConnection


class Connect(commands.Cog):
    def __init__(self, bot: commands.Bot, db_connection: DbConnection):
        self.bot = bot
        self.db_connection = db_connection
        self.select_roomcode: discord.Option = discord.Option(str, )

    @commands.slash_command(name="connect", description="Add discord user to among us user")
    @discord.default_permissions(connect=True)
    async def connect(self, ctx: discord.ApplicationContext,
                      user: discord.Option(discord.SlashCommandOptionType.user),
                      username: discord.Option(str, name="username", description="Among Us username to connect")):

        host_member: discord.Member = ctx.author
        member: discord.Member = user
        username: str = username

        if ";" in username or "'" in username or "`" in username or "DROP" in username.upper():
            await ctx.respond("Don't try it")
            return

        if member.voice is None:
            if member.voice is None:
                await ctx.send_response(content=f"{member.mention} is not in a voice Channel", ephemeral=True,
                                        delete_after=10)
                return

        channel: discord.VoiceChannel = member.voice.channel

        sql = f"SELECT roomcode FROM players WHERE discord_user_id = '{host_member.id}' and is_host = TRUE"
        result = self.db_connection.execute_list(sql)

        if len(result) < 1:
            await ctx.send_response(content=f"You are not the Host of the Lobby", ephemeral=True, delete_after=10)
            return

        code = result[0][0]

        sql = f"SELECT username, discord_user_id FROM players WHERE roomcode = '{code}' and username = '{username}'"
        result = self.db_connection.execute_list(sql)
        sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{code}'"
        result2 = self.db_connection.execute_list(sql)
        msg = discord.Message = self.bot.get_message(result2[0][0])

        if len(result) < 1:
            await ctx.send_response(content=f"No User {username} in Lobby with room code {code} found!", ephemeral=True,
                                    delete_after=10)
            return

        sql = f"UPDATE players SET discord_message_id = {result2[0][0]}, discord_voice_id = {channel.id}, discord_user_id = {member.id} WHERE roomcode = '{code}' and username = '{result[0][0]}'"
        self.db_connection.execute(sql)
        await updateEmbed(self.db_connection, msg, code)
        await ctx.send_response(content=f"{member.mention} conencted to the Among Us User {username}", ephemeral=True, delete_after=10)
