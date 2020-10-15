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

import yaml

from typing import Optional, List
from bs4 import BeautifulSoup
from requests import get

from telegram import Chat, Update, Bot, ParseMode
from telegram.ext import run_async

from hitsuki import dispatcher
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.tr_engine.strings import tld


@run_async
def checkfw(bot: Bot, update: Update, args: List[str]) -> str:
    if len(args) != 2:
        reply = 'Give me something to fetch, like:\n`/checkfw SM-N975F DBT`'
        update.effective_message.reply_text("{}".format(reply),
                                            parse_mode=ParseMode.MARKDOWN,
                                            disable_web_page_preview=True)
    temp, csc = args
    model = 'sm-'+temp if not temp.upper().startswith('SM-') else temp
    fota = get(f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml')
    test = get(f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.test.xml')
    if test.status_code != 200:
        reply = f"Couldn't check for {temp.upper()} and {csc.upper()}, please refine your search or try again later!"
        update.effective_message.reply_text("{}".format(reply),
                                            parse_mode=ParseMode.MARKDOWN,
                                            disable_web_page_preview=True)
    page1 = BeautifulSoup(fota.content, 'lxml')
    page2 = BeautifulSoup(test.content, 'lxml')
    os1 = page1.find("latest").get("o")
    os2 = page2.find("latest").get("o")
    if page1.find("latest").text.strip():
        pda1, csc1, phone1 = page1.find("latest").text.strip().split('/')
        reply = f'*Latest released firmware for {model.upper()} {csc.upper()}:*\n'
        reply += f'• PDA: `{pda1}`\n• CSC: `{csc1}`\n'
        if phone1:
            reply += f'• Phone: `{phone1}`\n'
        if os1:
            reply += f'• Android: `{os1}`\n'
        reply += '\n'
    else:
        reply = f'*No public release found for {model.upper()} and {csc.upper()}.*\n\n'
    reply += f'*Latest test firmware for {model.upper()} {csc.upper()}:*\n'
    if len(page2.find("latest").text.strip().split('/')) == 3:
        pda2, csc2, phone2 = page2.find("latest").text.strip().split('/')
        reply += f'• PDA: `{pda2}`\n• CSC: `{csc2}`\n'
        if phone2:
            reply += f'• Phone: `{phone2}`\n'
        if os2:
            reply += f'• Android: `{os2}`\n'
        reply += '\n'
    else:
        md5 = page2.find("latest").text.strip()
        reply += f'• Hash: `{md5}`\n• Android: `{os2}`\n\n'

    update.message.reply_text("{}".format(reply),
                              parse_mode=ParseMode.MARKDOWN,
                              disable_web_page_preview=True)


@run_async
def getfw(bot: Bot, update: Update, args: List[str]) -> str:
    if len(args) != 2:
        reply = 'Give me something to fetch, like:\n`/getfw SM-N975F DBT`'
        update.effective_message.reply_text("{}".format(reply),
                                            parse_mode=ParseMode.MARKDOWN,
                                            disable_web_page_preview=True)
    temp, csc = args
    model = 'sm-'+temp if not temp.upper().startswith('SM-') else temp
    test = get(f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.test.xml')
    if test.status_code != 200:
        reply = f"Couldn't find any firmware downloads for {temp.upper()} {csc.upper()}, please refine your search or try again later!"
        update.effective_message.reply_text("{}".format(reply),
                                            parse_mode=ParseMode.MARKDOWN,
                                            disable_web_page_preview=True)
    url1 = f'https://samfrew.com/model/{model.upper()}/region/{csc.upper()}/'
    url2 = f'https://www.sammobile.com/samsung/firmware/{model.upper()}/{csc.upper()}/'
    url3 = f'https://sfirmware.com/samsung-{model.lower()}/#tab=firmwares'
    url4 = f'https://samfw.com/firmware/{model.upper()}/{csc.upper()}/'
    fota = get(f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml')
    page = BeautifulSoup(fota.content, 'lxml')
    os = page.find("latest").get("o")
    reply = ""
    if page.find("latest").text.strip():
        pda, csc2, phone = page.find("latest").text.strip().split('/')
        reply += f'*Latest firmware for {model.upper()} {csc.upper()}:*\n'
        reply += f'• PDA: `{pda}`\n• CSC: `{csc2}`\n'
        if phone:
            reply += f'• Phone: `{phone}`\n'
        if os:
            reply += f'• Android: `{os}`\n'
    reply += '\n'
    reply += f'*Downloads for {model.upper()} {csc.upper()}:*\n'
    reply += f'• [samfrew.com]({url1})\n'
    reply += f'• [sammobile.com]({url2})\n'
    reply += f'• [sfirmware.com]({url3})\n'
    reply += f'• [samfw.com]({url4})\n'
    update.message.reply_text("{}".format(reply),
                              parse_mode=ParseMode.MARKDOWN,
                              disable_web_page_preview=True)


def miui(bot: Bot, update: Update, args):
    cmd_name = "miui"
    message = update.effective_message
    chat = update.effective_chat  # type: Optional[Chat]
    device = message.text[len(f'/{cmd_name} '):]

    giturl = "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/"

    if device == '':
        reply_text = tld(chat.id, "cmd_example").format(cmd_name)
        message.reply_text(reply_text,
                           parse_mode=ParseMode.MARKDOWN,
                           disable_web_page_preview=True)
        return

    result = tld(chat.id, "miui_release")
    stable_all = yaml.load(get(giturl +
                               "data/latest.yml").content,
                           Loader=yaml.FullLoader)
    data = [i for i in stable_all if device == i['codename']]
    if len(data) != 0:
        for i in data:
            result += "*Device:* " + i['name'] + "\n"
            result += "*Branch:* " + i['branch'] + "\n"
            result += "*Install method:* " + i['method'] + "\n"
            result += "*Miui version:* " "`" + i['version'] + "`\n"
            result += "*Android version:* " "`" + i['android'] + "`\n"
            result += "*Size:* " + "`" + i['size'] + "`\n"
            result += "*MD5:* " + "`" + i['md5'] + "`\n"
            result += "*Download:* [HERE]" + "(" + i['link'] + ")" "\n\n"

    else:
        result = tld(chat.id, "err_not_found")

    message.reply_text(result, parse_mode=ParseMode.MARKDOWN)


GETFW_HANDLER = DisableAbleCommandHandler("samget", getfw, pass_args=True)
CHECKFW_HANDLER = DisableAbleCommandHandler("samcheck", checkfw, pass_args=True)
MIUI_HANDLER = DisableAbleCommandHandler("miui", miui, pass_args=True)

dispatcher.add_handler(MIUI_HANDLER)
dispatcher.add_handler(GETFW_HANDLER)
dispatcher.add_handler(CHECKFW_HANDLER)
