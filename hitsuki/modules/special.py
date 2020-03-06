import html
import json
import math
import random
import PIL
import os
import urllib
import datetime
from typing import Optional, List
import time
import urbandict

import pyowm
import requests
import wikipedia
import base64

from bs4 import BeautifulSoup
from emoji import UNICODE_EMOJI
from pyowm import timeutils, exceptions
from googletrans import Translator
from PIL import Image

from telegram.error import BadRequest, Unauthorized
from telegram import Message, Chat, Update, Bot, MessageEntity, TelegramError
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html, mention_markdown

from hitsuki import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER, spamfilters
from hitsuki.__main__ import STATS, USER_INFO
from hitsuki.modules.disable import DisableAbleCommandHandler, DisableAbleRegexHandler
from hitsuki.modules.helper_funcs.extraction import extract_user
from hitsuki.modules.helper_funcs.filters import CustomFilters
from hitsuki.modules.sql import languages_sql as langsql

from hitsuki.modules.languages import tl
from hitsuki.modules.helper_funcs.alternate import send_message


reactions = [
    "( ͡° ͜ʖ ͡°)",
    "¯_(ツ)_/¯",
    "\'\'̵͇З= ( ▀ ͜͞ʖ▀) =Ε/̵͇/’’",
    "▄︻̷┻═━一",
    "( ͡°( ͡° ͜ʖ( ͡° ͜ʖ ͡°)ʖ ͡°) ͡°)",
    "ʕ•ᴥ•ʔ",
    "(▀Ĺ̯▀ )",
    "(ง ͠° ͟ل͜ ͡°)ง",
    "༼ つ ◕_◕ ༽つ",
    "ಠ_ಠ",
    "(づ｡◕‿‿◕｡)づ",
    "\'\'̵͇З=( ͠° ͟ʖ ͡°)=Ε/̵͇/\'",
    "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ ✧ﾟ･: *ヽ(◕ヮ◕ヽ)",
    "[̲̅$̲̅(̲̅5̲̅)̲̅$̲̅]",
    "┬┴┬┴┤ ͜ʖ ͡°) ├┬┴┬┴",
    "( ͡°╭͜ʖ╮͡° )",
    "(͡ ͡° ͜ つ ͡͡°)",
    "(• Ε •)",
    "(ง\'̀-\'́)ง",
    "(ಥ﹏ಥ)",
    "﴾͡๏̯͡๏﴿ O\'RLY?",
    "(ノಠ益ಠ)ノ彡┻━┻",
    "[̲̅$̲̅(̲̅ ͡° ͜ʖ ͡°̲̅)̲̅$̲̅]",
    "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧",
    "(☞ﾟ∀ﾟ)☞",
    "| (• ◡•)| (❍ᴥ❍Ʋ)",
    "(◕‿◕✿)",
    "(ᵔᴥᵔ)",
    "(╯°□°)╯︵ ꞰOOQƎƆⱯɟ",
    "(¬‿¬)",
    "(☞ﾟヮﾟ)☞ ☜(ﾟヮﾟ☜)",
    "(づ￣ ³￣)づ",
    "ლ(ಠ益ಠლ)",
    "ಠ╭╮ಠ",
    "\'\'̵͇З=(•_•)=Ε/̵͇/\'\'",
    "/╲/╭( ͡° ͡° ͜ʖ ͡° ͡°)╮/╱",
    "(;´༎ຶД༎ຶ)",
    "♪~ ᕕ(ᐛ)ᕗ",
    "♥️‿♥️",
    "༼ つ ͡° ͜ʖ ͡° ༽つ",
    "༼ つ ಥ_ಥ ༽つ",
    "(╯°□°）╯︵ ┻━┻",
    "( ͡ᵔ ͜ʖ ͡ᵔ )",
    "ヾ(⌐■_■)ノ♪",
    "~(˘▾˘~)",
    "◉_◉",
    "(•◡•) /",
    "(~˘▾˘)~",
    "(._.) ( L: ) ( .-. ) ( :L ) (._.)",
    "༼ʘ̚ل͜ʘ̚༽",
    "༼ ºل͟º ༼ ºل͟º ༼ ºل͟º ༽ ºل͟º ༽ ºل͟º ༽",
    "┬┴┬┴┤(･_├┬┴┬┴",
    "ᕙ(⇀‸↼‶)ᕗ",
    "ᕦ(Ò_Óˇ)ᕤ",
    "┻━┻ ︵ヽ(Д´)ﾉ︵ ┻━┻",
    "⚆ _ ⚆",
    "(•_•) ( •_•)>⌐■-■ (⌐■_■)",
    "(｡◕‿‿◕｡)",
    "ಥ_ಥ",
    "ヽ༼ຈل͜ຈ༽ﾉ",
    "⌐╦╦═─",
    "(☞ຈل͜ຈ)☞",
    "˙ ͜ʟ˙",
    "☜(˚▽˚)☞",
    "(•Ω•)",
    "(ง°ل͜°)ง",
    "(｡◕‿◕｡)",
    "（╯°□°）╯︵( .O.)",
    ":\')",
    "┬──┬ ノ( ゜-゜ノ)",
    "(っ˘ڡ˘Σ)",
    "ಠ⌣ಠ",
    "ლ(´ڡლ)",
    "(°ロ°)☝️",
    "｡◕‿‿◕｡",
    "( ಠ ͜ʖರೃ)",
    "╚(ಠ_ಠ)=┐",
    "(─‿‿─)",
    "ƪ(˘⌣˘)Ʃ",
    "(；一_一)",
    "(¬_¬)",
    "( ⚆ _ ⚆ )",
    "(ʘᗩʘ\')",
    "☜(⌒▽⌒)☞",
    "｡◕‿◕｡",
    "¯(°_O)/¯",
    "(ʘ‿ʘ)",
    "ლ,ᔑ•ﺪ͟͠•ᔐ.ლ",
    "(´・Ω・)",
    "ಠ~ಠ",
    "(° ͡ ͜ ͡ʖ ͡ °)",
    "┬─┬ノ( º _ ºノ)",
    "(´・Ω・)っ由",
    "ಠ_ಥ",
    "Ƹ̵̡Ӝ̵̨Ʒ",
    "(>ლ)",
    "ಠ‿↼",
    "ʘ‿ʘ",
    "(ღ˘⌣˘ღ)",
    "ಠOಠ",
    "ರ_ರ",
    "(▰˘◡˘▰)",
    "◔̯◔",
    "◔ ⌣ ◔",
    "(✿´‿`)",
    "¬_¬",
    "ب_ب",
    "｡゜(｀Д´)゜｡",
    "(Ó Ì_Í)=ÓÒ=(Ì_Í Ò)",
    "°Д°",
    "( ﾟヮﾟ)",
    "┬─┬﻿ ︵ /(.□. ）",
    "٩◔̯◔۶",
    "≧☉_☉≦",
    "☼.☼",
    "^̮^",
    "(>人<)",
    "〆(・∀・＠)",
    "(~_^)",
    "^̮^",
    "^̮^",
    ">_>",
    "(^̮^)",
    "(/) (°,,°) (/)",
    "^̮^",
    "^̮^",
    "=U",
    "(･.◤)"]

