import random
import re
import time

from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, ChatPermissions
from telegram.ext import CommandHandler, CallbackQueryHandler, Filters, run_async
from telegram.error import BadRequest
from telegram.utils.helpers import mention_markdown

from emilia import dispatcher, updater, spamcheck, IS_DEBUG
import emilia.modules.sql.welcome_sql as sql
from emilia.modules.languages import tl
from emilia.modules.connection import connected

from emilia.modules.helper_funcs.alternate import send_message, send_message_raw
from emilia.modules.helper_funcs.chat_status import user_admin
from emilia.modules.helper_funcs.string_handling import make_time, extract_time_int

def welcome_timeout(context):
	for cht in sql.get_all_chat_timeout():
		user_id = cht.user_id
		chat_id = cht.chat_id
		if int(time.time()) >= int(cht.timeout_int):
			getcur, extra_verify, cur_value, timeout, timeout_mode, cust_text = sql.welcome_security(chat_id)
			if timeout_mode == 1:
				try:
					context.bot.unbanChatMember(chat_id, user_id)
					send_message_raw(chat_id, tl(user_id, "Verification failed!\n{} was kicked!").format(mention_markdown(user_id, context.bot.getChatMember(chat_id, user_id).user.first_name)), parse_mode="markdown")
				except Exception as err:
					send_message_raw(chat_id, tl(user_id, "Verification failed!\nBut was failed to kick {}: {}").format(mention_markdown(user_id, context.bot.getChatMember(chat_id, user_id).user.first_name), str(err)), parse_mode="markdown")
			elif timeout_mode == 2:
				try:
					context.bot.kickChatMember(chat_id, user_id)
					send_message_raw(chat_id, tl(user_id, "Verification failed!\n{} was banned!").format(mention_markdown(user_id, context.bot.getChatMember(chat_id, user_id).user.first_name)), parse_mode="markdown")
				except Exception as err:
					send_message_raw(chat_id, tl(user_id, "Verification failed!\nBut was failed to banned {}: {}").format(mention_markdown(user_id, context.bot.getChatMember(chat_id, user_id).user.first_name), str(err)), parse_mode="markdown")
			sql.rm_from_timeout(chat_id, user_id)



@run_async
@spamcheck
@user_admin
def set_verify_welcome(update, context):
	args = context.args
	chat = update.effective_chat  # type: Optional[Chat]
	getcur, extra_verify, cur_value, timeout, timeout_mode, cust_text = sql.welcome_security(chat.id)
	if len(args) >= 1:
		var = args[0].lower()
		if (var == "yes" or var == "ya" or var == "on"):
			check = context.bot.getChatMember(chat.id, context.bot.id)
			if check.status == 'member' or check['can_restrict_members'] == False:
				text = tl(update.effective_message, "I can't restrict member here! Make sure I'm an admin an can mute someone!")
				send_message(update.effective_message, text, parse_mode="markdown")
				return ""
			sql.set_welcome_security(chat.id, getcur, True, str(cur_value), str(timeout), int(timeout_mode), cust_text)
			send_message(update.effective_message, tl(update.effective_message, "Security for new members is activated! New users are required to complete verification to chat"))
		elif (var == "no" or var == "ga" or var == "off"):
			sql.set_welcome_security(chat.id, getcur, False, str(cur_value), str(timeout), int(timeout_mode), cust_text)
			send_message(update.effective_message, tl(update.effective_message, "Disabled, users can once click the button to chat"))
		else:
			send_message(update.effective_message, tl(update.effective_message, "Please write `on`/`off`!"), parse_mode=ParseMode.MARKDOWN)
	else:
		getcur, extra_verify, cur_value, timeout, timeout_mode, cust_text = sql.welcome_security(chat.id)
		if cur_value[:1] == "0":
			cur_value = tl(update.effective_message, "Forever")
		text = tl(update.effective_message, "Current settings are:\nWelcome security: `{}`\nVerify security: `{}`\nMembers will be muted for: `{}`\nVerification timeout: `{}`\nUnmute custom button: `{}`").format(getcur, extra_verify, cur_value, make_time(int(timeout)), cust_text)
		send_message(update.effective_message, text, parse_mode="markdown")


