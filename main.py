import asyncio
import logging
import os

import discord
import dotenv
import socketio

from EventsListener import EventsListener
from amongus.GenerateCss import GenerateCss
from amongus.Link import Link
from amongus.Setup import Setup
from amongus.Unlink import Unlink
from amongus.VoicestateClass import VoicestateClass
from amongus.embed import updateEmbed
from amongus.voicestate import mute_deafen, unmute_undeafen, mute
from db.DbConnection import DbConnection

dotenv.load_dotenv()
logging.basicConfig()

db_connection = DbConnection(
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    host=os.getenv("MYSQL_HOST"),
    port=int(os.getenv("MYSQL_PORT")),
    database=os.getenv("MYSQL_DATABASE")
)

bot = EventsListener(db_connection=db_connection)
sio = socketio.AsyncClient()
JWT = os.getenv("JWT")


async def runserver():
    await sio.connect('http://localhost:3000',
                      headers={
                          "Authorization": f"Bearer {JWT}"
                      })
    print('my sid is', sio.sid)
    # sio.wait()


@sio.event
async def connect():
    print("I'm connected!")
    await sio.emit("room", "main")


@sio.event
def connect_error(data):
    print("The connection failed!")


@sio.event
def disconnect():
    print("I'm disconnected!")


@sio.on("on_join")
async def on_join(data: dict):
    sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{data[1][1]}'"
    result = db_connection.execute_list(sql)
    await bot.change_bot_presence(1)
    if result[0][0] is None:
        return
    await updateEmbed(db_connection, bot.get_message(result[0][0]), data[1][1], username=data[2][1])
    # print(data)


@sio.event
async def on_leave(data: dict):
    sql = f"SELECT username FROM players"
    result = db_connection.execute_list(sql)
    await bot.change_bot_presence(len(result), is_sum=True)
    if data[1][1] == "null":
        return
    await updateEmbed(db_connection, bot.get_message(int(data[1][1])), data[2][1])
    # print(data)


@sio.event
async def on_setcolor(data: dict):
    sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{data[1][1]}'"
    result = db_connection.execute_list(sql)
    if result[0][0] is None:
        return
    await updateEmbed(db_connection, bot.get_message(result[0][0]), data[1][1])


@sio.event
async def on_game_start(data):
    sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{data}'"
    result = db_connection.execute_list(sql)
    if result[0][0] is None:
        return
    sql = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}'"
    await voice_state.perform_tasks(sql, 0)
    await updateEmbed(db_connection, bot.get_message(result[0][0]), data, game_state=1)
    # await mute_deafen(bot, db_connection, sio, sql)


@sio.event
async def on_game_end(data):
    sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{data}'"
    result = db_connection.execute_list(sql)
    if result[0][0] is None:
        return
    sql = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}'"
    await voice_state.perform_tasks(sql, 1)
    # await unmute_undeafen(bot, db_connection, sio, sql)
    sql = f"UPDATE players SET is_ghost = FALSE WHERE is_ghost = TRUE and roomcode = '{data}'"
    db_connection.execute(sql)
    await updateEmbed(db_connection, bot.get_message(result[0][0]), data, game_state=0)


@sio.event
async def on_player_start_meeting(data):
    sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{data}'"
    result = db_connection.execute_list(sql)
    if result[0][0] is None:
        return
    sql_dead = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}' and is_ghost = TRUE"
    # calls: int = await mute(bot, db_connection, sio, sql)
    # print("calls")
    # print(calls)
    sql_alive = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}' and is_ghost = FALSE"
    # await unmute_undeafen(bot, db_connection, sio, sql, calls=calls)
    await voice_state.perform_tasks(sql_query_dead=sql_dead, sql_query_alive=sql_alive, game_state=2)
    await updateEmbed(db_connection, bot.get_message(result[0][0]), data, game_state=2)


@sio.event
async def on_meeting_voting_complete(data):
    sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{data}'"
    result = db_connection.execute_list(sql)
    if result[0][0] is None:
        return
    sql_alive = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}' and is_ghost = FALSE"
    # calls: int = await mute_deafen(bot, db_connection, sio, sql)
    # print("calls")
    # print(calls)
    sql_dead = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}' and is_ghost = TRUE"
    # await unmute_undeafen(bot, db_connection, sio, sql, calls=calls)
    await voice_state.perform_tasks(sql_query_alive=sql_alive, sql_query_dead=sql_dead, game_state=3)
    await updateEmbed(db_connection, bot.get_message(result[0][0]), data, game_state=1)


@sio.event
async def on_player_die(data):
    sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{data}'"
    result = db_connection.execute_list(sql)
    if result[0][0] is None:
        return
    sql_dead = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}' and is_ghost = TRUE"
    await voice_state.perform_tasks(sql_dead, 4)


loop = asyncio.get_event_loop()
loop.run_until_complete(runserver())
voice_state = VoicestateClass(bot, db_connection, sio)

bot.add_cog(Setup(bot=bot, db_connection=db_connection))
bot.add_cog(Link(bot=bot, db_connection=db_connection))
bot.add_cog(Unlink(bot, db_connection))
bot.add_cog(GenerateCss(bot, db_connection))
bot.run(os.getenv("TOKEN_MAIN"))
