import re
from datetime import datetime as dt
from typing import Callable, Sized, Dict
import string


def init(f: Callable):
    return f()


def localed(**locales: Dict[str, Callable]):
    def decorator(f):
        def impl(*args, locale: str = next(iter(locales))):
            return locales[locale](*args)

        return impl

    return decorator


@init
def cy2en():
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
        return mapping.get(c, '')

    return impl


@init
def sanitize_name():
    _allowed_chars = set(string.ascii_letters +
                         string.digits +
                         string.punctuation +
                         "йцукенгшщзхїфівапролджєячсмитьбю" +
                         "ЙЦУКЕНГШЩЗХЇФІВАПРОЛДЖЄЯЧСМИТЬБЮ")

    def impl(name):
        return ''.join(x for x in (name or '') if x in _allowed_chars)

    return impl


@init
def log():
    r = '\033[0m'
    b = '\033[36m'
    g = '\033[32m'
    y = '\033[33m'
    p = '\033[35m'
    f = "%H:%M:%S"

    def impl(invoker, event, subject='', result=''):
        t = dt.now().strftime(f)
        print(" ".join((
            f"{t}",
            f"{p}{invoker:<15}{r}",
            f"{g}{event.rstrip():>17}{r}",
            subject and f"[{y}{subject}{r}]" or '',
            result and f"{b}{result}{r}")) or '')

    return impl


def repr_seq(sequence: Sized, sep: str = ', ', last_sep: str = 'and') -> str:
    n = len(sequence)
    if n == 0:
        return ""
    if n == 1:
        return sequence[0]
    return f'{sep.join(sequence[:-1])} {last_sep} {sequence[-1]}'


@init
def pascal2snake():
    _capital_pattern = re.compile('[A-Z]')

    def repl(m: re.Match) -> str:
        return f'_{m.group(0).lower()}'

    def impl(s: str) -> str:
        return _capital_pattern.sub(repl, s).strip('_')

    return impl
