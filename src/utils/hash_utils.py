from sys import maxsize
import random
from typing import Any, Iterable, Callable

from utils import init

Projector = Callable[[Any], Any]


def h(x: Any) -> int:
    """
    Return the hash of the passed value,
    but preprocess the value if it's a string
    removing the space characters and casting the string to lower case

    :param x: a value to get the hash of
    :return: the hash of the value
    """
    return (abs(isinstance(x, str)
                and hash(x.lower().strip().replace(' ', ''))
                or hash(x)))


def one(x: Any) -> float:
    """
    Convert the passed value to a float within [0, 1]
    based on the hash of the passed value

    :param x: the value to get the hash of
    :return: the corresponding float within [0, 1]
    """
    return h(x) / maxsize


def make_ref_chooser(options: Iterable) -> Projector:
    """
    Make a function that returns an item from the options
    based on the hash of the passed value to that function.
    The returned function stores the reference
    to the passed collection of options, hence the options
    may be added after the function is made, and they would
    have a chance to be returned as well.

    :param options: collection of all the possible values to choose from
    :return: the function choosing one of options
    """
    def choice(x: Any) -> Any:
        return tuple(options)[h(x) % len(options)]

    return choice


def make_chooser(*options: Any) -> Projector:
    """
    Make a function that chooses one item from provided options
    based on the hash of the passed value.
    In contrast to the ``make_ref_chooser``,
    the choosers made by ``make_chooser`` doesn't allow adding options
    after the chooser function is made

    :param options: all the possible values to choose from
    :return: the function choosing one of options
    """
    return make_ref_chooser(options)


def accord_plural(n: int, plural: str, alt_plural: str) -> str:
    """
    Return either ``plural`` or ``alt_plural`` noun form
    to match the value of ``n``.

    For example, alt_plural(n, "секунди", "секунд") returns
    "секунд" if the last digit in ``n`` is 0, 5, 6, 7, 8, 9,
    or if ``n`` is 11, 12, 13, 14. Otherwise, the "секунди" is returned

    :param n: the value to choose based on
    :param plural: noun form for "lower" half of digits
    :param alt_plural: noun form for "upper" half of digits
    :return: plural form that corresponds to the ``n`` value
    """
    return ((n % 10 > 4 or n % 10 == 0 or n // 10 == 1)
            and alt_plural
            or plural)


@init
def get_time_delta() -> Projector:
    """
    Generate an arbitrary answer to the "when from now on?" question
    based on the hash of the passed value

    :param x: arbitrary value to get the hash of
    :return: the formatted time interval
    """
    def option(x: str) -> Callable[[Any], str]:
        return lambda _: x

    def factory(singular: str,
                plural: str,
                alt_plural: str,
                max_value: int) -> Callable[[int], str]:
        def f(x: int):
            prefix = 'десь ' * random.randint(0, 1)
            value = (x % max_value) + 1
            if value == 1:
                return f'{prefix}за {singular}'
            start = f'{prefix}за {value} '
            if value % 10 == 1:
                return f'{start}{singular}'
            return f'{start}{accord_plural(value, plural, alt_plural)}'

        return f

    options = make_chooser(
        option("зараз"),
        option("нині"),
        option("завтра"),
        option("ніколи"),
        factory("секунду", "секунди", "секунд", 60),
        factory("хвилину", "хвилини", "хвилин", 60),
        factory("годину", "години", "годин", 24),
        factory("день", "дні", "днів", 30),
        factory("місяць", "місяці", "місяців", 12),
        factory("рік", "роки", "років", 64)
    )

    def impl(x: Any) -> str:
        return options(x)(h(x))

    return impl
