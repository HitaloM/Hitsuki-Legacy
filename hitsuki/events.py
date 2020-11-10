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

from telethon import events

from hitsuki import tbot


def register(**args):
    """ Registers a new message. """
    pattern = args.get('pattern', None)

    r_pattern = r'^[/!]'

    if pattern is not None and not pattern.startswith('(?i)'):
        args['pattern'] = '(?i)' + pattern

    args['pattern'] = pattern.replace('^/', r_pattern, 1)

    def decorator(func):
        tbot.add_event_handler(func, events.NewMessage(**args))
        return func

    return decorator


def chataction(**args):
    """ Registers chat actions. """

    def decorator(func):
        tbot.add_event_handler(func, events.ChatAction(**args))
        return func

    return decorator


def userupdate(**args):
    """ Registers user updates. """

    def decorator(func):
        tbot.add_event_handler(func, events.UserUpdate(**args))
        return func

    return decorator


def inlinequery(**args):
    """ Registers inline query. """
    pattern = args.get('pattern', None)

    if pattern is not None and not pattern.startswith('(?i)'):
        args['pattern'] = '(?i)' + pattern

    def decorator(func):
        tbot.add_event_handler(func, events.InlineQuery(**args))
        return func

    return decorator


def callbackquery(**args):
    """ Registers inline query. """

    def decorator(func):
        tbot.add_event_handler(func, events.CallbackQuery(**args))
        return func

    return decorator
