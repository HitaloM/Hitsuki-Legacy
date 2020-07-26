import ast
import re
from io import BytesIO

from telegram import MAX_MESSAGE_LENGTH, ParseMode, InlineKeyboardMarkup
from telegram.error import BadRequest, Unauthorized
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import escape_markdown, mention_markdown

import hitsuki.modules.sql.notes_sql as sql
from hitsuki import dispatcher, MESSAGE_DUMP, LOGGER, spamcheck, OWNER_ID
from hitsuki.modules.connection import connected
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.helper_funcs.alternate import send_message
from hitsuki.modules.helper_funcs.chat_status import user_admin
from hitsuki.modules.helper_funcs.misc import build_keyboard_parser, revert_buttons
from hitsuki.modules.helper_funcs.msg_types import get_note_type
from hitsuki.modules.helper_funcs.string_handling import escape_invalid_curly_brackets
from hitsuki.modules.languages import tl

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")
STICKER_MATCHER = re.compile(r"^###sticker(!photo)?###:")
BUTTON_MATCHER = re.compile(r"^###button(!photo)?###:(.*?)(?:\s|$)")
MYFILE_MATCHER = re.compile(r"^###file(!photo)?###:")
MYPHOTO_MATCHER = re.compile(r"^###photo(!photo)?###:")
MYAUDIO_MATCHER = re.compile(r"^###audio(!photo)?###:")
MYVOICE_MATCHER = re.compile(r"^###voice(!photo)?###:")
MYVIDEO_MATCHER = re.compile(r"^###video(!photo)?###:")
MYVIDEONOTE_MATCHER = re.compile(r"^###video_note(!photo)?###:")

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
    sql.Types.VIDEO_NOTE.value: dispatcher.bot.send_video_note
}


