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

import random
import re
import rapidjson as json
import urllib.request
import urllib.parse
from typing import List

from telegram import Update, Bot, ParseMode
from telegram.ext import run_async
from telegram.utils.helpers import escape_markdown
from zalgo_text import zalgo

from hitsuki import dispatcher
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.helper_funcs.extraction import extract_user
from hitsuki.modules.tr_engine.strings import tld, tld_list

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

REACTS = (
    "ʘ‿ʘ",
    "ヾ(-_- )ゞ",
    "(っ˘ڡ˘ς)",
    "(´ж｀ς)",
    "( ಠ ʖ̯ ಠ)",
    "(° ͜ʖ͡°)╭∩╮",
    "(ᵟຶ︵ ᵟຶ)",
    "(งツ)ว",
    "ʚ(•｀",
    "(っ▀¯▀)つ",
    "(◠﹏◠)",
    "( ͡ಠ ʖ̯ ͡ಠ)",
    "( ఠ ͟ʖ ఠ)",
    "(∩｀-´)⊃━☆ﾟ.*･｡ﾟ",
    "(⊃｡•́‿•̀｡)⊃",
    "(._.)",
    "{•̃_•̃}",
    "(ᵔᴥᵔ)",
    "♨_♨",
    "⥀.⥀",
    "ح˚௰˚づ ",
    "(҂◡_◡)",
    "ƪ(ړײ)‎ƪ​​",
    "(っ•́｡•́)♪♬",
    "◖ᵔᴥᵔ◗ ♪ ♫ ",
    "(☞ﾟヮﾟ)☞",
    "[¬º-°]¬",
    "(Ծ‸ Ծ)",
    "(•̀ᴗ•́)و ̑̑",
    "ヾ(´〇`)ﾉ♪♪♪",
    "(ง'̀-'́)ง",
    "ლ(•́•́ლ)",
    "ʕ •́؈•̀ ₎",
    "♪♪ ヽ(ˇ∀ˇ )ゞ",
    "щ（ﾟДﾟщ）",
    "( ˇ෴ˇ )",
    "눈_눈",
    "(๑•́ ₃ •̀๑) ",
    "( ˘ ³˘)♥ ",
    "ԅ(≖‿≖ԅ)",
    "♥‿♥",
    "◔_◔",
    "⁽⁽ଘ( ˊᵕˋ )ଓ⁾⁾",
    "乁( ◔ ౪◔)「      ┑(￣Д ￣)┍",
    "( ఠൠఠ )ﾉ",
    "٩(๏_๏)۶",
    "┌(ㆆ㉨ㆆ)ʃ",
    "ఠ_ఠ",
    "(づ｡◕‿‿◕｡)づ",
    "(ノಠ ∩ಠ)ノ彡( \\o°o)\\",
    "“ヽ(´▽｀)ノ”",
    "༼ ༎ຶ ෴ ༎ຶ༽",
    "｡ﾟ( ﾟஇ‸இﾟ)ﾟ｡",
    "(づ￣ ³￣)づ",
    "(⊙.☉)7",
    "ᕕ( ᐛ )ᕗ",
    "t(-_-t)",
    "(ಥ⌣ಥ)",
    "ヽ༼ ಠ益ಠ ༽ﾉ",
    "༼∵༽ ༼⍨༽ ༼⍢༽ ༼⍤༽",
    "ミ●﹏☉ミ",
    "(⊙_◎)",
    "¿ⓧ_ⓧﮌ",
    "ಠ_ಠ",
    "(´･_･`)",
    "ᕦ(ò_óˇ)ᕤ",
    "⊙﹏⊙",
    "(╯°□°）╯︵ ┻━┻",
    r"¯\_(⊙︿⊙)_/¯",
    "٩◔̯◔۶",
    "°‿‿°",
    "ᕙ(⇀‸↼‶)ᕗ",
    "⊂(◉‿◉)つ",
    "V•ᴥ•V",
    "q(❂‿❂)p",
    "ಥ_ಥ",
    "ฅ^•ﻌ•^ฅ",
    "ಥ﹏ಥ",
    "（ ^_^）o自自o（^_^ ）",
    "ಠ‿ಠ",
    "ヽ(´▽`)/",
    "ᵒᴥᵒ#",
    "( ͡° ͜ʖ ͡°)",
    "┬─┬﻿ ノ( ゜-゜ノ)",
    "ヽ(´ー｀)ノ",
    "☜(⌒▽⌒)☞",
    "ε=ε=ε=┌(;*´Д`)ﾉ",
    "(╬ ಠ益ಠ)",
    "┬─┬⃰͡ (ᵔᵕᵔ͜ )",
    "┻━┻ ︵ヽ(`Д´)ﾉ︵﻿ ┻━┻",
    "ʕᵔᴥᵔʔ",
    "(`･ω･´)",
    "ʕ•ᴥ•ʔ",
    "ლ(｀ー´ლ)",
    "ʕʘ̅͜ʘ̅ʔ",
    "（　ﾟДﾟ）",
    r"¯\(°_o)/¯",
    "(｡◕‿◕｡)",
)

