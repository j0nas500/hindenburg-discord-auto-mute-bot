import discord
from discord.ext import commands

from amongus.embed import create_embed, create_user_options, SelectUserNameOptions, updateEmbed
from db.DbConnection import DbConnection


class Unlink(commands.Cog):
    def __init__(self, bot: commands.Bot, db_connection: DbConnection):
        self.bot = bot
        self.db_connection = db_connection

    @commands.slash_command(name="unlink", description="unlink discord user to in-game user")
    @discord.default_permissions(connect=True)
    async def unlink(self, ctx: discord.ApplicationContext,
                     user: discord.Option(discord.SlashCommandOptionType.user)):
        host_member: discord.Member = ctx.author
        member: discord.Member = user

        sql = f"SELECT roomcode, discord_voice_id, discord_user_id FROM players WHERE discord_user_id = '{host_member.id}' and is_host = TRUE"
        result = self.db_connection.execute_list(sql)

        if len(result) < 1:
            await ctx.send_response(content=f"You are not the Host of the Lobby", ephemeral=True, delete_after=10)
            return

        code = result[0][0]
        host_channel: discord.VoiceChannel = self.bot.get_channel(result[0][1])
        host_member: discord.Member = host_channel.guild.get_member(result[0][2])

        sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{code}'"
        result = self.db_connection.execute_list(sql)

        msg = discord.Message = self.bot.get_message(result[0][0])

        if user.id == host_member.id:
            await msg.edit(view=None)
            await msg.delete(delay=5)
            sql = f"UPDATE players SET discord_message_id = NULL, is_host = FALSE WHERE roomcode = '{code}'"
            self.db_connection.execute(sql)
            await ctx.send_response(content=f"Host Unlinked", ephemeral=True, delete_after=10)
            return

        sql = f"SELECT username, discord_user_id FROM players WHERE discord_user_id = {user.id}"
        result = self.db_connection.execute_list(sql)

        if len(result) < 1:
            await ctx.send_response(content=f"{user.mention} not linked in Lobby with room code {code}!",
                                    ephemeral=True,
                                    delete_after=10)
            return

        sql = f"UPDATE players SET discord_user_id = NULL, discord_voice_id = NULL WHERE discord_user_id = {user.id}"
        self.db_connection.execute(sql)

        await updateEmbed(self.db_connection, msg, code)
        await ctx.send_response(content=f"{member.mention} unlinked", ephemeral=True, delete_after=10)
