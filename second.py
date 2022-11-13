import asyncio
import json
import logging
import os

import discord
import dotenv
import socketio

from EventsListener import EventsListener
from amongus.Setup import Setup
from amongus.embed import updateEmbed
from amongus.voicestate import mute_deafen, unmute_undeafen
from db.DbConnection import DbConnection

dotenv.load_dotenv()
logging.basicConfig()
bot = EventsListener()
sio = socketio.AsyncClient()
JWT = os.getenv("JWT")


async def runserver():
    await sio.connect('http://localhost:3000', headers={
        "Authorization": f"Bearer {JWT}"
    })
    print('my sid is', sio.sid)
    # sio.wait()


@sio.event
async def connect():
    print("I'm connected!")
    await sio.emit("room", "second")


@sio.event
def connect_error(data):
    print("The connection failed!")


@sio.event
def disconnect():
    print("I'm disconnected!")


@sio.on("connection")
async def on_connection(socket):
    socket.join("bot")
    print("joined room bot")


@sio.on("on_mute_deafen")
async def on_mute_deafen(data: dict):
    data = list(data.values())
    guild_id = int(data[0])
    member_id = int(data[1])
    member: discord.Member = bot.get_guild(guild_id).get_member(member_id)
    await member.edit(mute=True, deafen=True)


@sio.event
async def on_unmute_undeafen(data):
    data = list(data.values())
    guild_id = int(data[0])
    member_id = int(data[1])
    member: discord.Member = bot.get_guild(guild_id).get_member(member_id)
    await member.edit(mute=False, deafen=False)


@sio.event
async def on_mute(data):
    data = list(data.values())
    guild_id = int(data[0])
    member_id = int(data[1])
    member: discord.Member = bot.get_guild(guild_id).get_member(member_id)
    await member.edit(mute=True, deafen=False)


loop = asyncio.get_event_loop()
loop.run_until_complete(runserver())

bot.run(os.getenv("TOKEN2"))
