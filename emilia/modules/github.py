import html
import random
import re
from datetime import datetime
from typing import Optional, List
from requests import get

import emilia.modules.helper_funcs.git_api as api
import emilia.modules.sql.github_sql as sql

from emilia import dispatcher, OWNER_ID, LOGGER, SUDO_USERS, SUPPORT_USERS, spamcheck
from emilia.modules.helper_funcs.filters import CustomFilters
from emilia.modules.helper_funcs.chat_status import user_admin
from emilia.modules.languages import tl

from telegram.ext import CommandHandler, run_async, Filters, MessageHandler
from telegram import Message, Chat, Update, Bot, User, ParseMode, InlineKeyboardMarkup, MAX_MESSAGE_LENGTH


#do not async
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
    message = "Author: [{}]({})\n".format(author, authorUrl)
    message += "Release Name: "+releaseName+"\n\n"
    for asset in assets:
        message += "*Asset:* \n"
        fileName = api.getReleaseFileName(asset)
        fileURL = api.getReleaseFileURL(asset)
        assetFile = "[{}]({})".format(fileName, fileURL)
        sizeB = ((api.getSize(asset))/1024)/1024
        size = "{0:.2f}".format(sizeB)
        downloadCount = api.getDownloadCount(asset)
        message += assetFile + "\n"
        message += "Size: " + size + " MB"
        message += "\nDownload Count: " + str(downloadCount) + "\n\n"
    return message


def getRepo(bot, update, reponame, show_none=True, no_format=False):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    chat_id = update.effective_chat.id
    repo = sql.get_repo(str(chat_id), reponame)
    if repo:
        return repo.value, repo.backoffset
    return None, None

@run_async
@spamcheck
def getRelease(update, context):
    args = context.args
    msg = update.effective_message
    if(len(args) != 1 and not (len(args) == 2 and args[1].isdigit()) and not ("/" in args[0])):
        msg.reply_text("Please specify a valid combination of <user>/<repo>")
        return
    index = 0
    if len(args) == 2:
        index = int(args[1])
    url = args[0]
    text = getData(url, index)
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return

