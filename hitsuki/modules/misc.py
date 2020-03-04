import html
import json
import random
from datetime import datetime
from typing import Optional, List
import time
import locale

import requests
from telegram.error import BadRequest, Unauthorized
from telegram import Message, Chat, Update, Bot, MessageEntity, InlineKeyboardMarkup
from telegram import ParseMode
from telegram.ext import CommandHandler, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_html, mention_markdown

from hitsuki import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, BAN_STICKER, spamfilters
from hitsuki.__main__ import STATS, USER_INFO
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.helper_funcs.extraction import extract_user
from hitsuki.modules.helper_funcs.filters import CustomFilters
from hitsuki.modules.helper_funcs.msg_types import get_message_type
from hitsuki.modules.helper_funcs.misc import build_keyboard_alternate

from hitsuki.modules.languages import tl
from hitsuki.modules.sql import languages_sql as lang_sql
import hitsuki.modules.sql.feds_sql as feds_sql
from hitsuki.modules.helper_funcs.alternate import send_message

# Change language locale to Indonesia
# Install language:
# - sudo apt-get install language-pack-id language-pack-id-base manpages
# locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')

RUN_STRINGS = (
    "Where do you think you're going?",
    "Huh? what? did they get away?",
    "ZZzzZZzz... Huh? what? oh, just them again, nevermind.",
    "Get back here!",
    "Not so fast...",
    "Look out for the wall!",
    "Don't leave me alone with them!!",
    "You run, you die.",
    "Jokes on you, I'm everywhere",
    "You're gonna regret that...",
    "You could also try /kickme, I hear that's fun.",
    "Go bother someone else, no-one here cares.",
    "You can run, but you can't hide.",
    "Is that all you've got?",
    "I'm behind you...",
    "You've got company!",
    "We can do this the easy way, or the hard way.",
    "You just don't get it, do you?",
    "Yeah, you better run!",
    "Please, remind me how much I care?",
    "I'd run faster if I were you.",
    "That's definitely the droid we're looking for.",
    "May the odds be ever in your favour.",
    "Famous last words.",
    "And they disappeared forever, never to be seen again.",
    "\"Oh, look at me! I'm so cool, I can run from a bot!\" - this person",
    "Yeah yeah, just tap /kickme already.",
    "Here, take this ring and head to Mordor while you're at it.",
    "Legend has it, they're still running...",
    "Unlike Harry Potter, your parents can't protect you from me.",
    "Fear leads to anger. Anger leads to hate. Hate leads to suffering. If you keep running in fear, you might "
    "be the next Vader.",
    "Multiple calculations later, I have decided my interest in your shenanigans is exactly 0.",
    "Legend has it, they're still running.",
    "Keep it up, not sure we want you here anyway.",
    "You're a wiza- Oh. Wait. You're not Harry, keep moving.",
    "NO RUNNING IN THE HALLWAYS!",
    "Hasta la vista, baby.",
    "Who let the dogs out?",
    "It's funny, because no one cares.",
    "Ah, what a waste. I liked that one.",
    "Frankly, my dear, I don't give a damn.",
    "My milkshake brings all the boys to yard... So run faster!",
    "You can't HANDLE the truth!",
    "A long time ago, in a galaxy far far away... Someone would've cared about that. Not anymore though.",
    "Hey, look at them! They're running from the inevitable banhammer... Cute.",
    "Han shot first. So will I.",
    "What are you running after, a white rabbit?",
    "As The Doctor would say... RUN!",
)
 
SLAP_TEMPLATES = (
    "{user1} {hits} {user2} with *{item}*. {emoji}",
    "{user1} {hits} {user2} in the face with *{item}*. {emoji}",
    "{user1} {hits} {user2} around a bit with *{item}*. {emoji}",
    "{user1} {throws} *{item}* at {user2}. {emoji}",
    "{user1} grabs *{item}* and {throws} it at {user2}'s face. {emoji}",
    "{user1} launches *{item}* in {user2}'s general direction. {emoji}",
    "{user1} starts slapping {user2} silly with *{item}*. {emoji}",
    "{user1} pins {user2} down and repeatedly {hits} them with *{item}*. {emoji}",
    "{user1} grabs up *{item}* and {hits} {user2} with it. {emoji}",
    "{user1} ties {user2} to a chair and {throws} *{item}* at them. {emoji}",
)
 
