# -*- coding: utf-8 -*-

"""
Number interfaces.
"""

from __future__ import print_function, division, absolute_import
from functools import wraps

from flypy import abstract, jit, ijit
from flypy.runtime.lowlevel_impls import add_impl_cls

from pykit import types as ptypes

__all__ = ['Number', 'Real', 'Complex', 'Rational', 'Irrational',
           'Integer', 'Floating']


def ojit(signature):
    """
    Simple helper that unboxes arguments and boxes results of opaque methods.
    These methods have external implementations assigned!
    """
    def decorator(f):
        @wraps(f)
        def wrapper(self, *args):
            args = [self.unwrap()] + [x.unwrap() for x in args]
            return self.wrap(f(*args))
        return jit(signature, opaque=True, inline=True, eval_if_const=True)(wrapper)
    return decorator


@abstract
class Number(object):
    """Interface for all numbers"""

    layout = []

    def __init__(self, x):
        self.x = x

    def wrap(self, x):
        return x

    def unwrap(self):
        return self.x

    #===------------------------------------------------------------------===
    # Arith
    #===------------------------------------------------------------------===

    @ojit('a -> a -> a')
    def __add__(self, other):
        return self + other

    @ojit('a -> a -> a')
    def __mul__(self, other):
        return self * other

    @ojit('a -> a -> a')
    def __sub__(self, other):
        return self - other

    @ojit('a -> a -> a')
    def __div__(self, other):
        return self / other

    @jit('a -> a -> a')
    def __truediv__(self, other):
        return self.__div__(other)

    @jit('a -> a -> a')
    def __floordiv__(self, other):
        # TODO: implement
        #return self // other
        return self.__div__(other)

    @ojit('a -> a -> a')
    def __mod__(self, other):
        return self % other

    @ojit('a -> a')
    def __invert__(self):
        return ~self

    @jit('a -> a')
    def __abs__(self):
        if self < 0:
            return -self
        return self

    #===------------------------------------------------------------------===
    # Compare
    #===------------------------------------------------------------------===

    @ojit('a -> a -> bool')
    def __eq__(self, other):
        return self == other

    @ojit('a -> a -> bool')
    def __ne__(self, other):
        return self != other

    @ojit('a -> a -> bool')
    def __lt__(self, other):
        return self < other

    @ojit('a -> a -> bool')
    def __le__(self, other):
        return self <= other

    @ojit('a -> a -> bool')
    def __gt__(self, other):
        return self > other

    @ojit('a -> a -> bool')
    def __ge__(self, other):
        return self >= other

    #===------------------------------------------------------------------===
    # Bitwise
    #===------------------------------------------------------------------===

    @ojit('a -> a -> a')
    def __and__(self, other):
        return self & other

    @ojit('a -> a -> a')
    def __or__(self, other):
        return self | other

    @ojit('a -> a -> a')
    def __xor__(self, other):
        return self ^ other

    @ojit('a -> a -> a')
    def __lshift__(self, other):
        return self << other

    @ojit('a -> a -> a')
    def __rshift__(self, other):
        return self >> other

    #===------------------------------------------------------------------===
    # Non-opaque methods
    #===------------------------------------------------------------------===

    @jit('a -> a')
    def __neg__(self):
        return 0 - self

    @jit('a -> bool')
    def __nonzero__(self):
        return self != 0


@abstract
class Real(Number):
    """Real numbers"""

@abstract
class Complex(Number):
    """Complex numbers"""

@abstract
class Rational(Real):
    """Rational numbers"""

@abstract
class Irrational(Real):
    """Irrational numbers"""

@abstract
class Integer(Real):
    """Integers"""

@abstract
class Floating(Real):
    """Floating point numbers"""


#===------------------------------------------------------------------===
# Binops
#===------------------------------------------------------------------===

def add_binop(cls, name, restype=None, pykitname=None):
    if not pykitname:
        pykitname = name
    special_name = "__%s__" % name
    impl = lambda b, _, x, y: b.ret(getattr(b, pykitname)(x, y))
    add_impl_cls(cls, special_name, impl, restype)


add_binop(Number, "add")
add_binop(Number, "mul")
add_binop(Number, "sub")
add_binop(Number, "div")
add_binop(Number, "mod")

add_binop(Number, "eq", restype=ptypes.Bool)
add_binop(Number, "ne", restype=ptypes.Bool)
add_binop(Number, "lt", restype=ptypes.Bool)
add_binop(Number, "le", restype=ptypes.Bool)
add_binop(Number, "gt", restype=ptypes.Bool)
add_binop(Number, "ge", restype=ptypes.Bool)

add_binop(Number, "and", pykitname="bitand")
add_binop(Number, "or", pykitname="bitor")
add_binop(Number, "xor", pykitname="bitxor")
add_binop(Number, "lshift")
add_binop(Number, "rshift")
