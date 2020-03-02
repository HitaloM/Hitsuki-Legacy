import html, time
import re
import threading
import requests
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User, CallbackQuery
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler, run_async, CallbackQueryHandler
from telegram.utils.helpers import mention_markdown, mention_html, escape_markdown

import hitsuki.modules.sql.welcome_sql as sql
from hitsuki import dispatcher, OWNER_ID, LOGGER, spamfilters
from hitsuki.modules.helper_funcs.chat_status import user_admin, is_user_ban_protected
from hitsuki.modules.helper_funcs.filters import CustomFilters
from hitsuki.modules.helper_funcs.misc import build_keyboard, revert_buttons
from hitsuki.modules.helper_funcs.msg_types import get_welcome_type
from hitsuki.modules.helper_funcs.string_handling import markdown_parser, \
	escape_invalid_curly_brackets, extract_time
from hitsuki.modules.log_channel import loggable

import hitsuki.modules.sql.feds_sql as fedsql
from hitsuki.modules.languages import tl
from hitsuki.modules.helper_funcs.alternate import send_message


OWNER_SPECIAL = False
VALID_WELCOME_FORMATTERS = ['first', 'last', 'fullname', 'username', 'id', 'count', 'chatname', 'mention']

ENUM_FUNC_MAP = {
	sql.Types.TEXT.value: dispatcher.bot.send_message,
	sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
	sql.Types.STICKER.value: dispatcher.bot.send_sticker,
	sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
	sql.Types.PHOTO.value: dispatcher.bot.send_photo,
	sql.Types.AUDIO.value: dispatcher.bot.send_audio,
	sql.Types.VOICE.value: dispatcher.bot.send_voice,
	sql.Types.VIDEO.value: dispatcher.bot.send_video
}


# do not async
def send(update, message, keyboard, backup_message):
	chat = update.effective_chat
	cleanserv = sql.clean_service(chat.id)
	reply = update.message.message_id
	# Clean service welcome
	if cleanserv:
		reply = False
	try:
		msg = dispatcher.bot.send_message(chat.id, message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard, reply_to_message_id=reply, disable_web_page_preview=True)
	except IndexError:
		msg = dispatcher.bot.send_message(chat.id, markdown_parser(backup_message +
																  tl(update.effective_message, "\nCatatan: pesan saat ini tidak valid "
																  "karena masalah markdown. Bisa jadi "
																  "karena nama pengguna.")),
												  reply_to_message_id=reply, 
												  parse_mode=ParseMode.MARKDOWN)
	except KeyError:
		msg = dispatcher.bot.send_message(chat.id, markdown_parser(backup_message +
																  tl(update.effective_message, "\nCatatan: pesan saat ini tidak valid "
																  "karena ada masalah dengan beberapa salah tempat. "
																  "Harap perbarui")),
												  reply_to_message_id=reply, 
												  parse_mode=ParseMode.MARKDOWN)
	except BadRequest as excp:
		if excp.message == "Button_url_invalid":
			msg = dispatcher.bot.send_message(chat.id, markdown_parser(backup_message +
																	  tl(update.effective_message, "\nCatatan: pesan saat ini memiliki url yang tidak "
																	  "valid di salah satu tombolnya. Harap perbarui.")),
													  reply_to_message_id=reply, 
													  parse_mode=ParseMode.MARKDOWN)
		elif excp.message == "Unsupported url protocol":
			msg = dispatcher.bot.send_message(chat.id, markdown_parser(backup_message +
																	  tl(update.effective_message, "\nCatatan: pesan saat ini memiliki tombol yang "
																	  "menggunakan protokol url yang tidak didukung "
																	  "oleh telegram. Harap perbarui.")),
													  reply_to_message_id=reply, 
													  parse_mode=ParseMode.MARKDOWN)
		elif excp.message == "Wrong url host":
			msg = dispatcher.bot.send_message(chat.id, markdown_parser(backup_message +
																	  tl(update.effective_message, "\nCatatan: pesan saat ini memiliki beberapa url "
																	  "yang buruk. Harap perbarui.")),
													  reply_to_message_id=reply, 
													  parse_mode=ParseMode.MARKDOWN)
			LOGGER.warning(message)
			LOGGER.warning(keyboard)
			LOGGER.exception("Could not parse! got invalid url host errors")
		else:
			try:
				msg = dispatcher.bot.send_message(chat.id, markdown_parser(backup_message +
																	  tl(update.effective_message, "\nCatatan: Terjadi kesalahan saat mengirim pesan "
																	  "kustom. Harap perbarui.")),
													  reply_to_message_id=reply, 
													  parse_mode=ParseMode.MARKDOWN)
				LOGGER.exception("ERROR!")
			except BadRequest:
				print("Cannot send welcome msg, bot is muted!")
				return ""
	return msg


