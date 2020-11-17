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

from emoji import UNICODE_EMOJI
from typing import Optional, List

from googletrans import LANGUAGES, Translator
from telegram import Message, Update, Bot, ParseMode, Chat
from telegram.ext import run_async

from hitsuki import dispatcher
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.tr_engine.strings import tld

# This module is based on
# Saitama and Emilia translator module


@run_async
def translator(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)
    try:
        if msg.reply_to_message:
            args = update.effective_message.text.split(None, 1)
            if msg.reply_to_message.text:
                text = msg.reply_to_message.text
            elif msg.reply_to_message.caption:
                text = msg.reply_to_message.caption

            msg = update.effective_message
            dest_lang = None

            try:
                src_lang = args[1].split(None, 1)[0]
            except Exception:
                src_lang = "en"

            if src_lang.count('-') == 2:
                for lang in problem_lang_code:
                    if lang in src_lang:
                        if src_lang.startswith(lang):
                            dest_lang = src_lang.rsplit("-", 1)[1]
                            src_lang = src_lang.rsplit("-", 1)[0]
                        else:
                            dest_lang = src_lang.split("-", 1)[1]
                            src_lang = src_lang.split("-", 1)[0]
            elif src_lang.count('-') == 1:
                for lang in problem_lang_code:
                    if lang in src_lang:
                        dest_lang = src_lang
                        src_lang = None
                        break
                if dest_lang is None:
                    dest_lang = src_lang.split("-")[1]
                    src_lang = src_lang.split("-")[0]
            else:
                dest_lang = src_lang
                src_lang = None

            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in text:
                    text = text.replace(emoji, '')

            trl = Translator()
            if src_lang is None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=dest_lang)
                return msg.reply_text((tld(chat.id,
                                           'translator_translated').format(src_lang,
                                                                           dest_lang,
                                                                           tekstr.text)),
                                      parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=src_lang)
                msg.reply_text((tld(chat.id,
                                    'translator_translated').format(src_lang,
                                                                    dest_lang,
                                                                    tekstr.text)),
                               parse_mode=ParseMode.MARKDOWN)
        else:
            args = update.effective_message.text.split(None, 2)
            msg = update.effective_message
            src_lang = args[1]
            text = args[2]
            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in text:
                    text = text.replace(emoji, '')
            dest_lang = None
            temp_src_lang = src_lang
            if temp_src_lang.count('-') == 2:
                for lang in problem_lang_code:
                    if lang in temp_src_lang:
                        if temp_src_lang.startswith(lang):
                            dest_lang = temp_src_lang.rsplit("-", 1)[1]
                            src_lang = temp_src_lang.rsplit("-", 1)[0]
                        else:
                            dest_lang = temp_src_lang.split("-", 1)[1]
                            src_lang = temp_src_lang.split("-", 1)[0]
            elif temp_src_lang.count('-') == 1:
                for lang in problem_lang_code:
                    if lang in temp_src_lang:
                        dest_lang = None
                        break
                    else:
                        dest_lang = temp_src_lang.split("-")[1]
                        src_lang = temp_src_lang.split("-")[0]
            trl = Translator()
            if dest_lang is None:
                detection = trl.detect(text)
                tekstr = trl.translate(text, dest=src_lang)
                return msg.reply_text((tld(chat.id,
                                           'translator_translated').format(detection.lang,
                                                                           dest_lang,
                                                                           tekstr.text)),
                                      parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(text, dest=dest_lang, src=src_lang)
                msg.reply_text((tld(chat.id,
                                    'translator_translated').format(src_lang,
                                                                    dest_lang,
                                                                    tekstr.text)),
                               parse_mode=ParseMode.MARKDOWN)

    except IndexError:
        msg.reply_text(tld(chat.id, "translator_usage"),
                       parse_mode="markdown",
                       disable_web_page_preview=True)

    except ValueError as e:
        msg.reply_text(tld(chat.id, 'translator_err').format(e))
    else:
        return


__help__ = True

TRANSLATOR_HANDLER = DisableAbleCommandHandler("tr",
                                               translator,
                                               pass_args=True)

dispatcher.add_handler(TRANSLATOR_HANDLER)
