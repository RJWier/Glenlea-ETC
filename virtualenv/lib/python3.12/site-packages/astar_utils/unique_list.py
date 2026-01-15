# -*- coding: utf-8 -*-
"""Contains UniqueList class."""

from typing import Any
from collections.abc import Iterable, MutableSequence


class UniqueList(MutableSequence):
    """Ordered collection with unique elements.

    Can be used like an ordinary ``list``, but will only store one copy of
    each item, at the index where it was first inserted. Direct setting of
    items will raise ``TypeError``. To change an item, use the `.remove()`
    method or the ``del`` statement to remove the item and insert the new item
    at the desired index. This class also implements a method
    `.append_first(value)`, which works like `.append()`, but inserts the item
    at index 0 instead of -1. All other items are shifted one index to the
    right, just like when inserting at any other position in between other
    items.
    """

    def __init__(self, initial: Iterable[Any] | None = None):
        self._set: set[Any] = set()  # For uniqueness
        self._list: list[Any] = []    # For order

        if initial is not None:
            self.extend(initial)

    def __getitem__(self, index: int):
        """x.__getitem__(y) <==> x[y]."""
        return self._list[index]

    def __setitem__(self, index: int, value) -> None:
        """Not supported."""
        raise TypeError(
            f"{self.__class__.__name__} does not support item mutation, only "
            "insertion, removal and reordering.")

    def __delitem__(self, index: int) -> None:
        """Delete self[key]."""
        self._set.discard(self._list.pop(index))

    def __len__(self) -> int:
        """Return len(self)."""
        return len(self._set)

    def __contains__(self, value) -> bool:
        """Return key in self."""
        return value in self._set

    def insert(self, index: int, value) -> None:
        """Insert value before index."""
        if value not in self:
            self._set.add(value)
            self._list.insert(index, value)

    def append_first(self, value) -> None:
        """
        Append element to the front of the list.

        If the element is already present in the list, move it to the front.
        """
        if value in self:
            self.remove(value)
        self.insert(0, value)

    def __repr__(self) -> str:
        """Return repr(self)."""
        return f"{self.__class__.__name__}({self._list!r})"