PUNCH_TEMPLATES = (
    "{user1} {punches} {user2} to assert dominance.",
    "{user1} {punches} {user2} to see if they shut the fuck up for once.",
    "{user1} {punches} {user2} because they were asking for it.",
    "It's over {user2}, they have the high ground.",
    "{user1} performs a superman punch on {user2}, {user2} is rekt now.",
    "{user1} kills off {user2} with a T.K.O",
    "{user1} attacks {user2} with a billiard cue. A bloody mess.",
    "{user1} disintegrates {user2} with a MG.",
    "A hit and run over {user2} performed by {user1}",
    "{user1} punches {user2} into the throat. Warning, choking hazard!",
    "{user1} drops a piano on top of {user2}. A harmonical death.",
    "{user1} throws rocks at {user2}",
    "{user1} forces {user2} to drink chlorox. What a painful death.",
    "{user2} got sliced in half by {user1}'s katana.",
    "{user1} makes {user2} fall on their sword. A stabby death lol.",
    "{user1} kangs {user2} 's life energy away.",
    "{user1} shoot's {user2} into a million pieces. Hasta la vista baby.",
    "{user1} drop's the frigde on {user2}. Beware of crushing.",
    "{user1} engage's a guerilla tactic on {user2}",
    "{user1} ignite's {user2} into flames. IT'S LIT FAM.",
    "{user1} pulls a loaded 12 gauge on {user2}.",
    "{user1} throws a Galaxy Note7 into {user2}'s general direction. A bombing massacre.",
    "{user1} walks with {user2} to the end of the world, then pushes him over the edge.",
    "{user1} performs a Stabby McStabby on {user2} with a butterfly.",
    "{user1} cut's {user2}'s neck off with a machete. A blood bath.",
    "{user1} secretly fills in {user2}'s cup with Belle Delphine's Gamer Girl Bathwater instead of water. Highly contagious herpes.",
    "{user1} is tea cupping on {user2} after a 1v1, to assert their dominance.",
    "{user1} ask's for {user2}'s last words. {user2} is ded now.",
    "{user1} let's {user2} know their position.",
    "{user1} makes {user2} to his slave. What is your bidding? My Master.",
    "{user1} forces {user2} to commit suicide.",
    "{user1} shout's 'it's garbage day' at {user2}.",
    "{user1} throws his axe at {user2}.",
    "{user1} is now {user2}'s grim reaper.",
)
 
PUNCH = (
    "punches",
    "RKOs",
    "smashes the skull of",
    "throws a pipe wrench at",
)
 
ITEMS = (
    "a Samsung J5 2017",
    "a Samsung S10+",
    "an iPhone XS MAX",
    "a Note 9",
    "a Note 10+",
    "knox 0x0",
    "OneUI 2.0",
    "OneUI 69.0",
    "TwoUI 1.0",
    "Secure Folder",
    "Samsung Pay",
    "prenormal RMM state",
    "prenormal KG state",
    "a locked bootloader",
    "payment lock",
    "stock rom",
    "good rom",
    "Good Lock apps",
    "Q port",
    "Pie port",
    "8.1 port",
    "Pie port",
    "Pie OTA",
    "Q OTA",
    "LineageOS 16",
    "LineageOS 17",
    "a bugless rom",
    "a kernel",
    "a kernal",
    "a karnal",
    "a karnel",
    "official TWRP",
    "VOLTE",
    "kanged rom",
    "an antikang",
    "audio fix",
    "hwcomposer fix",
    "mic fix",
    "random reboots",
    "bootloops",
    "unfiltered logs",
    "a keylogger",
    "120FPS",
    "a download link",
    "168h uptime",
    "a paypal link",
    "treble support",
    "EVO-X gsi",
    "Q gsi",
    "Q beta",
    "a Rom Control",
    "a hamburger",
    "a cheeseburger",
    "a Big-Mac",
)
 
