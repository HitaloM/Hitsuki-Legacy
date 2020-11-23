#    Hitsuki (A telegram bot project)

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
from requests import get
from bs4 import BeautifulSoup
from rapidjson import loads

from pyrogram import Client, filters
from pyrogram.types import Update, InlineKeyboardButton, InlineKeyboardMarkup

from hitsuki import pbot
from hitsuki.mwt import MWT

fw_links = {"SAMMOBILE": "https://www.sammobile.com/samsung/firmware/{}/{}/",
            "SAMFW": "https://samfw.com/firmware/{}/{}/",
            "SAMFREW": "https://samfrew.com/model/{}/region/{}/",
            }.items()


@MWT(timeout=60 * 10)
class GetDevice:
    def __init__(self, device):
        """Get device info by codename or model!"""
        self.device = device

    def get(self):
        if self.device.lower().startswith('sm-'):
            data = get(
                'https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_model.json').content
            db = loads(data)
            try:
                name = db[self.device.upper()][0]['name']
                device = db[self.device.upper()][0]['device']
                brand = db[self.device.upper()][0]['brand']
                model = self.device.lower()
                return {'name': name,
                        'device': device,
                        'model': model,
                        'brand': brand
                        }
            except KeyError:
                return False
        else:
            data = get(
                'https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_device.json').content
            db = loads(data)
            newdevice = self.device.strip('lte').lower() if self.device.startswith(
                'beyond') else self.device.lower()
            try:
                name = db[newdevice][0]['name']
                model = db[newdevice][0]['model']
                brand = db[newdevice][0]['brand']
                device = self.device.lower()
                return {'name': name,
                        'device': device,
                        'model': model,
                        'brand': brand
                        }
            except KeyError:
                return False


@pbot.on_message(filters.command(["specs", "spec"]))
async def specs(c: Client, update: Update):
    if len(update.command) != 2:
        message = (
            "Please write your codename or model into it,\ni.e <code>/specs herolte</code> or <code>/specs sm-g610f</code>")
        await c.send_message(
            chat_id=update.chat.id,
            text=message)
        return
    device = update.command[1]
    data = GetDevice(device).get()
    if data:
        name = data['name']
        model = data['model']
        device = name.lower().replace(' ', '-')
    else:
        message = "coudn't find your device, chack device & try!"
        await c.send_message(
            chat_id=update.chat.id,
            text=message)
        return
    sfw = get(f'https://sfirmware.com/samsung-{model.lower()}/')
    if sfw.status_code == 200:
        page = BeautifulSoup(sfw.content, 'lxml')
        message = '<b>Device:</b> Samsung {}\n'.format(name)
        res = page.find_all('tr', {'class': 'mdata-group-val'})
        res = res[2:]
        for info in res:
            title = re.findall(r'<td>.*?</td>', str(info)
                               )[0].strip().replace('td', 'b')
            data = re.findall(r'<td>.*?</td>', str(info)
                              )[-1].strip().replace('td', 'code')
            message += "• {}: <code>{}</code>\n".format(title, data)

    else:
        message = "Device specs not found in bot database, make sure this is a Samsung device!"
        await c.send_message(
            chat_id=update.chat.id,
            text=message)
        return

    await c.send_message(
        chat_id=update.chat.id,
        text=message)


@pbot.on_message(filters.command(["whatis", "device", "codename"]))
async def models(c: Client, update: Update):
    if len(update.command) != 2:
        message = "Please write your codename into it, i.e <code>/whatis herolte</code>"
        await c.send_message(
            chat_id=update.chat.id,
            text=message,
            disable_web_page_preview=True)
        return

    device = update.command[1]
    data = GetDevice(device).get()
    if data:
        name = data['name']
        device = data['device']
        brand = data['brand']
        model = data['model']
    else:
        message = "coudn't find your device, chack device & try!"
        await c.send_message(
            chat_id=update.chat.id,
            text=message)
        return

    message = f'<b>{device}/{model.upper()}</b> is <code>{brand} {name}</code>\n'
    await c.send_message(
        chat_id=update.chat.id,
        text=message,
        disable_web_page_preview=True)


@pbot.on_message(filters.command(["variants", "models"]))
async def variants(c: Client, update: Update):
    if len(update.command) != 2:
        message = "Please write your codename into it, i.e <code>/specs herolte</code>"
        await c.send_message(
            chat_id=update.chat.id,
            text=message)
        return

    device = update.command[1]
    data = GetDevice(device).get()
    if data:
        name = data['name']
        device = data['device']
    else:
        message = "coudn't find your device, chack device & try!"
        await c.send_message(
            chat_id=update.chat.id,
            text=message)
        return

    data = get(
        'https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_device.json').content
    db = loads(data)
    device = db[device]
    message = f'<b>{name}</b> variants:\n\n'

    for i in device:
        name = i['name']
        model = i['model']
        message += '<b>Model</b>: <code>{}</code> \n<b>Name:</b> <code>{}</code>\n\n'.format(
            model, name)

    await c.send_message(
        chat_id=update.chat.id,
        text=message)


