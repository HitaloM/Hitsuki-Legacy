# Adapted from https://github.com/AnimeKaizoku/SaitamaRobot
import html
import time
from datetime import datetime
from io import BytesIO
from typing import List

from telegram import Bot, Update, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import CommandHandler, MessageHandler, Filters, run_async
from telegram.utils.helpers import mention_html

import hitsuki.modules.sql.global_bans_sql as sql
from hitsuki import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, STRICT_GBAN, MESSAGE_DUMP
from hitsuki.modules.helper_funcs.chat_status import user_admin, is_user_admin
from hitsuki.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from hitsuki.modules.helper_funcs.misc import send_to_list
from hitsuki.modules.sql.users_sql import get_all_chats
from hitsuki.modules.languages import tl

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
}


@run_async
def gban(update, context):
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    user_id, reason = extract_user_and_text(message, args)
    if user_id == "error":
        send_message(update.effective_message, tl(update.effective_message, reason))
        return ""

    if not user_id:
        send_message(update.effective_message, tl(update.effective_message, "You don't seem to be referring to a user."))
        return

    if int(user_id) in SUDO_USERS:
        send_message(update.effective_message, tl(update.effective_message, "I spy, with my little eye... a sudo user war! Why are you guys turning on each other? 😱"))
        return

    if int(user_id) in SUPPORT_USERS:
        send_message(update.effective_message, tl(update.effective_message, "OOOH someone's trying to gban a support User! 😄 *grabs popcorn*"))
        return

    if user_id == context.bot.id:
        send_message(update.effective_message, tl(update.effective_message, "😑 So funny, lets gban myself why don't I? Nice try. 😒"))
        return

    try:
        user_chat = context.bot.get_chat(user_id)
    except BadRequest as excp:
        send_message(update.effective_message, excp.message)
        return

    if user_chat.type != 'private':
        send_message(update.effective_message, tl(update.effective_message, "That's not a user!"))
        return

    if sql.is_user_gbanned(user_id):

        if not reason:
            message.reply_text("This user is already gbanned; I'd change the reason, but you haven't given me one...")
            return

        old_reason = sql.update_gban_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            message.reply_text("This user is already gbanned, for the following reason:\n"
                               "<code>{}</code>\n"
                               "I've gone and updated it with your new reason!".format(html.escape(old_reason)),
                               parse_mode=ParseMode.HTML)

        else:
            message.reply_text("This user is already gbanned, but had no reason set; I've gone and updated it!")

        return

    message.reply_text("On it!")

    start_time = time.time()
    datetime_fmt = "%H:%M - %d-%m-%Y"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != 'private':
        chat_origin = "<b>{} ({})</b>\n".format(html.escape(chat.title), chat.id)
    else:
        chat_origin = "<b>{}</b>\n".format(chat.id)

    log_message = (f"#GBANNED\n"
                   f"<b>Originated from:</b> {chat_origin}\n"
                   f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                   f"<b>Banned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
                   f"<b>Banned User ID:</b> {user_chat.id}\n"
                   f"<b>Event Stamp:</b> {current_time}")

    if reason:
        if chat.type == chat.SUPERGROUP and chat.username:
            log_message += f"\n<b>Reason:</b> <a href=\"http://telegram.me/{chat.username}/{message.message_id}\">{reason}</a>"
        else:
            log_message += f"\n<b>Reason:</b> {reason}"

    if MESSAGE_DUMP:
        try:
            log = context.bot.send_message(MESSAGE_DUMP, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = context.bot.send_message(MESSAGE_DUMP,
                                   log_message + "\n\nFormatting has been disabled due to an unexpected error.")

    else:
        send_to_list(context.bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    gbanned_chats = 0

    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            context.bot.kick_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Could not gban due to: {excp.message}")
                if MESSAGE_DUMP:
                    context.bot.send_message(MESSAGE_DUMP, f"Could not gban due to {excp.message}",
                                     parse_mode=ParseMode.HTML)
                else:
                    send_to_list(context.bot, SUDO_USERS + SUPPORT_USERS, f"Could not gban due to: {excp.message}")
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if MESSAGE_DUMP:
        log.edit_text(log_message + f"\n<b>Chats affected:</b> {gbanned_chats}", parse_mode=ParseMode.HTML)
    else:
        send_to_list(context.bot, SUDO_USERS + SUPPORT_USERS, f"Gban complete! (User banned in {gbanned_chats} chats)")

    end_time = time.time()
    gban_time = round((end_time - start_time), 2)

    if gban_time > 60:
        gban_time = round((gban_time / 60), 2)
        message.reply_text(f"Done! This gban affected {gbanned_chats} chats, Took {gban_time} min")
    else:
        message.reply_text(f"Done! This gban affected {gbanned_chats} chats, Took {gban_time} sec")

    try:
        context.bot.send_message(user_id,
                         "You have been globally banned from all groups where I have administrative permissions.",
                         parse_mode=ParseMode.HTML)
    except:
        pass  # bot probably blocked by user


@run_async
def ungban(update, context):
    args = context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    user_chat = context.bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("This user is not gbanned!")
        return

    message.reply_text(f"I'll give {user_chat.first_name} a second chance, globally.")

    start_time = time.time()
    datetime_fmt = "%H:%M - %d-%m-%Y"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != 'private':
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (f"#UNGBANNED\n"
                   f"<b>Originated from:</b> {chat_origin}\n"
                   f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                   f"<b>Unbanned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
                   f"<b>Unbanned User ID:</b> {user_chat.id}\n"
                   f"<b>Event Stamp:</b> {current_time}")

    if MESSAGE_DUMP:
        try:
            log = context.bot.send_message(MESSAGE_DUMP, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = context.bot.send_message(MESSAGE_DUMP,
                                   log_message + "\n\nFormatting has been disabled due to an unexpected error.")
    else:
        send_to_list(context.bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    chats = get_all_chats()
    ungbanned_chats = 0

    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = context.bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Could not un-gban due to: {excp.message}")
                if MESSAGE_DUMP:
                    context.bot.send_message(MESSAGE_DUMP, f"Could not un-gban due to: {excp.message}",
                                     parse_mode=ParseMode.HTML)
                else:
                    context.bot.send_message(OWNER_ID, f"Could not un-gban due to: {excp.message}")
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if MESSAGE_DUMP:
        log.edit_text(log_message + f"\n<b>Chats affected:</b> {ungbanned_chats}", parse_mode=ParseMode.HTML)
    else:
        send_to_list(context.bot, SUDO_USERS + SUPPORT_USERS, "un-gban complete!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        message.reply_text(f"Person has been un-gbanned. Took {ungban_time} min")
    else:
        message.reply_text(f"Person has been un-gbanned. Took {ungban_time} sec")


@run_async
def gbanlist(update, context):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text("There aren't any gbanned users! You're kinder than I expected...")
        return

    banfile = 'Screw these guys.\n'
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["reason"]:
            banfile += f"Reason: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(document=output, filename="gbanlist.txt",
                                                caption="Here is the list of currently gbanned users.")


def check_and_ban(update, user_id, should_message=True):
    
    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text("Alert: This user is globally banned.\n"
                                                "*bans them from here*.)


@run_async
def enforce_gban(update, context):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    if sql.does_chat_gban(update.effective_chat.id) and update.effective_chat.get_member(bot.id).can_restrict_members:
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(update, context):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("I've enabled gbans in this group. This will help protect you "
                                                "from spammers, unsavoury characters, and the biggest trolls.")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("I've disabled gbans in this group. GBans wont affect your users "
                                                "anymore. You'll be less protected from any trolls and spammers "
                                                "though!")
    else:
        update.effective_message.reply_text("Give me some arguments to choose a setting! on/off, yes/no!\n\n"
                                            "Your current setting is: {}\n"
                                            "When True, any gbans that happen will also happen in your group. "
                                            "When False, they won't, leaving you at the possible mercy of "
                                            "spammers.".format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return tl(OWNER_ID, "{} gbanned users.").format(sql.num_gbanned_users())


def __user_info__(user_id, chat_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = tl(user_id, "Globally banned: <b>{}</b>" )
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += "\nReason: {}".format(html.escape(user.reason))
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"This chat is enforcing *gbans*: `{sql.does_chat_gban(chat_id)}`."


__help__ = "globalbans_help"

__mod_name__ = "Global Bans"

GBAN_HANDLER = CommandHandler("gban", gban, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
UNGBAN_HANDLER = CommandHandler("ungban", ungban, pass_args=True,
                                filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
GBAN_LIST = CommandHandler("gbanlist", gbanlist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)

GBAN_STATUS = CommandHandler("gbanstat", gbanstat, pass_args=True, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
