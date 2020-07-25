import html

from telegram import ParseMode, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CommandHandler, run_async
from telegram.utils.helpers import mention_html

from hitsuki import dispatcher, spamcheck
from hitsuki.modules.helper_funcs.chat_status import is_user_admin, user_admin
from hitsuki.modules.helper_funcs.string_handling import extract_time
from hitsuki.modules.log_channel import loggable
from hitsuki.modules.sql import antiflood_sql as sql
from hitsuki.modules.connection import connected

from hitsuki.modules.languages import tl
from hitsuki.modules.helper_funcs.alternate import send_message

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(update, context) -> str:
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    if not user:  # ignore channels
        return ""

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            chat.kick_member(user.id)
            execstrings = tl(update.effective_message, "Keluar!")
            tag = "BANNED"
        elif getmode == 2:
            chat.kick_member(user.id)
            chat.unban_member(user.id)
            execstrings = tl(update.effective_message, "Keluar!")
            tag = "KICKED"
        elif getmode == 3:
            context.bot.restrict_chat_member(chat.id, user.id, permissions=ChatPermissions(can_send_messages=False))
            execstrings = tl(update.effective_message, "Sekarang kamu diam!")
            tag = "MUTED"
        elif getmode == 4:
            bantime = extract_time(msg, getvalue)
            chat.kick_member(user.id, until_date=bantime)
            execstrings = tl(update.effective_message, "Keluar selama {}!").format(getvalue)
            tag = "TBAN"
        elif getmode == 5:
            mutetime = extract_time(msg, getvalue)
            context.bot.restrict_chat_member(chat.id, user.id, until_date=mutetime,
                                             permissions=ChatPermissions(can_send_messages=False))
            execstrings = tl(update.effective_message, "Sekarang kamu diam selama {}!").format(getvalue)
            tag = "TMUTE"
        send_message(update.effective_message, tl(update.effective_message,
                                                  "Saya tidak suka orang yang mengirim pesan beruntun. Tapi kamu hanya membuat "
                                                  "saya kecewa. {}").format(execstrings))

        return "<b>{}:</b>" \
               "\n#{}" \
               "\n<b>User:</b> {}" \
               "\nFlooded the group.".format(tag, html.escape(chat.title),
                                             mention_html(user.id, user.first_name))

    except BadRequest:
        send_message(update.effective_message, tl(update.effective_message,
                                                  "Saya tidak bisa menendang orang di sini, beri saya izin terlebih dahulu! Sampai saat itu, saya akan menonaktifkan antiflood."))
        sql.set_flood(chat.id, 0)
        return "<b>{}:</b>" \
               "\n#INFO" \
               "\n{}".format(chat.title, tl(update.effective_message,
                                            "Tidak memiliki izin kick, jadi secara otomatis menonaktifkan antiflood."))


@run_async
@spamcheck
@user_admin
@loggable
def set_flood(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message,
                         tl(update.effective_message, "Anda bisa lakukan command ini pada grup, bukan pada PM"))
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val in ("off", "no", "0"):
            sql.set_flood(chat_id, 0)
            if conn:
                text = tl(update.effective_message, "Antiflood telah dinonaktifkan di *{}*.").format(chat_name)
            else:
                text = tl(update.effective_message, "Antiflood telah dinonaktifkan.")
            send_message(update.effective_message, text, parse_mode="markdown")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat_id, 0)
                if conn:
                    text = tl(update.effective_message, "Antiflood telah dinonaktifkan di *{}*.").format(chat_name)
                else:
                    text = tl(update.effective_message, "Antiflood telah dinonaktifkan.")
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>Admin:</b> {}" \
                       "\nDisable antiflood.".format(html.escape(chat_name), mention_html(user.id, user.first_name))

            elif amount < 3:
                send_message(update.effective_message, tl(update.effective_message,
                                                          "Antiflood harus baik 0 (dinonaktifkan), atau nomor lebih besar dari 3!"))
                return ""

            else:
                sql.set_flood(chat_id, amount)
                if conn:
                    text = tl(update.effective_message,
                              "Antiflood telah diperbarui dan diatur menjadi *{}* pada *{}*").format(amount, chat_name)
                else:
                    text = tl(update.effective_message, "Antiflood telah diperbarui dan diatur menjadi *{}*").format(
                        amount)
                send_message(update.effective_message, text, parse_mode="markdown")
                return "<b>{}:</b>" \
                       "\n#SETFLOOD" \
                       "\n<b>Admin:</b> {}" \
                       "\nSet antiflood to <code>{}</code>.".format(html.escape(chat_name),
                                                                    mention_html(user.id, user.first_name), amount)

        else:
            send_message(update.effective_message,
                         tl(update.effective_message, "Argumen tidak dikenal - harap gunakan angka, 'off', atau 'no'."))
    else:
        send_message(update.effective_message, tl(update.effective_message,
                                                  "Gunakan `/setflood nomor` untuk menyetel anti pesan beruntun.\nAtau gunakan `/setflood off` untuk menonaktifkan anti pesan beruntun."),
                     parse_mode="markdown")
    return ""


