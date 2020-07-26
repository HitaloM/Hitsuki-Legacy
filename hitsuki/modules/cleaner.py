from typing import Optional

from telegram import Chat, User
from telegram.ext import Filters, MessageHandler, run_async

from hitsuki import dispatcher, spamcheck
from hitsuki.modules.connection import connected
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.helper_funcs.alternate import send_message
from hitsuki.modules.helper_funcs.chat_status import user_admin
from hitsuki.modules.languages import tl
from hitsuki.modules.sql import cleaner_sql as sql


@run_async
def clean_blue_text_must_click(update, context):
    if sql.is_enable(update.effective_chat.id):
        update.effective_message.delete()


@run_async
@spamcheck
@user_admin
def set_blue_text_must_click(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message,
                         tl(update.effective_message, "You can do this command in groups, not PM"))
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val in ("off", "no"):
            sql.set_cleanbt(chat_id, False)
            if conn:
                text = tl(update.effective_message, "Blue text cleaner was *disabled* in *{}*.").format(chat_name)
            else:
                text = tl(update.effective_message, "Blue text cleaner was *disabled*.")
            send_message(update.effective_message, text, parse_mode="markdown")

        elif val in ("yes", "on"):
            sql.set_cleanbt(chat_id, True)
            if conn:
                text = tl(update.effective_message, "Blue text cleaner was *enabled* in *{}*.").format(chat_name)
            else:
                text = tl(update.effective_message, "Blue text cleaner was *enabled*.")
            send_message(update.effective_message, text, parse_mode="markdown")

        else:
            send_message(update.effective_message,
                         tl(update.effective_message, "Unknown argument - please use 'yes', or 'no'."))
    else:
        send_message(update.effective_message,
                     tl(update.effective_message, "Curent settings for Blue text cleaner at {}: *{}*").format(chat_name,
                                                                                                              "Enabled" if sql.is_enable(
                                                                                                                  chat_id) else "Disabled"),
                     parse_mode="markdown")


__help__ = "cleaner_help"

__mod_name__ = "Cleaner"

SET_CLEAN_BLUE_TEXT_HANDLER = DisableAbleCommandHandler("cleanbluetext", set_blue_text_must_click, pass_args=True)
CLEAN_BLUE_TEXT_HANDLER = MessageHandler(Filters.command & Filters.group, clean_blue_text_must_click)

dispatcher.add_handler(SET_CLEAN_BLUE_TEXT_HANDLER)
dispatcher.add_handler(CLEAN_BLUE_TEXT_HANDLER, 15)
