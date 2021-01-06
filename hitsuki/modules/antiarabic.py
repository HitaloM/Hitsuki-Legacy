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

from typing import List

from hitsuki import dispatcher
from hitsuki.modules.helper_funcs.chat_status import (can_delete, user_admin,
                                                      user_not_admin)
from hitsuki.modules.helper_funcs.extraction import extract_text
from hitsuki.modules.sql import antiarabic_sql as sql
from hitsuki.modules.tr_engine.strings import tld
from telegram import Bot, ParseMode, Update
from telegram.ext import CommandHandler, Filters, MessageHandler
from telegram.ext.dispatcher import run_async

ANTIARABIC_GROUPS = 12


@run_async
@user_admin
def antiarabic_setting(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            if args[0].lower() in ("yes", "on", "true"):
                sql.set_chat_setting(chat.id, True)
                msg.reply_text(tld(chat.id, "antiarabic_enabled"))

            elif args[0].lower() in ("no", "off", "false"):
                sql.set_chat_setting(chat.id, False)
                msg.reply_text(tld(chat.id, "antiarabic_disabled"))
        else:
            msg.reply_text(tld(chat.id, "antiarabic_setting").format(
                sql.chat_antiarabic(chat.id)),
                parse_mode=ParseMode.MARKDOWN)


@user_not_admin
@run_async
def antiarabic(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    to_match = extract_text(msg)
    user = update.effective_user

    if not sql.chat_antiarabic(chat.id):
        return ""

    if not user:  # ignore channels
        return ""

    if user.id == 777000:  # ignore telegram
        return ""

    if not to_match:
        return

    if chat.type != chat.PRIVATE:
        for c in to_match:
            if ('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F'
                    or '\u08A0' <= c <= '\u08FF' or '\uFB50' <= c <= '\uFDFF'
                    or '\uFE70' <= c <= '\uFEFF'
                    or '\U00010E60' <= c <= '\U00010E7F'
                    or '\U0001EE00' <= c <= '\U0001EEFF'):
                if can_delete(chat, bot.id):
                    update.effective_message.delete()
                    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = True

SETTING_HANDLER = CommandHandler("antiarabic", antiarabic_setting,
                                 pass_args=True)
ANTI_ARABIC = MessageHandler(
    (Filters.text | Filters.command | Filters.sticker | Filters.photo) & Filters.group, antiarabic)

dispatcher.add_handler(SETTING_HANDLER)
dispatcher.add_handler(ANTI_ARABIC, group=ANTIARABIC_GROUPS)