reactionhappy = [
    "\'\'̵͇З= ( ▀ ͜͞ʖ▀) =Ε/̵͇/’’",
    "ʕ•ᴥ•ʔ",
    "(づ｡◕‿‿◕｡)づ",
    "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ ✧ﾟ･: *ヽ(◕ヮ◕ヽ)",
    "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧",
    "(☞ﾟ∀ﾟ)☞",
    "| (• ◡•)| (❍ᴥ❍Ʋ)",
    "(◕‿◕✿)",
    "(ᵔᴥᵔ)",
    "(☞ﾟヮﾟ)☞ ☜(ﾟヮﾟ☜)",
    "(づ￣ ³￣)づ",
    "♪~ ᕕ(ᐛ)ᕗ",
    "♥️‿♥️",
    "༼ つ ͡° ͜ʖ ͡° ༽つ",
    "༼ つ ಥ_ಥ ༽つ",
    "ヾ(⌐■_■)ノ♪",
    "~(˘▾˘~)",
    "◉_◉",
    "(•◡•) /",
    "(~˘▾˘)~",
    "(｡◕‿‿◕｡)",
    "☜(˚▽˚)☞",
    "(•Ω•)",
    "(｡◕‿◕｡)",
    "(っ˘ڡ˘Σ)",
    "｡◕‿‿◕｡"
    "☜(⌒▽⌒)☞",
    "｡◕‿◕｡",
    "(ღ˘⌣˘ღ)",
    "(▰˘◡˘▰)",
    "^̮^",
    "^̮^",
    ">_>",
    "(^̮^)",
    "^̮^",
    "^̮^"]