@run_async
def new_member(bot: Bot, update: Update):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]

	should_welc, cust_welcome, cust_content, welc_type = sql.get_welc_pref(chat.id)
	cust_welcome = markdown_to_html(cust_welcome)

	isAllowed = sql.isWhitelisted(str(chat.id))

	if isAllowed or user.id in SUDO_USERS:
		sql.whitelistChat(str(chat.id))
	else:
		msg.reply_text("This group is not whitelisted to use the bot, sorry.")
		bot.leave_chat(int(chat.id))
		return

	cleanserv = sql.clean_service(chat.id)
	if cleanserv:
		new_members = update.effective_message.new_chat_members
		for new_mem in new_members:
			try:
				dispatcher.bot.delete_message(chat.id, update.message.message_id)
			except BadRequest:
				pass
	if should_welc:
		sent = None
		new_members = update.effective_message.new_chat_members
		for new_mem in new_members:
			# Give the owner a special welcome
			if OWNER_SPECIAL and new_mem.id == OWNER_ID:
				if cleanserv:
					bot.send_message(chat.id, tl(update.effective_message, "Master telah pulang! Mari kita mulai pesta ini! 😆"))
				else:
					send_message(update.effective_message, tl(update.effective_message, "Master telah pulang! Mari kita mulai pesta ini! 😆"))
				continue

			# Don't welcome yourself
			elif new_mem.id == bot.id:
				continue

			else:
				# If welcome message is media, send with appropriate function
				if welc_type != sql.Types.TEXT and welc_type != sql.Types.BUTTON_TEXT:
					reply = update.message.message_id
					# Clean service welcome
					if cleanserv:
						reply = False
					# Formatting text
					first_name = new_mem.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.
					if new_mem.last_name:
						fullname = "{} {}".format(first_name, new_mem.last_name)
					else:
						fullname = first_name
					count = chat.get_members_count()
					mention = mention_markdown(new_mem.id, first_name)
					if new_mem.username:
						username = "@" + escape_markdown(new_mem.username)
					else:
						username = mention
					if cust_welcome:
						formatted_text = cust_welcome.format(first=escape_markdown(first_name),
											  last=escape_markdown(new_mem.last_name or first_name),
											  fullname=escape_markdown(fullname), username=username, mention=mention,
											  count=count, chatname=escape_markdown(chat.title), id=new_mem.id)
					else:
						formatted_text = ""
					# Build keyboard
					buttons = sql.get_welc_buttons(chat.id)
					keyb = build_keyboard(buttons)
					getsec, mutetime, custom_text = sql.welcome_security(chat.id)

					# If user ban protected don't apply security on him
					if is_user_ban_protected(chat, new_mem.id, chat.get_member(new_mem.id)):
						pass
					elif getsec:
						# If mute time is turned on
						if mutetime:
							if mutetime[:1] == "0":
								try:
									bot.restrict_chat_member(chat.id, new_mem.id, can_send_messages=False)
									canrest = True
								except BadRequest:
									canrest = False
							else:
								mutetime = extract_time(update.effective_message, mutetime)
								try:
									bot.restrict_chat_member(chat.id, new_mem.id, until_date=mutetime, can_send_messages=False)
									canrest = True
								except BadRequest:
									canrest = False
						# If security welcome is turned on
						if canrest:
							sql.add_to_userlist(chat.id, new_mem.id)
							keyb.append([InlineKeyboardButton(text=str(custom_text), callback_data="check_bot_({})".format(new_mem.id))])
					keyboard = InlineKeyboardMarkup(keyb)
					# Send message
					try:
						sent = ENUM_FUNC_MAP[welc_type](chat.id, cust_content, caption=formatted_text, reply_markup=keyboard, parse_mode="markdown", reply_to_message_id=reply)
					except BadRequest:
						sent = send_message(update.effective_message, tl(update.effective_message, "Catatan: Terjadi kesalahan saat mengirim pesan kustom. Harap perbarui."))
					return
				else:
					# else, move on
					first_name = new_mem.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.

					if cust_welcome:
						if new_mem.last_name:
							fullname = "{} {}".format(first_name, new_mem.last_name)
						else:
							fullname = first_name
						count = chat.get_members_count()
						mention = mention_markdown(new_mem.id, first_name)
						if new_mem.username:
							username = "@" + escape_markdown(new_mem.username)
						else:
							username = mention

						valid_format = escape_invalid_curly_brackets(cust_welcome, VALID_WELCOME_FORMATTERS)
						if valid_format:
							res = valid_format.format(first=escape_markdown(first_name),
												  last=escape_markdown(new_mem.last_name or first_name),
												  fullname=escape_markdown(fullname), username=username, mention=mention,
												  count=count, chatname=escape_markdown(chat.title), id=new_mem.id)
						else:
							res = ""
						buttons = sql.get_welc_buttons(chat.id)
						keyb = build_keyboard(buttons)
					else:
						res = sql.DEFAULT_WELCOME.format(first=first_name)
						keyb = []

					getsec, mutetime, custom_text = sql.welcome_security(chat.id)
					
					# If user ban protected don't apply security on him
					if is_user_ban_protected(chat, new_mem.id, chat.get_member(new_mem.id)):
						pass
					elif getsec:
						if mutetime:
							if mutetime[:1] == "0":
								try:
									bot.restrict_chat_member(chat.id, new_mem.id, can_send_messages=False)
									canrest = True
								except BadRequest:
									canrest = False
							else:
								mutetime = extract_time(update.effective_message, mutetime)
								try:
									bot.restrict_chat_member(chat.id, new_mem.id, until_date=mutetime, can_send_messages=False)
									canrest = True
								except BadRequest:
									canrest = False
						if canrest:
							sql.add_to_userlist(chat.id, new_mem.id)
							keyb.append([InlineKeyboardButton(text=str(custom_text), callback_data="check_bot_({})".format(new_mem.id))])
					keyboard = InlineKeyboardMarkup(keyb)

					sent = send(update, res, keyboard,
								sql.DEFAULT_WELCOME.format(first=first_name))  # type: Optional[Message]

				
			prev_welc = sql.get_clean_pref(chat.id)
			if prev_welc:
				try:
					if int(prev_welc) != 1:
						bot.delete_message(chat.id, prev_welc)
				except BadRequest as excp:
				   pass

				if sent:
					sql.set_clean_welcome(chat.id, sent.message_id)

	fed_id = fedsql.get_fed_id(chat.id)
	if fed_id == "TeamNusantaraDevs":
		new_members = update.effective_message.new_chat_members
		for new_mem in new_members:
			# CAS Security thread
			t = threading.Thread(target=check_cas, args=(bot, new_mem.id, new_mem, update.effective_message,))
			t.start()


