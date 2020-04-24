from io import BytesIO
from time import sleep
from typing import Optional

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

USERS_GROUP = 4


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
def broadcast(update, context):
    to_send = update.effective_message.text.split(None, 1)
    if len(to_send) >= 2:
        chats = sql.get_all_chats() or []
        failed = 0
        for chat in chats:
            try:
                context.bot.sendMessage(int(chat.chat_id), to_send[1])
                sleep(0.1)
            except TelegramError:
                failed += 1
                LOGGER.warning("Couldn't send broadcast to %s, group name %s", str(chat.chat_id), str(chat.chat_name))

        send_message(update.effective_message, "The broadcast is complete. `{}` groups failed to receive the message, maybe "
                                            "I'm kicked or muted.".format(failed))


@run_async
def log_user(update, context):
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
                send_message(update.effective_message, languages.tl(update.effective_message, "Pengguna ini dilarang di federasi saat ini!\nAlasan: `{}`").format(fbanreason), parse_mode="markdown")
                try:
                    context.bot.kick_chat_member(chat.id, user.id)
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
def chats(update, context):
    all_chats = sql.get_all_chats() or []
    chatfile = 'List of chats.\n0. Chat name | Chat ID | Members count | Invitelink\n'
    P = 1
    for chat in all_chats:
        try:
            curr_chat = context.bot.getChat(chat.chat_id)
            bot_member = curr_chat.get_member(context.bot.id)
            chat_members = curr_chat.get_members_count(context.bot.id)
            if bot_member.can_invite_users:
                invitelink = context.bot.exportChatInviteLink(chat.chat_id)
            else:
                invitelink = "0"
            chatfile += "{}. {} | {} | {} | {}\n".format(
                P, chat.chat_name, chat.chat_id, chat_members, invitelink)
            P = P + 1
        except:
            pass

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "chatlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="chatlist.txt",
            caption="Here is the list of chats in my database.")


def __user_info__(user_id, chat_id):
    if user_id == dispatcher.bot.id:
        return languages.tl(chat_id, """I have seen it... Wow. Are they following me? They're in all the same places with me... oh. This is me.""")
    num_chats = sql.get_user_num_chats(user_id)
    return languages.tl(chat_id, """I've seen them in <code>{}</code> chats in total.""").format(num_chats)


def __stats__():
    return languages.tl(OWNER_ID, "`{}` users, on `{}` chats").format(sql.num_users(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__help__ = ""  # no help string

__mod_name__ = "Users"

BROADCAST_HANDLER = CommandHandler("broadcast", broadcast, filters=Filters.user(OWNER_ID))
USER_HANDLER = MessageHandler(Filters.all & Filters.group, log_user)
CHATLIST_HANDLER = CommandHandler("chatlist", chats, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(USER_HANDLER, USERS_GROUP)
dispatcher.add_handler(BROADCAST_HANDLER)
dispatcher.add_handler(CHATLIST_HANDLER)
