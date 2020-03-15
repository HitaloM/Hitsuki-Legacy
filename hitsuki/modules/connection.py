import time
import re
from typing import Optional, List

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Message, Chat, Update, Bot, User, error
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters, CallbackQueryHandler
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

import hitsuki.modules.sql.connection_sql as sql
from hitsuki import dispatcher, LOGGER, SUDO_USERS, spamfilters
from hitsuki.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_admin, can_restrict
from hitsuki.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from hitsuki.modules.helper_funcs.string_handling import extract_time

from hitsuki.modules import languages
from hitsuki.modules.helper_funcs.alternate import send_message


@user_admin
@run_async
def allow_connections(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0]
            if (var == "no" or var == "false"):
                sql.set_allow_connect_to_chat(chat.id, False)
                send_message(update.effective_message, languages.tl(update.effective_message, "Connection has been disabled for this chat"))
            elif(var == "yes" or var == "true"):
                sql.set_allow_connect_to_chat(chat.id, True)
                send_message(update.effective_message, languages.tl(update.effective_message, "Connection has been enabled for this chat"))
            else:
                send_message(update.effective_message, languages.tl(update.effective_message, "Please enter `yes / true` or `no / false`!"), parse_mode=ParseMode.MARKDOWN)
        else:
            get_settings = sql.allow_connect_to_chat(chat.id)
            if get_settings:
                send_message(update.effective_message, languages.tl(update.effective_message, "Connections to this group are *Allowed* for members!"), parse_mode=ParseMode.MARKDOWN)
            else:
                send_message(update.effective_message, languages.tl(update.effective_message, "Connection to this group are *Not Allowed* for members!"), parse_mode=ParseMode.MARKDOWN)
    else:
        send_message(update.effective_message, languages.tl(update.effective_message, "You can do this command in groups, not PM"))