# Do not async
def get(bot, update, notename, show_none=True, no_format=False):
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        send_id = user.id
    else:
        chat_id = update.effective_chat.id
        send_id = chat_id

    note = sql.get_note(chat_id, notename)
    message = update.effective_message  # type: Optional[Message]

    if note:
        # If we're replying to a message, reply to that message (unless it's an error)
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id

        if note.is_reply:
            if MESSAGE_DUMP:
                try:
                    bot.forward_message(chat_id=chat_id, from_chat_id=MESSAGE_DUMP, message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        send_message(update.effective_message, tl(update.effective_message,
                                                                  "This message seems to have been lost - I'll remove it "
                                                                  "from your list of notes."))
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
            else:
                try:
                    bot.forward_message(chat_id=chat_id, from_chat_id=chat_id, message_id=note.value)
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        send_message(update.effective_message, tl(update.effective_message,
                                                                  "Looks like the original sender of this note has deleted "
                                                                  "their message - sorry! Get your bot admin to start using a message "
                                                                  "dump to avoid this. I'll remove this note from your saved notes. "))
                        sql.rm_note(chat_id, notename)
                    else:
                        raise
        else:

            VALID_WELCOME_FORMATTERS = ['first', 'last', 'fullname', 'username', 'id', 'chatname', 'mention', 'rules']
            valid_format = escape_invalid_curly_brackets(note.value, VALID_WELCOME_FORMATTERS)

            if valid_format:
                text = valid_format.format(first=escape_markdown(message.from_user.first_name),
                                           last=escape_markdown(
                                               message.from_user.last_name or message.from_user.first_name),
                                           fullname=escape_markdown(" ".join([message.from_user.first_name,
                                                                              message.from_user.last_name] if message.from_user.last_name else [
                                               message.from_user.first_name])),
                                           username="@" + message.from_user.username if message.from_user.username else mention_markdown(
                                               message.from_user.id, message.from_user.first_name),
                                           mention=mention_markdown(message.from_user.id, message.from_user.first_name),
                                           chatname=escape_markdown(
                                               message.chat.title if message.chat.type != "private" else message.from_user.first_name),
                                           id=message.from_user.id,
                                           rules="http://t.me/{}?start={}".format(bot.username, chat_id))
            else:
                text = ""

            keyb = []
            parseMode = ParseMode.MARKDOWN
            buttons = sql.get_buttons(chat_id, notename)
            if no_format:
                parseMode = None
                text += revert_buttons(buttons)
            else:
                keyb = build_keyboard_parser(bot, chat_id, buttons)

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                is_private, is_delete = sql.get_private_note(chat.id)
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    try:
                        if is_delete:
                            update.effective_message.delete()
                        if is_private:
                            bot.send_message(user.id, text,
                                             parse_mode=parseMode, disable_web_page_preview=True,
                                             reply_markup=keyboard)
                        else:
                            bot.send_message(send_id, text, reply_to_message_id=reply_id,
                                             parse_mode=parseMode, disable_web_page_preview=True,
                                             reply_markup=keyboard)
                    except BadRequest as excp:
                        if excp.message == "Wrong http url":
                            failtext = tl(update.effective_message,
                                          "Error: URL on the button is invalid! Please update this note.")
                            failtext += "\n\n```\n{}```".format(note.value + revert_buttons(buttons))
                            send_message(update.effective_message, failtext, parse_mode="markdown")
                        elif excp.message == "Button_url_invalid":
                            failtext = tl(update.effective_message,
                                          "Error: URL on the button is invalid! Please update this note.")
                            failtext += "\n\n```\n{}```".format(note.value + revert_buttons(buttons))
                            send_message(update.effective_message, failtext, parse_mode="markdown")
                        elif excp.message == "Message can't be deleted":
                            pass
                        elif excp.message == "Have no rights to send a message":
                            pass
                    except Unauthorized:
                        send_message(update.effective_message,
                                     tl(update.effective_message, "Contact me at PM to get this notes."),
                                     parse_mode="markdown")
                else:
                    try:
                        if is_delete:
                            update.effective_message.delete()
                        if is_private:
                            ENUM_FUNC_MAP[note.msgtype](user.id, note.file, caption=text, parse_mode=parseMode,
                                                        disable_web_page_preview=True, reply_markup=keyboard)
                        else:
                            ENUM_FUNC_MAP[note.msgtype](send_id, note.file, caption=text, reply_to_message_id=reply_id,
                                                        parse_mode=parseMode, disable_web_page_preview=True,
                                                        reply_markup=keyboard)
                    except BadRequest as excp:
                        if excp.message == "Message can't be deleted":
                            pass
                        elif excp.message == "Have no rights to send a message":
                            pass
                    except Unauthorized:
                        send_message(update.effective_message,
                                     tl(update.effective_message, "Contact me at PM to get this note."),
                                     parse_mode="markdown")
                        pass

            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    send_message(update.effective_message, tl(update.effective_message,
                                                              "It looks like you tried to mention someone who has never seen before. "
                                                              "If you really want to mention, forwarding one of their messages to me, "
                                                              "and I will be able to mark them!"))
                elif FILE_MATCHER.match(note.value):
                    send_message(update.effective_message, tl(update.effective_message,
                                                              "This note was an incorrectly imported file from another bot - "
                                                              "I can't use it. If you really need it, you'll have to save it again. "
                                                              "In the meantime, I'll remove it from your notes list."))
                    sql.rm_note(chat_id, notename)
                else:
                    send_message(update.effective_message, tl(update.effective_message,
                                                              "This note could not be sent, as it is incorrectly formatted."))
                    LOGGER.exception("Could not parse message #%s in the chat %s", notename, str(chat_id))
                    LOGGER.warning("The message: %s", str(note.value))
        return
    elif show_none:
        send_message(update.effective_message, tl(update.effective_message, "This note doesn't exist"))


@run_async
@spamcheck
def cmd_get(update, context):
    args = context.args
    if len(args) >= 2 and args[1].lower() == "noformat":
        get(context.bot, update, args[0], show_none=True, no_format=True)
    elif len(args) >= 1:
        get(context.bot, update, args[0], show_none=True)
    else:
        send_message(update.effective_message, tl(update.effective_message, "Get what?"))


@run_async
@spamcheck
def hash_get(update, context):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    get(context.bot, update, no_hash, show_none=False)


# TODO: FIX THIS
@run_async
@spamcheck
@user_admin
def save(update, context):
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(context.bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local notes"
        else:
            chat_name = chat.title

    msg = update.effective_message  # type: Optional[Message]

    checktext = msg.text.split()
    if msg.reply_to_message:
        if len(checktext) <= 1:
            send_message(update.effective_message,
                         tl(update.effective_message, "Anda harus memberi nama untuk catatan ini!"))
            return
    else:
        if len(checktext) <= 2:
            send_message(update.effective_message,
                         tl(update.effective_message, "Anda harus memberi nama untuk catatan ini!"))
            return

    note_name, text, data_type, content, buttons = get_note_type(msg)

    if data_type is None:
        send_message(update.effective_message, tl(update.effective_message, "Tidak ada catatan!"))
        return

    if len(text.strip()) == 0:
        text = "`" + note_name + "`"

    sql.add_note_to_db(chat_id, note_name, text, data_type, buttons=buttons, file=content)
    if conn:
        savedtext = tl(update.effective_message, "Ok, catatan `{note_name}` disimpan di *{chat_name}*.").format(
            note_name=note_name, chat_name=chat_name)
    else:
        savedtext = tl(update.effective_message, "Ok, catatan `{note_name}` disimpan.").format(note_name=note_name)
    try:
        send_message(update.effective_message, savedtext, parse_mode=ParseMode.MARKDOWN)
    except BadRequest:
        if conn:
            savedtext = tl(update.effective_message,
                           "Ok, catatan <code>{note_name}</code> disimpan di <b>{chat_name}</b>.").format(
                note_name=note_name, chat_name=chat_name)
        else:
            savedtext = tl(update.effective_message, "Ok, catatan <code>{note_name}</code> disimpan.").format(
                note_name=note_name)
        send_message(update.effective_message, savedtext, parse_mode=ParseMode.HTML)


@run_async
@spamcheck
@user_admin
def clear(update, context):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(context.bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "local notes"
        else:
            chat_name = chat.title

    if len(args) >= 1:
        catatan = []
        catatangagal = []
        for x in range(len(args)):
            notename = args[x]
            if sql.rm_note(chat_id, notename):
                catatan.append(notename)
            else:
                catatangagal.append(notename)
        if len(catatan) >= 1 and len(catatangagal) == 0:
            if conn:
                rtext = tl(update.effective_message, "Catatan di *{chat_name}* untuk `{note_name}` dihapus 😁").format(
                    chat_name=chat_name, note_name=", ".join(catatan))
            else:
                rtext = tl(update.effective_message, "Catatan `{note_name}` dihapus 😁").format(
                    note_name=", ".join(catatan))
            try:
                send_message(update.effective_message, rtext, parse_mode=ParseMode.MARKDOWN)
            except BadRequest:
                if conn:
                    rtext = tl(update.effective_message,
                               "Catatan di <b>{chat_name}</b> untuk <code>{note_name}</code> dihapus 😁").format(
                        chat_name=chat_name, note_name=", ".join(catatan))
                else:
                    rtext = tl(update.effective_message, "Catatan <code>{note_name}</code> dihapus 😁").format(
                        note_name=", ".join(catatan))
                send_message(update.effective_message, rtext, parse_mode=ParseMode.HTML)
        elif len(catatangagal) >= 0 and len(catatan) == 0:
            if conn:
                rtext = tl(update.effective_message,
                           "Catatan di *{chat_name}* untuk `{fnote_name}` gagal dihapus!").format(chat_name=chat_name,
                                                                                                  fnote_name=", ".join(
                                                                                                      catatangagal))
            else:
                rtext = tl(update.effective_message, "Catatan `{fnote_name}` gagal dihapus!").format(
                    fnote_name=", ".join(catatangagal))
            try:
                send_message(update.effective_message, rtext, parse_mode=ParseMode.MARKDOWN)
            except BadRequest:
                if conn:
                    rtext = tl(update.effective_message,
                               "Catatan di <b>{chat_name}</b> untuk <code>{fnote_name}</code> gagal dihapus!").format(
                        chat_name=chat_name, fnote_name=", ".join(catatangagal))
                else:
                    rtext = tl(update.effective_message, "Catatan <code>{fnote_name}</code> gagal dihapus!").format(
                        fnote_name=", ".join(catatangagal))
                send_message(update.effective_message, tl(update.effective_message, rtext), parse_mode=ParseMode.HTML)
        else:
            if conn:
                rtext = tl(update.effective_message,
                           "Catatan di *{chat_name}* untuk `{note_name}` dihapus 😁\nCatatan `{fnote_name}` gagal dihapus!").format(
                    chat_name=chat_name, note_name=", ".join(catatan), fnote_name=", ".join(catatangagal))
            else:
                rtext = tl(update.effective_message,
                           "Catatan `{note_name}` dihapus 😁\nCatatan `{fnote_name}` gagal dihapus!").format(
                    note_name=", ".join(catatan), fnote_name=", ".join(catatangagal))
            try:
                send_message(update.effective_message, rtext, parse_mode=ParseMode.MARKDOWN)
            except BadRequest:
                if conn:
                    rtext = tl(update.effective_message,
                               "Catatan di <b>{chat_name}</b> untuk <code>{note_name}</code> dihapus 😁\nCatatan <code>{fnote_name}</code> gagal dihapus!").format(
                        chat_name=chat_name, note_name=", ".join(catatan), fnote_name=", ".join(catatangagal))
                else:
                    rtext = tl(update.effective_message,
                               "Catatan <code>{note_name}</code> dihapus 😁\nCatatan <code>{fnote_name}</code> gagal dihapus!").format(
                        note_name=", ".join(catatan), fnote_name=", ".join(catatangagal))
                send_message(update.effective_message, tl(update.effective_message, rtext), parse_mode=ParseMode.HTML)

    else:
        send_message(update.effective_message, tl(update.effective_message, "Apa yang ingin dihapus?"))


@run_async
@spamcheck
@user_admin
def private_note(update, context):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(context.bot, update, chat, user.id)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = chat.title
        else:
            chat_name = chat.title

    if len(args) >= 1:
        if args[0] in ("yes", "on"):
            if len(args) >= 2:
                if args[1] == "del":
                    sql.private_note(str(chat_id), True, True)
                    send_message(update.effective_message, tl(update.effective_message,
                                                              "Private Note was *enabled*, when users get notes, the message will be sent to the PM and the hashtag message will be deleted."),
                                 parse_mode="markdown")
                else:
                    sql.private_note(str(chat_id), True, False)
                    send_message(update.effective_message, tl(update.effective_message,
                                                              "Private Note was *enabled*, when users get notes, the message will be sent to the PM."),
                                 parse_mode="markdown")
            else:
                sql.private_note(str(chat_id), True, False)
                send_message(update.effective_message, tl(update.effective_message,
                                                          "Private Note was *enabled*, when users get notes, the message will be sent to the PM."),
                             parse_mode="markdown")
        elif args[0] in ("no", "off"):
            sql.private_note(str(chat_id), False, False)
            send_message(update.effective_message,
                         tl(update.effective_message, "Private Note was *disabled*, notes will be sent to group."),
                         parse_mode="markdown")
        else:
            send_message(update.effective_message,
                         tl(update.effective_message, "Argumen tidak dikenal - harap gunakan 'yes', atau 'no'."))
    else:
        is_private, is_delete = sql.get_private_note(chat_id)
        print(is_private, is_delete)
        send_message(update.effective_message,
                     tl(update.effective_message, "Current Private Note settings at {}: *{}*{}").format(chat_name,
                                                                                                        "Enabled" if is_private else "Disabled",
                                                                                                        " - *Hash will be deleted*" if is_delete else ""),
                     parse_mode="markdown")


@run_async
@spamcheck
def list_notes(update, context):
    chat = update.effective_chat
    user = update.effective_user
    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
        msg = tl(update.effective_message, "*Notes on {}:*\n").format(chat_name)
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = ""
            msg = tl(update.effective_message, "*Local notes:*\n")
        else:
            chat_name = chat.title
            msg = tl(update.effective_message, "*Notes on {}:*\n").format(chat_name)

    note_list = sql.get_all_chat_notes(chat_id)

    for note in note_list:
        note_name = " • `#{}`\n".format(note.name)
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            send_message(update.effective_message, msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += note_name

    if msg == tl(update.effective_message, "*Notes on {}:*\n").format(chat_name) or msg == tl(update.effective_message,
                                                                                              "*Local notes:*\n"):
        if conn:
            send_message(update.effective_message, tl(update.effective_message, "No notes in *{}*!").format(chat_name),
                         parse_mode="markdown")
        else:
            send_message(update.effective_message, tl(update.effective_message, "No notes in this chat!"))

    elif len(msg) != 0:
        msg += tl(update.effective_message, "\nYou can retrieve these notes by using `/get notename`, or `#notename`")
        try:
            send_message(update.effective_message, msg, parse_mode=ParseMode.MARKDOWN)
        except BadRequest:
            if chat.type == "private":
                chat_name = ""
                msg = tl(update.effective_message, "<b>Local notes:</b>\n")
            else:
                chat_name = chat.title
                msg = tl(update.effective_message, "<b>Notes on {}:</b>\n").format(chat_name)
            for note in note_list:
                note_name = " - <code>{}</code>\n".format(note.name)
                if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
                    send_message(update.effective_message, msg, parse_mode=ParseMode.MARKDOWN)
                    msg = ""
                msg += note_name
            msg += tl(update.effective_message,
                      "\nYou can retrieve these notes by using <code>/get notename</code>, or <code>#notename</code>")
            send_message(update.effective_message, msg, parse_mode=ParseMode.HTML)


def __import_data__(chat_id, data, update):
    failures = []
    for notename, notedata in data.get('extra', {}).items():
        match = FILE_MATCHER.match(notedata)
        matchsticker = STICKER_MATCHER.match(notedata)
        matchbtn = BUTTON_MATCHER.match(notedata)
        matchfile = MYFILE_MATCHER.match(notedata)
        matchphoto = MYPHOTO_MATCHER.match(notedata)
        matchaudio = MYAUDIO_MATCHER.match(notedata)
        matchvoice = MYVOICE_MATCHER.match(notedata)
        matchvideo = MYVIDEO_MATCHER.match(notedata)
        matchvn = MYVIDEONOTE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end():].strip()
            if notedata:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)
        elif matchsticker:
            content = notedata[matchsticker.end():].strip()
            if content:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.STICKER, file=content)
        elif matchbtn:
            parse = notedata[matchbtn.end():].strip()
            notedata = parse.split("<###button###>")[0]
            buttons = parse.split("<###button###>")[1]
            buttons = ast.literal_eval(buttons)
            if buttons:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.BUTTON_TEXT, buttons=buttons)
        elif matchfile:
            file = notedata[matchfile.end():].strip()
            file = file.split("<###TYPESPLIT###>")
            notedata = file[1]
            content = file[0]
            if content:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.DOCUMENT, file=content)
        elif matchphoto:
            photo = notedata[matchphoto.end():].strip()
            photo = photo.split("<###TYPESPLIT###>")
            notedata = photo[1]
            content = photo[0]
            if content:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.PHOTO, file=content)
        elif matchaudio:
            audio = notedata[matchaudio.end():].strip()
            audio = audio.split("<###TYPESPLIT###>")
            notedata = audio[1]
            content = audio[0]
            if content:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.AUDIO, file=content)
        elif matchvoice:
            voice = notedata[matchvoice.end():].strip()
            voice = voice.split("<###TYPESPLIT###>")
            notedata = voice[1]
            content = voice[0]
            if content:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.VOICE, file=content)
        elif matchvideo:
            video = notedata[matchvideo.end():].strip()
            video = video.split("<###TYPESPLIT###>")
            notedata = video[1]
            content = video[0]
            if content:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.VIDEO, file=content)
        elif matchvn:
            video_note = notedata[matchvn.end():].strip()
            video_note = video_note.split("<###TYPESPLIT###>")
            notedata = video_note[1]
            content = video_note[0]
            if content:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.VIDEO_NOTE, file=content)
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            dispatcher.bot.send_document(chat_id, document=output, filename="failed_imports.txt",
                                         caption=tl(update.effective_message, "File/photo failed to import due to come "
                                                                              "from other bots. This is a limitation of Telegram API, and could not "
                                                                              "avoided. Sorry for the inconvenience!"))


