from io import BytesIO
from time import sleep
from typing import Optional
from typing import List

from telegram import TelegramError, Chat, Message
from telegram import Update, Bot
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async

import hitsuki.modules.sql.users_sql as sql
from hitsuki import dispatcher, OWNER_ID, LOGGER
from hitsuki.modules.helper_funcs.filters import CustomFilters

import hitsuki.modules.sql.feds_sql as fedsql
from hitsuki.modules import languages
from hitsuki.modules.helper_funcs.alternate import send_message

CHAT_GROUP = 5


def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

    if username.startswith('@'):
        username = username[1:]

    users = sql.get_userid_by_name(username)

    if not users:
        return None

    elif len(users) == 1:
        return users[0].user_id

    else:
        for user_obj in users:
            try:
                userdat = dispatcher.bot.get_chat(user_obj.user_id)
                if userdat.username == username:
                    return userdat.id

            except BadRequest as excp:
                if excp.message == 'Chat not found':
                    pass
                else:
                    LOGGER.exception("Error extracting user ID")

    return None


@run_async
def broadcast(bot: Bot, update: Update):
    to_send = update.effective_message.text.split(None, 1)
    if len(to_send) >= 2:
        chats = sql.get_all_chats() or []
        failed = 0
        for chat in chats:
            try:
                bot.sendMessage(int(chat.chat_id), to_send[1])
                sleep(0.1)
            except TelegramError:
                failed += 1
                LOGGER.warning("Couldn't send broadcast to %s, group name %s", str(chat.chat_id), str(chat.chat_name))

        send_message(update.effective_message, "The broadcast is complete. {} Group failed to receive the message, maybe "
                                            "the bot is kicked.".format(failed))


@run_async
def snipe(bot: Bot, update: Update, args: List[str]):
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError as excp:
        update.effective_message.reply_text("Please give me a chat to echo to!")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            bot.sendMessage(int(chat_id), str(to_send))
        except TelegramError:
            LOGGER.warning("Couldn't send to group %s", str(chat_id))
            update.effective_message.reply_text("Couldn't send the message. Perhaps I'm not part of that group?") 


@run_async
def log_user(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    """text = msg.text if msg.text else ""
                uid = msg.from_user.id
                uname = msg.from_user.name
                print("{} | {} | {} | {}".format(text, uname, uid, chat.title))"""
    fed_id = fedsql.get_fed_id(chat.id)
    if fed_id:
        user = update.effective_user
        if user:
            fban, fbanreason, fbantime = fedsql.get_fban_user(fed_id, user.id)
            if fban:
                send_message(update.effective_message, languages.tl(update.effective_message, "This user is banned in the current federation!\nReason: `{}`").format(fbanreason), parse_mode="markdown")
                try:
                     bot.kick_chat_member(chat.id, user.id)
                except:
                	 print("Fban: cannot banned this user")

    sql.update_user(msg.from_user.id,
                    msg.from_user.username,
                    chat.id,
                    chat.title)

    if msg.reply_to_message:
        sql.update_user(msg.reply_to_message.from_user.id,
                        msg.reply_to_message.from_user.username,
                        chat.id,
                        chat.title)

    if msg.forward_from:
        sql.update_user(msg.forward_from.id,
                        msg.forward_from.username)


@run_async
def chats(bot: Bot, update: Update):
    all_chats = sql.get_all_chats() or []
    chatfile = 'The chat list.\n'
    for chat in all_chats:
        chatfile += "{} - ({})\n".format(chat.chat_name, chat.chat_id)

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "chatlist.txt"
        update.effective_message.reply_document(document=output, filename="chatlist.txt",
                                                caption="Here is a list of chats in my database.")


@run_async
def chat_checker(bot: Bot, update: Update):
	if update.effective_message.chat.get_member(bot.id).can_send_messages == False:
		bot.leaveChat(update.effective_message.chat.id)
		bot.sendMessage(-1001332080671, "I am leave from {}".format(update.effective_message.chat.title))


def __user_info__(user_id, chat_id):
    if user_id == dispatcher.bot.id:
        return languages.tl(chat_id, """I've seen them in... Wow. Are they stalking me? They're in all the same places I am... oh. It's me.""")
    num_chats = sql.get_user_num_chats(user_id)
    return languages.tl(chat_id, """I've seen them in <code>{}</code> chats in total.""").format(num_chats)


def __stats__():
    return languages.tl(OWNER_ID, "{} users, across {} chats").format(sql.num_users(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = ""  # no help string

__mod_name__ = "Users"

BROADCAST_HANDLER = CommandHandler("broadcast", broadcast, filters=Filters.user(OWNER_ID))
USER_HANDLER = MessageHandler(Filters.all & Filters.group, log_user)
CHATLIST_HANDLER = CommandHandler("chatlist", chats, filters=CustomFilters.sudo_filter)
SNIPE_HANDLER = CommandHandler("snipe", snipe, pass_args=True, filters=Filters.user(OWNER_ID))
CHAT_CHECKER_HANDLER = MessageHandler(Filters.all & Filters.group, chat_checker)

dispatcher.add_handler(SNIPE_HANDLER)
dispatcher.add_handler(USER_HANDLER, CHAT_GROUP)
dispatcher.add_handler(BROADCAST_HANDLER)
dispatcher.add_handler(CHATLIST_HANDLER)
dispatcher.add_handler(CHAT_CHECKER_HANDLER, CHAT_GROUP)
