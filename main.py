import asyncio
import logging
import os

import discord
import dotenv
import socketio

from EventsListener import EventsListener
from amongus.Setup import Setup
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

bot = EventsListener(db_connection)
sio = socketio.AsyncClient()


async def runserver():
    await sio.connect('http://localhost:3000')
    print('my sid is', sio.sid)
    # sio.wait()


@sio.event
def connect():
    print("I'm connected!")


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
    if result[0][0] is None:
        return
    await updateEmbed(db_connection, bot.get_message(result[0][0]), data[1][1], username=data[2][1])
    print(data)


@sio.event
async def on_leave(data: dict):
    if data[1][1] == "null":
        return
    await updateEmbed(db_connection, bot.get_message(int(data[1][1])), data[2][1])
    # print(data)


@sio.event
async def on_game_start(data):
    sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{data}'"
    result = db_connection.execute_list(sql)
    if result[0][0] is None:
        return
    sql = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}'"
    await mute_deafen(bot, db_connection, sio, sql)


@sio.event
async def on_game_end(data):
    sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{data}'"
    result = db_connection.execute_list(sql)
    if result[0][0] is None:
        return
    sql = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}'"
    await unmute_undeafen(bot, db_connection, sio, sql)
    sql = f"UPDATE players SET is_ghost = FALSE WHERE is_ghost = TRUE and roomcode = '{data}'"
    db_connection.execute(sql)


@sio.event
async def on_player_start_meeting(data):
    sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{data}'"
    result = db_connection.execute_list(sql)
    if result[0][0] is None:
        return
    sql = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}' and is_ghost = TRUE"
    await mute(bot, db_connection, sio, sql)
    sql = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}' and is_ghost = FALSE"
    await unmute_undeafen(bot, db_connection, sio, sql)


@sio.event
async def on_meeting_voting_complete(data):
    sql = f"SELECT discord_message_id FROM players WHERE roomcode = '{data}'"
    result = db_connection.execute_list(sql)
    if result[0][0] is None:
        return
    sql = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}' and is_ghost = FALSE"
    await mute_deafen(bot, db_connection, sio, sql)
    sql = f"SELECT discord_user_id, discord_voice_id FROM players WHERE discord_user_id IS NOT NULL and roomcode = '{data}' and is_ghost = TRUE"
    await unmute_undeafen(bot, db_connection, sio, sql)





loop = asyncio.get_event_loop()
loop.run_until_complete(runserver())

bot.add_cog(Setup(bot=bot, db_connection=db_connection))
bot.run(os.getenv("TOKEN"))