@run_async
@spamcheck
@user_admin
def set_welctimeout(update, context):
	args = context.args
	chat = update.effective_chat  # type: Optional[Chat]
	message = update.effective_message  # type: Optional[Message]
	getcur, extra_verify, cur_value, timeout, timeout_mode, cust_text = sql.welcome_security(chat.id)
	if len(args) >= 1:
		var = args[0]
		if var[:1] == "0":
			mutetime = "0"
			sql.set_welcome_security(chat.id, getcur, extra_verify, cur_value, "0", timeout_mode, cust_text)
			text = tl(update.effective_message, "Verification timeout has been deactivated!")
		else:
			mutetime = extract_time_int(message, var)
			if mutetime == "":
				return
			sql.set_welcome_security(chat.id, getcur, extra_verify, cur_value, str(mutetime), timeout_mode, cust_text)
			text = tl(update.effective_message, "If the new member doesn't verify for *{}* then he/she will *{}*").format(var, "Kick" if timeout_mode == 1 else "Banned")
		send_message(update.effective_message, text, parse_mode="markdown")
	else:
		if timeout == "0":
			send_message(update.effective_message, tl(update.effective_message, "Timeout settings: *{}*").format("Disabled"), parse_mode="markdown")
		else:
			send_message(update.effective_message, tl(update.effective_message, "Timeout settings: *{}*").format(make_time(int(timeout))), parse_mode="markdown")

@run_async
@spamcheck
@user_admin
def timeout_mode(update, context):
	chat = update.effective_chat  # type: Optional[Chat]
	user = update.effective_user  # type: Optional[User]
	msg = update.effective_message  # type: Optional[Message]
	args = context.args

	conn = connected(context.bot, update, chat, user.id, need_admin=True)
	if conn:
		chat = dispatcher.bot.getChat(conn)
		chat_id = conn
		chat_name = dispatcher.bot.getChat(conn).title
	else:
		if update.effective_message.chat.type == "private":
			send_message(update.effective_message, tl(update.effective_message, "You can do this command in groups, not PM"))
			return ""
		chat = update.effective_chat
		chat_id = update.effective_chat.id
		chat_name = update.effective_message.chat.title

	getcur, extra_verify, cur_value, timeout, timeout_mode, cust_text = sql.welcome_security(chat.id)

	if args:
		if args[0].lower() == 'kick' or args[0].lower() == 'tendang' or args[0].lower() == 'leave':
			settypeblacklist = tl(update.effective_message, 'kick')
			sql.set_welcome_security(chat.id, getcur, extra_verify, cur_value, timeout, 1, cust_text)
		elif args[0].lower() == 'ban' or args[0].lower() == 'banned':
			settypeblacklist = tl(update.effective_message, 'banned')
			sql.set_welcome_security(chat.id, getcur, extra_verify, cur_value, timeout, 2, cust_text)
		else:
			send_message(update.effective_message, tl(update.effective_message, "I only understand kick/banned!"))
			return
		if conn:
			text = tl(update.effective_message, "Timeout mode changed, User will be `{}` at *{}*!").format(settypeblacklist, chat_name)
		else:
			text = tl(update.effective_message, "Timeout mode changed, User will be `{}`!").format(settypeblacklist)
		send_message(update.effective_message, text, parse_mode="markdown")
	else:
		if timeout_mode == 1:
			settypeblacklist = tl(update.effective_message, "kick")
		elif timeout_mode == 2:
			settypeblacklist = tl(update.effective_message, "banned")
		if conn:
			text = tl(update.effective_message, "The current timeout mode is set to *{}* at *{}*.").format(settypeblacklist, chat_name)
		else:
			text = tl(update.effective_message, "The current timeout mode is set to *{}*.").format(settypeblacklist)
		send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
	return



job = updater.job_queue

job_timeout_set = job.run_repeating(welcome_timeout, interval=10, first=1)
job_timeout_set.enabled = True


WELCVERIFY_HANDLER = CommandHandler("welcomeverify", set_verify_welcome, pass_args=True, filters=Filters.group)
WELTIMEOUT_HANDLER = CommandHandler("wtimeout", set_welctimeout, pass_args=True, filters=Filters.group)
WELMODE_HANDLER = CommandHandler("wtmode", timeout_mode, pass_args=True, filters=Filters.group)

dispatcher.add_handler(WELCVERIFY_HANDLER)
dispatcher.add_handler(WELTIMEOUT_HANDLER)
dispatcher.add_handler(WELMODE_HANDLER)
