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
from inspect import getfullargspec

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from hitsuki import pbot
from hitsuki.modules.tr_engine.strings import tld

url = 'https://graphql.anilist.co'


def shorten(description, info='anilist.co'):
    ms_g = ""
    if len(description) > 700:
        description = description[0:500] + '...'
        ms_g += f"\n**Description**: __{description}__ [Read More]({info})"
    else:
        ms_g += f"\n**Description**: __{description}__"
    return (
        ms_g.replace("<br>", "")
        .replace("</br>", "")
        .replace("<i>", "")
        .replace("</i>", "")
    )


# time formatter from uniborg
def t(milliseconds: int) -> str:
    """Inputs time in milliseconds, to get beautified time,
    as string"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + " Days, ") if days else "") + \
        ((str(hours) + " Hours, ") if hours else "") + \
        ((str(minutes) + " Minutes, ") if minutes else "") + \
        ((str(seconds) + " Seconds, ") if seconds else "") + \
        ((str(milliseconds) + " ms, ") if milliseconds else "")
    return tmp[:-2]


airing_query = '''
    query ($id: Int,$search: String) { 
      Media (id: $id, type: ANIME,search: $search) { 
        id
        episodes
        title {
          romaji
          english
          native
        }
        siteUrl
        nextAiringEpisode {
           airingAt
           timeUntilAiring
           episode
        } 
      }
    }
'''

fav_query = """
query ($id: Int) { 
      Media (id: $id, type: ANIME) { 
        id
        title {
          romaji
          english
          native
        }
     }
}
"""

anime_query = '''
   query ($id: Int,$search: String) { 
      Media (id: $id, type: ANIME,search: $search) { 
        id
        idMal
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          episodes
          season
          type
          format
          status
          duration
          siteUrl
          studios{
              nodes{
                   name
              }
          }
          trailer{
               id
               site 
               thumbnail
          }
          averageScore
          genres
          bannerImage
      }
    }
'''

character_query = """
    query ($query: String) {
        Character (search: $query) {
               id
               name {
                     first
                     last
                     full
               }
               siteUrl
               favourites
               image {
                        large
               }
               description
        }
    }
"""

manga_query = """
query ($id: Int,$search: String) { 
      Media (id: $id, type: MANGA,search: $search) { 
        id
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          type
          format
          status
          siteUrl
          averageScore
          genres
          bannerImage
      }
    }
