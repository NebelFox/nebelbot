from typing import Iterable, Callable, Any


def enumerate_reversed(collection):
    index = len(collection) - 1
    for item in reversed(collection):
        yield index, item
        index -= 1


def take_while(iterable: Iterable,
               predicate: Callable[[Any], bool]) -> Iterable:
    for i in iterable:
        if not predicate(i):
            break
        yield i
