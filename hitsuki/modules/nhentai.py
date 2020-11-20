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

import requests
from telegraph import Telegraph

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                            InlineQueryResultArticle, InputTextMessageContent)

from hitsuki import pbot

telegraph = Telegraph()
telegraph.create_account(short_name='hitsuki')


@pbot.on_message(filters.command('nhentai'))
async def nhentai(c: Client, m: Message):
    query = m.text.split(" ")[1]
    title, tags, artist, total_pages, post_url, cover_image = nhentai_data(query)
    await m.reply_text(
         f"<code>{title}</code>\n\n<b>Tags:</b>\n{tags}\n<b>Artists:</b>\n{artist}\n<b>Pages:</b>\n{total_pages}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Read Here",
                        url=post_url
                    )
                ]
            ]
        )
    )


def nhentai_data(noombers):
    url = f"https://nhentai.net/api/gallery/{noombers}"
    res = requests.get(url).json()
    pages = res["images"]["pages"]
    info = res["tags"]
    title = res["title"]["english"]
    links = []
    tags = ""
    artist = ''
    total_pages = res['num_pages']
    post_content = ""

    extensions = {
        'j':'jpg',
        'p':'png',
        'g':'gif'
    }
    for i, x in enumerate(pages):
        media_id = res["media_id"]
        temp = x['t']
        file = f"{i+1}.{extensions[temp]}"
        link = f"https://i.nhentai.net/galleries/{media_id}/{file}"
        links.append(link)

    for i in info:
        if i["type"]=="tag":
            tag = i['name']
            tag = tag.split(" ")
            tag = "_".join(tag)
            tags+=f"#{tag} "
        if i["type"]=="artist":
            artist=f"{i['name']} "

    for link in links:
        post_content+=f"<img src={link}><br>"

    post = telegraph.create_page(
        f"{title}",
        html_content=post_content,
        author_name="Hitsuki", 
        author_url="https://t.me/LordHitsuki_BOT"
    )
    return title,tags,artist,total_pages,post['url'],links[0]
