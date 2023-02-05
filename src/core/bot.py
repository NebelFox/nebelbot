import re
from datetime import datetime as dt
from typing import Callable, Dict, Any, Iterable

from telebot import TeleBot
from telebot.types import Message, User

from utils import sanitize_name, log, dump_time
from core import Config, Chat, Help, Assets, plugins


class Bot:
    """
    Wrapper around telebot.TeleBot class.

    Is designed to simulate human user and reply to direct address
    to the bot by its name.

    The name of the bot is taken from the Telegram account of the bot.

    Bot doesn't respond to everyone.
    Bot does always respond to the "master", i.e. who maintains the bot.
    Bot doesn't react to messages exceeding the max allowed length.
    Bot doesn't react to messages from chats it doesn't watch.

    Bot uses Help class to dynamically build help message.
    The headers may be provided in "help" object of the main config.
    The "{name}" placeholder may be used in the headers.
    It would be replaced with the Bot name in the displayed message.
    """

    Predicate = Callable[[Message], Any]
    Reply = Callable[[Message], str]

    def __init__(self, assets: Assets):
        self._assets = assets
        config = Config(self._assets['config'])
        self._master_id = config.master_id
        self._max_message_length = config.max_message_length
        self._default_only_roles = config.default_only_roles
        self._chats_asset = config.chats_asset

        self._bot = TeleBot(config.api_token)
        self._name = self.get_name(self._bot.get_me())

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
        """
        :return: the user id of the bot Telegram account
        """
        return self._bot.user.id

    @property
    def chats(self) -> Dict[int, Chat]:
        """
        :return: the dictionary of chat id to Chat object
        """
        return self._chats

    def add_chat(self, chat_id: int):
        """
        Add the chat to be watched by the bot.
        The bot will remember users of the chat upon interaction.
        The list of users is persisted between boots.

        :param chat_id: id of the Telegram chat to watch
        """
        self._chats[chat_id] = Chat(True, {},
                                    self.make_get_member_name(chat_id))

    def remove_chat(self, chat_id: int):
        """
        Stop the chat from being watched by bot.
        The list of members is deleted as well.

        :param chat_id: id of the Telegram chat to "forget"
        """
        self._chats.pop(chat_id)

    def start(self):
        """
        Start the bot to read the messages and respond accordingly
        to the rules defined via other Bot methods.
        """
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
        """
        For each user id from <user_ids> produce the markdown string,
        which Telegram interprets as the mention of the user with that id.
        Basically, it's `[user full name](tg://user?id=<user_id>)`.

        :param chat_id: the chat the users are members of
        :param user_ids: ids of users
        :return: iterable of user mentions
        """
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
        """
        Make a decorator for adding an "ability" to the bot.

        An ability is a phrase the bot can respond to, if the message
        is directed to the Bot, i.e. starts with its name.

        The message is divided into several consecutive components:

        - Name: the actual name of the bot at the beginning of the message
        - Phrase: the phrase the ability could be invoked with
        - Subject: all the text after the phrase

        The subject and the message itself is passed to the decorated function.

        If neither usage nor description is specified,
        the ability is not added to the help message.

        If only description is specified, the phrase is used as the usage
        in the help message.

        :param phrase: a phrase to respond to, may be regex
        :param only_roles: chat members roles allowed to use the ability
        :param md: True if the reply generates Markdown
        :param sanitizer: preprocessor of the Subject
        :param usage: how to invoke the ability, for help message
        :param description: description of the ability, for help message
        :param example: example of usage to be added to the help message
        :return:
        """
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
                            predicate: Predicate,
                            reply: Reply,
                            *only_roles: str,
                            md: bool = False,
                            only_new: bool = True):
        """
        Adds native message handler, but with advanced predicate,
        based on the arguments.

        :param predicate: the custom predicate to be used
        alongside generated ones
        :param reply: function to generate the reply text
        :param only_roles: the message is handled only if the role
        of the message sender in the message chat is in this collection
        :param md: True if <reply> generates markdown, False if plain text
        :param only_new: True to skip messages that were send
        before the bot started, but after the last time bot was stopped.
        """
        predicate = self.make_predicate(only_roles,
                                        predicate,
                                        only_new=only_new)
        self.add_native_message_handler(predicate, reply, md=md)

    def add_native_message_handler(self,
                                   predicate: Predicate,
                                   reply: Reply,
                                   md: bool = False):
        """
        Adds the handler to the underlying TeleBot instance.

        The <predicate> is used to determine
        whether to use this specific handler for a message.

        The <reply> is used to generate the text for the reply
        based on the matched message.

        The bot replies only if the <reply> returned non-empty response.

        :param predicate: determines whether to handle the message
        :param reply: generates the reply text
        :param md: True if <reply> generates markdown, False if plain text
        """

        parse_mode = md and "markdown" or None

        def handler(message):
            if response := reply(message):
                self._bot.reply_to(message, response, parse_mode=parse_mode)

        return self._bot.message_handler(func=predicate)(handler)

    def get_user(self, chat_id: int, user_id: int) -> User:
        """
        :param chat_id: Telegram chat id the user is a member of
        :param user_id: Telegram user id
        :return: The user with the user id from the chat
        """
        return self._bot.get_chat_member(chat_id, user_id).user

    def get_full_name(self, chat_id: int, user_id: int) -> str:
        """
        :param chat_id: Telegram chat id the user is a member of
        :param user_id: Telegram user id
        :return: The full name of the user
        """
        return self.get_user(chat_id, user_id).full_name

    def make_get_member_name(self, chat_id: int) -> Callable[[int], str]:
        """
        Make a function, that for given user id gets their name
        via Bot.get_name. Convenience method for making
        <get_name> argument for Chat object.

        :param chat_id: chat id to use in the returned function calls
        :return: function giving name for user id
        """
        return lambda user_id: self.get_name(self.get_user(chat_id, user_id))

    def get_help_message(self) -> str:
        """
        :return: help message with bot abilities
        """
        return self._help.make_message()

    def log(self,
            chat_id: int,
            user_id: int,
            phrase: str,
            subject: str,
            response: str = ''):
        """
        Log the interaction with a user from a chat.

        :param chat_id: id of the chat where the interaction happened
        :param user_id: id of the user interacted with
        :param phrase: the phrase that invoked the interaction
        :param subject: extra text of the message
        :param response: how the bot replied
        """
        log(self.chats[chat_id][user_id], phrase, subject, response)

    @staticmethod
    def get_name(user: User, full_name_threshold: int = 16) -> str:
        """
        Returns either username or full name of the given User.

        If the length of the full name is less than <full_name_threshhold>
        or is not greater than the username length, the full name is returned.

        Otherwise, username.

        Both username and full name are preprocessed via utils.sanitize_name

        :param user: User to get username and full_name from
        :param full_name_threshold: still return full name
        when its length is smaller than this threshold,
        even if the length of username is smaller.
        :return: either username or full name
        """
        un = sanitize_name(user.username)
        fn = sanitize_name(user.full_name)
        return ((len(fn) < full_name_threshold or len(fn) <= len(un))
                and fn
                or un)

    def make_predicate(self,
                       only_roles: Iterable[str],
                       *extra_predicates: Predicate,
                       only_new: bool = True) -> Predicate:
        """
        Make a predicate that matches messages based on complex criteria.

        :param only_roles: match only messages from users having
        any of those roles in the message chat.
        If empty, the default only roles are used from the config.
        To avoid it, e.g. match only messages from the "master" -
        specify any value different from the real possible roles,
        like "master" in this example. Still any real Telegram roles
        may be used.
        :param extra_predicates: any extra custom criteria to check
        :param only_new: True to skip messages that were send
        before the bot started, but after the last time bot was stopped.
        :return: a functon checking if a message satisfies the criteria.
        """
        predicates = [
            self.make_from_user_predicate(
                only_roles or self._default_only_roles),
            lambda m: len(m.text) < self._max_message_length
        ]
        only_new and predicates.insert(1, lambda m: m.date >= self._started_at)
        extra_predicates and predicates.extend(extra_predicates)
        predicates = tuple(predicates)
        return lambda m: all(p(m) for p in predicates)

    def make_from_user_predicate(self, only_roles: Iterable[str]) -> Predicate:
        """
        Make a predicate, that matches messages in added and active chats,
        whose sender role is in only_roles.

        The predicate a priory matches messages from "master"

        :param only_roles: allowed roles of message sender
        :return: predicate that matches only messages from specific users
        """
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

    def make_address_predicate(self, phrase: str) -> Predicate:
        """
        Make a predicate that matches only messages
        that start with direct address to the bot, i.e. start with the bot name,
        and have specific phrase after it.

        :param phrase: a phrase to match, may be regex
        :return: predicate that matches specific directed phrase
        """
        _pattern = re.compile(
            f"^{self._name.lower()}(?:,| |, )"
            f"({phrase.lower()})".replace(" ", "\\s+"))

        def predicate(message: Message) -> re.Match | None:
            return _pattern.match(message.text.lower())

        return predicate
