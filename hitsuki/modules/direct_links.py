#    Hitsuki (A telegram bot project)
#    Hitalo (C) 2019-2020
#    RaphielGang (C) 2019-2020

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

#    Thanks to github.com/alissonlauffer
#    Last.fm module ported from github.com/RaphielGang/Telegram-Paperplane

import re
import requests

from random import choice
from bs4 import BeautifulSoup
from telegram.ext import run_async, CommandHandler

from hitsuki import dispatcher


@run_async
def direct_link_generator(bot, update):
    message = update.effective_message
    text = message.text[len('/direct '):]

    if text:
        links = re.findall(r'\bhttps?://.*\.\S+', text)
    else:
        message.reply_text("Usage: /direct <url>")
        return
    reply = []
    if not links:
        message.reply_text("No links found!")
        return
    for link in links:
        if 'sourceforge.net' in link:
            reply.append(sourceforge(link))
        else:
            reply.append(
                re.findall(
                    r"\bhttps?://(.*?[^/]+)",
                    link)[0] +
                ' is not supported')

    message.reply_html("\n".join(reply))


def sourceforge(url: str) -> str:
    try:
        link = re.findall(r'\bhttps?://.*sourceforge\.net\S+', url)[0]
    except IndexError:
        reply = "<code>No SourceForge links found</code>\n"
        return reply
    file_path = re.findall(r'/files(.*)/download', link)
    if not file_path:
        file_path = re.findall(r'/files(.*)', link)
    file_path = file_path[0]
    reply = f"Mirrors for <i>{file_path.split('/')[-1]}</i>\n"
    project = re.findall(r'projects?/(.*?)/files', link)[0]
    mirrors = f'https://sourceforge.net/settings/mirror_choices?' \
              f'projectname={project}&filename={file_path}'
    page = BeautifulSoup(requests.get(mirrors).content, 'lxml')
    info = page.find('ul', {'id': 'mirrorList'}).findAll('li')
    for mirror in info[1:]:
        name = re.findall(r'\((.*)\)', mirror.text.strip())[0]
        dl_url = f'https://{mirror["id"]}.dl.sourceforge.net/project/{project}/{file_path}'
        reply += f'<a href="{dl_url}">{name}</a> '
    return reply


def useragent():
    useragents = BeautifulSoup(
        requests.get(
            'https://developers.whatismybrowser.com/'
            'useragents/explore/operating_system_name/android/').content,
        'lxml').findAll('td', {'class': 'useragent'})
    user_agent = choice(useragents)
    return user_agent.text


__help__ = True

DIRECT_HANDLER = CommandHandler("direct", direct_link_generator)

dispatcher.add_handler(DIRECT_HANDLER)
