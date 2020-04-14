import multiprocessing.dummy
from contextlib import contextmanager
from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import Optional
from typing import Tuple
from typing import TypeVar
from typing import Union


class _Missing:
    def __repr__(self) -> str:
        return "no value"


_missing = _Missing()


_T = TypeVar('_T')
_U = TypeVar('_U')


def zero_or_one(
    it: Iterable[_U],
    make_exc: Callable[[], Exception],
    default: Union[_Missing, _T] = _missing,
) -> Union[_U, _T]:
    things = list(it)
    if len(things) == 0:
        if isinstance(default, _Missing):
            raise make_exc()
        return default
    elif len(things) == 1:
        return things[0]
    else:
        assert False, "shouldn't get here"  # noqa: B011; # pragma: no cover


def join_paginated_iter(
    get_things: Callable[[int, Optional[_T]], Iterable[Tuple[_U, _T]]], chunk_size: int,
) -> Iterable[_U]:
    # At the moment get_things must take positional arguments.
    # We could make it work with kwargs by using protocols,
    # but mypy gets confused about partials with kwargs.
    # https://github.com/python/mypy/issues/1484

    last = None
    while True:

        things = get_things(chunk_size, last)

        # When chunk_size is 0, don't chunk the query.
        #
        # This will ensure there are no missing/duplicated entries, but
        # will block database writes until the whole generator is consumed.
        #
        # Currently not exposed through the public API.
        #
        if not chunk_size:
            yield from (t for t, _ in things)
            return

        things = list(things)
        if not things:
            break

        _, last = things[-1]

        yield from (t for t, _ in things)


# TODO: find a better way to represent a function like map (mypy)
#
#   _MapFunc = Callable[[Callable[[_T], _U], Iterable[_T]], Iterator[_U]]
#
#   @contextmanager
#   def make_pool_map(workers: int) -> Iterator[_MapFunc[_T, _U]]: ...
#
# results in:
#
#   src/reader/core/reader.py:227: error: Need type annotation for 'make_map'
#
# Using the whole type verbatim in the function definition doesn't.


@contextmanager
def make_pool_map(
    workers: int,
) -> Iterator[Callable[[Callable[[_T], _U], Iterable[_T]], Iterator[_U]]]:
    pool = multiprocessing.dummy.Pool(workers)
    try:
        yield pool.imap_unordered
    finally:
        pool.close()
        pool.join()


@contextmanager
def make_noop_map() -> Iterator[
    Callable[[Callable[[_T], _U], Iterable[_T]], Iterator[_U]]
]:
    yield map
