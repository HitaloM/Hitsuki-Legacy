import html
import hitsuki.modules.helper_funcs.cas_api as cas
import hitsuki.modules.sql.welcome_sql as sql

from typing import Optional, List

from telegram import User, Chat, ChatMember, Update, Bot, Message, ParseMode
from telegram.ext import CommandHandler, run_async, Filters, MessageHandler

from hitsuki import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS
from hitsuki.modules.helper_funcs.chat_status import user_admin
from hitsuki.modules.helper_funcs.extraction import extract_user
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.helper_funcs.filters import CustomFilters
from hitsuki.modules.helper_funcs.misc import send_to_list


@run_async
@user_admin
def setcas(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    split_msg = msg.text.split(' ')
    if len(split_msg) != 2:
        msg.reply_text("Invalid arguments!")
        return
    param = split_msg[1]
    if param == "on" or param == "true":
        sql.set_cas_status(chat.id, True)
        msg.reply_text("Successfully updated configuration.")
        return
    elif param == "off" or param == "false":
        sql.set_cas_status(chat.id, False)
        msg.reply_text("Successfully updated configuration.")
        return
    else:
        msg.reply_text("Invalid status to set!")  # on or off ffs
        return


@run_async
@user_admin
def setban(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    split_msg = msg.text.split(' ')
    if len(split_msg) != 2:
        msg.reply_text("Invalid arguments!")
        return
    param = split_msg[1]
    if param == "on" or param == "true":
        sql.set_cas_autoban(chat.id, True)
        msg.reply_text("Successfully updated configuration.")
        return
    elif param == "off" or param == "false":
        sql.set_cas_autoban(chat.id, False)
        msg.reply_text("Successfully updated configuration.")
        return
    else:
        msg.reply_text("Invalid autoban definition to set!")  # on or off ffs
        return


@run_async
@user_admin
def get_current_setting(bot: Bot, update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    stats = sql.get_cas_status(chat.id)
    autoban = sql.get_cas_autoban(chat.id)
    rtext = "<b>CAS Preferences</b>\n\nCAS Checking: {}\nAutoban: {}".format(
        stats, autoban)
    msg.reply_text(rtext, parse_mode=ParseMode.HTML)
    return


@run_async
def get_version(bot: Bot, update: Update):
    msg = update.effective_message
    ver = cas.vercheck()
    msg.reply_text("CAS API version: " + ver)
    return


@run_async
def caschecker(bot: Bot, update: Update, args: List[str]):
    # /info logic
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)
    if user_id and int(user_id) != 777000:
        user = bot.get_chat(user_id)
    elif user_id and int(user_id) == 777000:
        msg.reply_text(
            "This is Telegram. Unless you manually entered this reserved account's ID, it is likely a broadcast from a linked channel.")
        return
    elif not msg.reply_to_message and not args:
        user = msg.from_user
    elif not msg.reply_to_message and (not args or (
            len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
                [MessageEntity.TEXT_MENTION]))):
        msg.reply_text("I can't extract a user from this.")
        return
    else:
        return

    text = "<b>CAS Check</b>:" \
           "\nID: <code>{}</code>" \
           "\nFirst Name: {}".format(user.id, html.escape(user.first_name))
    if user.last_name:
        text += "\nLast Name: {}".format(html.escape(user.last_name))
    if user.username:
        text += "\nUsername: @{}".format(html.escape(user.username))
    text += "\n\nCAS Banned: "
    result = cas.banchecker(user.id)
    text += str(result)
    if result:
        text += "\nTotal of Offenses: "
        parsing = cas.offenses(user.id)
        text += str(parsing)
    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

# this sends direct request to combot server. Will return true if user is banned, false if
# id invalid or user not banned
@run_async
def casquery(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    try:
        user_id = msg.text.split(' ')[1]
    except BaseException:
        msg.reply_text("There was a problem parsing the query")
        return
    text = "Your query returned: "
    result = cas.banchecker(user_id)
    text += str(result)
    msg.reply_text(text)


@run_async
def watcher(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    casPrefs = sql.get_status(str(chat.id))  # check if enabled, obviously
    if casPrefs and not autoban and cas.banchecker(user.id):
        bot.restrict_chat_member(chat.id, user.id,
                                 can_send_messages=False,
                                 can_send_media_messages=False,
                                 can_send_other_messages=False,
                                 can_add_web_page_previews=False)
        msg.reply_text(
            "Warning! This user is CAS Banned. I have muted them to avoid spam. Ban is advised.")
        isUserGbanned = gbansql.is_user_gbanned(user.id)
        if not isUserGbanned:
            report = "CAS Banned user detected: <code>{}</code>".format(
                user.id)
            send_to_list(bot, SUDO_USERS + SUPPORT_USERS, report, html=True)
    elif casPrefs and autoban and cas.banchecker(user.id):
        chat.kick_member(user.id)
        msg.reply_text(
            "CAS banned user detected! User has been automatically banned!")
        isUserGbanned = gbansql.is_user_gbanned(user.id)
        if not isUserGbanned:
            report = "CAS Banned user detected: <code>{}</code>".format(
                user.id)
            send_to_list(bot, SUDO_USERS + SUPPORT_USERS, report, html=True)


__mod_name__ = "CAS Interface"

__help__ = """
The CAS Interface module is designed to work with a ported CAS API. CAS means Combot Anti-Spam System, and is a huge known list that contains spammers, scammers and more people that come to break peace.
This module will warn you of potential spammers that join your group, but you can check for them if they are already in group.

Commands:
 - /casver: Returns the API version that the bot is currently running
 - /cascheck: Checks you or another user for CAS BAN

 *Admin only:*
 - /setcas <on/off/true/false>: Enables/disables CAS Checking on welcome
 - /getcas: Gets the current CAS setting
 """

SETCAS_HANDLER = CommandHandler("setcas", setcas, filters=Filters.group)
GETCAS_HANDLER = CommandHandler(
    "getcas",
    get_current_setting,
    filters=Filters.group)
GETVER_HANDLER = DisableAbleCommandHandler("casver", get_version)
CASCHECK_HANDLER = CommandHandler("cascheck", caschecker, pass_args=True)
CASQUERY_HANDLER = CommandHandler(
    "casquery",
    casquery,
    pass_args=True,
    filters=CustomFilters.sudo_filter)
WATCHER_HANDLER = MessageHandler(
    Filters.status_update.new_chat_members, watcher)

dispatcher.add_handler(SETCAS_HANDLER)
dispatcher.add_handler(GETCAS_HANDLER)
dispatcher.add_handler(GETVER_HANDLER)
dispatcher.add_handler(CASCHECK_HANDLER)
dispatcher.add_handler(CASQUERY_HANDLER)
dispatcher.add_handler(WATCHER_HANDLER)