@run_async
@spamcheck
def flood(update, context):
    chat = update.effective_chat
    user = update.effective_user

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message,
                         tl(update.effective_message, "Anda bisa lakukan command ini pada grup, bukan pada PM"))
            return
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        if conn:
            text = tl(update.effective_message,
                      "Saat ini saya tidak memberlakukan pengendalian pesan beruntun pada *{}*!").format(chat_name)
        else:
            text = tl(update.effective_message, "Saat ini saya tidak memberlakukan pengendalian pesan beruntun")
        send_message(update.effective_message, text, parse_mode="markdown")
    else:
        if conn:
            text = tl(update.effective_message,
                      "Saat ini saya melarang pengguna jika mereka mengirim lebih dari *{}* pesan berturut-turut pada *{}*.").format(
                limit, chat_name)
        else:
            text = tl(update.effective_message,
                      "Saat ini saya melarang pengguna jika mereka mengirim lebih dari *{}* pesan berturut-turut.").format(
                limit)
        send_message(update.effective_message, text, parse_mode="markdown")


@run_async
@spamcheck
@user_admin
def set_flood_mode(update, context):
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    conn = connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = dispatcher.bot.getChat(conn)
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == "private":
            send_message(update.effective_message,
                         tl(update.effective_message, "Anda bisa lakukan command ini pada grup, bukan pada PM"))
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == 'ban':
            settypeflood = tl(update.effective_message, 'blokir')
            sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == 'kick':
            settypeflood = tl(update.effective_message, 'tendang')
            sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == 'mute':
            settypeflood = tl(update.effective_message, 'bisukan')
            sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == 'tban':
            if len(args) == 1:
                teks = tl(update.effective_message, """Sepertinya Anda mencoba menetapkan nilai sementara untuk anti-banjir, tetapi belum menentukan waktu; gunakan `/setfloodmode tban <timevalue>`.

Contoh nilai waktu: 4m = 4 menit, 3h = 3 jam, 6d = 6 hari, 5w = 5 minggu.""")
                send_message(update.effective_message, teks, parse_mode="markdown")
                return
            settypeflood = tl(update.effective_message, "blokir sementara selama {}").format(args[1])
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == 'tmute':
            if len(args) == 1:
                teks = tl(update.effective_message, """Sepertinya Anda mencoba menetapkan nilai sementara untuk anti-banjir, tetapi belum menentukan waktu; gunakan `/setfloodmode tban <timevalue>`.

Contoh nilai waktu: 4m = 4 menit, 3h = 3 jam, 6d = 6 hari, 5w = 5 minggu.""")
                send_message(update.effective_message, teks, parse_mode="markdown")
                return
            settypeflood = tl(update.effective_message, 'bisukan sementara selama {}').format(args[1])
            sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            send_message(update.effective_message,
                         tl(update.effective_message, "Saya hanya mengerti ban/kick/mute/tban/tmute!"))
            return
        if conn:
            text = tl(update.effective_message,
                      "Terlalu banyak mengirim pesan sekarang akan menghasilkan `{}` pada *{}*!").format(settypeflood,
                                                                                                         chat_name)
        else:
            text = tl(update.effective_message,
                      "Terlalu banyak mengirim pesan sekarang akan menghasilkan `{}`!").format(settypeflood)
        send_message(update.effective_message, text, parse_mode="markdown")
        return "<b>{}:</b>\n" \
               "<b>Admin:</b> {}\n" \
               "Has changed antiflood mode. User will {}.".format(settypeflood, html.escape(chat.title),
                                                                  mention_html(user.id, user.first_name))
    else:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            settypeflood = tl(update.effective_message, 'blokir')
        elif getmode == 2:
            settypeflood = tl(update.effective_message, 'tendang')
        elif getmode == 3:
            settypeflood = tl(update.effective_message, 'bisukan')
        elif getmode == 4:
            settypeflood = tl(update.effective_message, 'blokir sementara selama {}').format(getvalue)
        elif getmode == 5:
            settypeflood = tl(update.effective_message, 'bisukan sementara selama {}').format(getvalue)
        if conn:
            text = tl(update.effective_message,
                      "Jika member mengirim pesan beruntun, maka dia akan *di {}* pada *{}*.").format(settypeflood,
                                                                                                      chat_name)
        else:
            text = tl(update.effective_message, "Jika member mengirim pesan beruntun, maka dia akan *di {}*.").format(
                settypeflood)
        send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return tl(user_id, "*Not* currently enforcing flood control.")
    else:
        return tl(user_id, "Antiflood is set to `{}` messages.").format(limit)


__help__ = "antiflood_help"

__mod_name__ = "Antiflood"

FLOOD_BAN_HANDLER = MessageHandler(Filters.all & ~Filters.status_update & Filters.group, check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, pass_args=True)
SET_FLOOD_MODE_HANDLER = CommandHandler("setfloodmode", set_flood_mode, pass_args=True)
FLOOD_HANDLER = CommandHandler("flood", flood)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(SET_FLOOD_MODE_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
