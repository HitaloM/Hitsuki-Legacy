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

#    Thanks to t.me/Zero_cool7870 and t.me/TheRealPhoenix

from tg_bot import dispatcher, LOGGER
from telegram import Bot, Update
from telegram.ext.dispatcher import run_async
from tg_bot.modules.helper_funcs.chat_status import dev_user
from tg_bot.modules.helper_funcs.misc import sendMessage
from telegram.ext import CommandHandler, Filters
from subprocess import Popen, PIPE


def shell(command):
    process = Popen(command, stdout=PIPE, shell=True, stderr=PIPE)
    stdout, stderr = process.communicate()
    return (stdout, stderr)


@dev_user
@run_async
def shellExecute(bot: Bot, update: Update):
    cmd = update.message.text.split(' ', maxsplit=1)
    if len(cmd) == 1:
        sendMessage("No command provided!", bot, update)
        return
    LOGGER.info(cmd)
    output = shell(cmd[1])
    if output[1].decode():
        LOGGER.error(f"Shell: {output[1].decode()}")
    if len(output[0].decode()) > 4000:
        with open("shell.txt", 'w') as f:
            f.write(f"Output\n-----------\n{output[0].decode()}\n")
            if output[1]:
                f.write(f"STDError\n-----------\n{output[1].decode()}\n")
        with open("shell.txt", 'rb') as f:
            bot.send_document(document=f, filename=f.name,
                              reply_to_message_id=update.message.message_id,
                              chat_id=update.message.chat_id)
    else:
        if output[1].decode():
            sendMessage(f"<code>{output[1].decode()}</code>", bot, update)
            return
        else:
            sendMessage(f"<code>{output[0].decode()}</code>", bot, update)


shell_handler = CommandHandler(('sh', 'shell'), shellExecute, filters=Filters.user(OWNER_ID))

dispatcher.add_handler(shell_handler)
