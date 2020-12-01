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

from telegram import User, Chat

# This module has been ported from SkyleeBot
# Created by @starry69 on GitHub
# Ported from github.com/SensiPeeps/skyleebot


# checks whether the user is allowed to promote users
def user_can_promote(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_promote_members


# checks whether the user is allowed to ban users
def user_can_ban(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_restrict_members


# checks whether the user is allowed to pin messages
def user_can_pin(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_pin_messages


# checks whether the user is allowed to change group info
def user_can_changeinfo(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_change_info
