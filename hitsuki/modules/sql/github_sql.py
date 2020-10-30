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

import threading

from sqlalchemy import Column, String, UnicodeText, Integer, func, distinct

from hitsuki.modules.sql import SESSION, BASE


class GitHub(BASE):
    __tablename__ = "github"
    chat_id = Column(String(14), primary_key=True)  # string because int is too large to be stored in a PSQL database.
    name = Column(UnicodeText, primary_key=True)
    value = Column(UnicodeText, nullable=False)
    backoffset = Column(Integer, nullable=False, default=0)

    def __init__(self, chat_id, name, value, backoffset):
        self.chat_id = str(chat_id)
        self.name = name
        self.value = value
        self.backoffset = backoffset

    def __repr__(self):
        return "<Git Repo %s>" % self.name


GitHub.__table__.create(checkfirst=True)

GIT_LOCK = threading.RLock()


def add_repo_to_db(chat_id, name, value, backoffset):
    with GIT_LOCK:
        prev = SESSION.query(GitHub).get((str(chat_id), name))
        if prev:
            SESSION.delete(prev)
        repo = GitHub(str(chat_id), name, value, backoffset)
        SESSION.add(repo)
        SESSION.commit()


def get_repo(chat_id, name):
    try:
        return SESSION.query(GitHub).get((str(chat_id), name))
    finally:
        SESSION.close()


def rm_repo(chat_id, name):
    with GIT_LOCK:
        repo = SESSION.query(GitHub).get((str(chat_id), name))
        if repo:
            SESSION.delete(repo)
            SESSION.commit()
            return True
        else:
            SESSION.close()
            return False


def get_all_repos(chat_id):
    try:
        return SESSION.query(GitHub).filter(GitHub.chat_id == str(chat_id)).order_by(GitHub.name.asc()).all()
    finally:
        SESSION.close()


def num_repos():
    try:
        return SESSION.query(GitHub).count()
    finally:
        SESSION.close()


def num_chats():
    try:
        return SESSION.query(func.count(distinct(GitHub.chat_id))).scalar()
    finally:
        SESSION.close()