normiefont = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
weebyfont = ['卂','乃','匚','刀','乇','下','厶','卄','工','丁','长','乚','从','𠘨','口','尸','㔿','尺','丂','丅','凵','リ','山','乂','丫','乙']

WIDE_MAP = {i: i + 0xFEE0 for i in range(0x21, 0x7F)}
WIDE_MAP[0x20] = 0x3000

# D A N K modules by @deletescape vvv


@run_async
def owo(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat
    message = update.effective_message

    noreply = False
    if message.reply_to_message:
        data = message.reply_to_message.text
    elif args:
        noreply = True
        data = message.text.split(None, 1)[1]
    else:
        noreply = True
        data = tld(chat.id, "memes_no_message")

    faces = [
        '(・`ω´・)', ';;w;;', 'owo', 'UwU', '>w<', '^w^', '\(^o\) (/o^)/',
        '( ^ _ ^)∠☆', '(ô_ô)', '~:o', ';____;', '(*^*)', '(>_', '(♥_♥)',
        '*(^O^)*', '((+_+))'
    ]
    reply_text = re.sub(r'[rl]', "w", data)
    reply_text = re.sub(r'[ｒｌ]', "ｗ", data)
    reply_text = re.sub(r'[RL]', 'W', reply_text)
    reply_text = re.sub(r'[ＲＬ]', 'Ｗ', reply_text)
    reply_text = re.sub(r'n([aeiouａｅｉｏｕ])', r'ny\1', reply_text)
    reply_text = re.sub(r'ｎ([ａｅｉｏｕ])', r'ｎｙ\1', reply_text)
    reply_text = re.sub(r'N([aeiouAEIOU])', r'Ny\1', reply_text)
    reply_text = re.sub(r'Ｎ([ａｅｉｏｕＡＥＩＯＵ])', r'Ｎｙ\1', reply_text)
    reply_text = re.sub(r'\!+', ' ' + random.choice(faces), reply_text)
    reply_text = re.sub(r'！+', ' ' + random.choice(faces), reply_text)
    reply_text = reply_text.replace("ove", "uv")
    reply_text = reply_text.replace("ｏｖｅ", "ｕｖ")
    reply_text += ' ' + random.choice(faces)

    if noreply:
        message.reply_text(reply_text)
    else:
        message.reply_to_message.reply_text(reply_text)


@run_async
def stretch(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat
    message = update.effective_message

    noreply = False
    if message.reply_to_message:
        data = message.reply_to_message.text
    elif args:
        noreply = True
        data = message.text.split(None, 1)[1]
    else:
        noreply = True
        data = tld(chat.id, "memes_no_message")

    count = random.randint(3, 10)
    reply_text = re.sub(r'([aeiouAEIOUａｅｉｏｕＡＥＩＯＵ])', (r'\1' * count), data)

    if noreply:
        message.reply_text(reply_text)
    else:
        message.reply_to_message.reply_text(reply_text)


@run_async
def vapor(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    chat = update.effective_chat

    noreply = False
    if message.reply_to_message:
        data = message.reply_to_message.text
    elif args:
        noreply = True
        data = message.text.split(None, 1)[1]
    else:
        noreply = True
        data = tld(chat.id, "memes_no_message")

    reply_text = str(data).translate(WIDE_MAP)

    if noreply:
        message.reply_text(reply_text)
    else:
        message.reply_to_message.reply_text(reply_text)


@run_async
def zalgotext(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    chat = update.effective_chat

    noreply = False
    if message.reply_to_message:
        data = message.reply_to_message.text
    elif args:
        noreply = True
        data = message.text.split(None, 1)[1]
    else:
        noreply = True
        data = tld(chat.id, "memes_no_message")

    reply_text = zalgo.zalgo().zalgofy(data)
    if noreply:
        message.reply_text(reply_text)
    else:
        message.reply_to_message.reply_text(reply_text)


# Less D A N K modules by @skittles9823 # holi fugg I did some maymays ^^^


@run_async
def shout(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message
    chat = update.effective_chat

    if message.reply_to_message:
        data = message.reply_to_message.text
    elif args:
        data = " ".join(args)
    else:
        data = tld(chat.id, "memes_no_message")

    msg = "```"
    result = [' '.join(list(data))]
    for pos, symbol in enumerate(data[1:]):
        result.append(symbol + ' ' + '  ' * pos + symbol)
    result = list("\n".join(result))
    result[0] = data[0]
    result = "".join(result)
    msg = "```\n" + result + "```"
    return update.effective_message.reply_text(msg, parse_mode="MARKDOWN")


@run_async
def insults(bot: Bot, update: Update):
    message = update.effective_message
    chat = update.effective_chat
    text = random.choice(tld_list(chat.id, "memes_insults_list"))

    if message.reply_to_message:
        message.reply_to_message.reply_text(text)
    else:
        message.reply_text(text)


@run_async
def runs(bot: Bot, update: Update):
    chat = update.effective_chat
    update.effective_message.reply_text(
        random.choice(tld_list(chat.id, "memes_runs_list")))


@run_async
def slap(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat
    msg = update.effective_message

    # reply to correct message
    reply_text = msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text

    # get user who sent message
    if msg.from_user.username:
        curr_user = "@" + escape_markdown(msg.from_user.username)
    else:
        curr_user = "[{}](tg://user?id={})".format(msg.from_user.first_name,
                                                   msg.from_user.id)

    user_id = extract_user(update.effective_message, args)
    if user_id:
        slapped_user = bot.get_chat(user_id)
        user1 = curr_user
        if slapped_user.username == "RealAkito":
            reply_text(tld(chat.id, "memes_not_doing_that"))
            return
        if slapped_user.username:
            user2 = "@" + escape_markdown(slapped_user.username)
        else:
            user2 = "[{}](tg://user?id={})".format(slapped_user.first_name,
                                                   slapped_user.id)

    # if no target found, bot targets the sender
    else:
        user1 = "[{}](tg://user?id={})".format(bot.first_name, bot.id)
        user2 = curr_user

    temp = random.choice(tld_list(chat.id, "memes_slaps_templates_list"))
    item = random.choice(tld_list(chat.id, "memes_items_list"))
    hit = random.choice(tld_list(chat.id, "memes_hit_list"))
    throw = random.choice(tld_list(chat.id, "memes_throw_list"))
    itemp = random.choice(tld_list(chat.id, "memes_items_list"))
    itemr = random.choice(tld_list(chat.id, "memes_items_list"))

    repl = temp.format(user1=user1,
                       user2=user2,
                       item=item,
                       hits=hit,
                       throws=throw,
                       itemp=itemp,
                       itemr=itemr)

    reply_text(repl, parse_mode=ParseMode.MARKDOWN)


# Some bad memes from TheRealPhoenix Bot [github.com/rsktg/TheRealPhoenixBot] vvv


@run_async
def shrug(bot: Bot, update: Update):
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text = reply_text(random.choice(SHRUGS))


@run_async
def hug(bot: Bot, update: Update):
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text = reply_text(random.choice(HUGS))


@run_async
def react(bot: Bot, update: Update):
    reply_text = update.effective_message.reply_to_message.reply_text if update.effective_message.reply_to_message else update.effective_message.reply_text
    reply_text = reply_text(random.choice(REACTS))


@run_async
def pat(bot: Bot, update: Update):
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
def weebify(bot: Bot, update: Update, args):
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


# Some bad memes from TheRealPhoenix Bot [github.com/rsktg/TheRealPhoenixBot] ^^^


__help__ = True

OWO_HANDLER = DisableAbleCommandHandler("owo",
                                        owo,
                                        admin_ok=True,
                                        pass_args=True)
STRETCH_HANDLER = DisableAbleCommandHandler("stretch", stretch, pass_args=True)
VAPOR_HANDLER = DisableAbleCommandHandler("vapor",
                                          vapor,
                                          pass_args=True,
                                          admin_ok=True)
ZALGO_HANDLER = DisableAbleCommandHandler("zalgofy", zalgotext, pass_args=True)
SHOUT_HANDLER = DisableAbleCommandHandler("shout", shout, pass_args=True)
INSULTS_HANDLER = DisableAbleCommandHandler("insults", insults, admin_ok=True)
RUNS_HANDLER = DisableAbleCommandHandler("runs", runs, admin_ok=True)
SLAP_HANDLER = DisableAbleCommandHandler("slap",
                                         slap,
                                         pass_args=True,
                                         admin_ok=True)
SHRUG_HANDLER = DisableAbleCommandHandler(["shrug", "shg"], shrug, admin_ok=True)
HUG_HANDLER = DisableAbleCommandHandler("hug", hug, admin_ok=True)
REACT_HANDLER = DisableAbleCommandHandler("react", react, admin_ok=True)
PAT_HANDLER = DisableAbleCommandHandler("pat", pat, admin_ok=True)
WEEBIFY_HANDLER = DisableAbleCommandHandler("weebify",
                                            weebify,
                                            pass_args=True,
                                            admin_ok=True)

dispatcher.add_handler(OWO_HANDLER)
dispatcher.add_handler(STRETCH_HANDLER)
dispatcher.add_handler(VAPOR_HANDLER)
dispatcher.add_handler(ZALGO_HANDLER)
dispatcher.add_handler(SHOUT_HANDLER)
dispatcher.add_handler(INSULTS_HANDLER)
dispatcher.add_handler(RUNS_HANDLER)
dispatcher.add_handler(SLAP_HANDLER)
dispatcher.add_handler(SHRUG_HANDLER)
dispatcher.add_handler(HUG_HANDLER)
dispatcher.add_handler(REACT_HANDLER)
dispatcher.add_handler(PAT_HANDLER)
dispatcher.add_handler(WEEBIFY_HANDLER)
