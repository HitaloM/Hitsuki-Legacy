#    Hitsuki (A telegram bot project)
# This module is ported from Telegram-UserBot (Paperplane) all rights
# reserved.

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re
import requests

from random import choice
from bs4 import BeautifulSoup

from hitsuki.events import register


@register(pattern=r"^/direct(?: |$)([\s\S]*)")
async def direct_link_generator(request):
    await request.reply("`Processing...`")
    textx = await request.get_reply_message()
    message = request.pattern_match.group(1)
    if message:
        pass
    elif textx:
        message = textx.text
    else:
        await request.reply("Usage: `/direct <url>`")
        return
    reply = ''
    links = re.findall(r'\bhttps?://.*\.\S+', message)
    if not links:
        reply = "No links found!"
        await request.reply(reply)
    for link in links:
        if 'sourceforge.net' in link:
            reply += sourceforge(link)
        else:
            reply += '`' + re.findall(r"\bhttps?://(.*?[^/]+)",
                                      link)[0] + 'is not supported`\n'
    await request.reply(reply)


def sourceforge(url: str) -> str:
    try:
        link = re.findall(r'\bhttps?://.*sourceforge\.net\S+', url)[0]
    except IndexError:
        reply = "No SourceForge links found\n"
        return reply
    file_path = re.findall(r'files(.*)/download', link)[0]
    reply = f"Mirrors for __{file_path.split('/')[-1]}__\n"
    project = re.findall(r'projects?/(.*?)/files', link)[0]
    mirrors = f'https://sourceforge.net/settings/mirror_choices?' \
              f'projectname={project}&filename={file_path}'
    page = BeautifulSoup(requests.get(mirrors).content, 'html.parser')
    info = page.find('ul', {'id': 'mirrorList'}).findAll('li')
    for mirror in info[1:]:
        name = re.findall(r'\((.*)\)', mirror.text.strip())[0]
        dl_url = f'https://{mirror["id"]}.dl.sourceforge.net/project/{project}/{file_path}'
        reply += f'[{name}]({dl_url}) '
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
