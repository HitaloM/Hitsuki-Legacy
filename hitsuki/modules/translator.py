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
from typing import Optional, List
from emoji import UNICODE_EMOJI
from googletrans import LANGUAGES

from telegram import Update, Bot, ParseMode
from telegram.ext import run_async

from hitsuki import dispatcher, trl
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.tr_engine.strings import tld, tld_list


@run_async
def do_translate(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat
    msg = update.effective_message
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)

    if msg.reply_to_message and (msg.reply_to_message.audio
                                 or msg.reply_to_message.voice) or (
                                     args and args[0] == 'animal'):
        reply = random.choice(tld_list(chat.id, 'translator_animal_lang'))

        if args:
            translation_type = "text"
        else:
            translation_type = "audio"

        msg.reply_text(tld(chat.id, 'translator_animal_translated').format(
            translation_type, reply),
            parse_mode=ParseMode.MARKDOWN)
        return

    try:
        if msg.reply_to_message:
            args = update.effective_message.text.split(None, 1)
            if msg.reply_to_message.text:
                text = msg.reply_to_message.text
            elif msg.reply_to_message.caption:
                text = msg.reply_to_message.caption

            message = update.effective_message
            dest_lang = None

            try:
                source_lang = args[1].split(None, 1)[0]
            except:
                source_lang = "en"

            if source_lang.count('-') == 2:
                for lang in problem_lang_code:
                    if lang in source_lang:
                        if source_lang.startswith(lang):
                            dest_lang = source_lang.rsplit("-", 1)[1]
                            source_lang = source_lang.rsplit("-", 1)[0]
                        else:
                            dest_lang = source_lang.split("-", 1)[1]
                            source_lang = source_lang.split("-", 1)[0]
            elif source_lang.count('-') == 1:
                for lang in problem_lang_code:
                    if lang in source_lang:
                        dest_lang = source_lang
                        source_lang = None
                        break
                if dest_lang is None:
                    dest_lang = source_lang.split("-")[1]
                    source_lang = source_lang.split("-")[0]
            else:
                dest_lang = source_lang
                source_lang = None

            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in text:
                    text = text.replace(emoji, '')

            if source_lang is None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=dest_lang)
                return message.reply_text(
                    tld(chat.id, "translator_translated").format(
                        detection.lang, dest_lang, tekstr.text),
                    parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=source_lang)
                message.reply_text(
                    tld(chat.id, "translator_translated").format(
                        source_lang, dest_lang, tekstr.text),
                    parse_mode=ParseMode.MARKDOWN)
        else:
            args = update.effective_message.text.split(None, 2)
            message = update.effective_message
            source_lang = args[1]
            text = args[2]
            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in text:
                    text = text.replace(emoji, '')
            dest_lang = None
            temp_source_lang = source_lang
            if temp_source_lang.count('-') == 2:
                for lang in problem_lang_code:
                    if lang in temp_source_lang:
                        if temp_source_lang.startswith(lang):
                            dest_lang = temp_source_lang.rsplit("-", 1)[1]
                            source_lang = temp_source_lang.rsplit("-", 1)[0]
                        else:
                            dest_lang = temp_source_lang.split("-", 1)[1]
                            source_lang = temp_source_lang.split("-", 1)[0]
            elif temp_source_lang.count('-') == 1:
                for lang in problem_lang_code:
                    if lang in temp_source_lang:
                        dest_lang = None
                        break
                    else:
                        dest_lang = temp_source_lang.split("-")[1]
                        source_lang = temp_source_lang.split("-")[0]

            if dest_lang is None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=source_lang)
                return message.reply_text(
                    tld(chat.id, "translator_translated").format(
                        detection.lang, dest_lang, tekstr.text),
                    parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=source_lang)
                message.reply_text(tld(chat.id, "translator_translated").format(
                    source_lang, dest_lang, tekstr.text),
                    parse_mode=ParseMode.MARKDOWN)

    except IndexError:
        update.effective_message.reply_text(tld(chat.id, "translator_no_args"),
                                            parse_mode="markdown",
                                            disable_web_page_preview=True)
    except ValueError:
        update.effective_message.reply_text(tld(chat.id, "translator_err"))
    else:
        return


__help__ = True

TR_HANDLER = DisableAbleCommandHandler("tr", do_translate, pass_args=True)

dispatcher.add_handler(TR_HANDLER)
