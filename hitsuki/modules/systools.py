import subprocess
import os
import requests
import speedtest

import hitsuki.modules.helper_funcs.git_api as git

from platform import python_version
from telegram import Update, Bot, Message, Chat, ParseMode
from telegram.ext import CommandHandler, run_async, Filters

from hitsuki import dispatcher, OWNER_ID, SUDO_USERS
from hitsuki.modules.helper_funcs.filters import CustomFilters
from hitsuki.modules.helper_funcs.extraction import extract_text
from hitsuki.modules.disable import DisableAbleCommandHandler


@run_async
def status(bot: Bot, update: Update):
    reply = "<b>System Status:</b> <code>operational</code>\n\n"
    reply += "<b>Hitsuki version:</b> <code>1.0 - X Edition</code>\n"
    reply += "<b>Python version:</b> <code>"+python_version()+"</code>\n"
    reply += "<b>GitHub API version:</b> <code>"+str(git.vercheck())+"</code>\n\n"
    update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


def speed_convert(size):
    """
    Hi human, you can't read bytes?
    """
    power = 2 ** 10
    zero = 0
    units = {0: '', 1: 'Kb/s', 2: 'Mb/s', 3: 'Gb/s', 4: 'Tb/s'}
    while size > power:
        size /= power
        zero += 1
    return f"{round(size, 2)} {units[zero]}"


@run_async
def speedtst(bot: Bot, update: Update):
    chat = update.effective_chat
    del_msg = bot.send_message(chat.id, "<code>🔄 Running speedtest...</code>",
                               parse_mode=ParseMode.HTML)
    test = speedtest.Speedtest()
    test.get_best_server()
    test.download()
    test.upload()
    test.results.share()
    result = test.results.dict()
    del_msg.delete()
    update.effective_message.reply_text("<b>SpeedTest Results</b> \n\n"
                                        "<b>Download:</b> "
                                        f"<code>{speed_convert(result['download'])}</code> \n"
                                        "<b>Upload:</b> "
                                        f"<code>{speed_convert(result['upload'])}</code> \n"
                                        "<b>Ping:</b> "
                                        f"<code>{result['ping']}</code> \n"
                                        "<b>ISP:</b> "
                                        f"<code>{result['client']['isp']}</code>",
                                        parse_mode=ParseMode.HTML)


STATUS_HANDLER = CommandHandler("status", status)
SPEED_HANDLER = CommandHandler("speedtest", speedtst, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(STATUS_HANDLER)
dispatcher.add_handler(SPEED_HANDLER)