@run_async
def check_bot_button(bot: Bot, update: Update):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	query = update.callback_query  # type: Optional[CallbackQuery]
	match = re.match(r"check_bot_\((.+?)\)", query.data)
	user_id = int(match.group(1))
	message = update.effective_message  # type: Optional[Message]
	print("-> {} was clicked welcome sec button".format(user.id))

	# This method will unmute user when that user is clicked welc security button
	# It has two method, so select one method. I'm using first method as default.

	# With second script, bot will edit welcome message and remove welcome security button
	# But when muted user in old welcomes, bot will remove that button,
	# and then new member will not have welcome security button.
	# The problem is bot using list of new member which has been muted,
	# and when that user is match, bot will response True and unmute him/her.
	# All we need is using different filter, it easy but old member has muted by
	# welcome security is no longer unmuted on any welcome security button,
	# need to search their welcome button to get unmute.
	# And you will need two decision, unmute specific user or unmute all user
	# who has muted by security button.
	# Also you can remove add_to_userlist and rm_from_userlist script
	# if you want to use second method since it unused.

	# PLEASE SELECT ONE
	# use """ to set it as comment and disable that script

	# => Use this if you want to unmute user who has muted by welcome security
	getalluser = sql.get_chat_userlist(chat.id)
	if user.id in getalluser:
		try:
			query.answer(text=tl(update.effective_message, "Kamu telah disuarakan!"))
		except BadRequest as err:
			print("-> Failed: {}".format(err))
			return
		# Unmute user
		bot.restrict_chat_member(chat.id, user.id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
		sql.rm_from_userlist(chat.id, user.id)
	else:
		print("Not new user")
		try:
			query.answer(text=tl(update.effective_message, "Kamu bukan pengguna baru!"))
		except BadRequest as err:
			print("-> Failed: {}".format(err))
			return

	# => Or use this to unmute specific user and remove that security button
	"""
	if int(user.id) != int(user_id):
		print("Not that user")
		query.answer(text=tl(update.effective_message, "Kamu bukan pengguna yang di tuju!"))
		return
	bot.restrict_chat_member(chat.id, user.id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
	sql.rm_from_userlist(chat.id, user.id)
	should_welc, cust_welcome, cust_content, welc_type = sql.get_welc_pref(chat.id)
	# If welcome message is media, send with appropriate function
	if welc_type != sql.Types.TEXT and welc_type != sql.Types.BUTTON_TEXT:
		# Formatting text
		first_name = query.from_user.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.
		if query.from_user.last_name:
			fullname = "{} {}".format(first_name, query.from_user.last_name)
		else:
			fullname = first_name
		count = chat.get_members_count()
		mention = mention_markdown(query.from_user.id, first_name)
		if query.from_user.username:
			username = "@" + escape_markdown(query.from_user.username)
		else:
			username = mention
		formatted_text = cust_welcome.format(first=escape_markdown(first_name),
											 last=escape_markdown(query.from_user.last_name or first_name),
											 fullname=escape_markdown(fullname), username=username, mention=mention,
											 count=count, chatname=escape_markdown(chat.title), id=query.from_user.id)
		# Build keyboard
		buttons = sql.get_welc_buttons(chat.id)
		keyb = build_keyboard(buttons)
		getsec, mutetime, custom_text = sql.welcome_security(chat.id)
		keyboard = InlineKeyboardMarkup(keyb)
		# Send message
		try:
			if welc_type != sql.Types.STICKER or welc_type != sql.Types.VOICE:
				bot.editMessageCaption(chat.id, message_id=query.message.message_id, caption=formatted_text, reply_markup=keyboard, parse_mode="markdown")
		except BadRequest:
			pass
		query.answer(text=tl(update.effective_message, "Kamu telah disuarakan!"))
		return
	# else, move on
	first_name = query.from_user.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.
	if cust_welcome:
		if query.from_user.last_name:
			fullname = "{} {}".format(first_name, query.from_user.last_name)
		else:
			fullname = first_name
		count = chat.get_members_count()
		mention = mention_markdown(query.from_user.id, first_name)
		if query.from_user.username:
			username = "@" + escape_markdown(query.from_user.username)
		else:
			username = mention

		valid_format = escape_invalid_curly_brackets(cust_welcome, VALID_WELCOME_FORMATTERS)
		res = valid_format.format(first=escape_markdown(first_name),
								  last=escape_markdown(query.from_user.last_name or first_name),
								  fullname=escape_markdown(fullname), username=username, mention=mention,
								  count=count, chatname=escape_markdown(chat.title), id=query.from_user.id)
		buttons = sql.get_welc_buttons(chat.id)
		keyb = build_keyboard(buttons)
	else:
		res = sql.DEFAULT_WELCOME.format(first=first_name)
		keyb = []
	keyboard = InlineKeyboardMarkup(keyb)
	bot.editMessageText(chat.id, message_id=query.message.message_id, text=res, reply_markup=keyboard, parse_mode="markdown")
	query.answer(text=tl(update.effective_message, "Kamu telah disuarakan!"))
	"""
	#TODO need kick users after 2 hours and remove message 


@run_async
def left_member(bot: Bot, update: Update):
	chat = update.effective_chat  # type: Optional[Chat]
	should_goodbye, cust_goodbye, cust_content, goodbye_type = sql.get_gdbye_pref(chat.id)
	if should_goodbye:
		left_mem = update.effective_message.left_chat_member
		if left_mem:
			# Ignore bot being kicked
			if left_mem.id == bot.id:
				return

			# Give the owner a special goodbye
			if OWNER_SPECIAL and left_mem.id == OWNER_ID:
				send_message(update.effective_message, tl(update.effective_message, "Selamat jalan master 😢"))
				return

			# if media goodbye, use appropriate function for it
			if goodbye_type != sql.Types.TEXT and goodbye_type != sql.Types.BUTTON_TEXT:
				reply = update.message.message_id
				cleanserv = sql.clean_service(chat.id)
				# Clean service welcome
				if cleanserv:
					try:
						dispatcher.bot.delete_message(chat.id, update.message.message_id)
					except BadRequest:
						pass
					reply = False
				# Formatting text
				first_name = left_mem.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.
				if left_mem.last_name:
					fullname = "{} {}".format(first_name, left_mem.last_name)
				else:
					fullname = first_name
				count = chat.get_members_count()
				mention = mention_markdown(left_mem.id, first_name)
				if left_mem.username:
					username = "@" + escape_markdown(left_mem.username)
				else:
					username = mention
				if cust_goodbye:
					formatted_text = cust_goodbye.format(first=escape_markdown(first_name),
											  last=escape_markdown(left_mem.last_name or first_name),
											  fullname=escape_markdown(fullname), username=username, mention=mention,
											  count=count, chatname=escape_markdown(chat.title), id=left_mem.id)
				else:
					formatted_text = ""
				# Build keyboard
				buttons = sql.get_gdbye_buttons(chat.id)
				keyb = build_keyboard(buttons)
				keyboard = InlineKeyboardMarkup(keyb)
				# Send message
				try:
					ENUM_FUNC_MAP[goodbye_type](chat.id, cust_content, caption=formatted_text, reply_markup=keyboard, parse_mode="markdown", reply_to_message_id=reply)
				except BadRequest:
					send_message(update.effective_message, tl(update.effective_message, "Catatan: Terjadi kesalahan saat mengirim pesan kustom. Harap perbarui."))
				return

			first_name = left_mem.first_name or "PersonWithNoName"  # edge case of empty name - occurs for some bugs.
			if cust_goodbye:
				if left_mem.last_name:
					fullname = "{} {}".format(first_name, left_mem.last_name)
				else:
					fullname = first_name
				count = chat.get_members_count()
				mention = mention_markdown(left_mem.id, first_name)
				if left_mem.username:
					username = "@" + escape_markdown(left_mem.username)
				else:
					username = mention

				valid_format = escape_invalid_curly_brackets(cust_goodbye, VALID_WELCOME_FORMATTERS)
				if valid_format:
					res = valid_format.format(first=escape_markdown(first_name),
										  last=escape_markdown(left_mem.last_name or first_name),
										  fullname=escape_markdown(fullname), username=username, mention=mention,
										  count=count, chatname=escape_markdown(chat.title), id=left_mem.id)
				else:
					res = ""
				buttons = sql.get_gdbye_buttons(chat.id)
				keyb = build_keyboard(buttons)

			else:
				res = sql.DEFAULT_GOODBYE
				keyb = []

			keyboard = InlineKeyboardMarkup(keyb)

			send(update, res, keyboard, sql.DEFAULT_GOODBYE)


@run_async
@user_admin
def security(bot: Bot, update: Update, args: List[str]) -> str:
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat = update.effective_chat  # type: Optional[Chat]
	getcur, cur_value, cust_text = sql.welcome_security(chat.id)
	if len(args) >= 1:
		var = args[0].lower()
		if (var == "yes" or var == "ya" or var == "on"):
			check = bot.getChatMember(chat.id, bot.id)
			if check.status == 'member' or check['can_restrict_members'] == False:
				text = tl(update.effective_message, "Saya tidak bisa membatasi orang di sini! Pastikan saya admin agar bisa membisukan seseorang!")
				send_message(update.effective_message, text, parse_mode="markdown")
				return ""
			sql.set_welcome_security(chat.id, True, str(cur_value), cust_text)
			send_message(update.effective_message, tl(update.effective_message, "Keamanan untuk member baru di aktifkan!"))
		elif (var == "no" or var == "ga" or var == "off"):
			sql.set_welcome_security(chat.id, False, str(cur_value), cust_text)
			send_message(update.effective_message, tl(update.effective_message, "Di nonaktifkan, saya tidak akan membisukan member masuk lagi"))
		else:
			send_message(update.effective_message, tl(update.effective_message, "Silakan tulis `on`/`ya`/`off`/`ga`!"), parse_mode=ParseMode.MARKDOWN)
	else:
		getcur, cur_value, cust_text = sql.welcome_security(chat.id)
		if cur_value[:1] == "0":
			cur_value = tl(update.effective_message, "Selamanya")
		text = tl(update.effective_message, "Pengaturan saat ini adalah:\nWelcome security: `{}`\nMember akan di mute selama: `{}`\nTombol unmute custom: `{}`").format(getcur, cur_value, cust_text)
		send_message(update.effective_message, text, parse_mode="markdown")


@run_async
@user_admin
def security_mute(bot: Bot, update: Update, args: List[str]) -> str:
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat = update.effective_chat  # type: Optional[Chat]
	message = update.effective_message  # type: Optional[Message]
	getcur, cur_value, cust_text = sql.welcome_security(chat.id)
	if len(args) >= 1:
		var = args[0]
		if var[:1] == "0":
			mutetime = "0"
			sql.set_welcome_security(chat.id, getcur, "0", cust_text)
			text = tl(update.effective_message, "Setiap member baru akan di bisukan selamanya sampai dia menekan tombol selamat datang!")
		else:
			mutetime = extract_time(message, var)
			if mutetime == "":
				return
			sql.set_welcome_security(chat.id, getcur, str(var), cust_text)
			text = tl(update.effective_message, "Setiap member baru akan di bisukan selama {} sampai dia menekan tombol selamat datang!").format(var)
		send_message(update.effective_message, text)
	else:
		if str(cur_value) == "0":
			send_message(update.effective_message, tl(update.effective_message, "Pengaturan saat ini: member baru akan di bisukan selamanya sampai dia menekan tombol selamat datang!"))
		else:
			send_message(update.effective_message, tl(update.effective_message, "Pengaturan saat ini: member baru akan di bisukan selama {} sampai dia menekan tombol selamat datang!").format(cur_value))


@run_async
@user_admin
def security_text(bot: Bot, update: Update, args: List[str]) -> str:
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat = update.effective_chat  # type: Optional[Chat]
	message = update.effective_message  # type: Optional[Message]
	getcur, cur_value, cust_text = sql.welcome_security(chat.id)
	if len(args) >= 1:
		text = " ".join(args)
		sql.set_welcome_security(chat.id, getcur, cur_value, text)
		text = tl(update.effective_message, "Tombol custom teks telah di ubah menjadi: `{}`").format(text)
		send_message(update.effective_message, text, parse_mode="markdown")
	else:
		send_message(update.effective_message, tl(update.effective_message, "Tombol teks security saat ini adalah: `{}`").format(cust_text), parse_mode="markdown")


@run_async
@user_admin
def security_text_reset(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat = update.effective_chat  # type: Optional[Chat]
	message = update.effective_message  # type: Optional[Message]
	getcur, cur_value, cust_text = sql.welcome_security(chat.id)
	sql.set_welcome_security(chat.id, getcur, cur_value, tl(update.effective_message, "Klik disini untuk mensuarakan"))
	send_message(update.effective_message, tl(update.effective_message, "Tombol custom teks security telah di reset menjadi: `Klik disini untuk mensuarakan`"), parse_mode="markdown")


@run_async
@user_admin
def cleanservice(bot: Bot, update: Update, args: List[str]) -> str:
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat = update.effective_chat  # type: Optional[Chat]
	if chat.type != chat.PRIVATE:
		if len(args) >= 1:
			var = args[0].lower()
			if (var == "no" or var == "off" or var == "tidak"):
				sql.set_clean_service(chat.id, False)
				send_message(update.effective_message, tl(update.effective_message, "Saya meninggalkan pesan layanan"))
			elif(var == "yes" or var == "ya" or var == "on"):
				sql.set_clean_service(chat.id, True)
				send_message(update.effective_message, tl(update.effective_message, "Saya akan membersihkan pesan layanan"))
			else:
				send_message(update.effective_message, tl(update.effective_message, "Silakan masukkan yes/ya atau no/tidak!"), parse_mode=ParseMode.MARKDOWN)
		else:
			send_message(update.effective_message, tl(update.effective_message, "Silakan masukkan yes/ya atau no/tidak!"), parse_mode=ParseMode.MARKDOWN)
	else:
		curr = sql.clean_service(chat.id)
		if curr:
			send_message(update.effective_message, tl(update.effective_message, "Saat ini saya akan membersihkan `x joined the group` ketika ada member baru."), parse_mode=ParseMode.MARKDOWN)
		else:
			send_message(update.effective_message, tl(update.effective_message, "Saat ini saya tidak akan membersihkan `x joined the group` ketika ada member baru."), parse_mode=ParseMode.MARKDOWN)



@run_async
@user_admin
def welcome(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]
	# if no args, show current replies.
	if len(args) == 0 or args[0].lower() == "noformat":
		noformat = args and args[0].lower() == "noformat"
		pref, welcome_m, cust_content, welcome_type = sql.get_welc_pref(chat.id)
		prev_welc = sql.get_clean_pref(chat.id)
		if prev_welc:
			prev_welc = True
		else:
			prev_welc = False
		cleanserv = sql.clean_service(chat.id)
		getcur, cur_value, cust_text = sql.welcome_security(chat.id)
		if getcur:
			welcsec = tl(update.effective_message, "Aktif ")
		else:
			welcsec = tl(update.effective_message, "Tidak aktif ")
		if cur_value[:1] == "0":
			welcsec += tl(update.effective_message, "(di bisukan selamanya sampai menekan tombol unmute)")
		else:
			welcsec += tl(update.effective_message, "(di bisukan selama {})").format(cur_value)
		text = tl(update.effective_message, "Obrolan ini diatur dengan setelan selamat datang: `{}`\n").format(pref)
		text += tl(update.effective_message, "Saat ini Saya menghapus pesan selamat datang lama: `{}`\n").format(prev_welc)
		text += tl(update.effective_message, "Saat ini Saya menghapus layanan pesan: `{}`\n").format(cleanserv)
		text += tl(update.effective_message, "Saat ini saya membisukan pengguna ketika mereka bergabung: `{}`\n").format(welcsec)
		text += tl(update.effective_message, "Tombol welcomemute akan mengatakan: `{}`\n").format(cust_text)
		text += tl(update.effective_message, "\n*Pesan selamat datang (tidak mengisi {{}}) adalah:*")
		send_message(update.effective_message, text,
			parse_mode=ParseMode.MARKDOWN)

		buttons = sql.get_welc_buttons(chat.id)
		if welcome_type == sql.Types.BUTTON_TEXT or welcome_type == sql.Types.TEXT:
			if noformat:
				welcome_m += revert_buttons(buttons)
				send_message(update.effective_message, welcome_m)

			else:
				if buttons:
					keyb = build_keyboard(buttons)
					keyboard = InlineKeyboardMarkup(keyb)
				else:
					keyboard = None

				send(update, welcome_m, keyboard, sql.DEFAULT_WELCOME)

		else:
			if noformat:
				welcome_m += revert_buttons(buttons)
				ENUM_FUNC_MAP[welcome_type](chat.id, cust_content, caption=welcome_m)

			else:
				if buttons:
					keyb = build_keyboard(buttons)
					keyboard = InlineKeyboardMarkup(keyb)
				else:
					keyboard = None
				ENUM_FUNC_MAP[welcome_type](chat.id, cust_content, caption=welcome_m, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

	elif len(args) >= 1:
		if args[0].lower() in ("on", "yes"):
			sql.set_welc_preference(str(chat.id), True)
			send_message(update.effective_message, tl(update.effective_message, "Saya akan sopan 😁"))

		elif args[0].lower() in ("off", "no"):
			sql.set_welc_preference(str(chat.id), False)
			send_message(update.effective_message, tl(update.effective_message, "Aku ngambek, tidak menyapa lagi. 😣"))

		else:
			# idek what you're writing, say yes or no
			send_message(update.effective_message, tl(update.effective_message, "Saya hanya mengerti 'on/yes' atau 'off/no' saja!"))


@run_async
@user_admin
def goodbye(bot: Bot, update: Update, args: List[str]):
	chat = update.effective_chat  # type: Optional[Chat]

	if len(args) == 0 or args[0] == "noformat":
		noformat = args and args[0] == "noformat"
		pref, goodbye_m, cust_content, goodbye_type = sql.get_gdbye_pref(chat.id)
		send_message(update.effective_message, 
			tl(update.effective_message, "Obrolan ini memiliki setelan selamat tinggal yang disetel ke: `{}`.\n*Pesan selamat tinggal "
			"(tidak mengisi {{}}) adalah:*").format(pref),
			parse_mode=ParseMode.MARKDOWN)

		buttons = sql.get_gdbye_buttons(chat.id)
		if goodbye_type == sql.Types.BUTTON_TEXT:
			if noformat:
				goodbye_m += revert_buttons(buttons)
				send_message(update.effective_message, goodbye_m)

			else:
				if buttons:
					keyb = build_keyboard(buttons)
					keyboard = InlineKeyboardMarkup(keyb)
				else:
					keyboard = None

				send(update, goodbye_m, keyboard, sql.DEFAULT_GOODBYE)

		else:
			if noformat:
				goodbye_m += revert_buttons(buttons)
				ENUM_FUNC_MAP[goodbye_type](chat.id, cust_content, caption=goodbye_m)
				
			else:
				if buttons:
					keyb = build_keyboard(buttons)
					keyboard = InlineKeyboardMarkup(keyb)
				else:
					keyboard = None
				ENUM_FUNC_MAP[goodbye_type](chat.id, cust_content, caption=goodbye_m, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

	elif len(args) >= 1:
		if args[0].lower() in ("on", "yes"):
			sql.set_gdbye_preference(str(chat.id), True)
			send_message(update.effective_message, tl(update.effective_message, "Aku akan menyesal jika orang-orang pergi!"))

		elif args[0].lower() in ("off", "no"):
			sql.set_gdbye_preference(str(chat.id), False)
			send_message(update.effective_message, tl(update.effective_message, "Mereka pergi, mereka sudah mati bagi saya."))

		else:
			# idk what you're writing, say yes or no
			send_message(update.effective_message, tl(update.effective_message, "Saya hanya mengerti 'on/yes' atau 'off/no' saja!"))


@run_async
@user_admin
@loggable
def set_welcome(bot: Bot, update: Update) -> str:
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]

	# If user is not set text and not reply a message
	if not msg.reply_to_message:
		if len(msg.text.split()) == 1:
			send_message(update.effective_message, tl(update.effective_message, "Anda harus memberikan isi dalam pesan selamat datang!\nKetik `/welcomehelp` untuk beberapa bantuan pada welcome"), parse_mode="markdown")
			return ""

	text, data_type, content, buttons = get_welcome_type(msg)

	if data_type is None:
		send_message(update.effective_message, tl(update.effective_message, "Anda tidak menentukan apa yang harus dibalas!"))
		return ""

	sql.set_custom_welcome(chat.id, content, text, data_type, buttons)
	send_message(update.effective_message, tl(update.effective_message, "Berhasil mengatur pesan sambutan kustom!"))

	return "<b>{}:</b>" \
		   "\n#SET_WELCOME" \
		   "\n<b>Admin:</b> {}" \
		   "\nSet a welcome message.".format(html.escape(chat.title),
											   mention_html(user.id, user.first_name))


@run_async
@user_admin
@loggable
def reset_welcome(bot: Bot, update: Update) -> str:
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	sql.set_custom_welcome(chat.id, None, sql.DEFAULT_WELCOME, sql.Types.TEXT)
	send_message(update.effective_message, tl(update.effective_message, "Berhasil menyetel ulang pesan sambutan ke default!"))
	return "<b>{}:</b>" \
		   "\n#RESET_WELCOME" \
		   "\n<b>Admin:</b> {}" \
		   "\nReset the welcome message to default.".format(html.escape(chat.title),
															mention_html(user.id, user.first_name))


@run_async
@user_admin
@loggable
def set_goodbye(bot: Bot, update: Update) -> str:
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]

	# If user is not set text and not reply a message
	if not msg.reply_to_message:
		if len(msg.text.split()) == 1:
			send_message(update.effective_message, tl(update.effective_message, "Anda harus memberikan isi dalam pesan selamat datang!\nKetik `/welcomehelp` untuk beberapa bantuan pada welcome"), parse_mode="markdown")
			return ""

	text, data_type, content, buttons = get_welcome_type(msg)

	if data_type is None:
		send_message(update.effective_message, tl(update.effective_message, "Anda tidak menentukan apa yang harus dibalas!"))
		return ""

	sql.set_custom_gdbye(chat.id, content, text, data_type, buttons)
	send_message(update.effective_message, tl(update.effective_message, "Berhasil mengatur pesan selamat tinggal kustom!"))
	return "<b>{}:</b>" \
		   "\n#SET_GOODBYE" \
		   "\n<b>Admin:</b> {}" \
		   "\nSet a goodbye message.".format(html.escape(chat.title),
											   mention_html(user.id, user.first_name))


@run_async
@user_admin
@loggable
def reset_goodbye(bot: Bot, update: Update) -> str:
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	sql.set_custom_gdbye(chat.id, sql.DEFAULT_GOODBYE, sql.Types.TEXT)
	send_message(update.effective_message, tl(update.effective_message, "Berhasil me-reset pesan selamat tinggal ke default!"))
	return "<b>{}:</b>" \
		   "\n#RESET_GOODBYE" \
		   "\n<b>Admin:</b> {}" \
		   "\nSetel ulang pesan selamat tinggal.".format(html.escape(chat.title),
												 mention_html(user.id, user.first_name))


@run_async
@user_admin
@loggable
def clean_welcome(bot: Bot, update: Update, args: List[str]) -> str:
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]

	if not args:
		clean_pref = sql.get_clean_pref(chat.id)
		if clean_pref:
			send_message(update.effective_message, tl(update.effective_message, "Saya *akan* menghapus pesan selamat datang hingga dua hari."), parse_mode="markdown")
		else:
			send_message(update.effective_message, tl(update.effective_message, "Saat ini saya *tidak akan* menghapus pesan selamat datang yang lama!"), parse_mode="markdown")
		return ""

	if args[0].lower() in ("on", "yes"):
		sql.set_clean_welcome(str(chat.id), True)
		send_message(update.effective_message, tl(update.effective_message, "Saya *akan* mencoba menghapus pesan selamat datang yang lama!"), parse_mode="markdown")
		return "<b>{}:</b>" \
			   "\n#CLEAN_WELCOME" \
			   "\n<b>Admin:</b> {}" \
			   "\nHas toggled clean welcomes to <code>ON</code>.".format(html.escape(chat.title),
																							 mention_html(user.id, user.first_name))
	elif args[0].lower() in ("off", "no"):
		sql.set_clean_welcome(str(chat.id), False)
		send_message(update.effective_message, tl(update.effective_message, "Saya *tidak akan* menghapus pesan selamat datang yang lama."), parse_mode="markdown")
		return "<b>{}:</b>" \
			   "\n#CLEAN_WELCOME" \
			   "\n<b>Admin:</b> {}" \
			   "\nHas toggled clean welcomes to <code>OFF</code>.".format(html.escape(chat.title),
																		  mention_html(user.id, user.first_name))
	else:
		# idk what you're writing, say yes or no
		send_message(update.effective_message, tl(update.effective_message, "Saya hanya mengerti 'on/yes' or 'off/no' saja!"))
		return ""


@run_async
@user_admin
def welcome_help(bot: Bot, update: Update):
	spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
	if spam == True:
		return
	send_message(update.effective_message, tl(update.effective_message, "WELC_HELP_TXT").format(dispatcher.bot.username), parse_mode=ParseMode.MARKDOWN)


# TODO: get welcome data from group butler snap
# def __import_data__(chat_id, data):
#     welcome = data.get('info', {}).get('rules')
#     welcome = welcome.replace('$username', '{username}')
#     welcome = welcome.replace('$name', '{fullname}')
#     welcome = welcome.replace('$id', '{id}')
#     welcome = welcome.replace('$title', '{chatname}')
#     welcome = welcome.replace('$surname', '{lastname}')
#     welcome = welcome.replace('$rules', '{rules}')
#     sql.set_custom_welcome(chat_id, welcome, sql.Types.TEXT)


def __migrate__(old_chat_id, new_chat_id):
	sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
	welcome_pref, _, _, _ = sql.get_welc_pref(chat_id)
	goodbye_pref, _, _, _ = sql.get_gdbye_pref(chat_id)
	cleanserv = sql.clean_service(chat_id)
	return tl(user_id, "Obrolan ini memiliki preferensi `{}` untuk pesan sambutan.\n" \
		   "Untuk preferensi pesan selamat tinggal `{}`.\n" \
		   "Bot `{}` menghapus notifikasi member masuk/keluar secara otomatis").format(welcome_pref, goodbye_pref, cleanserv)

"""
def __chat_settings_btn__(chat_id, user_id):
	welcome_pref, _, _, _ = sql.get_welc_pref(chat_id)
	goodbye_pref, _, _, _ = sql.get_gdbye_pref(chat_id)
	cleanserv = sql.clean_service(chat_id)
	if welcome_pref:
		welc = "✅ Aktif"
	else:
		welc = "❎ Tidak Aktif"
	if goodbye_pref:
		gdby = "✅ Aktif"
	else:
		gdby = "❎ Tidak Aktif"
	if cleanserv:
		clserv = "✅ Aktif"
	else:
		clserv = "❎ Tidak Aktif"
	button = []
	button.append([InlineKeyboardButton(text="Selamat datang", callback_data="set_welc=w?|{}".format(chat_id)),
		InlineKeyboardButton(text=welc, callback_data="set_welc=w|{}".format(chat_id))])
	button.append([InlineKeyboardButton(text="Selamat tinggal", callback_data="set_welc=g?|{}".format(chat_id)),
		InlineKeyboardButton(text=gdby, callback_data="set_welc=g|{}".format(chat_id))])
	button.append([InlineKeyboardButton(text="Clean Service", callback_data="set_welc=s?|{}".format(chat_id)),
		InlineKeyboardButton(text=clserv, callback_data="set_welc=s|{}".format(chat_id))])
	return button

def WELC_EDITBTN(bot: Bot, update: Update):
	query = update.callback_query
	user = update.effective_user
	print("User {} clicked button WELC EDIT".format(user.id))
	chat_id = query.data.split("|")[1]
	data = query.data.split("=")[1].split("|")[0]
	if data == "w?":
		bot.answerCallbackQuery(query.id, "Bot akan mengirim pesan setiap ada member baru masuk jika di aktifkan.", show_alert=True)
	if data == "g?":
		bot.answerCallbackQuery(query.id, "Bot akan mengirim pesan setiap ada member yang keluar jika di aktifkan. Akan aktif hanya untuk grup dibawah 100 member.", show_alert=True)
	if data == "s?":
		bot.answerCallbackQuery(query.id, "Bot akan menghapus notifikasi member masuk atau member keluar secara otomatis jika di aktifkan.", show_alert=True)
	if data == "w":
		welcome_pref, _, _, _ = sql.get_welc_pref(chat_id)
		goodbye_pref, _, _, _ = sql.get_gdbye_pref(chat_id)
		cleanserv = sql.clean_service(chat_id)
		if welcome_pref:
			welc = "❎ Tidak Aktif"
			sql.set_welc_preference(str(chat_id), False)
		else:
			welc = "✅ Aktif"
			sql.set_welc_preference(str(chat_id), True)
		if goodbye_pref:
			gdby = "✅ Aktif"
		else:
			gdby = "❎ Tidak Aktif"
		if cleanserv:
			clserv = "✅ Aktif"
		else:
			clserv = "❎ Tidak Aktif"
		chat = bot.get_chat(chat_id)
		text = "*{}* memiliki pengaturan berikut untuk modul *Welcomes/Goodbyes*:\n\n".format(escape_markdown(chat.title))
		text += "Obrolan ini preferensi pesan sambutannya telah diganti menjadi `{}`.\n".format(welc)
		text += "Untuk preferensi pesan selamat tinggal `{}`.\n".format(gdby)
		text += "Bot `{}` menghapus notifikasi member masuk/keluar secara otomatis".format(clserv)
		button = []
		button.append([InlineKeyboardButton(text="Selamat datang", callback_data="set_welc=w?|{}".format(chat_id)),
			InlineKeyboardButton(text=welc, callback_data="set_welc=w|{}".format(chat_id))])
		button.append([InlineKeyboardButton(text="Selamat tinggal", callback_data="set_welc=g?|{}".format(chat_id)),
			InlineKeyboardButton(text=gdby, callback_data="set_welc=g|{}".format(chat_id))])
		button.append([InlineKeyboardButton(text="Clean Service", callback_data="set_welc=s?|{}".format(chat_id)),
			InlineKeyboardButton(text=clserv, callback_data="set_welc=s|{}".format(chat_id))])
		button.append([InlineKeyboardButton(text="Kembali", callback_data="stngs_back({})".format(chat_id))])
		query.message.edit_text(text=text,
								  parse_mode=ParseMode.MARKDOWN,
								  reply_markup=InlineKeyboardMarkup(button))
		bot.answer_callback_query(query.id)
	if data == "g":
		welcome_pref, _, _, _ = sql.get_welc_pref(chat_id)
		goodbye_pref, _, _, _ = sql.get_gdbye_pref(chat_id)
		cleanserv = sql.clean_service(chat_id)
		if welcome_pref:
			welc = "✅ Aktif"
		else:
			welc = "❎ Tidak Aktif"
		if goodbye_pref:
			gdby = "❎ Tidak Aktif"
			sql.set_gdbye_preference(str(chat_id), False)
		else:
			gdby = "✅ Aktif"
			sql.set_gdbye_preference(str(chat_id), True)
		if cleanserv:
			clserv = "✅ Aktif"
		else:
			clserv = "❎ Tidak Aktif"
		chat = bot.get_chat(chat_id)
		text = "*{}* memiliki pengaturan berikut untuk modul *Welcomes/Goodbyes*:\n\n".format(escape_markdown(chat.title))
		text += "Obrolan ini preferensi pesan selamat tinggal telah diganti menjadi `{}`.\n".format(gdby)
		text += "Untuk preferensi pesan sambutan `{}`.\n".format(welc)
		text += "Bot `{}` menghapus notifikasi member masuk/keluar secara otomatis".format(clserv)
		button = []
		button.append([InlineKeyboardButton(text="Selamat datang", callback_data="set_welc=w?|{}".format(chat_id)),
			InlineKeyboardButton(text=welc, callback_data="set_welc=w|{}".format(chat_id))])
		button.append([InlineKeyboardButton(text="Selamat tinggal", callback_data="set_welc=g?|{}".format(chat_id)),
			InlineKeyboardButton(text=gdby, callback_data="set_welc=g|{}".format(chat_id))])
		button.append([InlineKeyboardButton(text="Clean Service", callback_data="set_welc=s?|{}".format(chat_id)),
			InlineKeyboardButton(text=clserv, callback_data="set_welc=s|{}".format(chat_id))])
		button.append([InlineKeyboardButton(text="Kembali", callback_data="stngs_back({})".format(chat_id))])
		query.message.edit_text(text=text,
								  parse_mode=ParseMode.MARKDOWN,
								  reply_markup=InlineKeyboardMarkup(button))
		bot.answer_callback_query(query.id)
	if data == "s":
		welcome_pref, _, _, _ = sql.get_welc_pref(chat_id)
		goodbye_pref, _, _, _ = sql.get_gdbye_pref(chat_id)
		cleanserv = sql.clean_service(chat_id)
		if welcome_pref:
			welc = "✅ Aktif"
		else:
			welc = "❎ Tidak Aktif"
		if goodbye_pref:
			gdby = "✅ Aktif"
		else:
			gdby = "❎ Tidak Aktif"
		if cleanserv:
			clserv = "❎ Tidak Aktif"
			sql.set_clean_service(chat_id, False)
		else:
			clserv = "✅ Aktif"
			sql.set_clean_service(chat_id, True)
		chat = bot.get_chat(chat_id)
		text = "*{}* memiliki pengaturan berikut untuk modul *Welcomes/Goodbyes*:\n\n".format(escape_markdown(chat.title))
		text += "Pengaturan clean service telah di ubah. Bot `{}` menghapus notifikasi member masuk/keluar.\n".format(clserv)
		text += "Untuk preferensi pesan sambutan `{}`.\n".format(welc)
		text += "Untuk preferensi pesan selamat tinggal `{}`.".format(gdby)
		button = []
		button.append([InlineKeyboardButton(text="Selamat datang", callback_data="set_welc=w?|{}".format(chat_id)),
			InlineKeyboardButton(text=welc, callback_data="set_welc=w|{}".format(chat_id))])
		button.append([InlineKeyboardButton(text="Selamat tinggal", callback_data="set_welc=g?|{}".format(chat_id)),
			InlineKeyboardButton(text=gdby, callback_data="set_welc=g|{}".format(chat_id))])
		button.append([InlineKeyboardButton(text="Clean Service", callback_data="set_welc=s?|{}".format(chat_id)),
			InlineKeyboardButton(text=clserv, callback_data="set_welc=s|{}".format(chat_id))])
		button.append([InlineKeyboardButton(text="Kembali", callback_data="stngs_back({})".format(chat_id))])
		query.message.edit_text(text=text,
								  parse_mode=ParseMode.MARKDOWN,
								  reply_markup=InlineKeyboardMarkup(button))
		bot.answer_callback_query(query.id)
"""


@run_async
def whChat(bot: Bot, update: Update, args: List[str]):
    if args and len(args) == 1:
        chat_id = str(args[0])
        del args[0]
        try:
            banner = update.effective_user
            bot.send_message(MESSAGE_DUMP,
                     "<b>Chat WhiteList</b>" \
                     "\n#WHCHAT" \
                     "\n<b>Status:</b> <code>Whitelisted</code>" \
                     "\n<b>Sudo Admin:</b> {}" \
                     "\n<b>Chat Name:</b> {}" \
                     "\n<b>ID:</b> <code>{}</code>".format(mention_html(banner.id, banner.first_name),userssql.get_chat_name(chat_id),chat_id), parse_mode=ParseMode.HTML)
            sql.whitelistChat(chat_id)
            update.effective_message.reply_text("Chat has been successfully whitelisted!")
        except:
            update.effective_message.reply_text("Error whitelisting chat!")
    else:
        update.effective_message.reply_text("Give me a valid chat id!")


@run_async
def unwhChat(bot: Bot, update: Update, args: List[str]):
    if args and len(args) == 1:
        chat_id = str(args[0])
        del args[0]
        try:
            banner = update.effective_user
            bot.send_message(MESSAGE_DUMP,
                     "<b>Regression of Chat WhiteList</b>" \
                     "\n#UNWHCHAT" \
                     "\n<b>Status:</b> <code>Un-Whitelisted</code>" \
                     "\n<b>Sudo Admin:</b> {}" \
                     "\n<b>Chat Name:</b> {}" \
                     "\n<b>ID:</b> <code>{}</code>".format(mention_html(banner.id, banner.first_name),userssql.get_chat_name(chat_id),chat_id), parse_mode=ParseMode.HTML)
            sql.unwhitelistChat(chat_id)
            update.effective_message.reply_text("Chat has been successfully un-whitelisted!")
            bot.leave_chat(int(chat_id))
        except:
            update.effective_message.reply_text("Error un-whitelisting chat!")
    else:
        update.effective_message.reply_text("Give me a valid chat id!")


__help__ = "welcome_help"

__mod_name__ = "Greetings"

NEW_MEM_HANDLER = MessageHandler(Filters.status_update.new_chat_members, new_member)
LEFT_MEM_HANDLER = MessageHandler(Filters.status_update.left_chat_member, left_member)
WELC_PREF_HANDLER = CommandHandler("welcome", welcome, pass_args=True, filters=Filters.group)
GOODBYE_PREF_HANDLER = CommandHandler("goodbye", goodbye, pass_args=True, filters=Filters.group)
SET_WELCOME = CommandHandler("setwelcome", set_welcome, filters=Filters.group)
SET_GOODBYE = CommandHandler("setgoodbye", set_goodbye, filters=Filters.group)
RESET_WELCOME = CommandHandler("resetwelcome", reset_welcome, filters=Filters.group)
RESET_GOODBYE = CommandHandler("resetgoodbye", reset_goodbye, filters=Filters.group)
CLEAN_WELCOME = CommandHandler("cleanwelcome", clean_welcome, pass_args=True, filters=Filters.group)
WELCOME_HELP = CommandHandler("welcomehelp", welcome_help)
SECURITY_HANDLER = CommandHandler("welcomemute", security, pass_args=True, filters=Filters.group)
SECURITY_MUTE_HANDLER = CommandHandler("welcomemutetime", security_mute, pass_args=True, filters=Filters.group)
SECURITY_BUTTONTXT_HANDLER = CommandHandler("setmutetext", security_text, pass_args=True, filters=Filters.group)
SECURITY_BUTTONRESET_HANDLER = CommandHandler("resetmutetext", security_text_reset, filters=Filters.group)
CLEAN_SERVICE_HANDLER = CommandHandler("cleanservice", cleanservice, pass_args=True, filters=Filters.group)
WHCHAT_HANDLER = CommandHandler("whchat", whChat, pass_args=True, filters=CustomFilters.sudo_filter)
UNWHCHAT_HANDLER = CommandHandler("unwhchat", unwhChat, pass_args=True, filters=CustomFilters.sudo_filter)

welcomesec_callback_handler = CallbackQueryHandler(check_bot_button, pattern=r"check_bot_")
# WELC_BTNSET_HANDLER = CallbackQueryHandler(WELC_EDITBTN, pattern=r"set_welc")

dispatcher.add_handler(NEW_MEM_HANDLER)
dispatcher.add_handler(LEFT_MEM_HANDLER)
dispatcher.add_handler(WELC_PREF_HANDLER)
dispatcher.add_handler(GOODBYE_PREF_HANDLER)
dispatcher.add_handler(SET_WELCOME)
dispatcher.add_handler(SET_GOODBYE)
dispatcher.add_handler(RESET_WELCOME)
dispatcher.add_handler(RESET_GOODBYE)
dispatcher.add_handler(CLEAN_WELCOME)
dispatcher.add_handler(WELCOME_HELP)
dispatcher.add_handler(SECURITY_HANDLER)
dispatcher.add_handler(SECURITY_MUTE_HANDLER)
dispatcher.add_handler(SECURITY_BUTTONTXT_HANDLER)
dispatcher.add_handler(SECURITY_BUTTONRESET_HANDLER)
dispatcher.add_handler(CLEAN_SERVICE_HANDLER)
dispatcher.add_handler(WHCHAT_HANDLER)
dispatcher.add_handler(UNWHCHAT_HANDLER)

dispatcher.add_handler(welcomesec_callback_handler)
#dispatcher.add_handler(WELC_BTNSET_HANDLER)