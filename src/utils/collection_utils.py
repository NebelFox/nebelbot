from typing import Iterable, Callable, Any, Union, Tuple


def enumerate_reversed(collection: Union[list, tuple]
                       ) -> Iterable[Tuple[int, Any]]:
    """
    Like built-in ``enumerate``,
    but yielding items and indices in reversed order

    :param collection: Sized and Reversible collection
    :return: generator yielding a pair of index and item
    """
    index = len(collection) - 1
    for item in reversed(collection):
        yield index, item
        index -= 1


def take_while(iterable: Iterable[Any],
               predicate: Callable[[Any], bool]) -> Iterable[Any]:
    """
    Yield items from the ``iterable`` until the predicate mismatches the item

    :param iterable: source of items
    :param predicate: continuing condition
    :return: generator yielding the matched "init" of the ``iterable``
    """
    for i in iterable:
        if not predicate(i):
            break
        yield i
