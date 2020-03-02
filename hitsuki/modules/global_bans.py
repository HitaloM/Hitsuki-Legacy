import html
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram.utils.helpers import mention_html, escape_markdown

import hitsuki.modules.sql.global_bans_sql as sql
from hitsuki import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN, spamfilters
from hitsuki.modules.helper_funcs.chat_status import user_admin, is_user_admin
from hitsuki.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from hitsuki.modules.helper_funcs.filters import CustomFilters
from hitsuki.modules.helper_funcs.misc import send_to_list
from hitsuki.modules.sql.users_sql import get_all_chats

from hitsuki.modules.languages import tl
from hitsuki.modules.helper_funcs.alternate import send_message

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
def gban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        send_message(update.effective_message, tl(update.effective_message, "You do not seem to be referring to a user."))
        return

    if int(user_id) in SUDO_USERS:
        send_message(update.effective_message, tl(update.effective_message, "I am spying, with my little eyes... Sudo war!  Why are you turning away? 😱"))
        return

    if int(user_id) in SUPPORT_USERS:
        send_message(update.effective_message, tl(update.effective_message, "OOOH someone is trying to globally ban a support user! 😄 *picks up popcorn*"))
        return

    if user_id == bot.id:
        send_message(update.effective_message, tl(update.effective_message, "😑 Very funny, let's block globally myself? Good effort 😒"))
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        send_message(update.effective_message, excp.message)
        return

    if user_chat.type != 'private':
        send_message(update.effective_message, tl(update.effective_message, "That's not a user!"))
        return

    if sql.is_user_gbanned(user_id):
        if not reason:
            send_message(update.effective_message, tl(update.effective_message, "This user has been banned globally; I will change the reason, but you haven't given me one..."))
            return

        old_reason = sql.update_gban_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            send_message(update.effective_message, tl(update.effective_message, "This user has been banned, due to the following reason:\n"
                               "<code>{}</code>\n"
                               "I've gone and updated it with your new reason!").format(html.escape(old_reason)),
                               parse_mode=ParseMode.HTML)
        else:
            send_message(update.effective_message, tl(update.effective_message, "This user has been banned, but no reason has been set; I've gone and updated it!"))

        return

    send_message(update.effective_message, tl(update.effective_message, "*It's gban time* 😉"))

    banner = update.effective_user  # type: Optional[User]
    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 tl(update.effective_message, "{} is gbanning user {} "
                 "because:\n{}").format(mention_html(banner.id, banner.first_name),
                                       mention_html(user_chat.id, user_chat.first_name), reason or tl(update.effective_message, "No reason given")),
                 html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                send_message(update.effective_message, tl(update.effective_message, "Cannot gban because: {}").format(excp.message))
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS, tl(update.effective_message, "Cannot gban because of: {}").format(excp.message))
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, tl(update.effective_message, "Global Ban is complete!"))
    send_message(update.effective_message, tl(update.effective_message, "This person has been gbanned."))


@run_async
def ungban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        send_message(update.effective_message, tl(update.effective_message, "You do not seem to be referring to a user."))
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        send_message(update.effective_message, tl(update.effective_message, "That's not a user!"))
        return

    if not sql.is_user_gbanned(user_id):
        send_message(update.effective_message, tl(update.effective_message, "This user is not gbanned!"))
        return

    banner = update.effective_user  # type: Optional[User]

    send_message(update.effective_message, tl(update.effective_message, "I will give {} a second chance, globally unbanned.").format(user_chat.first_name))

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 tl(update.effective_message, "{} has removed the global ban for user {}").format(mention_html(banner.id, banner.first_name),
                                                   mention_html(user_chat.id, user_chat.first_name)),
                 html=True)

    sql.ungban_user(user_id)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                send_message(update.effective_message, tl(update.effective_message, "Cannot remove global ban because: {}").format(excp.message))
                bot.send_message(OWNER_ID, tl(update.effective_message, "Cannot remove global ban because: {}").format(excp.message))
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, tl(update.effective_message, "Removing global ban complete!"))

    send_message(update.effective_message, tl(update.effective_message, "This person has been removed from the ban."))


@run_async
def gbanlist(bot: Bot, update: Update):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_send_message(update.effective_message, tl(update.effective_message, "There are no banned users globally! You are better than I expected..."))
        return

    banfile = tl(update.effective_message, 'Fuck these people.\n')
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(document=output, filename="gbanlist.txt",
                                                caption=tl(update.effective_message, "Here is a list of users who are currently banned globally."))


def check_and_ban(update, user_id, should_message=True):
    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_send_message(update.effective_message, tl(update.effective_message, "These bad people, they shouldn't be here!"))


@run_async
def enforce_gban(bot: Bot, update: Update):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    if sql.does_chat_gban(update.effective_chat.id) and update.effective_chat.get_member(bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_send_message(update.effective_message, tl(update.effective_message, "I have enabled global bans in this group. This will help protect you "
                                                "from spammers, unpleasant characters, and the biggest trolls."))
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_send_message(update.effective_message, tl(update.effective_message, "I have disabled the global ban on this group. Global bans will not affect your users "
                                                "again. You will be less protected from trolls and spammers though"))
    else:
        update.effective_send_message(update.effective_message, tl(update.effective_message, "Give me some arguments for choosing settings! on/off, yes/no!\n\n"
                                            "Your current settings: {}\n"
                                            "When True, any global ban that occur will also occur in your group. "
                                            "When False, they won't, leaving you at the possible mercy of "
                                            "spammers.").format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return tl(OWNER_ID, "{} gbanned users.").format(sql.num_gbanned_users())


def __user_info__(user_id, chat_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = tl(user_id, "Global banned: <b>{}</b>")
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
    return tl(user_id, "This chat is enforcing *gbans*: `{}`.").format(sql.does_chat_gban(chat_id))


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
# GBAN_BTNSET_HANDLER = CallbackQueryHandler(GBAN_EDITBTN, pattern=r"set_gstats")

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)
# dispatcher.add_handler(GBAN_BTNSET_HANDLER)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