reactionangry = [
    "▄︻̷┻═━一",
    "(▀Ĺ̯▀ )",
    "(ง ͠° ͟ل͜ ͡°)ง",
    "༼ つ ◕_◕ ༽つ",
    "ಠ_ಠ",
    "\'\'̵͇З=( ͠° ͟ʖ ͡°)=Ε/̵͇/\'",
    "(ง\'̀-\'́)ง",
    "(ノಠ益ಠ)ノ彡┻━┻",
    "(╯°□°)╯︵ ꞰOOQƎƆⱯɟ",
    "ლ(ಠ益ಠლ)",
    "ಠ╭╮ಠ",
    "\'\'̵͇З=(•_•)=Ε/̵͇/\'\'",
    "(╯°□°）╯︵ ┻━┻",
    "┻━┻ ︵ヽ(Д´)ﾉ︵ ┻━┻",
    "⌐╦╦═─",
    "（╯°□°）╯︵( .O.)",
    ":\')",
    "┬──┬ ノ( ゜-゜ノ)",
    "ლ(´ڡლ)",
    "(°ロ°)☝️",
    "ლ,ᔑ•ﺪ͟͠•ᔐ.ლ",
    "┬─┬ノ( º _ ºノ)",
    "┬─┬﻿ ︵ /(.□. ）"]


@run_async
def react(bot: Bot, update: Update):
    spam = spamfilters(
        update.effective_message.text,
        update.effective_message.from_user.id,
        update.effective_chat.id,
        update.effective_message)
    if spam:
        return
    message = update.effective_message
    react = random.choice(reactions)
    if message.reply_to_message:
        message.reply_to_message.reply_text(react)
    else:
        message.reply_text(react)


@run_async
def rhappy(bot: Bot, update: Update):
    spam = spamfilters(
        update.effective_message.text,
        update.effective_message.from_user.id,
        update.effective_chat.id,
        update.effective_message)
    if spam:
        return
    message = update.effective_message
    rhappy = random.choice(reactionhappy)
    if message.reply_to_message:
        message.reply_to_message.reply_text(rhappy)
    else:
        message.reply_text(rhappy)


@run_async
def rangry(bot: Bot, update: Update):
    spam = spamfilters(
        update.effective_message.text,
        update.effective_message.from_user.id,
        update.effective_chat.id,
        update.effective_message)
    if spam:
        return
    message = update.effective_message
    rangry = random.choice(reactionangry)
    if message.reply_to_message:
        message.reply_to_message.reply_text(rangry)
    else:
        message.reply_text(rangry)


@run_async
def stickerid(bot: Bot, update: Update):
    spam = spamfilters(
        update.effective_message.text,
        update.effective_message.from_user.id,
        update.effective_chat.id,
        update.effective_message)
    if spam:
        return
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        send_message(
            update.effective_message,
            tl(
                update.effective_message,
                "Hai {}, Id stiker yang anda balas adalah :\n```{}```").format(
                mention_markdown(
                    msg.from_user.id,
                    msg.from_user.first_name),
                msg.reply_to_message.sticker.file_id),
            parse_mode=ParseMode.MARKDOWN)
    else:
        send_message(update.effective_message,
                     tl(update.effective_message,
                        "Tolong balas pesan stiker untuk mendapatkan id stiker"),
                     parse_mode=ParseMode.MARKDOWN)