@run_async
@spamcheck
@user_admin
def remove_all_notes(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if chat.type == "private":
        chat.title = tl(chat.id, "local notes")
    else:
        owner = chat.get_member(user.id)
        chat.title = chat.title
        if owner.status != 'creator':
            message.reply_text(tl(chat.id, "You must be this chat creator."))
            return

    note_list = sql.get_all_chat_notes(chat.id)
    if not note_list:
        message.reply_text(tl(chat.id,
                              "No notes in *{}*!").format(chat.title),
                           parse_mode=ParseMode.MARKDOWN)
        return

    x = 0
    a_note = []
    for notename in note_list:
        x += 1
        note = notename.name.lower()
        a_note.append(note)

    for note in a_note:
        sql.rm_note(chat.id, note)

    message.reply_text(tl(chat.id, "{} notes from this chat have been removed.").format(x))


def __stats__():
    return tl(OWNER_ID, "`{}` notes, on `{}` chat.").format(sql.num_notes(), sql.num_chats())


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return tl(user_id, "There are `{}` notes in this chat.").format(len(notes))


__help__ = "notes_help"

__mod_name__ = "Notes"

GET_HANDLER = CommandHandler("get", cmd_get, pass_args=True)
HASH_GET_HANDLER = MessageHandler(Filters.regex(r"^#[^\s]+"), hash_get)

SAVE_HANDLER = CommandHandler("save", save)
REMOVE_ALL_NOTES_HANDLER = CommandHandler("clearall", remove_all_notes)
DELETE_HANDLER = CommandHandler("clear", clear, pass_args=True)

PMNOTE_HANDLER = CommandHandler("privatenote", private_note, pass_args=True)

LIST_HANDLER = DisableAbleCommandHandler(["notes", "saved"], list_notes, admin_ok=True)

dispatcher.add_handler(GET_HANDLER)
dispatcher.add_handler(SAVE_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(DELETE_HANDLER)
dispatcher.add_handler(PMNOTE_HANDLER)
dispatcher.add_handler(HASH_GET_HANDLER)
dispatcher.add_handler(REMOVE_ALL_NOTES_HANDLER)
