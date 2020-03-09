import html
import random
import re
from datetime import datetime
from typing import Optional, List
from requests import get

import hitsuki.modules.helper_funcs.git_api as api
import hitsuki.modules.sql.github_sql as sql

from hitsuki import dispatcher, OWNER_ID, LOGGER, SUDO_USERS, SUPPORT_USERS, spamfilters
from hitsuki.modules.helper_funcs.filters import CustomFilters
from hitsuki.modules.helper_funcs.chat_status import user_admin
from hitsuki.modules.languages import tl as tld

from telegram.ext import CommandHandler, run_async, Filters, RegexHandler
from telegram import Message, Chat, Update, Bot, User, ParseMode, InlineKeyboardMarkup, MAX_MESSAGE_LENGTH


def getData(url):
    if not api.getData(url):
        return "Invalid <user>/<repo> combo"
    recentRelease = api.getReleaseData(api.getData(url))
    author = api.getAuthor(recentRelease)
    authorUrl = api.getAuthorUrl(recentRelease)
    name = api.getReleaseName(recentRelease)
    assets = api.getAssets(recentRelease)
    releaseName = api.getReleaseName(recentRelease)
    message = "<b>Author:</b> <a href='{}'>{}</a> \n".format(authorUrl, author)
    message += "Release Name: "+releaseName+"\n\n"
    for asset in assets:
        message += "<b>Asset:</b> \n"
        fileName = api.getReleaseFileName(asset)
        fileURL = api.getReleaseFileURL(asset)
        assetFile = "<a href='{}'>{}</a>".format(fileURL, fileName)
        sizeB = ((api.getSize(asset))/1024)/1024
        size = "{0:.2f}".format(sizeB)
        downloadCount = api.getDownloadCount(asset)
        message += assetFile + "\n"
        message += "Size: " + size + " MB"
        message += "\nDownload Count: " + str(downloadCount) + "\n\n"
    return message

#likewise, aux function, not async
def getRepo(bot, update, reponame):
    chat_id = update.effective_chat.id
    repo = sql.get_repo(str(chat_id), reponame)
    if repo:
        return repo.value
    return None

@run_async
def getRelease(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    msg = update.effective_message
    if(len(args) != 1):
        msg.reply_text("Please specify a valid combination of <user>/<repo>")
        return
    url = args[0]
    text = getData(url)
    msg.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    return

@run_async
def hashFetch(bot: Bot, update: Update): #kanged from notes
    message = update.effective_message.text
    msg = update.effective_message
    fst_word = message.split()[0]
    no_hash = fst_word[1:]
    url = getRepo(bot, update, no_hash)
    text = getData(url)
    msg.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    return
    
@run_async
def cmdFetch(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    if(len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url = getRepo(bot, update, args[0])
    text = getData(url)
    msg.reply_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    return


@run_async
def changelog(bot: Bot, update: Update, args: List[str]):
    msg = update.effective_message
    if(len(args) != 1):
        msg.reply_text("Invalid repo name")
        return
    url = getRepo(bot, update, args[0])
    if not api.getData(url):
        msg.reply_text("Invalid <user>/<repo> combo")
        return
    data = api.getData(url)
    release = api.getReleaseData(data)
    body = api.getBody(release)
    msg.reply_text(body)
    return


@run_async
@user_admin
def saveRepo(bot: Bot, update: Update, args: List[str]):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if(len(args) != 2):
        msg.reply_text(tld(chat_id, "Invalid data, use <reponame> <user>/<repo>"))
        return
    sql.add_repo_to_db(str(chat_id), args[0], args[1])
    msg.reply_text(tld(chat_id, "Repo shortcut saved successfully!"))
    return
    
@run_async
@user_admin
def delRepo(bot: Bot, update: Update, args: List[str]):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if(len(args)!=1):
        msg.reply_text(tld(chat_id, "Invalid repo name!"))
        return
    sql.rm_repo(str(chat_id), args[0])
    msg.reply_text(tld(chat_id, "Repo shortcut deleted successfully!"))
    return
    
@run_async
def listRepo(bot: Bot, update: Update):
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    chat_name = chat.title or chat.first or chat.username
    repo_list = sql.get_all_repos(str(chat_id))
    msg = tld(chat.id, "*List of repo shotcuts in {}:*\n")
    des = tld(chat.id, "\nYou can get repo shortcuts by using `/fetch repo`, or `&repo`.\n")
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
        
def getVer(bot: Bot, update: Update):
    msg = update.effective_message
    ver = api.vercheck()
    msg.reply_text("GitHub API version: "+ver)
    return

@run_async
def github(bot: Bot, update: Update):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
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
def repo(bot: Bot, update: Update, args: List[str]):
    spam = spamfilters(update.effective_message.text, update.effective_message.from_user.id, update.effective_chat.id, update.effective_message)
    if spam == True:
        return
    message = update.effective_message
    text = message.text[len('/repo '):]
    usr = get(f'https://api.github.com/users/{text}/repos?per_page=40').json()
    reply_text = "*Repo*\n"
    for i in range(len(usr)):
        reply_text += f"[{usr[i]['name']}]({usr[i]['html_url']})\n"
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)


def __stats__():
	return (tld(OWNER_ID, "{} repos, accross {} chats.").format(sql.num_github(), sql.num_chats())) 


__help__ = "github_help"

__mod_name__ = "GitHub"

GITHUB_HANDLER = CommandHandler("git", github)
REPO_HANDLER = CommandHandler("repo", repo, pass_args=True)
RELEASEHANDLER = CommandHandler("gitr", getRelease, pass_args=True)
FETCH_HANDLER = CommandHandler("fetch", cmdFetch, pass_args=True)
SAVEREPO_HANDLER = CommandHandler("saverepo", saveRepo)
DELREPO_HANDLER = CommandHandler("delrepo", delRepo)
LISTREPO_HANDLER = CommandHandler("listrepo", listRepo)
VERCHECKER_HANDLER = CommandHandler("gitver", getVer)
CHANGELOG_HANDLER = CommandHandler("changelog", changelog, pass_args=True)

HASHFETCH_HANDLER = RegexHandler(r"^&[^\s]+", hashFetch)

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
