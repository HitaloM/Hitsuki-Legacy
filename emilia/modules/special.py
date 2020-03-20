import html
import json
import random
import PIL
import os
import urllib
import datetime
from typing import Optional, List
import time
import urbandict

import pyowm
from pyowm import timeutils, exceptions
from googletrans import Translator
import wikipedia
import base64
from bs4 import BeautifulSoup
from emoji import UNICODE_EMOJI

import requests
from telegram.error import BadRequest, Unauthorized
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html, mention_markdown

from emilia import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER, spamcheck
from emilia.__main__ import STATS, USER_INFO
from emilia.modules.disable import DisableAbleCommandHandler
from emilia.modules.helper_funcs.extraction import extract_user
from emilia.modules.helper_funcs.filters import CustomFilters
from emilia.modules.sql import languages_sql as langsql

from emilia.modules.languages import tl
from emilia.modules.helper_funcs.alternate import send_message


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
@spamcheck
def react(update, context):
    message = update.effective_message
    react = random.choice(reactions)
    if message.reply_to_message:
        message.reply_to_message.reply_text(react)
    else:
        message.reply_text(react)


@run_async
@spamcheck
def rhappy(update, context):
    message = update.effective_message
    rhappy = random.choice(reactionhappy)
    if message.reply_to_message:
        message.reply_to_message.reply_text(rhappy)
    else:
        message.reply_text(rhappy)


@run_async
@spamcheck
def rangry(update, context):
    message = update.effective_message
    rangry = random.choice(reactionangry)
    if message.reply_to_message:
        message.reply_to_message.reply_text(rangry)
    else:
        message.reply_text(rangry)


@run_async
@spamcheck
def getsticker(update, context):
	msg = update.effective_message
	chat_id = update.effective_chat.id
	if msg.reply_to_message and msg.reply_to_message.sticker:
		send_message(update.effective_message, "Hai " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
											msg.from_user.id) + ", Silahkan cek file yang anda minta dibawah ini."
											"\nTolong gunakan fitur ini dengan bijak!",
											parse_mode=ParseMode.MARKDOWN)
		context.bot.sendChatAction(chat_id, "upload_document")
		file_id = msg.reply_to_message.sticker.file_id
		newFile = context.bot.get_file(file_id)
		newFile.download('sticker.png')
		context.bot.sendDocument(chat_id, document=open('sticker.png', 'rb'))
		context.bot.sendChatAction(chat_id, "upload_photo")
		context.bot.send_photo(chat_id, photo=open('sticker.png', 'rb'))
		
	else:
		send_message(update.effective_message, "Hai " + "[{}](tg://user?id={})".format(msg.from_user.first_name,
											msg.from_user.id) + ", Tolong balas pesan stiker untuk mendapatkan gambar stiker",
											parse_mode=ParseMode.MARKDOWN)


@run_async
def getlink(update, context):
	args = context.args
	if args:
		chat_id = int(args[0])
	else:
		send_message(update.effective_message, tl(update.effective_message, "Anda sepertinya tidak mengacu pada obrolan"))
	chat = context.bot.getChat(chat_id)
	bot_member = chat.get_member(context.bot.id)
	if bot_member.can_invite_users:
		titlechat = context.bot.get_chat(chat_id).title
		invitelink = context.bot.get_chat(chat_id).invite_link
		send_message(update.effective_message, tl(update.effective_message, "Sukses mengambil link invite di grup {}. \nInvite link : {}").format(titlechat, invitelink))
	else:
		send_message(update.effective_message, tl(update.effective_message, "Saya tidak memiliki akses ke tautan undangan!"))
	
@run_async
def leavechat(update, context):
	args = context.args
	if args:
		chat_id = int(args[0])
	else:
		send_message(update.effective_message, tl(update.effective_message, "Anda sepertinya tidak mengacu pada obrolan"))
	try:
		chat = context.bot.getChat(chat_id)
		titlechat = context.bot.get_chat(chat_id).title
		context.bot.sendMessage(chat_id, tl(update.effective_message, "Selamat tinggal semua 😁"))
		context.bot.leaveChat(chat_id)
		send_message(update.effective_message, tl(update.effective_message, "Saya telah keluar dari grup {}").format(titlechat))

	except BadRequest as excp:
		if excp.message == "Chat not found":
			send_message(update.effective_message, tl(update.effective_message, "Sepertinya saya sudah keluar atau di tendang di grup tersebut"))
		else:
			return

@run_async
@spamcheck
def ping(update, context):
	start_time = time.time()
	test = send_message(update.effective_message, "Pong!")
	end_time = time.time()
	ping_time = float(end_time - start_time)
	context.bot.editMessageText(chat_id=update.effective_chat.id, message_id=test.message_id,
						text=tl(update.effective_message, "Pong!\nKecepatannya: {0:.2f} detik").format(round(ping_time, 2) % 60))

@run_async
@spamcheck
def ramalan(update, context):
	text = ""
	if random.randint(1,10) >= 7:
		text += random.choice(tl(update.effective_message, "RAMALAN_FIRST"))
	text += random.choice(tl(update.effective_message, "RAMALAN_STRINGS"))
	send_message(update.effective_message, text)    

