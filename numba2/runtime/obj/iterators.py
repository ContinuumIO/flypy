# -*- coding: utf-8 -*-

"""
Counting iterators.
"""

from __future__ import print_function, division, absolute_import

from numba2 import jit, sjit, ijit
from ..interfaces import Sequence, Iterator

@sjit('CountingIterator[obj]')
class CountingIterator(Iterator):

    layout = [('obj', 'obj'), ('idx', 'int64'), ('length', 'int64')]

    @ijit # CountingIterator[Sequence[a]] -> a
    def __next__(self):
        if self.idx < self.length:
            result = self.obj[self.idx]
            self.idx += 1
            return result
        raise StopIteration

    def __str__(self):
        return "counting_iterator(idx=%d, length=%d)" % (self.idx, self.length)

    __repr__ = __str__


@jit('a -> CountingIterator[a]') # TODO: eat a Sequence[a]
def counting_iterator(obj):
    return CountingIterator(obj, 0, len(obj))