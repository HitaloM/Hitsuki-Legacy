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

from typing import List

from telegram import Update, Bot, ParseMode, MAX_MESSAGE_LENGTH
from telegram.ext import run_async, RegexHandler

import hitsuki.modules.helper_funcs.git_api as api
import hitsuki.modules.sql.github_sql as sql
from hitsuki import dispatcher
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.helper_funcs.chat_status import user_admin


# do not async
def getData(url, index):
    if not api.getData(url):
        return "Invalid <user>/<repo> combo"
    recentRelease = api.getReleaseData(api.getData(url), index)
    if recentRelease is None:
        return "The specified release could not be found"
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "<b>Author:</b> <a href='{}'>{}</a>\n".format(authorUrl, author)
    message += "<b>Release Name:</b> " + releaseName + "\n\n"
    for asset in assets:
        message += "<b>Asset:</b> \n"
        fileName = api.getReleaseFileName(asset)
        fileURL = api.getReleaseFileURL(asset)
        assetFile = "<a href='{}'>{}</a>".format(fileURL, fileName)
        sizeB = ((api.getSize(asset)) / 1024) / 1024
        size = "{0:.2f}".format(sizeB)
        downloadCount = api.getDownloadCount(asset)
        message += assetFile + "\n"
        message += "Size: " + size + " MB"
        message += "\nDownload Count: " + str(downloadCount) + "\n\n"
    return message


# likewise, aux function, not async
def getRepo(bot, update, reponame):
    chat_id = update.effective_chat.id
    repo = sql.get_repo(str(chat_id), reponame)
    if repo:
        return repo.value, repo.backoffset
    return None, None


@run_async
def getRelease(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    if not args:
        msg.reply_text("Please use some arguments!")
        return
    if (
            len(args) != 1
            and (len(args) != 2 or not args[1].isdigit())
            and "/" not in args[0]
    ):
        msg.reply_text("Please specify a valid combination of <user>/<repo>")
        return
    index = 0
    if len(args) == 2:
        index = int(args[1])
    url = args[0]
    text = getData(url, index)
    msg.reply_text(text, parse_mode=ParseMode.HTML,
                   disable_web_page_preview=True)
    return


@run_async
def hashFetch(bot: Bot, update: Update):
    message = update.effective_message.text
    msg = update.effective_message
    fst_word = message.split()[0].lower()
    no_hash = fst_word[1:]
    url, index = getRepo(bot, update, no_hash)
    if url is None and index is None:
        msg.reply_text("There was a problem parsing your request. Likely this is not a saved repo shortcut",
                       parse_mode=ParseMode.HTML,
                       disable_web_page_preview=True)
        return
    text = getData(url, index)
    msg.reply_text(text, parse_mode=ParseMode.HTML,
                   disable_web_page_preview=True)
    return


@run_async
def cmdFetch(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    if (len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url, index = getRepo(bot, update, args[0].lower())
    if url is None and index is None:
        msg.reply_text("There was a problem parsing your request. Likely this is not a saved repo shortcut",
                       parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        return
    text = getData(url, index)
    msg.reply_text(text, parse_mode=ParseMode.HTML,
                   disable_web_page_preview=True)
    return


@run_async
def changelog(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    if (len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url, index = getRepo(bot, update, args[0].lower())
    if not api.getData(url):
        msg.reply_text("Invalid <user>/<repo> combo")
        return
    data = api.getData(url)
    release = api.getReleaseData(data, index)
    body = api.getBody(release)
    msg.reply_text(body)
    return


@run_async
@user_admin
def saveRepo(bot: Bot, update: Update, args: List[str]):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if (
            len(args) != 2
            and (len(args) != 3 and not args[2].isdigit())
            or "/" not in args[1]
    ):
        msg.reply_text(
            "Invalid data, use <reponame> <user>/<repo> <value (optional)>")
        return
    index = 0
    if len(args) == 3:
        index = int(args[2])
    sql.add_repo_to_db(str(chat_id), args[0].lower(), args[1], index)
    msg.reply_text("Repo shortcut saved successfully!")
    return


@run_async
@user_admin
def delRepo(bot: Bot, update: Update, args: List[str]):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if (len(args) != 1):
        msg.reply_text("Invalid repo name!")
        return
    sql.rm_repo(str(chat_id), args[0].lower())
    msg.reply_text("Repo shortcut deleted successfully!")
    return


@run_async
def listRepo(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    chat_name = chat.title or chat.first or chat.username
    repo_list = sql.get_all_repos(str(chat_id))
    msg = "<b>GitHub repo shotcuts in {}:</b>\n"
    des = "\nYou can retrieve these repos by using <code>/fetch repo</code>, or <code>&repo</code>\n"
    for repo in repo_list:
        repo_name = (" • <code>&{}</code>\n".format(repo.name))
        if len(msg) + len(repo_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
            msg = ""
        msg += repo_name
    if msg == "<b>GitHub repo shotcuts in {}:</b>\n":
        update.effective_message.reply_text("No repo shortcuts in this chat!")
    elif len(msg) != 0:
        update.effective_message.reply_text(msg.format(chat_name) + des,
                                            parse_mode=ParseMode.HTML)


def __stats__():
    return "• <code>{}</code> repos shortcuts, accross <code>{}</code> chats.".format(sql.num_repos(),
                                                                                      sql.num_chats())


__help__ = True

RELEASE_HANDLER = DisableAbleCommandHandler("gitr", getRelease, pass_args=True,
                                            admin_ok=True)
FETCH_HANDLER = DisableAbleCommandHandler("fetch", cmdFetch, pass_args=True,
                                          admin_ok=True)
SAVEREPO_HANDLER = DisableAbleCommandHandler("saverepo", saveRepo,
                                             pass_args=True)
DELREPO_HANDLER = DisableAbleCommandHandler("delrepo", delRepo, pass_args=True)
LISTREPO_HANDLER = DisableAbleCommandHandler("listrepo", listRepo,
                                             admin_ok=True)
CHANGELOG_HANDLER = DisableAbleCommandHandler("changelog", changelog,
                                              pass_args=True,
                                              admin_ok=True)

HASHFETCH_HANDLER = RegexHandler(r"^&[^\s]+", hashFetch)

dispatcher.add_handler(RELEASE_HANDLER)
dispatcher.add_handler(FETCH_HANDLER)
dispatcher.add_handler(SAVEREPO_HANDLER)
dispatcher.add_handler(DELREPO_HANDLER)
dispatcher.add_handler(LISTREPO_HANDLER)
dispatcher.add_handler(HASHFETCH_HANDLER)
dispatcher.add_handler(CHANGELOG_HANDLER)
