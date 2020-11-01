# Copyright (C) 2018-2020 Amano Team <contact@amanoteam.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import sys
import html
import regex
import aiohttp
import asyncio
import speedtest

from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import Message

from hitsuki import TOKEN, SUDO_USERS, MESSAGE_DUMP, pbot


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
            await pbot.send_message(MESSAGE_DUMP,
                              "**Hitsuki has been successfully updated!**")
            args = [sys.executable, "-m", "hitsuki"]
            os.execl(sys.executable, *args)
    else:
        await sm.edit_text(f"Upgrade failed (process exited with {proc.returncode}):\n{stdout.decode()}")
        proc = await asyncio.create_subprocess_shell("git merge --abort")
        await proc.communicate()


@pbot.on_message(filters.command("speedtest") & filters.user(SUDO_USERS))
async def test_speed(c: Client, m: Message):
    string = (
        "**Speedtest:**\n\n**🌐 Host:** `{host}`\n\n**🏓 Ping:** `{ping} ms`\n**⬇️ Download:** `{download} Mbps`\n**⬆️ Upload:** `{upload} Mbps`")
    sent = await m.reply_text(string.format(host="", ping="", download="", upload=""))
    s = speedtest.Speedtest()
    bs = s.get_best_server()
    await sent.edit_text(string.format(host=bs["sponsor"], ping=int(bs["latency"]), download="", upload=""))
    dl = round(s.download() / 1024 / 1024, 2)
    await sent.edit_text(string.format(host=bs["sponsor"], ping=int(bs["latency"]), download=dl, upload=""))
    ul = round(s.upload() / 1024 / 1024, 2)
    await sent.edit_text(string.format(host=bs["sponsor"], ping=int(bs["latency"]), download=dl, upload=ul))


@pbot.on_message(filters.command("restart") & filters.user(SUDO_USERS))
async def restart(c: Client, m: Message):
    await m.reply_text("Restarting...")
    await pbot.send_message(MESSAGE_DUMP, "**Hitsuki is restarting...**")
    args = [sys.executable, "-m", "hitsuki"]
    os.execl(sys.executable, *args)