"""


async def edrep(m: Message, **kwargs):
    func = m.edit_text if m.from_user.is_self else m.reply
    spec = getfullargspec(func.__wrapped__).args
    await func(**{k: v for k, v in kwargs.items() if k in spec})


@pbot.on_message(filters.command('airing'))
async def anime_airing(c: Client, m: Message):
    search_str = m.text.split(' ', 1)
    chat_id = m.chat.id
    if len(search_str) == 1:
        await m.reply_text(tld(chat_id, "anime_no_arg"))
        return
    variables = {'search': search_str[1]}
    response = requests.post(
        url, json={'query': airing_query, 'variables': variables}).json()['data']['Media']
    ms_g = f"**Name**: **{response['title']['romaji']}**(`{response['title']['native']}`)\n**ID**: `{response['id']}`"
    if response['nextAiringEpisode']:
        airing_time = response['nextAiringEpisode']['timeUntilAiring'] * 1000
        airing_time_final = t(airing_time)
        ms_g += f"\n**Episode**: `{response['nextAiringEpisode']['episode']}`\n**Airing In**: `{airing_time_final}`"
    else:
        ms_g += f"\n**Episode**:{response['episodes']}\n**Status**: `N/A`"
    await m.reply_text(ms_g)


@pbot.on_message(filters.command('anime'))
async def anime_search(c: Client, m: Message):
    search = m.text.split(' ', 1)
    chat_id = m.chat.id
    if len(search) == 1:
        await m.reply_text(tld(chat_id, "anime_no_arg"))
        return
    else:
        search = search[1]
    variables = {'search': search}
    json = requests.post(url, json={'query': anime_query, 'variables': variables}).json()[
        'data'].get('Media', None)
    if json:
        msg = f"**{json['title']['romaji']}**(`{json['title']['native']}`)\n**Type**: {json['format']}\n**Status**: {json['status']}\n**Episodes**: {json.get('episodes', 'N/A')}\n**Duration**: {json.get('duration', 'N/A')} Per Ep.\n**Score**: {json['averageScore']}\n**Genres**: `"
        for x in json['genres']:
            msg += f"{x}, "
        msg = msg[:-2] + '`\n'
        msg += tld(chat_id, "anime_studios")
        for x in json['studios']['nodes']:
            msg += f"{x['name']}, "
        msg = msg[:-2] + '`\n'
        info = json.get('siteUrl')
        trailer = json.get('trailer', None)
        if trailer:
            trailer_id = trailer.get('id', None)
            site = trailer.get('site', None)
            if site == "youtube":
                trailer = 'https://youtu.be/' + trailer_id
        description = json.get(
            'description', 'N/A').replace('<i>', '').replace('</i>', '').replace('<br>', '')
        msg += shorten(description, info)
        image = info.replace('anilist.co/anime/', 'img.anili.st/media/')
        more_info = tld(chat_id, "anime_more_info")
        if trailer:
            buttons = [
                [InlineKeyboardButton(more_info, url=info),
                 InlineKeyboardButton("Trailer 🎬", url=trailer)]
            ]
        else:
            buttons = [
                [InlineKeyboardButton(more_info, url=info)]
            ]
        if image:
            try:
                await m.reply_photo(image, caption=msg, reply_markup=InlineKeyboardMarkup(buttons))
            except:
                msg += f" [〽️]({image})"
                await m.edit(msg)
        else:
            await m.edit(msg)


@pbot.on_message(filters.command('character'))
async def character_search(c: Client, m: Message):
    search = m.text.split(' ', 1)
    chat_id = m.chat.id
    if len(search) == 1:
        await m.reply_text(tld(chat_id, "character_no_arg"))
        return
    search = search[1]
    variables = {'query': search}
    json = requests.post(url, json={'query': character_query, 'variables': variables}).json()[
        'data'].get('Character', None)
    if json:
        ms_g = f"**{json.get('name').get('full')}**(`{json.get('name').get('native')}`)\n"
        description = f"{json['description']}"
        site_url = json.get('siteUrl')
        ms_g += shorten(description, site_url)
        image = json.get('image', None)
        if image:
            image = image.get('large')
            await m.reply_photo(image, caption=ms_g)
        else:
            await edrep(m, text=ms_g)


@pbot.on_message(filters.command('manga'))
async def manga_search(c: Client, m: Message):
    search = m.text.split(' ', 1)
    chat_id = m.chat.id
    if len(search) == 1:
        await m.reply_text(tld(chat_id, "manga_no_arg"))
        return
    search = search[1]
    variables = {'search': search}
    json = requests.post(url, json={'query': manga_query, 'variables': variables}).json()[
        'data'].get('Media', None)
    ms_g = ''
    if json:
        title, title_native = json['title'].get(
            'romaji', False), json['title'].get('native', False)
        start_date, status, score = json['startDate'].get('year', False), json.get(
            'status', False), json.get('averageScore', False)
        if title:
            ms_g += f"**{title}**"
            if title_native:
                ms_g += f"(`{title_native}`)"
        if start_date:
            ms_g += tld(chat_id, "manga_start_date").format(start_date)
        if status:
            ms_g += tld(chat_id, "manga_status").format(status)
        if score:
            ms_g += tld(chat_id, "manga_score").format(score)
        ms_g += tld(chat_id, "manga_genre")
        for x in json.get('genres', []):
            ms_g += f"{x}, "
        ms_g = ms_g[:-2]

        image = json.get("bannerImage", False)
        ms_g += f"\n__{json.get('description', None)}__"
        if image:
            try:
                await m.reply_photo(image, caption=ms_g)
            except:
                ms_g += f" [〽️]({image})"
                await edrep(m, text=ms_g)
        else:
            await edrep(m, text=ms_g)
