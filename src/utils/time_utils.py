import re
from typing import Tuple

from utils import init, take_while, localed


@init
def parse_duration_en():
    __units = 'smh'
    __pattern = re.compile(
        f"(?:(?P<value>[1-9]\\d*)(?P<unit>[{''.join(__units)}]?))")

    def __parse_token(m: re.Match):
        return int(m[0]) * (60 ** __units.index(m[1]))

    def __parse(s):
        matches = __pattern.findall(s)

        if 1 > len(matches) < 3:
            raise ValueError(
                f"Duration must contain from 1 to 3 tokens, "
                f"but got {len(matches)}")
        if len(set(m[1] for m in matches)) != len(matches):
            raise ValueError(f"All units must be unique, but got {s}")
        return sum(map(__parse_token, matches))

    def impl(s: str) -> int:
        return __parse(s.lower().strip())

    return impl


@init
def parse_duration_uk():
    __pattern = re.compile("\\s*(\\d+)\\s*(г(?:од)?|хв?|с(?:ек)?)")
    __units = {'г': 'h', 'х': 'm', 'с': 's', '': 's'}

    def impl(s: str):
        if not (matches := __pattern.findall(s.strip().lower())):
            raise ValueError(f"Invalid duration format: {s}")
        return parse_duration_en(
            ''.join(f"{m[0]}{__units[m[1][0]]}" for m in matches))

    return impl


@localed(en=parse_duration_en, uk=parse_duration_uk)
def parse_duration():
    pass


@init
def parse_time():
    to_23 = "[01]?[0-9]|2[0-3]"
    to_59 = "0?[0-9]|[1-5][0-9]"
    _pattern = re.compile(
        f"^(?P<H>{to_23}) (: (?P<M> {to_59} ) (: (?P<S> {to_59} ) )? )?$", re.X)

    def _get_tokens(s: str):
        if not (m := _pattern.match(s)):
            return ()
        g = m.groupdict()
        return g.get('H'), g.get('M'), g.get('S')

    def impl(s: str) -> int:
        return sum(
            int(v) * (60 ** (2 - i))
            for (i, v) in enumerate(_get_tokens(s))
            if v)

    return impl


@init
def unix2parts():
    _hour = 3600
    _minute = 60

    def impl(seconds: int) -> Tuple[int, int, int]:
        s = int(seconds)
        return (s // _hour,
                (s % _hour) // _minute,
                s % _minute)

    return impl


def _make_dump_duration(units):
    def impl(seconds: int) -> str:
        parts = unix2parts(seconds)
        return ''.join(f"{v}{units[i]}" for (i, v) in enumerate(parts) if v)

    return impl


@localed(en=_make_dump_duration('hms'),
         uk=_make_dump_duration(('год', 'хв', 'сек')))
def dump_duration():
    pass


def dump_time(seconds: int) -> str:
    return ':'.join(f"{v:0>2}" for v in unix2parts(seconds))


def dump_time_tiny(seconds: int) -> str:
    return ':'.join(f"{v:0>2}" for v in take_while(unix2parts(seconds), bool))
