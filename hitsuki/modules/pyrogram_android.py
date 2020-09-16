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
from rapidjson import loads
from bs4 import BeautifulSoup

from pyrogram import Client, filters
from pyrogram.types import Message, Update

from hitsuki import pbot


class GetDevice:
    def __init__(self, device):
        """Get device info by codename or model!"""
        self.device = device
    def get(self):
        if self.device.lower().startswith('sm-'):
            data = get('https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_model.json').content
            db = loads(data)
            try:
                name = db[self.device.upper()][0]['name']
                device = db[self.device.upper()][0]['device']
                brand = db[self.device.upper()][0]['brand']
                model = self.device.lower()
                return {'name': name,'device': device,'model':model,'brand': brand}
            except KeyError:
                return False
        else:
            data = get('https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_device.json').content
            db = loads(data)
            newdevice = self.device.strip('lte').lower() if self.device.startswith('beyond') else self.device.lower()
            try:
                name = db[newdevice][0]['name']
                model = db[newdevice][0]['model']
                brand = db[newdevice][0]['brand']
                device = self.device.lower()
                return {'name': name,'device': device,'model':model,'brand': brand}
            except KeyError:
                return False


@pbot.on_message(filters.command(["specs", "spec"]))
async def specs(c: Client, update: Update):
    if not len(update.command) == 2:
        message = "Please write your codename or model into it,\ni.e <code>/specs herolte</code> or <code>/specs sm-g610f</code>"
        await c.send_message(
                chat_id=update.chat.id,
                text=message)
        return
    device = update.command[1]
    data = GetDevice(device).get()
    if data:
        name = data['name']
        model = data['model']
        device = name.lower().replace(' ' , '-')
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
            title = re.findall(r'<td>.*?</td>', str(info))[0].strip().replace('td', 'b')
            data = re.findall(r'<td>.*?</td>', str(info))[-1].strip().replace('td', 'code')
            message += "• {}: <code>{}</code>\n".format(title, data)
        await c.send_message(
                    chat_id=update.chat.id,
                    text=message)
    else:
        giz = get(f'https://www.gizmochina.com/product/samsung-{device}/')
        if giz.status_code == 404:
            message = "device specs not found in bot databases!"
            await c.send_message(
                    chat_id=update.chat.id,
                    text=message)
            return
        page = BeautifulSoup(giz.content, 'lxml')
        message = '<b>Device:</b> Samsung {}\n'.format(name)
        for info in page.find_all('div', {'class': 'aps-feature-info'}):
            title = info.find('strong').text
            data = info.find('span').text
            message += "• {}: <code>{}</code>\n".format(title, data)
        await c.send_message(
                    chat_id=update.chat.id,
                    text=message)


@pbot.on_message(filters.command(["whatis", "device", "codename"]))
async def models(c: Client, update: Update):
    if not len(update.command) == 2:
        message = "Please write your codename into it, i.e <code>/whatis herolte</code>"
        await c.send_message(
                chat_id=update.chat.id,
                text=message,
                disable_web_page_preview=True
            )
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
                disable_web_page_preview=True
            )


@pbot.on_message(filters.command(["variants", "models"]))
async def variants(c: Client, update: Update):
    if not len(update.command) == 2:
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
    data = get('https://raw.githubusercontent.com/androidtrackers/certified-android-devices/master/by_device.json').content
    db = loads(data)
    device=db[device]
    message = f'<b>{name}</b> variants:\n\n'
    for i in device:
        name =  i['name']
        model = i['model']
        message += '<b>Model</b>: <code>{}</code> \n<b>Name:</b> <code>{}</code>\n\n'.format(model, name)

    await c.send_message(
        chat_id=update.chat.id,
        text=message)