@run_async
def getlink(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = int(args[0])
    else:
        send_message(
            update.effective_message, tl(
                update.effective_message, "Anda sepertinya tidak mengacu pada obrolan"))
    chat = bot.getChat(chat_id)
    bot_member = chat.get_member(bot.id)
    if bot_member.can_invite_users:
        titlechat = bot.get_chat(chat_id).title
        invitelink = bot.get_chat(chat_id).invite_link
        send_message(
            update.effective_message, tl(
                update.effective_message, "Sukses mengambil link invite di grup {}. \nInvite link : {}").format(
                titlechat, invitelink))
    else:
        send_message(
            update.effective_message, tl(
                update.effective_message, "Saya tidak memiliki akses ke tautan undangan!"))


@run_async
def leavechat(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = int(args[0])
    else:
        send_message(
            update.effective_message, tl(
                update.effective_message, "Anda sepertinya tidak mengacu pada obrolan"))
    try:
        chat = bot.getChat(chat_id)
        titlechat = bot.get_chat(chat_id).title
        bot.sendMessage(
            chat_id, tl(
                update.effective_message, "Selamat tinggal semua 😁"))
        bot.leaveChat(chat_id)
        send_message(
            update.effective_message, tl(
                update.effective_message, "Saya telah keluar dari grup {}").format(titlechat))

    except BadRequest as excp:
        if excp.message == "Chat not found":
            send_message(update.effective_message, tl(update.effective_message,
                                                      "Sepertinya saya sudah keluar atau di tendang di grup tersebut"))
        else:
            return


@run_async
def ping(bot: Bot, update: Update):
    spam = spamfilters(
        update.effective_message.text,
        update.effective_message.from_user.id,
        update.effective_chat.id,
        update.effective_message)
    if spam:
        return
    start_time = time.time()
    test = send_message(update.effective_message, "Pong!")
    end_time = time.time()
    ping_time = float(end_time - start_time)
    bot.editMessageText(
        chat_id=update.effective_chat.id,
        message_id=test.message_id,
        text=tl(
            update.effective_message,
            "Pong!\nKecepatannya: {0:.2f} detik").format(
            round(
                ping_time,
                2) %
            60))


@run_async
def ramalan(bot: Bot, update: Update):
    spam = spamfilters(
        update.effective_message.text,
        update.effective_message.from_user.id,
        update.effective_chat.id,
        update.effective_message)
    if spam:
        return
    text = ""
    if random.randint(1, 10) >= 7:
        text += random.choice(tl(update.effective_message, "RAMALAN_FIRST"))
    text += random.choice(tl(update.effective_message, "RAMALAN_STRINGS"))
    send_message(update.effective_message, text)


@run_async
def terjemah(bot: Bot, update: Update):
    spam = spamfilters(
        update.effective_message.text,
        update.effective_message.from_user.id,
        update.effective_chat.id,
        update.effective_message)
    if spam:
        return
    msg = update.effective_message
    chat_id = update.effective_chat.id
    getlang = langsql.get_lang(update.effective_message.from_user.id)
    try:
        if msg.reply_to_message and msg.reply_to_message.text:
            args = update.effective_message.text.split()
            if len(args) >= 2:
                target = args[1]
                if "-" in target:
                    target2 = target.split("-")[1]
                    target = target.split("-")[0]
                else:
                    target2 = None
            else:
                if getlang:
                    target = getlang
                    target2 = None
                else:
                    raise IndexError
            teks = msg.reply_to_message.text
            #teks = deEmojify(teks)
            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in teks:
                    teks = teks.replace(emoji, '')
            message = update.effective_message
            trl = Translator()
            if target2 is None:
                deteksibahasa = trl.detect(teks)
                tekstr = trl.translate(teks, dest=target)
                send_message(
                    update.effective_message, tl(
                        update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(
                        deteksibahasa.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(teks, dest=target2, src=target)
                send_message(
                    update.effective_message, tl(
                        update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(
                        target, target2, tekstr.text), parse_mode=ParseMode.MARKDOWN)

        else:
            args = update.effective_message.text.split(None, 2)
            if len(args) != 1:
                target = args[1]
                teks = args[2]
                target2 = None
                if "-" in target:
                    target2 = target.split("-")[1]
                    target = target.split("-")[0]
            else:
                target = getlang
                teks = args[1]
            #teks = deEmojify(teks)
            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in teks:
                    teks = teks.replace(emoji, '')
            message = update.effective_message
            trl = Translator()
            if target2 is None:
                deteksibahasa = trl.detect(teks)
                tekstr = trl.translate(teks, dest=target)
                return send_message(
                    update.effective_message, tl(
                        update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(
                        deteksibahasa.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(teks, dest=target2, src=target)
                send_message(
                    update.effective_message, tl(
                        update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(
                        target, target2, tekstr.text), parse_mode=ParseMode.MARKDOWN)
    except IndexError:
        send_message(
            update.effective_message,
            tl(
                update.effective_message,
                "Balas pesan atau tulis pesan dari bahasa lain untuk "
                "diterjemahkan kedalam bahasa yang di dituju\n\n"
                "Contoh: `/tr en-id` untuk menerjemahkan dari Bahasa inggris ke Bahasa Indonesia\n"
                "Atau gunakan: `/tr id` untuk deteksi otomatis dan menerjemahkannya kedalam bahasa indonesia"),
            parse_mode="markdown")
    except ValueError:
        send_message(update.effective_message, tl(
            update.effective_message, "Bahasa yang di tuju tidak ditemukan!"))
    else:
        return


@run_async
def wiki(bot: Bot, update: Update):
    spam = spamfilters(
        update.effective_message.text,
        update.effective_message.from_user.id,
        update.effective_chat.id,
        update.effective_message)
    if spam:
        return
    msg = update.effective_message
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split(None, 1)
    teks = args[1]
    message = update.effective_message
    getlang = langsql.get_lang(chat_id)
    if str(getlang) == "id":
        wikipedia.set_lang("id")
    else:
        wikipedia.set_lang("en")
    try:
        pagewiki = wikipedia.page(teks)
    except wikipedia.exceptions.PageError:
        send_message(
            update.effective_message, tl(
                update.effective_message, "Hasil tidak ditemukan"))
        return
    except wikipedia.exceptions.DisambiguationError as refer:
        rujuk = str(refer).split("\n")
        if len(rujuk) >= 6:
            batas = 6
        else:
            batas = len(rujuk)
        teks = ""
        for x in range(batas):
            if x == 0:
                if getlang == "id":
                    teks += rujuk[x].replace('may refer to',
                                             'dapat merujuk ke') + "\n"
                else:
                    teks += rujuk[x] + "\n"
            else:
                teks += "- `" + rujuk[x] + "`\n"
        send_message(update.effective_message, teks, parse_mode="markdown")
        return
    except IndexError:
        send_message(
            update.effective_message, tl(
                update.effective_message, "Tulis pesan untuk mencari dari sumber wikipedia"))
        return
    judul = pagewiki.title
    summary = pagewiki.summary
    if update.effective_message.chat.type == "private":
        send_message(update.effective_message,
                     tl(update.effective_message,
                        "Hasil dari {} adalah:\n\n<b>{}</b>\n{}").format(teks,
                                                                         judul,
                                                                         summary),
                     parse_mode=ParseMode.HTML)
    else:
        if len(summary) >= 200:
            judul = pagewiki.title
            summary = summary[:200] + "..."
            button = InlineKeyboardMarkup([[InlineKeyboardButton(text=tl(
                update.effective_message, "Baca Lebih Lengkap"), url="t.me/{}?start=wiki-{}".format(bot.username, teks.replace(' ', '_')))]])
        else:
            button = None
        send_message(update.effective_message,
                     tl(update.effective_message,
                        "Hasil dari {} adalah:\n\n<b>{}</b>\n{}").format(teks,
                                                                         judul,
                                                                         summary),
                     parse_mode=ParseMode.HTML,
                     reply_markup=button)


@run_async
def urbandictionary(bot: Bot, update: Update, args):
    spam = spamfilters(
        update.effective_message.text,
        update.effective_message.from_user.id,
        update.effective_chat.id,
        update.effective_message)
    if spam:
        return
    msg = update.effective_message
    chat_id = update.effective_chat.id
    message = update.effective_message
    if args:
        text = " ".join(args)
        try:
            mean = urbandict.define(text)
        except Exception as err:
            send_message(update.effective_message, "Error: " + str(err))
            return
        if len(mean) >= 0:
            teks = ""
            if len(mean) >= 3:
                for x in range(3):
                    teks = "*Result of {}*\n\n*{}*\n*Meaning:*\n`{}`\n\n*Example:*\n`{}`\n\n".format(
                        text, mean[x].get("word")[:-7], mean[x].get("def"), mean[x].get("example"))
            else:
                for x in range(len(mean)):
                    teks = "*Result of {}*\n\n*{}*\n**Meaning:*\n`{}`\n\n*Example:*\n`{}`\n\n".format(
                        text, mean[x].get("word")[:-7], mean[x].get("def"), mean[x].get("example"))
            send_message(update.effective_message, teks,
                         parse_mode=ParseMode.MARKDOWN)
        else:
            send_message(
                update.effective_message,
                "{} couldn't be found in urban dictionary!".format(text),
                parse_mode=ParseMode.MARKDOWN)
    else:
        send_message(
            update.effective_message,
            "Use `/ud <text` for search meaning from urban dictionary.",
            parse_mode=ParseMode.MARKDOWN)


@run_async
def log(bot: Bot, update: Update):
    message = update.effective_message
    eventdict = message.to_dict()
    jsondump = json.dumps(eventdict, indent=4)
    send_message(update.effective_message, jsondump)


def deEmojify(inputString):
    return inputString.encode('ascii', 'ignore').decode('ascii')


@run_async
def getsticker(bot: Bot, update: Update):
    spam = spamfilters(
        update.effective_message.text,
        update.effective_message.from_user.id,
        update.effective_chat.id,
        update.effective_message)
    if spam:
        return
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        file_id = msg.reply_to_message.sticker.file_id
        newFile = bot.get_file(file_id)
        newFile.download('sticker.png')
        bot.send_document(chat_id, document=open('sticker.png', 'rb'))
        os.remove("sticker.png")
    else:
        update.effective_message.reply_text(
            "Please reply to a sticker for me to upload its PNG.")


@run_async
def kang(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(
        update.effective_message.text,
        update.effective_message.from_user.id,
        update.effective_chat.id,
        update.effective_message)
    if spam:
        return
    msg = update.effective_message
    user = update.effective_user
    packnum = 0
    packname = "a" + str(user.id) + "_by_" + bot.username
    packname_found = 0
    max_stickers = 120
    while packname_found == 0:
        try:
            stickerset = bot.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                packnum += 1
                packname = "a" + str(packnum) + "_" + \
                    str(user.id) + "_by_" + bot.username
            else:
                packname_found = 1
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = 1
    kangsticker = "kangsticker.png"
    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            file_id = msg.reply_to_message.sticker.file_id
        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        else:
            msg.reply_text("Yea, I can't kang that.")
        kang_file = bot.get_file(file_id)
        kang_file.download('kangsticker.png')
        if args:
            sticker_emoji = str(args[0])
        elif msg.reply_to_message.sticker and msg.reply_to_message.sticker.emoji:
            sticker_emoji = msg.reply_to_message.sticker.emoji
        else:
            sticker_emoji = "🤔"
        try:
            im = Image.open(kangsticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512 / size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512 / size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            if not msg.reply_to_message.sticker:
                im.save(kangsticker, "PNG")
            bot.add_sticker_to_set(
                user_id=user.id,
                name=packname,
                png_sticker=open(
                    'kangsticker.png',
                    'rb'),
                emojis=sticker_emoji)
            msg.reply_text(
                f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                f"\nEmoji is: {sticker_emoji}",
                parse_mode=ParseMode.MARKDOWN)
        except OSError as e:
            msg.reply_text("I can only kang images m8.")
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(
                    msg,
                    user,
                    open(
                        'kangsticker.png',
                        'rb'),
                    sticker_emoji,
                    bot,
                    packname,
                    packnum)
            elif e.message == "Sticker_png_dimensions":
                im.save(kangsticker, "PNG")
                bot.add_sticker_to_set(
                    user_id=user.id, name=packname, png_sticker=open(
                        'kangsticker.png', 'rb'), emojis=sticker_emoji)
                msg.reply_text(
                    f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                    f"\nEmoji is: {sticker_emoji}",
                    parse_mode=ParseMode.MARKDOWN)
            elif e.message == "Invalid sticker emojis":
                msg.reply_text("Invalid emoji(s).")
            elif e.message == "Stickers_too_much":
                msg.reply_text("Max packsize reached. Press F to pay respecc.")
            elif e.message == "Internal Server Error: sticker set not found (500)":
                msg.reply_text(
                    "Sticker successfully added to [pack](t.me/addstickers/%s)" %
                    packname +
                    "\n"
                    "Emoji is:" +
                    " " +
                    sticker_emoji,
                    parse_mode=ParseMode.MARKDOWN)
            print(e)
    elif args:
        try:
            try:
                urlemoji = msg.text.split(" ")
                png_sticker = urlemoji[1]
                sticker_emoji = urlemoji[2]
            except IndexError:
                sticker_emoji = "🤔"
            urllib.urlretrieve(png_sticker, kangsticker)
            im = Image.open(kangsticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512 / size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512 / size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            im.save(kangsticker, "PNG")
            msg.reply_photo(photo=open('kangsticker.png', 'rb'))
            bot.add_sticker_to_set(
                user_id=user.id,
                name=packname,
                png_sticker=open(
                    'kangsticker.png',
                    'rb'),
                emojis=sticker_emoji)
            msg.reply_text(
                f"Sticker successfully added to [pack](t.me/addstickers/{packname})" +
                f"\nEmoji is: {sticker_emoji}",
                parse_mode=ParseMode.MARKDOWN)
        except OSError as e:
            msg.reply_text("I can only kang images m8.")
            print(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(
                    msg,
                    user,
                    open(
                        'kangsticker.png',
                        'rb'),
                    sticker_emoji,
                    bot,
                    packname,
                    packnum)
            elif e.message == "Sticker_png_dimensions":
                im.save(kangsticker, "PNG")
                bot.add_sticker_to_set(
                    user_id=user.id, name=packname, png_sticker=open(
                        'kangsticker.png', 'rb'), emojis=sticker_emoji)
                msg.reply_text(
                    "Sticker successfully added to [pack](t.me/addstickers/%s)" %
                    packname +
                    "\n" +
                    "Emoji is:" +
                    " " +
                    sticker_emoji,
                    parse_mode=ParseMode.MARKDOWN)
            elif e.message == "Invalid sticker emojis":
                msg.reply_text("Invalid emoji(s).")
            elif e.message == "Stickers_too_much":
                msg.reply_text("Max packsize reached. Press F to pay respecc.")
            elif e.message == "Internal Server Error: sticker set not found (500)":
                msg.reply_text(
                    "Sticker successfully added to [pack](t.me/addstickers/%s)" %
                    packname +
                    "\n"
                    "Emoji is:" +
                    " " +
                    sticker_emoji,
                    parse_mode=ParseMode.MARKDOWN)
            print(e)
    else:
        packs = "Please reply to a sticker, or image to kang it!\nOh, by the way. here are your packs:\n"
        if packnum > 0:
            firstpackname = "a" + str(user.id) + "_by_" + bot.username
            for i in range(0, packnum + 1):
                if i == 0:
                    packs += f"[pack](t.me/addstickers/{firstpackname})\n"
                else:
                    packs += f"[pack{i}](t.me/addstickers/{packname})\n"
        else:
            packs += f"[pack](t.me/addstickers/{packname})"
        msg.reply_text(packs, parse_mode=ParseMode.MARKDOWN)
    if os.path.isfile("kangsticker.png"):
        os.remove("kangsticker.png")


def makepack_internal(msg, user, png_sticker, emoji, bot, packname, packnum):
    name = user.first_name
    name = name[:50]
    try:
        extra_version = ""
        if packnum > 0:
            extra_version = " " + str(packnum)
        success = bot.create_new_sticker_set(
            user.id,
            packname,
            f"{name}s Hitsuki pack" +
            extra_version,
            png_sticker=png_sticker,
            emojis=emoji)
    except TelegramError as e:
        print(e)
        if e.message == "Sticker set name is already occupied":
            msg.reply_text(
                "Your pack can be found [here](t.me/addstickers/%s)" %
                packname, parse_mode=ParseMode.MARKDOWN)
        elif e.message == "Peer_id_invalid":
            msg.reply_text("Contact me in PM first.", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Start", url=f"t.me/{bot.username}")]]))
        elif e.message == "Internal Server Error: created sticker set not found (500)":
            msg.reply_text(
                "Sticker pack successfully created. Get it [here](t.me/addstickers/%s)" %
                packname, parse_mode=ParseMode.MARKDOWN)
        return

    if success:
        msg.reply_text(
            "Sticker pack successfully created. Get it [here](t.me/addstickers/%s)" %
            packname, parse_mode=ParseMode.MARKDOWN)
    else:
        msg.reply_text(
            "Failed to create sticker pack. Possibly due to blek mejik.")


__help__ = """
*Group tools:*
 - /id: get the current group id. If used by replying to a message, gets that user's id.
 - /info: get information about a user.
 - /markdownhelp: quick summary of how markdown works in telegram - can only be called in private chats.

*Useful tools:*
 - /paste: Create a paste or a shortened url using [dogbin](https://del.dog)
 - /getpaste: Get the content of a paste or shortened url from [dogbin](https://del.dog)
 - /pastestats: Get stats of a paste or shortened url from [dogbin](https://del.dog)
 - /stickerid: reply message sticker at PM to get ID sticker
 - /getsticker: reply to a sticker to me to upload its raw PNG file.
 - /kang: reply to a sticker to add it to your pack.
 - /ping: check the speed of the bot
 - /tr <from>-<to> <text>: translate text written or reply for any language to the intended language,Â or
 - /tr <to> <text>: translate text written or reply for any language to the intended language
 - /wiki <text>: search for text written from the wikipedia source
 - /ud <text>: search from urban dictionary

*Other things:*
 - /runs: reply a random string from an array of replies.
 - /insults: reply a random string from an array of replies.
 - /slap: slap a user, or get slapped if not a reply.
 - /status: Shows some bot information.
 - /weebify: as a reply to a message, "weebifies" the message.
 - /pat: give a headpat :3
 - /shg or /shrug: pretty self-explanatory.
 - /hug: give a hug and spread the love :)
 - /react: reacts with normal reactions.
 - /happy: reacts with happiness.
 - /angry: reacts angrily.
 - /fortune: give a fortune
 - /status: Get the hitsuki version, python, and APIs used by the bot.
"""

__mod_name__ = "🚀 Hitsuki Extras 🚀"

STICKERID_HANDLER = DisableAbleCommandHandler("stickerid", stickerid)
PING_HANDLER = DisableAbleCommandHandler("ping", ping)
GETLINK_HANDLER = CommandHandler(
    "getlink",
    getlink,
    pass_args=True,
    filters=Filters.user(OWNER_ID))
LEAVECHAT_HANDLER = CommandHandler(["leavechat",
                                    "leavegroup",
                                    "leave"],
                                   leavechat,
                                   pass_args=True,
                                   filters=Filters.user(OWNER_ID))
RAMALAN_HANDLER = DisableAbleCommandHandler(["fortune"], ramalan)
TERJEMAH_HANDLER = DisableAbleCommandHandler(["tr"], terjemah)
WIKIPEDIA_HANDLER = DisableAbleCommandHandler("wiki", wiki)
UD_HANDLER = DisableAbleCommandHandler("ud", urbandictionary, pass_args=True)
LOG_HANDLER = DisableAbleCommandHandler(
    "log", log, filters=Filters.user(OWNER_ID))
REACT_HANDLER = DisableAbleCommandHandler("react", react)
RHAPPY_HANDLER = DisableAbleCommandHandler("happy", rhappy)
RANGRY_HANDLER = DisableAbleCommandHandler("angry", rangry)
GETSTICKER_HANDLER = CommandHandler("getsticker", getsticker)
KANG_HANDLER = DisableAbleCommandHandler("kang", kang, pass_args=True)

dispatcher.add_handler(GETSTICKER_HANDLER)
dispatcher.add_handler(KANG_HANDLER)
dispatcher.add_handler(REACT_HANDLER)
dispatcher.add_handler(RHAPPY_HANDLER)
dispatcher.add_handler(RANGRY_HANDLER)
dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(STICKERID_HANDLER)
dispatcher.add_handler(GETLINK_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
dispatcher.add_handler(RAMALAN_HANDLER)
dispatcher.add_handler(TERJEMAH_HANDLER)
dispatcher.add_handler(WIKIPEDIA_HANDLER)
dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(LOG_HANDLER)
