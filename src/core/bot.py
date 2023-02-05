import re
from datetime import datetime as dt
from typing import Callable, Dict, Any, Iterable

from telebot import TeleBot
from telebot.types import Message, User

from utils import sanitize_name, log, dump_time
from core import Config, Chat, Help, Assets, plugins


class Bot:
    def __init__(self, assets: Assets):
        self._assets = assets
        config = Config(self._assets['config'])
        self._master_id = config.master_id
        self._max_message_length = config.max_message_length
        self._default_only_roles = config.default_only_roles
        self._chats_asset = config.chats_asset

        self._bot = TeleBot(config.api_token)
        self._name = self._get_name(self._bot.get_me())

        format_kwargs = {'name': self._name}
        self._help = Help(**{k: v.format(**format_kwargs)
                             for k, v in config.help.items()})

        self._chats = {
            chat_id: Chat.from_dict(chat, self.make_get_member_name(chat_id))
            for chat_id, chat in self._assets[self._chats_asset].items()}

        self._plugins = tuple(
            plugins[name](self, Config(plugin_config), assets)
            for name, plugin_config in config.plugins.items())

        self._started_at = -1

    @property
    def user_id(self) -> int:
        return self._bot.user.id

    @property
    def chats(self) -> Dict[int, Chat]:
        return self._chats

    def add_chat(self, chat_id: int):
        self._chats[chat_id] = Chat(True, {},
                                    self.make_get_member_name(chat_id))

    def remove_chat(self, chat_id: int):
        self._chats.pop(chat_id)

    def start(self):
        self._started_at = int(dt.now().timestamp())
        log("Bot", "start", f"ts: {self._started_at}",
            dump_time(self._started_at % (24 * 60 * 60)))

        self._bot.infinity_polling()

        self._assets[self._chats_asset] = {
            chat_id: chat.to_dict()
            for chat_id, chat in self._chats.items()}

        for plugin in self._plugins:
            plugin.finalize()

    def make_mentions(self,
                      chat_id: int,
                      user_ids: Iterable[int]) -> Iterable[str]:
        names = {uid: self._bot.get_chat_member(chat_id, uid).user.full_name
                 for uid in user_ids}
        return (f"[{name}](tg://user?id={uid})"
                for uid, name in names.items())

    def replies_to(self,
                   phrase: str,
                   *only_roles: str,
                   md: bool = False,
                   sanitizer: Callable[[str], str] = (
                           lambda s: s.rstrip('?').strip()),
                   usage: str = None,
                   description: str = None,
                   example: str = None):
        parse_mode = md and "markdown" or None
        matcher = self.make_address_predicate(phrase)
        predicate = self.make_predicate(only_roles, matcher)

        def decorator(reply):
            if usage or description:
                self._help.add_ability(usage or phrase.strip(),
                                       description or '')
            if example:
                self._help.add_example(example)

            def handler(message: Message):
                match = matcher(message)

                subject = sanitizer(message.text[match.span()[1]:])
                if response := reply(subject, message):
                    uid = message.from_user.id
                    chat_id = message.chat.id
                    if chat_id in self.chats and uid not in self.chats[chat_id]:
                        self.chats[chat_id].add_member(uid)
                        log("Bot", "add new chat member",
                            self.chats[chat_id][uid])
                    self._bot.reply_to(message, response, parse_mode=parse_mode)
                    self.log(message.chat.id,
                             message.from_user.id,
                             match.group(1),
                             subject.replace('\n', ' ')[:64],
                             response.replace('\n', ' ')[:96])

            return self._bot.message_handler(func=predicate)(handler)

        return decorator

    def add_message_handler(self,
                            predicate: Callable[[Message], Any],
                            reply: Callable[[Message], str],
                            *only_roles: str,
                            md: bool = False,
                            only_new: bool = True):
        predicate = self.make_predicate(only_roles,
                                        predicate,
                                        only_new=only_new)
        self.add_native_message_handler(predicate, reply, md=md)

    def add_native_message_handler(self,
                                   predicate: Callable[[Message], bool],
                                   reply: Callable[[Message], str],
                                   md: bool = False):
        parse_mode = md and "markdown" or None

        def handler(message):
            if response := reply(message):
                self._bot.reply_to(message, response, parse_mode=parse_mode)

        return self._bot.message_handler(func=predicate)(handler)

    def get_user(self, chat_id: int, user_id: int) -> User:
        return self._bot.get_chat_member(chat_id, user_id).user

    def get_full_name(self, chat_id: int, user_id: int) -> str:
        return self.get_user(chat_id, user_id).full_name

    def make_get_member_name(self, chat_id: int) -> Callable[[int], str]:
        return lambda user_id: self._get_name(self.get_user(chat_id, user_id))

    def get_help_message(self):
        return self._help.make_message()

    def log(self,
            chat_id: int,
            user_id: int,
            phrase: str,
            subject: str,
            response: str = ''):
        log(self.chats[chat_id][user_id], phrase, subject, response)

    @staticmethod
    def _get_name(user: User) -> str:
        un = sanitize_name(user.username)
        fn = sanitize_name(user.full_name)
        return ((len(fn) < 16 or len(fn) <= len(un))
                and fn
                or un)

    def make_predicate(self,
                       only_roles: Iterable[str],
                       *extra_predicates: Callable[[Message], Any],
                       only_new: bool = True):
        predicates = [
            self._make_from_user_predicate(
                only_roles or self._default_only_roles),
            lambda m: len(m.text) < self._max_message_length
        ]
        only_new and predicates.insert(1, lambda m: m.date >= self._started_at)
        extra_predicates and predicates.extend(extra_predicates)
        predicates = tuple(predicates)
        return lambda m: all(p(m) for p in predicates)

    def _make_from_user_predicate(self, only_roles: Iterable[str]):
        _only_roles = set(only_roles)

        def predicate(message):
            uid = message.from_user.id
            if uid == self._master_id:
                return True

            chat_id = message.chat.id
            if chat_id not in self._chats or not self._chats[chat_id].is_active:
                return False

            role = self._bot.get_chat_member(chat_id, uid).status
            return role in _only_roles

        return predicate

    def make_address_predicate(self, phrase: str):
        _pattern = re.compile(
            f"^{self._name.lower()}(?:,| |, )"
            f"({phrase.lower()})".replace(" ", "\\s+"))

        def predicate(message):
            return _pattern.match(message.text.lower())

        return predicate
