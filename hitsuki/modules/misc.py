#    Hitsuki (A telegram bot project)

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import html
import urllib.parse as urlparse
from datetime import datetime
from typing import Optional, List

import requests
import wikipedia
from covid import Covid
from requests import get
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram import (ParseMode, ReplyKeyboardRemove,
                      InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html

from hitsuki import (dispatcher, OWNER_ID, SUDO_USERS,
                     SUPPORT_USERS, WHITELIST_USERS, sw)
from hitsuki.__main__ import STATS, USER_INFO
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.helper_funcs.extraction import extract_user
from hitsuki.modules.tr_engine.strings import tld

cvid = Covid(source="worldometers")


@run_async
def get_bot_ip(bot: Bot, update: Update):
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


@run_async
def get_id(bot: Bot, update: Update, args: List[str]):
    user_id = extract_user(update.effective_message, args)
    chat = update.effective_chat  # type: Optional[Chat]
    if user_id:
        if update.effective_message.reply_to_message and update.effective_message.reply_to_message.forward_from:
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            update.effective_message.reply_markdown(
                tld(chat.id,
                    "misc_get_id_1").format(escape_markdown(user2.first_name),
                                            user2.id,
                                            escape_markdown(user1.first_name),
                                            user1.id))
        else:
            user = bot.get_chat(user_id)
            update.effective_message.reply_markdown(
                tld(chat.id,
                    "misc_get_id_2").format(escape_markdown(user.first_name),
                                            user.id))
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            update.effective_message.reply_markdown(
                tld(chat.id, "misc_id_1").format(chat.id))

        else:
            update.effective_message.reply_markdown(
                tld(chat.id, "misc_id_2").format(chat.id))


@run_async
def info(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message  # type: Optional[Message]
    user_id = extract_user(update.effective_message, args)
    chat = update.effective_chat  # type: Optional[Chat]

    if user_id:
        user = bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif not msg.reply_to_message and (
            not args or
        (len(args) >= 1 and not args[0].startswith("@")
         and not args[0].isdigit()
         and not msg.parse_entities([MessageEntity.TEXT_MENTION]))):
        msg.reply_text(tld(chat.id, "misc_info_extract_error"))
        return

    else:
        return

    text = tld(chat.id, "misc_info_1")
    text += tld(chat.id, "misc_info_id").format(user.id)
    text += tld(chat.id,
                "misc_info_first").format(html.escape(user.first_name))

    if user.last_name:
        text += tld(chat.id,
                    "misc_info_name").format(html.escape(user.last_name))

    if user.username:
        text += tld(chat.id,
                    "misc_info_username").format(html.escape(user.username))

    text += tld(chat.id,
                "misc_info_user_link").format(mention_html(user.id, "link"))

    try:
        spamwatch = sw.get_ban(int(user.id))
        if spamwatch:
            text += tld(chat.id, "misc_info_swban1")
            text += tld(chat.id, "misc_info_swban2").format(spamwatch.reason)
            text += tld(chat.id, "misc_info_swban3")
        else:
            pass
    except Exception:
        pass  # avoids crash if api is down

    if user.id == OWNER_ID:
        text += tld(chat.id, "misc_info_is_owner")
    else:
        if user.id == int(254318997):
            text += tld(chat.id, "misc_info_is_original_owner")

        if user.id in SUDO_USERS:
            text += tld(chat.id, "misc_info_is_sudo")
        else:
            if user.id in SUPPORT_USERS:
                text += tld(chat.id, "misc_info_is_support")

            if user.id in WHITELIST_USERS:
                text += tld(chat.id, "misc_info_is_whitelisted")

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def echo(bot: Bot, update: Update):
    message = update.effective_message
    message.delete()
    args = update.effective_message.text.split(None, 1)
    if message.reply_to_message:
        message.reply_to_message.reply_text(args[1])
    else:
        message.reply_text(args[1], quote=False)


@run_async
def reply_keyboard_remove(bot: Bot, update: Update):
    reply_keyboard = []
    reply_keyboard.append([ReplyKeyboardRemove(remove_keyboard=True)])
    reply_markup = ReplyKeyboardRemove(remove_keyboard=True)
    old_message = bot.send_message(
        chat_id=update.message.chat_id,
        text='trying',  # This text will not get translated
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id)
    bot.delete_message(chat_id=update.message.chat_id,
                       message_id=old_message.message_id)


@run_async
def markdown_help(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]
    update.effective_message.reply_text(tld(chat.id, "misc_md_list"),
                                        parse_mode=ParseMode.HTML)
    update.effective_message.reply_text(tld(chat.id, "misc_md_try"))
    update.effective_message.reply_text(tld(chat.id, "misc_md_help"))


@run_async
def stats(bot: Bot, update: Update):
    update.effective_message.reply_text(
        # This text doesn't get translated as it is internal message.
        "<b>Current Stats:</b>\n" + \
        "\n".join([mod.__stats__() for mod in STATS]),
        parse_mode=ParseMode.HTML)


@run_async
def github(bot: Bot, update: Update):
    message = update.effective_message
    text = message.text[len('/git '):]
    usr = get(f'https://api.github.com/users/{text}').json()
    if usr.get('login'):
        text = f"*Username:* [{usr['login']}](https://github.com/{usr['login']})"

        whitelist = [
            'name', 'id', 'type', 'location', 'blog', 'bio', 'followers',
            'following', 'hireable', 'public_gists', 'public_repos', 'email',
            'company', 'updated_at', 'created_at'
        ]

        difnames = {
            'id': 'Account ID',
            'type': 'Account type',
            'created_at': 'Account created at',
            'updated_at': 'Last updated',
            'public_repos': 'Public Repos',
            'public_gists': 'Public Gists'
        }

        goaway = [None, 0, 'null', '']

        for x, y in usr.items():
            if x in whitelist:
                x = difnames.get(x, x.title())

                if x in ('Account created at', 'Last updated'):
                    y = datetime.strptime(y, "%Y-%m-%dT%H:%M:%SZ")

                if y not in goaway:
                    if x == 'Blog':
                        x = "Website"
                        y = f"[Here!]({y})"
                        text += ("\n*{}:* {}".format(x, y))
                    else:
                        text += ("\n*{}:* `{}`".format(x, y))
        reply_text = text
    else:
        reply_text = "User not found. Make sure you entered valid username!"
    message.reply_text(reply_text,
                       parse_mode=ParseMode.MARKDOWN,
                       disable_web_page_preview=True)


@run_async
def repo(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    text = message.text[len('/repo '):]
    usr = get(f'https://api.github.com/users/{text}/repos?per_page=40').json()
    reply_text = "*Repo*\n"
    for i in range(len(usr)):
        reply_text += f"[{usr[i]['name']}]({usr[i]['html_url']})\n"
    message.reply_text(reply_text,
                       parse_mode=ParseMode.MARKDOWN,
                       disable_web_page_preview=True)


@run_async
def paste(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    BURL = 'https://del.dog'
    message = update.effective_message
    if message.reply_to_message:
        data = message.reply_to_message.text
    elif len(args) >= 1:
        data = message.text.split(None, 1)[1]
    else:
        message.reply_text(tld(chat.id, "misc_paste_invalid"))
        return

    r = requests.post(f'{BURL}/documents', data=data.encode('utf-8'))

    if r.status_code == 404:
        update.effective_message.reply_text(tld(chat.id, "misc_paste_404"))
        r.raise_for_status()

    res = r.json()

    if r.status_code != 200:
        update.effective_message.reply_text(res['message'])
        r.raise_for_status()

    key = res['key']
    if res['isUrl']:
        reply = tld(chat.id, "misc_paste_success").format(BURL, key, BURL, key)
    else:
        reply = f'{BURL}/{key}'
    update.effective_message.reply_text(reply,
                                        parse_mode=ParseMode.MARKDOWN,
                                        disable_web_page_preview=True)


@run_async
def get_paste_content(bot: Bot, update: Update, args: List[str]):
    BURL = 'https://del.dog'
    message = update.effective_message
    chat = update.effective_chat  # type: Optional[Chat]

    if len(args) >= 1:
        key = args[0]
    else:
        message.reply_text(tld(chat.id, "misc_get_pasted_invalid"))
        return

    format_normal = f'{BURL}/'
    format_view = f'{BURL}/v/'

    if key.startswith(format_view):
        key = key[len(format_view):]
    elif key.startswith(format_normal):
        key = key[len(format_normal):]

    r = requests.get(f'{BURL}/raw/{key}')

    if r.status_code != 200:
        try:
            res = r.json()
            update.effective_message.reply_text(res['message'])
        except Exception:
            if r.status_code == 404:
                update.effective_message.reply_text(
                    tld(chat.id, "misc_paste_404"))
            else:
                update.effective_message.reply_text(
                    tld(chat.id, "misc_get_pasted_unknown"))
        r.raise_for_status()

    update.effective_message.reply_text('```' + escape_markdown(r.text) +
                                        '```',
                                        parse_mode=ParseMode.MARKDOWN)


@run_async
def get_paste_stats(bot: Bot, update: Update, args: List[str]):
    BURL = 'https://del.dog'
    message = update.effective_message
    chat = update.effective_chat  # type: Optional[Chat]

    if len(args) >= 1:
        key = args[0]
    else:
        message.reply_text(tld(chat.id, "misc_get_pasted_invalid"))
        return

    format_normal = f'{BURL}/'
    format_view = f'{BURL}/v/'

    if key.startswith(format_view):
        key = key[len(format_view):]
    elif key.startswith(format_normal):
        key = key[len(format_normal):]

    r = requests.get(f'{BURL}/documents/{key}')

    if r.status_code != 200:
        try:
            res = r.json()
            update.effective_message.reply_text(res['message'])
        except Exception:
            if r.status_code == 404:
                update.effective_message.reply_text(
                    tld(chat.id, "misc_paste_404"))
            else:
                update.effective_message.reply_text(
                    tld(chat.id, "misc_get_pasted_unknown"))
        r.raise_for_status()

    document = r.json()['document']
    key = document['_id']
    views = document['viewCount']
    reply = f'Stats for **[/{key}]({BURL}/{key})**:\nViews: `{views}`'
    update.effective_message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


@run_async
def ud(bot: Bot, update: Update):
    message = update.effective_message
    text = message.text[len('/ud '):]
    if text == '':
        text = "Cockblocked By Steve Jobs"
    results = get(
        f'http://api.urbandictionary.com/v0/define?term={text}').json()
    reply_text = f'Word: {text}\nDefinition: {results["list"][0]["definition"]}'
    message.reply_text(reply_text)


@run_async
def wiki(bot: Bot, update: Update):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split(None, 1)
    text = args[1]
    wikipedia.set_lang("en")
    try:
        pagewiki = wikipedia.page(text)
    except wikipedia.exceptions.PageError:
        msg.reply_text("No results found!")
        return
    except wikipedia.exceptions.DisambiguationError as refer:
        refer = str(refer).split("\n")
        if len(refer) >= 6:
            batas = 6
        else:
            batas = len(refer)
        text = ""
        for x in range(batas):
            if x == 0:
                text += refer[x]+"\n"
            else:
                text += "- `"+refer[x]+"`\n"
        msg.reply_text(text, parse_mode="markdown")
        return
    except IndexError:
        msg.reply_text("Write a message to search from wikipedia sources.")
        return
    title = pagewiki.title
    summary = pagewiki.summary
    if update.effective_message.chat.type == "private":
        msg.reply_text(("The result of {} is:\n\n<b>{}</b>\n{}").format(text,
                                                                        title, summary), parse_mode=ParseMode.HTML)
    else:
        if len(summary) >= 200:
            title = pagewiki.title
            summary = summary[:200]+"..."
            button = InlineKeyboardMarkup([[InlineKeyboardButton(
                text="Read More...", url="t.me/{}?start=wiki-{}".format(bot.username, title.replace(' ', '_')))]])
        else:
            button = None
        msg.reply_text(("The result of {} is:\n\n<b>{}</b>\n{}").format(text,
                                                                        title, summary), parse_mode=ParseMode.HTML, reply_markup=button)


@run_async
def covid(bot: Bot, update: Update):
    message = update.effective_message
    chat = update.effective_chat
    country = str(message.text[len('/covid '):])
    if country == '':
        country = "world"
    if country.lower() in ["south korea", "korea"]:
        country = "s. korea"
    try:
        c_case = cvid.get_status_by_country_name(country)
    except Exception:
        message.reply_text(tld(chat.id, "misc_covid_error"))
        return
    active = format_integer(c_case["active"])
    confirmed = format_integer(c_case["confirmed"])
    country = c_case["country"]
    critical = format_integer(c_case["critical"])
    deaths = format_integer(c_case["deaths"])
    new_cases = format_integer(c_case["new_cases"])
    new_deaths = format_integer(c_case["new_deaths"])
    recovered = format_integer(c_case["recovered"])
    total_tests = c_case["total_tests"]
    if total_tests == 0:
        total_tests = "N/A"
    else:
        total_tests = format_integer(c_case["total_tests"])
    reply = tld(chat.id,
                "misc_covid").format(country, confirmed, new_cases, active,
                                     critical, deaths, new_deaths, recovered,
                                     total_tests)
    message.reply_markdown(reply)


@run_async
def outline(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    chat = update.effective_chat
    if message.reply_to_message:
        data = message.reply_to_message.text
    elif len(args) >= 1:
        data = message.text.split(None, 1)[1]
    else:
        message.reply_text(tld(chat.id, "misc_paste_invalid"))
        return
    if urlparse.urlparse(data).scheme:
        update.message.reply_text("https://outline.com/" + data)
    else:
        update.message.reply_text("This is not a valid URL")
        return


def format_integer(number, thousand_separator=','):
    def reverse(string):
        string = "".join(reversed(string))
        return string

    s = reverse(str(number))
    count = 0
    result = ''
    for char in s:
        count = count + 1
        if count % 3 == 0:
            if len(s) == count:
                result = char + result
            else:
                result = thousand_separator + char + result
        else:
            result = char + result
    return result


__help__ = True

ID_HANDLER = DisableAbleCommandHandler("id",
                                       get_id,
                                       pass_args=True,
                                       admin_ok=True)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=Filters.chat(OWNER_ID))
INFO_HANDLER = DisableAbleCommandHandler("info",
                                         info,
                                         pass_args=True,
                                         admin_ok=True)
GITHUB_HANDLER = DisableAbleCommandHandler("git", github, admin_ok=True)
REPO_HANDLER = DisableAbleCommandHandler("repo",
                                         repo,
                                         pass_args=True,
                                         admin_ok=True)

ECHO_HANDLER = CommandHandler("echo", echo, filters=Filters.user(OWNER_ID))
MD_HELP_HANDLER = CommandHandler("markdownhelp",
                                 markdown_help,
                                 filters=Filters.private)

STATS_HANDLER = CommandHandler("stats", stats, filters=Filters.user(OWNER_ID))
PASTE_HANDLER = DisableAbleCommandHandler("paste", paste, pass_args=True)
GET_PASTE_HANDLER = DisableAbleCommandHandler("getpaste",
                                              get_paste_content,
                                              pass_args=True)
PASTE_STATS_HANDLER = DisableAbleCommandHandler("pastestats",
                                                get_paste_stats,
                                                pass_args=True)
UD_HANDLER = DisableAbleCommandHandler("ud", ud)
WIKI_HANDLER = DisableAbleCommandHandler("wiki", wiki)
COVID_HANDLER = DisableAbleCommandHandler("covid", covid, admin_ok=True)
OUTLINE_HANDLER = DisableAbleCommandHandler("outline", outline, pass_args=True)

dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(PASTE_HANDLER)
dispatcher.add_handler(GET_PASTE_HANDLER)
dispatcher.add_handler(PASTE_STATS_HANDLER)
dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(GITHUB_HANDLER)
dispatcher.add_handler(REPO_HANDLER)
dispatcher.add_handler(
    DisableAbleCommandHandler("removebotkeyboard", reply_keyboard_remove))
dispatcher.add_handler(WIKI_HANDLER)
dispatcher.add_handler(COVID_HANDLER)
dispatcher.add_handler(OUTLINE_HANDLER)
