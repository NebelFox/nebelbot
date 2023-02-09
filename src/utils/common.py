import re
from datetime import datetime as dt
from typing import Callable, Sized, Any
import string
from functools import wraps


def init(f: Callable):
    """
    Call the decorated function and replace it with the call result.

    Is purposed for encapsulating some extra context for a function,
    like constants and other functions, i.e. perform an initialization
    of the function. This way, the entities of this extra context
    doesn't go into the global scope.

    :param f: a function with no parameters that returns an arbitrary function
    :return: the function produced by ``f``
    """
    return wraps(f)(f())


def make_localed(**locales: Callable):
    """
    Compose a set of functions and corresponding locale codes
    into one function with extra ``locale`` parameter,
    which calls one of the originally passed functions by the passed
    ``locale`` keyword argument value.

    The default value of the ``locale`` is set to the first kwarg key passed.

    :param locales: string codes corresponding to a function to be called
    :return: composed function with extra ``locale`` kwarg
    """

    def impl(*args, locale: str = next(iter(locales))):
        return locales[locale](*args)

    return impl


@init
def cy2en():
    """
    Translate a cyrillic character into the latin character
    that looks identical in upper case.

    An empty string is returned if there is no such corresponding
    character for passed string.

    :param c: character to translate
    :return: latin character or an empty string
    """

    mapping = {
        'е': 'e',
        'у': 'y',
        'т': 't',
        'і': 'l',
        'о': 'o',
        'р': 'p',
        'а': 'a',
        'н': 'h',
        'к': 'k',
        'х': 'x',
        'с': 'c',
        'в': 'b',
        'м': 'm'
    }

    def impl(c: str) -> str:
        return mapping.get(c.lower(), '')

    return impl


@init
def sanitize_name():
    """
    Remove any symbols from teh provided string,
    keeping only ascii letters, digits, punctuation chars, and cyrillic chars.

    :param name: the string to sanitize
    :return: string containing only allowed characters, with order preserved
    """

    _allowed_chars = set(string.ascii_letters +
                         string.digits +
                         string.punctuation +
                         "йцукенгшщзхїфівапролджєячсмитьбю" +
                         "ЙЦУКЕНГШЩЗХЇФІВАПРОЛДЖЄЯЧСМИТЬБЮ")

    def impl(name: str) -> str:
        return ''.join(x for x in (name or '') if x in _allowed_chars)

    return impl


@init
def log():
    """
    Print the passed message, adding time info
    and formatting and coloring the parts of the message
    to be more readable and distinguishable

    :param invoker: who/what caused the event
    :param event: what happened
    :param subject: additional details of the event
    :param result: the consequence of the event
    """

    r = '\033[0m'
    b = '\033[36m'
    g = '\033[32m'
    y = '\033[33m'
    p = '\033[35m'
    f = "%H:%M:%S"

    def impl(invoker: Any,
             event: Any,
             subject: Any = '',
             result: Any = '') -> None:
        t = dt.now().strftime(f)
        print(" ".join((
            f"{t}",
            f"{p}{invoker:<15}{r}",
            f"{g}{event.rstrip():>17}{r}",
            subject and f"[{y}{subject}{r}]" or '',
            result and f"{b}{result}{r}")) or '')

    return impl


def repr_seq(sequence: Sized, sep: str = ', ', last_sep: str = 'and') -> str:
    """
    Convert a sequence to a string but with another separator for the last pair

    :param sequence: source of the items to join
    :param sep: separator for all the items except the last two
    :param last_sep: separator for the last two items
    :return: string of joined items of the sequence
    """

    n = len(sequence)
    if n == 0:
        return ""
    if n == 1:
        return sequence[0]
    return f'{sep.join(sequence[:-1])} {last_sep} {sequence[-1]}'


@init
def pascal2snake():
    """
    Convert a string in PascalCase to snake_case

    :param s: a string in PascalCase to convert
    :return: the passed string converted to snake_case
    """
    _capital_pattern = re.compile('[A-Z]')

    def repl(m: re.Match) -> str:
        return f'_{m.group(0).lower()}'

    def impl(s: str) -> str:
        return _capital_pattern.sub(repl, s).strip('_')

    return impl