THROW = (
    "throws",
    "flings",
    "chucks",
    "hurls",
)
 
HIT = (
    "hits",
    "whacks",
    "slaps",
    "smacks",
    "spanks",
    "bashes",
)

EMOJI = (
    "\U0001F923",
    "\U0001F602",
    "\U0001F922",
    "\U0001F605",
    "\U0001F606",
    "\U0001F609",
    "\U0001F60E",
    "\U0001F929",
    "\U0001F623",
    "\U0001F973",
    "\U0001F9D0",
    "\U0001F632",
)

SHRUGS = (
    "┐(´д｀)┌",
    "┐(´～｀)┌",
    "┐(´ー｀)┌",
    "┐(￣ヘ￣)┌",
    "╮(╯∀╰)╭",
    "╮(╯_╰)╭",
    "┐(´д`)┌",
    "┐(´∀｀)┌",
    "ʅ(́◡◝)ʃ",
    "┐(ﾟ～ﾟ)┌",
    "┐('д')┌",
    "┐(‘～`;)┌",
    "ヘ(´－｀;)ヘ",
    "┐( -“-)┌",
    "ʅ（´◔౪◔）ʃ",
    "ヽ(゜～゜o)ノ",
    "ヽ(~～~ )ノ",
    "┐(~ー~;)┌",
    "┐(-。ー;)┌",
    r"¯\_(ツ)_/¯",
    r"¯\_(⊙_ʖ⊙)_/¯",
    r"¯\_༼ ಥ ‿ ಥ ༽_/¯",
    "乁( ⁰͡  Ĺ̯ ⁰͡ ) ㄏ",
)
 
HUGS = (
"⊂(・﹏・⊂)",
"⊂(・ヮ・⊂)",
"⊂(・▽・⊂)",
"(っಠ‿ಠ)っ",
"ʕっ•ᴥ•ʔっ",
"（っ・∀・）っ",
"(っ⇀⑃↼)っ",
"(つ´∀｀)つ",
"(.づσ▿σ)づ.",
"⊂(´・ω・｀⊂)",
"(づ￣ ³￣)づ",
"(.づ◡﹏◡)づ.",
)

normiefont = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
weebyfont = ['卂','乃','匚','刀','乇','下','厶','卄','工','丁','长','乚','从','𠘨','口','尸','㔿','尺','丂','丅','凵','リ','山','乂','丫','乙']


