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

import requests
from telegram import Bot, Update, ParseMode
from telegram.ext import run_async, CommandHandler

import hitsuki.modules.sql.last_fm_sql as sql
from hitsuki import dispatcher, LASTFM_API_KEY
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.tr_engine.strings import tld

# Last.fm module ported from https://github.com/rsktg


@run_async
def set_user(bot: Bot, update: Update, args):
    msg = update.effective_message
    chat = update.effective_chat
    if args:
        user = update.effective_user.id
        username = " ".join(args)
        sql.set_user(user, username)
        msg.reply_text(tld(chat.id, "misc_setuser_lastfm").format(username))
    else:
        msg.reply_text(
            tld(chat.id, "misc_setuser_lastfm_error"))


@run_async
def clear_user(bot: Bot, update: Update):
    user = update.effective_user.id
    chat = update.effective_chat
    sql.set_user(user, "")
    update.effective_message.reply_text(
        tld(chat.id, "misc_clearuser_lastfm"))


@run_async
def last_fm(bot: Bot, update: Update):
    msg = update.effective_message
    user = update.effective_user.first_name
    user_id = update.effective_user.id
    username = sql.get_user(user_id)
    chat = update.effective_chat
    if not username:
        msg.reply_text(tld(chat.id, "misc_lastfm_usernotset"))
        return

    base_url = "http://ws.audioscrobbler.com/2.0"
    res = requests.get(
        f"{base_url}?method=user.getrecenttracks&limit=3&extended=1&user={username}&api_key={LASTFM_API_KEY}&format=json")
    if res.status_code != 200:
        msg.reply_text(tld(chat.id, "misc_lastfm_userwrong"))
        return

    try:
        first_track = res.json().get("recenttracks").get("track")[0]
    except IndexError:
        msg.reply_text(tld(chat.id, "misc_lastfm_nonetracks"))
        return
    if first_track.get("@attr"):
        # Ensures the track is now playing
        image = first_track.get("image")[3].get(
            "#text")  # Grab URL of 300x300 image
        artist = first_track.get("artist").get("name")
        song = first_track.get("name")
        loved = int(first_track.get("loved"))
        rep = tld(chat.id, "misc_lastfm_inp").format(user)
        if not loved:
            rep += tld(chat.id, "misc_lastfm_pn").format(artist, song)
        else:
            rep += tld(chat.id, "misc_lastfm_pn_loved").format(artist, song)
        if image:
            rep += f"<a href='{image}'>\u200c</a>"
    else:
        tracks = res.json().get("recenttracks").get("track")
        track_dict = {tracks[i].get("artist").get(
            "name"): tracks[i].get("name") for i in range(3)}
        rep = tld(chat.id, "misc_lastfm_np").format(user)
        for artist, song in track_dict.items():
            rep += tld(chat.id, "misc_lastfm_scrr").format(artist, song)
        last_user = requests.get(
            f"{base_url}?method=user.getinfo&user={username}&api_key={LASTFM_API_KEY}&format=json").json().get("user")
        scrobbles = last_user.get("playcount")
        rep += tld(chat.id, "misc_lastfm_scr").format(scrobbles)

    msg.reply_text(rep, parse_mode=ParseMode.HTML)


__help__ = True

SET_USER_HANDLER = CommandHandler("setuser", set_user, pass_args=True)
CLEAR_USER_HANDLER = CommandHandler("clearuser", clear_user)
LASTFM_HANDLER = DisableAbleCommandHandler("lastfm", last_fm)

dispatcher.add_handler(SET_USER_HANDLER)
dispatcher.add_handler(CLEAR_USER_HANDLER)
dispatcher.add_handler(LASTFM_HANDLER)
