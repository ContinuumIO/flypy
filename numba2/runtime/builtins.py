# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

try:
    import __builtin__ as builtins
except ImportError:
    import builtins

from .. import jit, ijit, overlay, overload
from .interfaces import Sequence, Iterable, Iterator

# ____________________________________________________________

@jit('Iterable[a] -> Iterator[a]')
def iter(x):
    return x.__iter__()

@jit('Iterator[a] -> a')
def next(x):
    return x.__next__()

# ____________________________________________________________

# TODO: Implement generator fusion

@jit
def len_range(start, stop, step):
    if step < 0:
        start, stop, step = stop, start, -step
    if stop <= start:
        return 0
    return (stop - start - 1) // step + 1

@jit
def range(start, stop=0xdeadbeef, step=1):
    # TODO: We need to either optimize variants, or recognize that
    # 'x is None' is equivalent to isinstance(x, NoneType) and prune the
    # alternative branch during type inference
    if stop == 0xdeadbeef:
        stop = start
        start = 0

    return Range(start, stop, step)

@jit
class Range(Sequence):

    layout = [('start', 'int64'), ('stop', 'int64'), ('step', 'int64')]

    @jit
    def __iter__(self):
        return RangeIterator(self.start, self.step, len(self))

    @jit
    def __len__(self):
        return len_range(self.start, self.stop, self.step)


@jit
class RangeIterator(Iterator):

    layout = [('start', 'int64'), ('step', 'int64'), ('length', 'int64')]

    @jit
    def __next__(self):
        if self.length > 0:
            result = self.start
            self.start += self.step
            self.length -= 1
            return result
        raise StopIteration

# ____________________________________________________________

overlay(builtins.iter, iter)
overlay(builtins.next, next)
overlay(builtins.range, range)