@run_async
@spamcheck
def hashFetch(update, context):
    args = context.args
    message = update.effective_message.text
    msg = update.effective_message
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    url, index = getRepo(context.bot, update, no_hash)
    if url is None and index is None:
        msg.reply_text("There was a problem parsing your request", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        return
    text = getData(url, index)
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return
    
@run_async
@spamcheck
def cmdFetch(update, context):
    args = context.args
    msg = update.effective_message
    if(len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url, index = getRepo(context.bot, update, args[0])
    if url is None and index is None:
        msg.reply_text("There was a problem parsing your request", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        return
    text = getData(url, index)
    msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return


@run_async
@spamcheck
def changelog(update, context):
    args = context.args
    msg = update.effective_message
    if(len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url, index = getRepo(context.bot, update, args[0])
    if url is None and index is None:
        msg.reply_text("There was a problem parsing your request", parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        return
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
@spamcheck
def saveRepo(update, context):
    args = context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if(len(args) != 2 and (len(args) != 3 and not args[2].isdigit()) or not ("/" in args[1])):
        msg.reply_text("Invalid data, use <reponame> <user>/<repo> <value (optional)>")
        return
    index = 0
    if len(args) == 3:
        index = int(args[2])
    sql.add_repo_to_db(str(chat_id), args[0], args[1], index)
    msg.reply_text("Repo shortcut saved successfully!")
    return
    
@run_async
@user_admin
@spamcheck
def delRepo(update, context):
    args = context.args
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if(len(args)!=1):
        msg.reply_text("Invalid repo name!")
        return
    sql.rm_repo(str(chat_id), args[0])
    msg.reply_text("Repo shortcut deleted successfully!")
    return
    
@run_async
@spamcheck
def listRepo(update, context):
    args = context.args
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    chat_name = chat.title or chat.first or chat.username
    repo_list = sql.get_all_repos(str(chat_id))
    msg = "*GitHub repo shotcuts in {}:*\n"
    des = "\nYou can retrieve these repos by using `/fetch repo`, or `&repo`\n"
    for repo in repo_list:
        repo_name = (" • `&{}`\n".format(repo.name))
        if len(msg) + len(repo_name) > MAX_MESSAGE_LENGTH:
            update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
        msg += repo_name
    if msg == "*List of repo shotcuts in {}:*\n":
        update.effective_message.reply_text("No repo shortcuts in this chat!")
    elif len(msg) != 0:
        update.effective_message.reply_text(msg.format(chat_name) + des, parse_mode=ParseMode.MARKDOWN)
        
def getVer(update, context):
    msg = update.effective_message
    ver = api.vercheck()
    msg.reply_text("GitHub API version: "+ver)
    return

@run_async
@spamcheck
def github(update, context):
    args = context.args
    message = update.effective_message
    text = message.text[len('/git '):]
    usr = get(f'https://api.github.com/users/{text}').json()
    if usr.get('login'):
        text = f"*Username:* [{usr['login']}](https://github.com/{usr['login']})"

        whitelist = ['name', 'id', 'type', 'location', 'blog',
                     'bio', 'followers', 'following', 'hireable',
                     'public_gists', 'public_repos', 'email',
                     'company', 'updated_at', 'created_at']

        difnames = {'id': 'Account ID', 'type': 'Account type', 'created_at': 'Account created at',
                    'updated_at': 'Last updated', 'public_repos': 'Public Repos', 'public_gists': 'Public Gists'}

        goaway = [None, 0, 'null', '']

        for x, y in usr.items():
            if x in whitelist:
                if x in difnames:
                    x = difnames[x]
                else:
                    x = x.title()

                if x == 'Account created at' or x == 'Last updated':
                    y = datetime.strptime(y, "%Y-%m-%dT%H:%M:%SZ")

                if y not in goaway:
                    if x == 'Blog':
                        x = "Website"
                        y = f"[Here!]({y})"
                        text += ("\n*{}:* {}".format(x, y))
                    else:
                        text += ("\n*{}:* `{}`".format(x, y))
        reply_text = text
    else:
        reply_text = "User not found. Make sure you entered valid username!"
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


@run_async
@spamcheck
def repo(update, context):
    args = context.args
    message = update.effective_message
    text = message.text[len('/repo '):]
    usr = get(f'https://api.github.com/users/{text}/repos?per_page=40').json()
    reply_text = "*Repo*\n"
    for i in range(len(usr)):
        reply_text += f"[{usr[i]['name']}]({usr[i]['html_url']})\n"
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


__help__ = "github_help"

__mod_name__ = "GitHub"

GITHUB_HANDLER = CommandHandler("git", github)
REPO_HANDLER = CommandHandler("repo", repo, pass_args=True)

RELEASEHANDLER = CommandHandler("gitr", getRelease, pass_args=True)
FETCH_HANDLER = CommandHandler("fetch", cmdFetch, pass_args=True)
CHANGELOG_HANDLER = CommandHandler("changelog", changelog, pass_args=True)
HASHFETCH_HANDLER = MessageHandler(Filters.regex(r"^&[^\s]+"), hashFetch)

SAVEREPO_HANDLER = CommandHandler("saverepo", saveRepo)
DELREPO_HANDLER = CommandHandler("delrepo", delRepo)
LISTREPO_HANDLER = CommandHandler("listrepo", listRepo)

VERCHECKER_HANDLER = CommandHandler("gitver", getVer)

dispatcher.add_handler(RELEASEHANDLER)
dispatcher.add_handler(REPO_HANDLER)
dispatcher.add_handler(GITHUB_HANDLER)
dispatcher.add_handler(FETCH_HANDLER)
dispatcher.add_handler(SAVEREPO_HANDLER)
dispatcher.add_handler(DELREPO_HANDLER)
dispatcher.add_handler(LISTREPO_HANDLER)
dispatcher.add_handler(HASHFETCH_HANDLER)
dispatcher.add_handler(VERCHECKER_HANDLER)
dispatcher.add_handler(CHANGELOG_HANDLER)
