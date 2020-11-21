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

from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator, ChannelParticipantsAdmins

from hitsuki import tbot, SUDO_USERS, WHITELIST_USERS
from hitsuki.mwt import MWT


async def user_is_ban_protected(user_id: int, message):
    if message.is_private or user_id in (WHITELIST_USERS + SUDO_USERS):
        return True

    if message.is_channel:
        participant = await tbot(
            GetParticipantRequest(message.chat_id, user_id))
        return isinstance(participant.participant,
                          (ChannelParticipantAdmin, ChannelParticipantCreator))

    async for user in tbot.iter_participants(message.chat_id,
                                             filter=ChannelParticipantsAdmins):
        if user_id == user.id:
            return True
    return False


async def user_is_admin(user_id: int, message):
    if message.is_private or user_id in SUDO_USERS:
        return True

    if message.is_channel:
        participant = await tbot(
            GetParticipantRequest(message.chat_id, user_id))
        return isinstance(participant.participant,
                          (ChannelParticipantAdmin, ChannelParticipantCreator))

    async for user in tbot.iter_participants(message.chat_id,
                                             filter=ChannelParticipantsAdmins):
        if user_id == user.id:
            return True
    return False


# Cache admin status for 10 mins to avoid extra API requests.
@MWT(timeout=60 * 10)
async def is_user_admin(user_id: int, chat_id):
    if user_id in SUDO_USERS:
        return True

    try:
        participant = await tbot(GetParticipantRequest(chat_id, user_id))
        return isinstance(participant.participant,
                          (ChannelParticipantAdmin, ChannelParticipantCreator))
    except TypeError:
        async for user in tbot.iter_participants(
                chat_id, filter=ChannelParticipantsAdmins):
            if user_id == user.id:
                return True
    return False


async def hitsuki_is_admin(chat_id: int):
    try:
        participant = await tbot(GetParticipantRequest(chat_id, 'me'))
        return isinstance(participant.participant, ChannelParticipantAdmin)
    except TypeError:
        async for user in tbot.iter_participants(
                chat_id, filter=ChannelParticipantsAdmins):
            if user.is_self:
                return True
    return False


async def is_user_in_chat(chat_id: int, user_id: int):
    status = False
    async for user in tbot.iter_participants(chat_id):
        if user_id == user.id:
            status = True
            break
    return status


async def can_delete_messages(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.delete_messages
    return status


async def can_change_info(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.change_info
    return status


async def can_ban_users(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.ban_users
    return status


async def can_invite_users(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.invite_users
    return status


async def can_add_admins(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.add_admins
    return status


async def can_pin_messages(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.pin_messages
    return status