@run_async
@spamcheck
def terjemah(update, context):
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
			if target2 == None:
				deteksibahasa = trl.detect(teks)
				tekstr = trl.translate(teks, dest=target)
				send_message(update.effective_message, tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(deteksibahasa.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
			else:
				tekstr = trl.translate(teks, dest=target2, src=target)
				send_message(update.effective_message, tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(target, target2, tekstr.text), parse_mode=ParseMode.MARKDOWN)
			
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
			if target2 == None:
				deteksibahasa = trl.detect(teks)
				tekstr = trl.translate(teks, dest=target)
				return send_message(update.effective_message, tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(deteksibahasa.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
			else:
				tekstr = trl.translate(teks, dest=target2, src=target)
				send_message(update.effective_message, tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(target, target2, tekstr.text), parse_mode=ParseMode.MARKDOWN)
	except IndexError:
		send_message(update.effective_message, tl(update.effective_message, "Balas pesan atau tulis pesan dari bahasa lain untuk "
											"diterjemahkan kedalam bahasa yang di dituju\n\n"
											"Contoh: `/tr en-id` untuk menerjemahkan dari Bahasa inggris ke Bahasa Indonesia\n"
											"Atau gunakan: `/tr id` untuk deteksi otomatis dan menerjemahkannya kedalam bahasa indonesia"), parse_mode="markdown")
	except ValueError:
		send_message(update.effective_message, tl(update.effective_message, "Bahasa yang di tuju tidak ditemukan!"))
	else:
		return


@run_async
@spamcheck
def wiki(update, context):
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
		send_message(update.effective_message, tl(update.effective_message, "Hasil tidak ditemukan"))
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
					teks += rujuk[x].replace('may refer to', 'dapat merujuk ke')+"\n"
				else:
					teks += rujuk[x]+"\n"
			else:
				teks += "- `"+rujuk[x]+"`\n"
		send_message(update.effective_message, teks, parse_mode="markdown")
		return
	except IndexError:
		send_message(update.effective_message, tl(update.effective_message, "Tulis pesan untuk mencari dari sumber wikipedia"))
		return
	judul = pagewiki.title
	summary = pagewiki.summary
	if update.effective_message.chat.type == "private":
		send_message(update.effective_message, tl(update.effective_message, "Hasil dari {} adalah:\n\n<b>{}</b>\n{}").format(teks, judul, summary), parse_mode=ParseMode.HTML)
	else:
		if len(summary) >= 200:
			judul = pagewiki.title
			summary = summary[:200]+"..."
			button = InlineKeyboardMarkup([[InlineKeyboardButton(text=tl(update.effective_message, "Baca Lebih Lengkap"), url="t.me/{}?start=wiki-{}".format(context.bot.username, teks.replace(' ', '_')))]])
		else:
			button = None
		send_message(update.effective_message, tl(update.effective_message, "Hasil dari {} adalah:\n\n<b>{}</b>\n{}").format(teks, judul, summary), parse_mode=ParseMode.HTML, reply_markup=button)


@run_async
@spamcheck
def urbandictionary(update, context):
	args = context.args
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
					teks = "*Result of {}*\n\n*{}*\n*Meaning:*\n`{}`\n\n*Example:*\n`{}`\n\n".format(text, mean[x].get("word")[:-7], mean[x].get("def"), mean[x].get("example"))
			else:
				for x in range(len(mean)):
					teks = "*Result of {}*\n\n*{}*\n**Meaning:*\n`{}`\n\n*Example:*\n`{}`\n\n".format(text, mean[x].get("word")[:-7], mean[x].get("def"), mean[x].get("example"))
			send_message(update.effective_message, teks, parse_mode=ParseMode.MARKDOWN)
		else:
			send_message(update.effective_message, "{} couldn't be found in urban dictionary!".format(text), parse_mode=ParseMode.MARKDOWN)
	else:
		send_message(update.effective_message, "Use `/ud <text` for search meaning from urban dictionary.", parse_mode=ParseMode.MARKDOWN)

@run_async
def log(update, context):
	message = update.effective_message
	eventdict = message.to_dict()
	jsondump = json.dumps(eventdict, indent=4)
	send_message(update.effective_message, jsondump)

def deEmojify(inputString):
    return inputString.encode('ascii', 'ignore').decode('ascii')


__help__ = "exclusive_help"

__mod_name__ = "🚀 Hitsuki Exclusive 🚀"

PING_HANDLER = DisableAbleCommandHandler("ping", ping)
GETLINK_HANDLER = CommandHandler("getlink", getlink, pass_args=True, filters=Filters.user(OWNER_ID))
LEAVECHAT_HANDLER = CommandHandler(["leavechat", "leavegroup", "leave"], leavechat, pass_args=True, filters=Filters.user(OWNER_ID))
RAMALAN_HANDLER = DisableAbleCommandHandler("fortune", ramalan)
TERJEMAH_HANDLER = DisableAbleCommandHandler(["tr", "tl"], terjemah)
WIKIPEDIA_HANDLER = DisableAbleCommandHandler("wiki", wiki)
UD_HANDLER = DisableAbleCommandHandler("ud", urbandictionary, pass_args=True)
LOG_HANDLER = DisableAbleCommandHandler("log", log, filters=Filters.user(OWNER_ID))
REACT_HANDLER = DisableAbleCommandHandler("react", react)
RHAPPY_HANDLER = DisableAbleCommandHandler("happy", rhappy)
RANGRY_HANDLER = DisableAbleCommandHandler("angry", rangry)

dispatcher.add_handler(REACT_HANDLER)
dispatcher.add_handler(RHAPPY_HANDLER)
dispatcher.add_handler(RANGRY_HANDLER)
dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(GETLINK_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
dispatcher.add_handler(RAMALAN_HANDLER)
dispatcher.add_handler(TERJEMAH_HANDLER)
dispatcher.add_handler(WIKIPEDIA_HANDLER)
dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(LOG_HANDLER)
