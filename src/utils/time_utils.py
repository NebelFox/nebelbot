import re
from typing import Tuple, List, Callable, Mapping

from utils import init, take_while, make_localed


@init
def parse_duration_en() -> Callable[[str], int]:
    """
    Parse a human-readable-formatted duration
    with time units as 's', 'm' and 'h' for seconds, minutes and hours
    respectively into the duration in seconds. The units may appear
    in arbitrary order, but each unit must appear at most once

    :param s: duration in human-readable format
    :return: parsed duration in seconds
    """
    __units = 'smh'
    __pattern = re.compile(
        f"(?:(?P<value>[1-9]\\d*)(?P<unit>[{''.join(__units)}]?))")

    def __parse_token(m: re.Match) -> int:
        return int(m[0]) * (60 ** __units.index(m[1]))

    def impl(s: str) -> int:
        matches = __pattern.findall(s.lower().strip())

        if 1 > len(matches) < 3:
            raise ValueError(
                f"Duration must contain from 1 to 3 tokens, "
                f"but got {len(matches)}")
        if len(set(m[1] for m in matches)) != len(matches):
            raise ValueError(f"All units must be unique, but got {s}")
        return sum(map(__parse_token, matches))

    return impl


@init
def parse_duration_uk() -> Callable[[str], int]:
    """
    Parse a human-readable-formatted duration
    with time units as 'с/сек', 'х/хв' and 'г/год'
    for seconds, minutes and hours respectively
    into the duration in seconds. The units may appear
    in arbitrary order, but each unit must appear at most once

    :param s: duration in human-readable format
    :return: parsed duration in seconds

    :return:
    """
    __pattern = re.compile("\\s*(\\d+)\\s*(г(?:од)?|хв?|с(?:ек)?)")
    __units = {'г': 'h', 'х': 'm', 'с': 's', '': 's'}

    def impl(s: str) -> int:
        if not (matches := __pattern.findall(s.strip().lower())):
            raise ValueError(f"Invalid duration format: {s}")
        return parse_duration_en(
            ''.join(f"{m[0]}{__units[m[1][0]]}" for m in matches))

    return impl


parse_duration = make_localed(en=parse_duration_en, uk=parse_duration_uk)


@init
def parse_time() -> Callable[[str], int]:
    """
    Parse time in format HH:MM:SS into the total of seconds of that time

    :param s: the formatted string to parse
    :return: the int indicating the number of seconds the passed time contains
    """
    to_23 = "[01]?[0-9]|2[0-3]"
    to_59 = "0?[0-9]|[1-5][0-9]"
    _pattern = re.compile(
        f"^(?P<H>{to_23}) (: (?P<M> {to_59} ) (: (?P<S> {to_59} ) )? )?$", re.X)

    def _get_tokens(s: str) -> Tuple | Tuple[str, str, str]:
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
def unix2parts() -> Callable[[int], Tuple[int, int, int]]:
    """
    For given time in seconds extract number of hours, remaining minutes,
    and remaining seconds the passed amount of seconds contains

    :param seconds: total seconds in time to extract parts from
    :return: three parts - hours, minutes, and seconds
    """
    _hour = 3600
    _minute = 60

    def impl(seconds: int) -> Tuple[int, int, int]:
        s = int(seconds)
        return (s // _hour,
                (s % _hour) // _minute,
                s % _minute)

    return impl


def _make_dump_duration(units: Mapping[int, str]) -> Callable[[int], str]:
    """
    Make a function that serializes the given duration in seconds
    into human-readable format using the provided strings for time units.

    The mapping from int to time unit is expected to be the following:

    - 0 -> hours
    - 1 -> minutes
    - 2 -> seconds

    :param units: time units for hours, minutes and seconds respectively
    :return: function that formats the duration using given units
    """
    def impl(seconds: int) -> str:
        parts = unix2parts(seconds)
        return ''.join(f"{v}{units[i]}" for (i, v) in enumerate(parts) if v)

    return impl


dump_duration = make_localed(en=_make_dump_duration('hms'),
                             uk=_make_dump_duration(('год', 'хв', 'сек')))


def dump_time(seconds: int) -> str:
    """
    Format the total time in seconds into format HH:MM:SS

    :param seconds: total time in seconds to format
    :return: the formatted human-readable time
    """
    return ':'.join(f"{v:0>2}" for v in unix2parts(seconds))


def dump_time_tiny(seconds: int) -> str:
    """
    Format the total time in seconds into format HH:MM:SS.
    If the remaining seconds = 0, the format is HH:MM
    Additinally, if the remaining minutes = 0 as well, the format is HH

    :param seconds:
    :return:
    """
    return ':'.join(f"{v:0>2}" for v in take_while(unix2parts(seconds), bool))
