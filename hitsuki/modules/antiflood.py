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

import html
import re
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, MessageHandler, CallbackQueryHandler, run_async
from telegram.utils.helpers import mention_html, escape_markdown

from hitsuki import SUDO_USERS, WHITELIST_USERS, dispatcher
from hitsuki.modules.helper_funcs.chat_status import (
    bot_admin, can_restrict, is_user_admin, user_admin,
    user_admin_no_reply)
from hitsuki.modules.log_channel import loggable
from hitsuki.modules.sql import antiflood_sql as sql
from hitsuki import dispatcher
from hitsuki.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict
from hitsuki.modules.helper_funcs.string_handling import extract_time
from hitsuki.modules.log_channel import loggable
from hitsuki.modules.sql import antiflood_sql as sql
from hitsuki.modules.helper_funcs.alternate import send_message
from hitsuki.modules.tr_engine.strings import tld

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(bot: Bot, update: Update) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    if not user:  # ignore channels
        return ""

    if user.id == 777000:
        return ""

    # ignore admins
    if (is_user_admin(chat, user.id) or user.id in WHITELIST_USERS or user.id in SUDO_USERS):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            chat.kick_member(user.id)
            execstrings = ("Banned")
            tag = "BANNED"
        elif getmode == 2:
            chat.kick_member(user.id)
            chat.unban_member(user.id)
            execstrings = ("Kicked")
            tag = "KICKED"
        elif getmode == 3:
            bot.restrict_chat_member(chat.id, user.id, can_send_messages=False)
            execstrings = ("Muted")
            tag = "MUTED"
        elif getmode == 4:
            bantime = extract_time(msg, getvalue)
            chat.kick_member(user.id, until_date=bantime)
            execstrings = ("Banned for {}".format(getvalue))
            tag = "TBAN"
        elif getmode == 5:
            mutetime = extract_time(msg, getvalue)
            bot.restrict_chat_member(
                chat.id, user.id, until_date=mutetime, can_send_messages=False
            )
            execstrings = ("Muted for {}".format(getvalue))
            tag = "TMUTE"
        send_message(update.effective_message, "Wonderful, I like to leave flooding to natural disasters but you, "
                       "you were just a disappointment {}!".format(execstrings))

        return "<b>{}:</b>" \
               "\n#{}" \
               "\n<b>User:</b> {}" \
               "\nFlooded the group.".format(html.escape(chat.title), tag,
                                             mention_html(user.id, user.first_name))

    except BadRequest:
        msg.reply_text("I can't restrict people here, give me permissions first! Until then, I'll disable anti-flood.")
        sql.set_flood(chat.id, 0)
        return "<b>{}:</b>\n" \
               "\n#INFO" \
               "\nDon't have enough permission to restrict users so automatically disabled anti-flood".format(html.escape(chat.title))


@run_async
@user_admin
@can_restrict
@loggable
def set_flood(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""

    chat_id = update.effective_chat.id
    chat_name = update.effective_message.chat.title
    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat_id, 0)
            text = message.reply_text("Antiflood has been disabled.")


        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat_id, 0)
                text = message.reply_text("Antiflood has been disabled.")
                return "<b>{}:</b>\n" \
                       "#SETFLOOD" \
                       "\n<b>Admin:</b> {}" \
                       "\nDisable antiflood.".format(html.escape(chat.title), mention_html(user.id, user.first_name))

            elif amount <= 3:
                send_message(update.effective_message, "Antiflood must be either 0 (disabled) or number greater than 3!")
                return ""

            else:
                sql.set_flood(chat_id, amount)
                text = message.reply_text("Successfully updated anti-flood limit to {}!".format(amount))

                return "<b>{}:</b>\n" \
                       "#SETFLOOD" \
                       "\n<b>Admin:</b> {}" \
                       "\nSet antiflood to <code>{}</code>.".format(html.escape(chat.title), mention_html(user.id, user.first_name), amount)

        else:
            message.reply_text("Invalid argument please use a number, 'off' or 'no'")
    else:
        message.reply_text(("Use `/setflood number` to enable anti-flood.\nOr use `/setflood off` to disable antiflood!."), parse_mode="markdown")
    return ""


@run_async
def flood(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message

    chat_id = update.effective_chat.id
    chat_name = update.effective_message.chat.title
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        text = msg.reply_text("I'm not enforcing any flood control here!")

    else:
        text = msg.reply_text("I'm currently restricting members after {} consecutive messages.".format(limit))


@run_async
@user_admin
@loggable
def set_flood_mode(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    cat = update.effective_chat
    chat_id = update.effective_chat.id
    chat_name = update.effective_message.chat.title
    if args:
        if args[0].lower() == 'ban':
            settypeflood = ('ban')
            sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == 'kick':
            settypeflood = ('kick')
            sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == 'mute':
            settypeflood = ('mute')
            sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == 'tban':
            if len(args) == 1:
                msg.reply_text ("""It looks like you tried to set time value for antiflood but you didn't specified time; Try, `/setfloodmode tban <timevalue>`.

Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks.""", parse_mode="markdown")
                return
            settypeflood = ("tban for {}".format(args[1]))
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == 'tmute':
            if len(args) == 1:
                msg.reply_text ("""It looks like you tried to set time value for antiflood but you didn't specified time; Try, `/setfloodmode tmute <timevalue>`.

Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks.""", parse_mode="markdown")
                return
            settypeflood = ("tmute for {}".format(args[1]))
            sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            send_message(update.effective_message, "I only understand ban/kick/mute/tban/tmute!")
            return
        text = msg.reply_text("Exceeding consecutive flood limit will result in {}!".format(settypeflood))

        return "<b>{}:</b>\n" \
               "#SETFLOO_MODE\n" \
               "<b>Admin:</b> {}\n" \
               "Has changed antiflood mode. User will {}.".format(html.escape(chat.title), mention_html(user.id, user.first_name), settypeflood)
    else:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            settypeflood = ('ban')
        elif getmode == 2:
            settypeflood = ('kick')
        elif getmode == 3:
            settypeflood = ('mute')
        elif getmode == 4:
            settypeflood = ('tban for {}'.format(getvalue))
        elif getmode == 5:
            settypeflood = ('tmute for {}'.format(getvalue))
        text = msg.reply_text("Sending more message than flood limit will result in {}.".format(settypeflood))

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = True

FLOOD_BAN_HANDLER = MessageHandler(
    Filters.all & ~Filters.status_update & Filters.group, check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood",
                                   set_flood,
                                   pass_args=True,
                                   filters=Filters.group)
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.group)
SET_FLOOD_MODE_HANDLER = CommandHandler("setfloodmode",
                                        set_flood_mode,
                                        pass_args=True,
                                        filters=Filters.group)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(SET_FLOOD_MODE_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