@pbot.on_message(filters.command(["samget", "samcheck"]))
async def check(c: Client, update: Update):
    if len(update.command) != 3:
        message = "Please type your device <b>MODEL</b> and <b>CSC</b> into it!\ni.e <code>/fw SM-G975F XSG!</code>"
        await c.send_message(
            chat_id=update.chat.id,
            text=message)
        return

    cmd, temp, csc = update.command
    model = 'sm-' + temp if not temp.upper().startswith('SM-') else temp
    fota = get(
        f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.xml')
    test = get(
        f'http://fota-cloud-dn.ospserver.net/firmware/{csc.upper()}/{model.upper()}/version.test.xml')
    if test.status_code != 200:
        message = f"Couldn't find any firmwares for {temp.upper()} - {csc.upper()}, please refine your search or try again later!"
        await c.send_message(
            chat_id=update.chat.id,
            text=message)
        return

    page1 = BeautifulSoup(fota.content, 'lxml')
    page2 = BeautifulSoup(test.content, 'lxml')
    os1 = page1.find("latest").get("o")
    os2 = page2.find("latest").get("o")
    if page1.find("latest").text.strip():
        pda1, csc1, phone1 = page1.find("latest").text.strip().split('/')
        message = f'<b>\nMODEL:</b> <code>{model.upper()}</code>\n<b>CSC:</b> <code>{csc.upper()}</code>\n'
        message += '<b>Latest Avaliable Firmware:</b>\n'
        message += f'• PDA: <code>{pda1}</code>\n• CSC: <code>{csc1}</code>\n'
        if phone1:
            message += f'• Phone: <code>{phone1}</code>\n'
        if os1:
            message += f'• Android: <code>{os1}</code>\n'
        message += '\n'
    else:
        message = f'<b>No public release found for {model.upper()} and {csc.upper()}.</b>\n\n'
    message += '<b>Latest Test Firmware:</b>\n'
    if len(page2.find("latest").text.strip().split('/')) == 3:
        pda2, csc2, phone2 = page2.find("latest").text.strip().split('/')
        message += f'• PDA: <code>{pda2}</code>\n• CSC: <code>{csc2}</code>\n'
        if phone2:
            message += f'• Phone: <code>{phone2}</code>\n'
        if os2:
            message += f'• Android: <code>{os2}</code>\n'
    else:
        md5 = page2.find("latest").text.strip()
        message += f'• Hash: <code>{md5}</code>\n• Android: <code>{os2}</code>\n\n'
    cmd.split()
    if cmd in ("samcheck"):
        await c.send_message(
            chat_id=update.chat.id,
            text=message)
    elif cmd in ("samget"):
        message += "\n**Download from below:**\n"
        keyboard = [
            [
                InlineKeyboardButton(
                    site_name, url=fw_link.format(model.upper(), csc.upper())
                )
            ]
            for site_name, fw_link in fw_links
        ]

        await c.send_message(
            chat_id=update.chat.id,
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard))


@pbot.on_message(filters.command("twrp"))
async def twrp(c: Client, update: Update):
    if not len(update.command) == 2:
        m = "Type the device codename, example: <code>/twrp j7xelte</code>"
        await c.send_message(
            chat_id=update.chat.id,
            text=m)
        return

    device = update.command[1]
    url = get(f'https://dl.twrp.me/{device}/')
    if url.status_code == 404:
        m = "TWRP is not available for <code>{device}</code>"
        await c.send_message(
            chat_id=update.chat.id,
            text=m)
        return
    m = f'<b>Latest TWRP for {device}</b>\n'
    page = BeautifulSoup(url.content, 'lxml')
    date = page.find("em").text.strip()
    m += f'📅 <b>Updated:</b> <code>{date}</code>\n'
    trs = page.find('table').find_all('tr')
    row = 2 if trs[0].find('a').text.endswith('tar') else 1

    for i in range(row):
        download = trs[i].find('a')
        dl_link = f"https://dl.twrp.me{download['href']}"
        dl_file = download.text
        size = trs[i].find("span", {"class": "filesize"}).text
    m += f'📥 <b>Size:</b> <code>{size}</code>\n'
    m += f'📦 <b>File:</b> <code>{dl_file.lower()}</code>'
    keyboard = [[InlineKeyboardButton(
        text="Click here to download", url=dl_link)]]
    await c.send_message(
        chat_id=update.chat.id,
        text=m,
        reply_markup=InlineKeyboardMarkup(keyboard))
