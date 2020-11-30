#    Hitsuki (A telegram bot project)

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import html
import os
import re
import sys
import aiohttp
import regex
from datetime import datetime
from aiohttp import ClientSession

from pyrogram import Client, filters
from pyrogram.types import Message, Update

from hitsuki import TOKEN, SUDO_USERS, SYSTEM_DUMP, pbot

# Some commands in this module are EduuRobot ports (authorized)
# EduuRobot commands:
# /dice, /ping, /pyroid, sed/regex, /upgrade, /cmd, /restart
#
# The /ip command is a pyrogram adaptation of MicroBot
#
# EduuRobot: github.com/AmanoTeam/EduuRobot
# MicroBot: github.com/Nick80835/microbot
#
# Please do not remove these comments!


@pbot.on_message(filters.command('dice'))
async def dice(c: Client, m: Message):
    dicen = await c.send_dice(m.chat.id, reply_to_message_id=m.message_id)
    await dicen.reply_text(
        f"The dice stopped at the number {dicen.dice.value}", quote=True)


@pbot.on_message(filters.command("pyroid") & filters.private)
async def ids_private(c: Client, m: Message):
    await m.reply_text("<b>Info:</b>\n\n"
                       "<b>Name:</b> <code>{first_name} {last_name}</code>\n"
                       "<b>Username:</b> @{username}\n"
                       "<b>User ID:</b> <code>{user_id}</code>\n"
                       "<b>Language:</b> {lang}\n"
                       "<b>Chat type:</b> {chat_type}".format(
                           first_name=m.from_user.first_name,
                           last_name=m.from_user.last_name or "",
                           username=m.from_user.username,
                           user_id=m.from_user.id,
                           lang=m.from_user.language_code,
                           chat_type=m.chat.type
                       ),
                       parse_mode="HTML")


@pbot.on_message(filters.command("pyroid") & filters.group)
async def ids(c: Client, m: Message):
    d = m.reply_to_message or m
    await m.reply_text("<b>Info:</b>\n\n"
                       "<b>Name:</b> <code>{first_name} {last_name}</code>\n"
                       "<b>Username:</b> @{username}\n"
                       "<b>User ID:</b> <code>{user_id}</code>\n"
                       "<b>Datacenter:</b> {user_dc}\n"
                       "<b>Language:</b> {lang}\n\n"
                       "<b>Chat name:</b> <code>{chat_title}</code>\n"
                       "<b>Chat username:</b> @{chat_username}\n"
                       "<b>Chat ID:</b> <code>{chat_id}</code>\n"
                       "<b>Chat type:</b> {chat_type}".format(
                           first_name=html.escape(d.from_user.first_name),
                           last_name=html.escape(d.from_user.last_name or ""),
                           username=d.from_user.username,
                           user_id=d.from_user.id,
                           user_dc=d.from_user.dc_id,
                           lang=d.from_user.language_code or "-",
                           chat_title=m.chat.title,
                           chat_username=m.chat.username,
                           chat_id=m.chat.id,
                           chat_type=m.chat.type
                       ),
                       parse_mode="HTML")


@pbot.on_message(filters.command("ping"))
async def ping(c: Client, m: Message):
    first = datetime.now()
    sent = await m.reply_text("**Pong!**")
    second = datetime.now()
    await sent.edit_text(
        f"**Pong!** `{(second - first).microseconds / 1000}`ms")


@pbot.on_message(filters.regex(r'^s/(.+)?/(.+)?(/.+)?') & filters.reply)
async def sed(c: Client, m: Message):
    exp = regex.split(r'(?<![^\\]\\)/', m.text)
    pattern = exp[1]
    replace_with = exp[2].replace(r'\/', '/')
    flags = exp[3] if len(exp) > 3 else ''

    count = 1
    rflags = 0

    if 'g' in flags:
        count = 0
    if 'i' in flags and 's' in flags:
        rflags = regex.I | regex.S
    elif 'i' in flags:
        rflags = regex.I
    elif 's' in flags:
        rflags = regex.S

    text = m.reply_to_message.text or m.reply_to_message.caption

    if not text:
        return

    try:
        res = regex.sub(
            pattern,
            replace_with,
            text,
            count=count,
            flags=rflags,
            timeout=1)
    except TimeoutError:
        await m.reply_text("Oops, your regex pattern ran for too long.")
    except regex.error as e:
        await m.reply_text(str(e))
    else:
        await c.send_message(m.chat.id, f'<pre>{html.escape(res)}</pre>',
                             reply_to_message_id=m.reply_to_message.message_id)


