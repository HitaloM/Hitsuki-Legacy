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

from typing import List

from emoji import UNICODE_EMOJI
from google_trans_new import LANGUAGES, google_translator
from hitsuki import dispatcher
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.tr_engine.strings import tld
from telegram import Bot, ParseMode, Update
from telegram.ext import run_async


@run_async
def totranslate(bot: Bot, update: Update, args: List[str]):
    chat = update.effective_chat
    message = update.effective_message
    problem_lang_code = []
    for key in LANGUAGES:
        if "-" in key:
            problem_lang_code.append(key)

    try:
        if message.reply_to_message:
            args = update.effective_message.text.split(None, 1)
            if message.reply_to_message.text:
                text = message.reply_to_message.text
            elif message.reply_to_message.caption:
                text = message.reply_to_message.caption

            try:
                source_lang = args[1].split(None, 1)[0]
            except (IndexError, AttributeError):
                source_lang = "en"

        else:
            args = update.effective_message.text.split(None, 2)
            text = args[2]
            source_lang = args[1]

        if source_lang.count("-") == 2:
            for lang in problem_lang_code:
                if lang in source_lang:
                    if source_lang.startswith(lang):
                        dest_lang = source_lang.rsplit("-", 1)[1]
                        source_lang = source_lang.rsplit("-", 1)[0]
                    else:
                        dest_lang = source_lang.split("-", 1)[1]
                        source_lang = source_lang.split("-", 1)[0]
        elif source_lang.count("-") == 1:
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
                text = text.replace(emoji, "")

        trl = google_translator()
        if source_lang is None:
            detection = trl.detect(text)
            trans_str = trl.translate(text, lang_tgt=dest_lang)
            return message.reply_text(
                f"Translated from `{detection[0]}` to `{dest_lang}`:\n`{trans_str}`",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            trans_str = trl.translate(
                text, lang_tgt=dest_lang, lang_src=source_lang)
            message.reply_text(
                f"Translated from `{source_lang}` to `{dest_lang}`:\n`{trans_str}`",
                parse_mode=ParseMode.MARKDOWN,
            )

    except IndexError:
        update.effective_message.reply_text(tld(chat.id, "translator_no_str"))
    except ValueError:
        update.effective_message.reply_text(
            "The intended language is not found!")
    else:
        return


__help__ = True

dispatcher.add_handler(DisableAbleCommandHandler(
    "tr", totranslate, pass_args=True))
