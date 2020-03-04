import html
from typing import Optional, List

from telegram import Message, Update, Bot, User
from telegram import ParseMode, MAX_MESSAGE_LENGTH
from telegram.ext.dispatcher import run_async
from telegram.ext import CommandHandler
from telegram.utils.helpers import escape_markdown

import hitsuki.modules.sql.userinfo_sql as sql
from hitsuki import dispatcher, SUDO_USERS, OWNER_ID
from hitsuki.modules.helper_funcs.extraction import extract_user
from hitsuki.modules.languages import tl as tld


@run_async
def my_bio(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
	message = update.effective_message  # type: Optional[Message]
    user_id = extract_user(message, args)

    if user_id:
        user = bot.get_chat(user_id)
    else:
        user = message.from_user

    info = sql.get_user_bio(user.id)

    if info:
        update.effective_message.reply_text("*{}*:\n{}".format(user.first_name, escape_markdown(info)),
                                            parse_mode=ParseMode.MARKDOWN)
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        update.effective_message.reply_text(username + " hasn't set an info message about themselves  yet!")
    else:
        update.effective_message.reply_text("You haven't set an info message about yourself yet!")


@run_async
def set_bio(bot: Bot, update: Update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
	message = update.effective_message  # type: Optional[Message]
    user_id = message.from_user.id
    text = message.text
    info = text.split(None, 1)  # use python's maxsplit to only remove the cmd, hence keeping newlines.
    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_bio(user_id, info[1])
            message.reply_text("Updated your info!")
        else:
            message.reply_text(
                "Your info needs to be under {} characters! You have {}.".format(MAX_MESSAGE_LENGTH // 4, len(info[1])))


def __user_info__(user_id, chat_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    if bio:
        return "<b>About user:</b>\n{bio}\n".format(bio=bio)
    else:
        return ""


__help__ = """
*With this module you can know a little more about other bot users.*

*Available commands:*
 - /setbio <text>: will set your info
 - /bio: will get your or another user's info
 
*Note:* you can delete your bio using the /gdpr command here in private
"""

__mod_name__ = "Biography"

SET_BIO_HANDLER = CommandHandler("setbio", set_bio)
GET_BIO_HANDLER = CommandHandler("bio", my_bio, pass_args=True)

dispatcher.add_handler(SET_BIO_HANDLER)
dispatcher.add_handler(GET_BIO_HANDLER)
