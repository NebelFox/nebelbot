from sys import maxsize
import random

from utils import init


def h(x):
    return (abs(isinstance(x, str)
                and hash(x.lower().strip().replace(' ', ''))
                or hash(x)))


def one(x):
    return h(x) / maxsize


def ref_chooser(options):
    def choice(x):
        return list(options)[h(x) % len(options)]

    return choice


def chooser(*options):
    return ref_chooser(options)


def accord_plural(n, plural, alt_plural):
    return ((n % 10 > 4 or n % 10 == 0 or n // 10 == 1)
            and alt_plural
            or plural)


@init
def get_time_delta():
    def option(x: str):
        return lambda _: x

    def factory(singular: str,
                plural: str,
                alt_plural: str,
                max_value: int):
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

    options = chooser(
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

    def impl(x: Any):
        return options(x)(h(x))

    return impl