@pbot.on_message(filters.command("banall") &
                 filters.group & filters.user(SUDO_USERS))
async def ban_all(c: Client, m: Message):
    chat = m.chat.id

    async for member in c.iter_chat_members(chat):
        user_id = member.user.id
        url = (
            f"https://api.telegram.org/bot{TOKEN}/kickChatMember?chat_id={chat}&user_id={user_id}")
        async with aiohttp.ClientSession() as session:
            await session.get(url)


@pbot.on_message(filters.command("upgrade") & filters.user(SUDO_USERS))
async def upgrade(c: Client, m: Message):
    sm = await m.reply_text("Upgrading sources...")
    proc = await asyncio.create_subprocess_shell("git pull --no-edit",
                                                 stdout=asyncio.subprocess.PIPE,
                                                 stderr=asyncio.subprocess.STDOUT)
    stdout = (await proc.communicate())[0]
    if proc.returncode == 0:
        if "Already up to date." in stdout.decode():
            await sm.edit_text("There's nothing to upgrade.")
        else:
            await sm.edit_text("Restarting...")
            await pbot.send_message(SYSTEM_DUMP,
                                    "**Hitsuki is updating!**")
            args = [sys.executable, "-m", "hitsuki"]
            os.execl(sys.executable, *args)
    else:
        await sm.edit_text(f"Upgrade failed (process exited with {proc.returncode}):\n{stdout.decode()}")
        proc = await asyncio.create_subprocess_shell("git merge --abort")
        await proc.communicate()


@pbot.on_message(filters.command("cmd") & filters.user(SUDO_USERS))
async def run_cmd(c: Client, m: Message):
    cmd = m.text.split(maxsplit=1)[1]
    if re.match('(?i)poweroff|halt|shutdown|reboot', cmd):
        res = ('Forbidden command.')
    else:
        proc = await asyncio.create_subprocess_shell(cmd,
                                                     stdout=asyncio.subprocess.PIPE,
                                                     stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        res = ("<b>Output:</b>\n<code>{}</code>".format(html.escape(stdout.decode().strip())) if stdout else '') + \
              ("\n<b>Errors:</b>\n<code>{}</code>".format(
                  html.escape(stderr.decode().strip())) if stderr else '')
    await m.reply_text(res)


@pbot.on_message(filters.command("restart") & filters.user(SUDO_USERS))
async def restart(c: Client, m: Message):
    await m.reply_text("Restarting...")
    await pbot.send_message(SYSTEM_DUMP, "**Hitsuki is restarting...**")
    args = [sys.executable, "-m", "hitsuki"]
    os.execl(sys.executable, *args)


@pbot.on_message(filters.command("logs") & filters.user(SUDO_USERS))
async def logs(c: Client, m: Message):
    await m.reply_text("Sending LOGs...")
    await pbot.send_document(
        document='log.txt',
        caption="`Hitsuki's System LOGs`",
        chat_id=SYSTEM_DUMP,
        parse_mode="markdown")
    await m.reply_text("Done! LOGs are sent to system_dump.")


@pbot.on_message(filters.command("ip"))
async def ip(c: Client, update: Update):
    ip = update.command[1]

    aioclient = ClientSession()
    if not ip:
        await update.reply_text("Provide an IP!")
        return

    async with aioclient.get(f"http://ip-api.com/json/{ip}") as response:
        if response.status == 200:
            lookup_json = await response.json()
        else:
            await update.reply_text(f"An error occurred when looking for **{ip}**: **{response.status}**")
            return

    fixed_lookup = {}

    for key, value in lookup_json.items():
        special = {"lat": "Latitude", "lon": "Longitude",
                   "isp": "ISP", "as": "AS", "asname": "AS name"}
        if key in special:
            fixed_lookup[special[key]] = str(value)
            continue

        key = re.sub(r"([a-z])([A-Z])", r"\g<1> \g<2>", key)
        key = key.capitalize()

        if not value:
            value = "None"

        fixed_lookup[key] = str(value)

    text = ""

    for key, value in fixed_lookup.items():
        text = text + f"**{key}:** `{value}`\n"

    await update.reply_text(text)