@run_async
def connection_chat(bot, update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    conn = connected(bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type != "private":
            return
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if conn:
        teks = languages.tl(update.effective_message, "You are currently connected with {}.\n").format(chat_name)
    else:
        teks = languages.tl(update.effective_message, "You are currently not connected in any group.\n")
    teks += languages.tl(update.effective_message, "supportcmd")
    send_message(update.effective_message, teks, parse_mode="markdown")

@run_async
def connect_chat(bot, update, args):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return

    if update.effective_chat.type == 'private':
        if len(args) >= 1:
            try:
                connect_chat = int(args[0])
                getstatusadmin = bot.get_chat_member(connect_chat, update.effective_message.from_user.id)
            except ValueError:
                try:
                    connect_chat = str(args[0])
                    get_chat = bot.getChat(connect_chat)
                    connect_chat = get_chat.id
                    getstatusadmin = bot.get_chat_member(connect_chat, update.effective_message.from_user.id)
                except error.BadRequest:
                    send_message(update.effective_message, languages.tl(update.effective_message, "Invalid Chat ID!"))
                    return
            except error.BadRequest:
                send_message(update.effective_message, languages.tl(update.effective_message, "Invalid Chat ID!"))
                return
            isadmin = getstatusadmin.status in ('administrator', 'creator')
            ismember = getstatusadmin.status in ('member')
            isallow = sql.allow_connect_to_chat(connect_chat)
            if (isadmin) or (isallow and ismember) or (user.id in SUDO_USERS):
                connection_status = sql.connect(update.effective_message.from_user.id, connect_chat)
                if connection_status:
                    conn_chat = dispatcher.bot.getChat(connected(bot, update, chat, user.id, need_admin=False))
                    chat_name = conn_chat.title
                    send_message(update.effective_message, languages.tl(update.effective_message, "Successfully connected to *{}*. Use /connection for see current available commands.").format(chat_name), parse_mode=ParseMode.MARKDOWN)
                    sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
                    # send_message(update.effective_message, languages.tl(update.effective_message, "supportcmd"), parse_mode="markdown")
                else:
                    send_message(update.effective_message, languages.tl(update.effective_message, "Connection failed!"))
            else:
                send_message(update.effective_message, languages.tl(update.effective_message, "Connection to this chat is not allowed!"))
        else:
            gethistory = sql.get_history_conn(user.id)
            if gethistory:
                buttons = [InlineKeyboardButton(text=languages.tl(update.effective_message, "❎ Close button"), callback_data="connect_close"), InlineKeyboardButton(text=languages.tl(update.effective_message, "🧹 Hapus riwayat"), callback_data="connect_clear")]
            else:
                buttons = []
            conn = connected(bot, update, chat, user.id, need_admin=False)
            if conn:
                connectedchat = dispatcher.bot.getChat(conn)
                text = languages.tl(update.effective_message, "You are connected to *{}* (`{}`)").format(connectedchat.title, conn)
                buttons.append(InlineKeyboardButton(text=languages.tl(update.effective_message, "🔌 Putuskan sambungan"), callback_data="connect_disconnect"))
            else:
                text = languages.tl(update.effective_message, "Write the chat ID or tag to connect!")
            if gethistory:
                text += languages.tl(update.effective_message, "\n\n*Connection history:*\n")
                text += languages.tl(update.effective_message, "╒═══「 *Info* 」\n")
                text += languages.tl(update.effective_message, "│  Sorted: `Newest`\n")
                text += "│\n"
                buttons = [buttons]
                for x in sorted(gethistory.keys(), reverse=True):
                    htime = time.strftime("%d/%m/%Y", time.localtime(x))
                    text += "╞═「 *{}* 」\n│   `{}`\n│   `{}`\n".format(gethistory[x]['chat_name'], gethistory[x]['chat_id'], htime)
                    text += "│\n"
                    buttons.append([InlineKeyboardButton(text=gethistory[x]['chat_name'], callback_data="connect({})".format(gethistory[x]['chat_id']))])
                text += "╘══「 Total {} Chats 」".format(str(len(gethistory)) + " (max)" if len(gethistory) == 5 else str(len(gethistory)))
                conn_hist = InlineKeyboardMarkup(buttons)
            elif buttons:
                conn_hist = InlineKeyboardMarkup([buttons])
            else:
                conn_hist = None
            send_message(update.effective_message, text, parse_mode="markdown", reply_markup=conn_hist)

    else:
        getstatusadmin = bot.get_chat_member(chat.id, update.effective_message.from_user.id)
        isadmin = getstatusadmin.status in ('administrator', 'creator')
        ismember = getstatusadmin.status in ('member')
        isallow = sql.allow_connect_to_chat(chat.id)
        if (isadmin) or (isallow and ismember) or (user.id in SUDO_USERS):
            connection_status = sql.connect(update.effective_message.from_user.id, chat.id)
            if connection_status:
                chat_name = dispatcher.bot.getChat(chat.id).title
                send_message(update.effective_message, languages.tl(update.effective_message, "Successfully connected to *{}*. Use /connection for see current available commands.").format(chat_name), parse_mode=ParseMode.MARKDOWN)
                try:
                    sql.add_history_conn(user.id, str(chat.id), chat_name)
                    bot.send_message(update.effective_message.from_user.id, languages.tl(update.effective_message, "You have connected with *{}*. Use /connection for see current available commands.").format(chat_name), parse_mode="markdown")
                except BadRequest:
                    pass
                except error.Unauthorized:
                    pass
            else:
                send_message(update.effective_message, languages.tl(update.effective_message, "Connection failed!"))
        else:
            send_message(update.effective_message, languages.tl(update.effective_message, "Connection to this chat is not allowed!"))


def disconnect_chat(bot, update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return

    if update.effective_chat.type == 'private':
        disconnection_status = sql.disconnect(update.effective_message.from_user.id)
        if disconnection_status:
           sql.disconnected_chat = send_message(update.effective_message, languages.tl(update.effective_message, "Disconnected from chat!"))
        else:
           send_message(update.effective_message, languages.tl(update.effective_message, "You're not connected!"))
    else:
        send_message(update.effective_message, languages.tl(update.effective_message, "This command only available in PM"))


def connected(bot, update, chat, user_id, need_admin=True):
    user = update.effective_user  # type: Optional[User]
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
        
    if chat.type == chat.PRIVATE and sql.get_connected_chat(user_id):
        conn_id = sql.get_connected_chat(user_id).chat_id
        getstatusadmin = bot.get_chat_member(conn_id, update.effective_message.from_user.id)
        isadmin = getstatusadmin.status in ('administrator', 'creator')
        ismember = getstatusadmin.status in ('member')
        isallow = sql.allow_connect_to_chat(conn_id)
        if (isadmin) or (isallow and ismember) or (user.id in SUDO_USERS):
            if need_admin == True:
                if getstatusadmin.status in ('administrator', 'creator') or user_id in SUDO_USERS:
                    return conn_id
                else:
                    send_message(update.effective_message, languages.tl(update.effective_message, "You must be an admin in the connected group!"))
                    raise Exception("Bukan admin!")
            else:
                return conn_id
        else:
            send_message(update.effective_message, languages.tl(update.effective_message, "The group changes the connection rights or you are no longer an admin.\nI've disconnect you."))
            disconnect_chat(bot, update)
            raise Exception("I'm not admin!")
    else:
        return False

@run_async
def help_connect_chat(bot, update, args):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    if update.effective_message.chat.type != "private":
        send_message(update.effective_message, languages.tl(update.effective_message, "PM me with that command to get help"))
        return
    else:
        send_message(update.effective_message, languages.tl(update.effective_message, "supportcmd"), parse_mode="markdown")

@run_async
def connect_button(bot: Bot, update: Update) -> str:
    query = update.callback_query
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    connect_match = re.match(r"connect\((.+?)\)", query.data)
    disconnect_match = query.data == "connect_disconnect"
    clear_match = query.data == "connect_clear"
    connect_close = query.data == "connect_close"

    if connect_match:
        target_chat = connect_match.group(1)
        getstatusadmin = bot.get_chat_member(target_chat, query.from_user.id)
        isadmin = getstatusadmin.status in ('administrator', 'creator')
        ismember = getstatusadmin.status in ('member')
        isallow = sql.allow_connect_to_chat(target_chat)
        if (isadmin) or (isallow and ismember) or (user.id in SUDO_USERS):
            connection_status = sql.connect(query.from_user.id, target_chat)
            if connection_status:
                conn_chat = dispatcher.bot.getChat(connected(bot, update, chat, user.id, need_admin=False))
                chat_name = conn_chat.title
                query.message.edit_text(languages.tl(update.effective_message, "Successfully connected to *{}*. Use /connection for see current available commands.").format(chat_name), parse_mode=ParseMode.MARKDOWN)
                sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
            else:
                query.message.edit_text(languages.tl(update.effective_message, "Connection failed!"))
        else:
            bot.answer_callback_query(query.id, languages.tl(update.effective_message, "Connection to this chat is not allowed!"), show_alert=True)
    elif disconnect_match:
        disconnection_status = sql.disconnect(query.from_user.id)
        if disconnection_status:
           sql.disconnected_chat = query.message.edit_text(languages.tl(update.effective_message, "Disconnected from chat!"))
        else:
           bot.answer_callback_query(query.id, languages.tl(update.effective_message, "You're not connected!"), show_alert=True)
    elif clear_match:
        sql.clear_history_conn(query.from_user.id)
        query.message.edit_text(languages.tl(update.effective_message, "Connections historic has been cleared!"))
    elif connect_close:
        query.message.edit_text(languages.tl(update.effective_message, "Closed.\nTo open again, type /connect"))
    else:
        connect_chat(bot, update, [])


__help__ = "connection_help"

__mod_name__ = "Connection"

CONNECT_CHAT_HANDLER = CommandHandler("connect", connect_chat, allow_edited=True, pass_args=True)
CONNECTION_CHAT_HANDLER = CommandHandler("connection", connection_chat)
DISCONNECT_CHAT_HANDLER = CommandHandler("disconnect", disconnect_chat, allow_edited=True)
ALLOW_CONNECTIONS_HANDLER = CommandHandler("allowconnect", allow_connections, allow_edited=True, pass_args=True)
HELP_CONNECT_CHAT_HANDLER = CommandHandler("helpconnect", help_connect_chat, allow_edited=True, pass_args=True)
CONNECT_BTN_HANDLER = CallbackQueryHandler(connect_button, pattern=r"connect")

dispatcher.add_handler(CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECTION_CHAT_HANDLER)
dispatcher.add_handler(DISCONNECT_CHAT_HANDLER)
dispatcher.add_handler(ALLOW_CONNECTIONS_HANDLER)
dispatcher.add_handler(HELP_CONNECT_CHAT_HANDLER)
dispatcher.add_handler(CONNECT_BTN_HANDLER)
