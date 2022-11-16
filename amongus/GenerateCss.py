import discord
from discord.ext import commands

from amongus.emoji import get_color_name
from db.DbConnection import DbConnection


class GenerateCss(commands.Cog):
    def __init__(self, bot: commands.Bot, db_connection: DbConnection):
        self.bot = bot
        self.db_connection = db_connection

    @commands.slash_command(name="generate", description="only for j0")
    @discord.default_permissions(connect=True)
    async def generate(self, ctx: discord.ApplicationContext,
                       code: discord.Option(str, min_length=4, max_length=6)):

        if ctx.author.id != 257468686347141120:
            await ctx.send_response(content="No permission", delete_after=5)
            return

        code: str = code
        code = code.upper()

        sql = f"SELECT discord_user_id, color_id FROM players WHERE roomcode = '{code}' and discord_user_id IS NOT NULL"
        result = self.db_connection.execute_list(sql)

        str_list = []
        str_list.append("""
.voice-state .avatar {
display: none;
}""")

        for entry in result:
            str_list.append(
                """
.voice-state[data-reactid*="%s"] .avatar {
display: block;
content: url('https://j0nas500.de/projects/amongus/color/%s.png');
}""" % (entry[0], get_color_name(entry[1])))

        str_list.append(
            """
.avatar {
height:100px !important;
width:76px !important;
border-radius:10px !important;
filter: brightness(70%);
}
.speaking {
border-color:rgba(0,255,0,0.7) !important;
position:relative;
animation-name: speak-now;
animation-duration: 5000ms;
animation-fill-mode:forwards;
filter: brightness(100%) ;
}
@keyframes speak-now {
0% { bottom:0px; }
5% { bottom:10px; }
10% { bottom:0px; }
15% { bottom:10px; }
20% { bottom:0px; }
25% { bottom:10px; }
30% { bottom:0px; }
35% { bottom:10px; }
40% { bottom:0px; }
45% { bottom:10px; }
50% { bottom:0px; }
55% { bottom:10px; }
60% { bottom:0px; }
65% { bottom:10px; }
70% { bottom:0px; }
75% { bottom:10px; }
80% { bottom:0px; }
85% { bottom:10px; }
90% { bottom:0px; }
95% { bottom:10px; }
100% { bottom:0px; }
}
li.voice-state{
width: 90px;
height: 90px;
position: static;
display: inline-block;
}
.user{
background: rgba(0,0,0,.7);
padding: 0px 0px 0px !important;
border-radius: 4px;
display: inline-block;
}
span.name{
display: none;
}
body {
background-color: rgba(0, 0, 0, 0);
margin: 0;
padding: 0;
overflow: hidden;
}
""")
        with open('discord.css', 'w') as f:
            f.writelines(str_list)

        await ctx.send_response(file=discord.File('discord.css'), ephemeral=True, delete_after=60)