@run_async
def shrug(bot: Bot, update: Update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text = reply_text(random.choice(SHRUGS))
 
 
@run_async
def hug(bot: Bot, update: Update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text = reply_text(random.choice(HUGS))


@run_async
def runs(bot: Bot, update: Update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    send_message(update.effective_message, random.choice(tl(update.effective_message, "RUN_STRINGS")))


@run_async
def slap(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    msg = update.effective_message  # type: Optional[Message]

    # reply to correct message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name, msg.from_user.id)

    user_id = extract_user(update.effective_message, args)
    if user_id == bot.id or user_id == 777000:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user
    elif user_id:
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        if slapped_user.username:
            user2 = "@" + escape_markdown(slapped_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(slapped_user.first_name,
                                                   slapped_user.id)

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = random.choice(SLAP_TEMPLATES)
    item = random.choice(ITEMS)
    hit = random.choice(HIT)
    throw = random.choice(THROW)
    emoji = random.choice(EMOJI)

    repl = temp.format(user1=user1, user2=user2, item=item, hits=hit, throws=throw, emoji=emoji)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)


BASE_URL = 'https://del.dog'


@run_async
def paste(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    message = update.effective_message

    if message.reply_to_message:
        data = message.reply_to_message.text
    elif len(args) >= 1:
        data = message.text.split(None, 1)[1]
    else:
        message.reply_text("What am I supposed to do with this?!")
        return

    r = requests.post(f'{BASE_URL}/documents', data=data.encode('utf-8'))

    if r.status_code == 404:
        update.effective_message.reply_text('Failed to reach dogbin')
        r.raise_for_status()

    res = r.json()

    if r.status_code != 200:
        update.effective_message.reply_text(res['message'])
        r.raise_for_status()

    key = res['key']
    if res['isUrl']:
        reply = f'Shortened URL: {BASE_URL}/{key}\nYou can view stats, etc. [here]({BASE_URL}/v/{key})'
    else:
        reply = f'{BASE_URL}/{key}'
    update.effective_message.reply_text(reply, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


@run_async
def get_paste_content(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    message = update.effective_message

    if len(args) >= 1:
        key = args[0]
    else:
        message.reply_text("Please supply a paste key!")
        return

    format_normal = f'{BASE_URL}/'
    format_view = f'{BASE_URL}/v/'

    if key.startswith(format_view):
        key = key[len(format_view):]
    elif key.startswith(format_normal):
        key = key[len(format_normal):]

    r = requests.get(f'{BASE_URL}/raw/{key}')

    if r.status_code != 200:
        try:
            res = r.json()
            update.effective_message.reply_text(res['message'])
        except Exception:
            if r.status_code == 404:
                update.effective_message.reply_text('Failed to reach dogbin')
            else:
                update.effective_message.reply_text('Unknown error occured')
        r.raise_for_status()

    update.effective_message.reply_text('```' + escape_markdown(r.text) + '```', parse_mode=ParseMode.MARKDOWN)


@run_async
def get_paste_stats(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    message = update.effective_message

    if len(args) >= 1:
        key = args[0]
    else:
        message.reply_text("Please supply a paste key!")
        return

    format_normal = f'{BASE_URL}/'
    format_view = f'{BASE_URL}/v/'

    if key.startswith(format_view):
        key = key[len(format_view):]
    elif key.startswith(format_normal):
        key = key[len(format_normal):]

    r = requests.get(f'{BASE_URL}/documents/{key}')

    if r.status_code != 200:
        try:
            res = r.json()
            update.effective_message.reply_text(res['message'])
        except Exception:
            if r.status_code == 404:
                update.effective_message.reply_text('Failed to reach dogbin')
            else:
                update.effective_message.reply_text('Unknown error occured')
        r.raise_for_status()

    document = r.json()['document']
    key = document['_id']
    views = document['viewCount']
    reply = f'Stats for **[/{key}]({BASE_URL}/{key})**:\nViews: `{views}`'
    update.effective_message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


@run_async
def weebify(bot: Bot, update: Update, args):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    msg = update.effective_message
    if args:
        string = " ".join(args).lower()
    elif msg.reply_to_message:
        string = msg.reply_to_message.text.lower()
    else:
        msg.reply_text("Enter some text to weebify or reply to someone's message!")
        return
        
    for normiecharacter in string:
        if normiecharacter in normiefont:
            weebycharacter = weebyfont[normiefont.index(normiecharacter)]
            string = string.replace(normiecharacter, weebycharacter)
 
    if msg.reply_to_message:
        msg.reply_to_message.reply_text(string)
    else:
        msg.reply_text(string)


@run_async
def pat(bot: Bot, update: Update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    chat_id = update.effective_chat.id
    msg = str(update.message.text)
    try:
        msg = msg.split(" ", 1)[1]
    except IndexError:
        msg = ""
    msg_id = update.effective_message.reply_to_message.message_id if update.effective_message.reply_to_message else update.effective_message.message_id
    pats = []
    pats = json.loads(urllib.request.urlopen(urllib.request.Request(
    'http://headp.at/js/pats.json',
    headers={'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686) '
         'Gecko/20071127 Firefox/2.0.0.11'}
    )).read().decode('utf-8'))
    if "@" in msg and len(msg) > 5:
        bot.send_photo(chat_id, f'https://headp.at/pats/{urllib.parse.quote(random.choice(pats))}', caption=msg)
    else:
        bot.send_photo(chat_id, f'https://headp.at/pats/{urllib.parse.quote(random.choice(pats))}', reply_to_message_id=msg_id)


@run_async
def get_bot_ip(bot: Bot, update: Update):
    """ Sends the bot's IP address, so as to be able to ssh in if necessary.
        OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    send_message(update.effective_message, res.text)


@run_async
def get_id(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    user_id = extract_user(update.effective_message, args)
    if user_id:
        if update.effective_message.reply_to_message and update.effective_message.reply_to_message.forward_from:
            user1 = update.effective_message.reply_to_message.from_user
            user2 = update.effective_message.reply_to_message.forward_from
            send_message(update.effective_message, 
                tl(update.effective_message, "Pengirim asli, {}, memiliki ID `{}`.\nSi penerus pesan, {}, memiliki ID `{}`.").format(
                    escape_markdown(user2.first_name),
                    user2.id,
                    escape_markdown(user1.first_name),
                    user1.id),
                parse_mode=ParseMode.MARKDOWN)
        else:
            user = bot.get_chat(user_id)
            send_message(update.effective_message, tl(update.effective_message, "Id {} adalah `{}`.").format(escape_markdown(user.first_name), user.id),
                                                parse_mode=ParseMode.MARKDOWN)
    else:
        chat = update.effective_chat  # type: Optional[Chat]
        if chat.type == "private":
            send_message(update.effective_message, tl(update.effective_message, "Id Anda adalah `{}`.").format(chat.id),
                                                parse_mode=ParseMode.MARKDOWN)

        else:
            send_message(update.effective_message, tl(update.effective_message, "Id grup ini adalah `{}`.").format(chat.id),
                                                parse_mode=ParseMode.MARKDOWN)


@run_async
def info(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user_id = extract_user(update.effective_message, args)

    if user_id:
        user = bot.get_chat(user_id)

    elif not msg.reply_to_message and not args:
        user = msg.from_user

    elif not msg.reply_to_message and (not args or (
            len(args) >= 1 and not args[0].startswith("@") and not args[0].isdigit() and not msg.parse_entities(
        [MessageEntity.TEXT_MENTION]))):
        send_message(update.effective_message, tl(update.effective_message, "Saya tidak dapat mengekstrak pengguna dari ini."))
        return

    else:
        return

    text = tl(update.effective_message, "<b>Info Pengguna</b>:") \
           + "\nID: <code>{}</code>".format(user.id) + \
           tl(update.effective_message, "\nNama depan: {}").format(html.escape(user.first_name))

    if user.last_name:
        text += tl(update.effective_message, "\nNama belakang: {}").format(html.escape(user.last_name))

    if user.username:
        text += tl(update.effective_message, "\nNama pengguna: @{}").format(html.escape(user.username))

    text += tl(update.effective_message, "\nTautan pengguna permanen: {}").format(mention_html(user.id, "link"))

    if user.id == OWNER_ID:
        text += tl(update.effective_message, "\n\nOrang ini adalah pemilik saya - saya tidak akan pernah melakukan apa pun terhadap mereka!")
    else:
        if user.id in SUDO_USERS:
            text += tl(update.effective_message, "\n\nOrang ini adalah salah satu pengguna sudo saya! " \
                    "Hampir sama kuatnya dengan pemilik saya - jadi tontonlah.")
        else:
            if user.id in SUPPORT_USERS:
                text += tl(update.effective_message, "\n\nOrang ini adalah salah satu pengguna dukungan saya! " \
                        "Tidak sekuat pengguna sudo, tetapi masih dapat menyingkirkan Anda dari peta.")

            if user.id in WHITELIST_USERS:
                text += tl(update.effective_message, "\n\nOrang ini telah dimasukkan dalam daftar putih! " \
                        "Itu berarti saya tidak diizinkan untuk melarang/menendang mereka.")

    fedowner = feds_sql.get_user_owner_fed_name(user.id)
    if fedowner:
        text += tl(update.effective_message, "\n\n<b>Pengguna ini adalah pemilik federasi ini:</b>\n<code>")
        text += "</code>, <code>".join(fedowner)
        text += "</code>"
    # fedadmin = feds_sql.get_user_admin_fed_name(user.id)
    # if fedadmin:
    #     text += tl(update.effective_message, "\n\nThis user is a fed admin in the current federation:\n")
    #     text += ", ".join(fedadmin)

    for mod in USER_INFO:
        mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@run_async
def get_time(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    location = " ".join(args)
    if location.lower() == bot.first_name.lower():
        send_message(update.effective_message, tl(update.effective_message, "Selalu ada waktu banned untukku!"))
        bot.send_sticker(update.effective_chat.id, BAN_STICKER)
        return

    res = requests.get(GMAPS_LOC, params=dict(address=location, key=MAPS_API))
    print(res.text)

    if res.status_code == 200:
        loc = json.loads(res.text)
        if loc.get('status') == 'OK':
            lat = loc['results'][0]['geometry']['location']['lat']
            long = loc['results'][0]['geometry']['location']['lng']

            country = None
            city = None

            address_parts = loc['results'][0]['address_components']
            for part in address_parts:
                if 'country' in part['types']:
                    country = part.get('long_name')
                if 'administrative_area_level_1' in part['types'] and not city:
                    city = part.get('long_name')
                if 'locality' in part['types']:
                    city = part.get('long_name')

            if city and country:
                location = "{}, {}".format(city, country)
            elif country:
                location = country

            timenow = int(datetime.utcnow().timestamp())
            res = requests.get(GMAPS_TIME, params=dict(location="{},{}".format(lat, long), timestamp=timenow))
            if res.status_code == 200:
                offset = json.loads(res.text)['dstOffset']
                timestamp = json.loads(res.text)['rawOffset']
                time_there = datetime.fromtimestamp(timenow + timestamp + offset).strftime("%H:%M:%S hari %A %d %B")
                send_message(update.effective_message, "Sekarang pukul {} di {}".format(time_there, location))


@run_async
def get_time_alt(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    if args:
        location = " ".join(args)
        if location.lower() == bot.first_name.lower():
            send_message(update.effective_message, "Selalu ada waktu banned untukku!")
            bot.send_sticker(update.effective_chat.id, BAN_STICKER)
            return

        res = requests.get('https://dev.virtualearth.net/REST/v1/timezone/?query={}&key={}'.format(location, MAPS_API))

        if res.status_code == 200:
            loc = res.json()
            if len(loc['resourceSets'][0]['resources'][0]['timeZoneAtLocation']) == 0:
                send_message(update.effective_message, tl(update.effective_message, "Lokasi tidak di temukan!"))
                return
            placename = loc['resourceSets'][0]['resources'][0]['timeZoneAtLocation'][0]['placeName']
            localtime = loc['resourceSets'][0]['resources'][0]['timeZoneAtLocation'][0]['timeZone'][0]['convertedTime']['localTime']
            if lang_sql.get_lang(update.effective_chat.id) == "id":
                locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
                time = datetime.strptime(localtime, '%Y-%m-%dT%H:%M:%S').strftime("%H:%M:%S hari %A, %d %B")
            else:
                time = datetime.strptime(localtime, '%Y-%m-%dT%H:%M:%S').strftime("%H:%M:%S %A, %d %B")
            send_message(update.effective_message, tl(update.effective_message, "Sekarang pukul `{}` di `{}`").format(time, placename), parse_mode="markdown")
    else:
        send_message(update.effective_message, tl(update.effective_message, "Gunakan `/time nama daerah`\nMisal: `/time jakarta`"), parse_mode="markdown")


@run_async
def echo(bot: Bot, update: Update):
    message = update.effective_message
    chat_id = update.effective_chat.id
    try:
        message.delete()
    except BadRequest:
        pass
    # Advanced
    text, data_type, content, buttons = get_message_type(message)
    tombol = build_keyboard_alternate(buttons)
    if str(data_type) in ('Types.BUTTON_TEXT', 'Types.TEXT'):
        try:
            if message.reply_to_message:
                bot.send_message(chat_id, text, parse_mode="markdown", reply_to_message_id=message.reply_to_message.message_id, disable_web_page_preview=True, reply_markup=InlineKeyboardMarkup(tombol))
            else:
                bot.send_message(chat_id, text, quote=False, disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(tombol))
        except BadRequest:
            bot.send_message(chat_id, tl(update.effective_message, "Teks markdown salah!\nJika anda tidak tahu apa itu markdown, silahkan ketik `/markdownhelp` pada PM."), parse_mode="markdown")
            return


@run_async
def markdown_help(bot: Bot, update: Update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    send_message(update.effective_message, tl(update.effective_message, "MARKDOWN_HELP").format(dispatcher.bot.first_name), parse_mode=ParseMode.HTML)
    send_message(update.effective_message, tl(update.effective_message, "Coba teruskan pesan berikut kepada saya, dan Anda akan lihat!"))
    send_message(update.effective_message, tl(update.effective_message, "/save test Ini adalah tes markdown. _miring_, *tebal*, `kode`, "
                                        "[URL](contoh.com) [tombol](buttonurl:github.com) "
                                        "[tombol2](buttonurl:google.com:same)"))


@run_async
def stats(bot: Bot, update: Update):
    send_message(update.effective_message, tl(update.effective_message, "Statistik saat ini:\n") + "\n".join([mod.__stats__() for mod in STATS]))


# /ip is for private use
__help__ = """
*Group tools:*
 - /id: get the current group id. If used by replying to a message, gets that user's id.
 - /info: get information about a user.
 - /markdownhelp: quick summary of how markdown works in telegram - can only be called in private chats.

*Useful tools:*
 - /paste: Create a paste or a shortened url using [dogbin](https://del.dog)
 - /getpaste: Get the content of a paste or shortened url from [dogbin](https://del.dog)
 - /pastestats: Get stats of a paste or shortened url from [dogbin](https://del.dog)
 - /removebotkeyboard: Got a nasty bot keyboard stuck in your group?

*Other things:*
 - /runs: reply a random string from an array of replies.
 - /insults: reply a random string from an array of replies.
 - /slap: slap a user, or get slapped if not a reply.
 - /status: Shows some bot information.
 - /weebify: as a reply to a message, "weebifies" the message.
 - /pat: give a headpat :3
 - /shg or /shrug: pretty self-explanatory.
 - /hug: give a hug and spread the love :)
"""

__mod_name__ = "Misc"

ID_HANDLER = DisableAbleCommandHandler("id", get_id, pass_args=True)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=Filters.chat(OWNER_ID))

TIME_HANDLER = DisableAbleCommandHandler("time", get_time_alt, pass_args=True)

RUNS_HANDLER = DisableAbleCommandHandler(["runs", "lari"], runs)
SLAP_HANDLER = DisableAbleCommandHandler("slap", slap, pass_args=True)
INFO_HANDLER = DisableAbleCommandHandler("info", info, pass_args=True)

PASTE_HANDLER = CommandHandler("paste", paste, pass_args=True)
GET_PASTE_HANDLER = CommandHandler("getpaste", get_paste_content, pass_args=True)
PASTE_STATS_HANDLER = CommandHandler("pastestats", get_paste_stats, pass_args=True)

ECHO_HANDLER = CommandHandler("echo", echo, filters=Filters.user(OWNER_ID))
MD_HELP_HANDLER = CommandHandler("markdownhelp", markdown_help, filters=Filters.private)

STATS_HANDLER = CommandHandler("stats", stats, filters=CustomFilters.sudo_filter)
WEEBIFY_HANDLER = DisableAbleCommandHandler("weebify", weebify, pass_args=True)
PAT_HANDLER = DisableAbleCommandHandler("pat", pat)
SHRUG_HANDLER = DisableAbleCommandHandler(["shrug", "shg"], shrug)
HUG_HANDLER = DisableAbleCommandHandler("hug", hug)

dispatcher.add_handler(ID_HANDLER)
dispatcher.add_handler(IP_HANDLER)
dispatcher.add_handler(TIME_HANDLER)
dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(INFO_HANDLER)
dispatcher.add_handler(ECHO_HANDLER)
dispatcher.add_handler(MD_HELP_HANDLER)
dispatcher.add_handler(STATS_HANDLER)
dispatcher.add_handler(WEEBIFY_HANDLER)
dispatcher.add_handler(PAT_HANDLER)
dispatcher.add_handler(SHRUG_HANDLER)
dispatcher.add_handler(HUG_HANDLER)
dispatcher.add_handler(PASTE_HANDLER)
dispatcher.add_handler(GET_PASTE_HANDLER)
dispatcher.add_handler(PASTE_STATS_HANDLER)
