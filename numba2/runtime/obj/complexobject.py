# -*- coding: utf-8 -*-

"""
Complex object implementation.
"""

from __future__ import print_function, division, absolute_import

try:
    import __builtin__ as builtins
except ImportError:
    import builtins

import numba2
from numba2 import jit, sjit, typeof, overlay

#===------------------------------------------------------------------===
# Pointer
#===------------------------------------------------------------------===

@sjit('Complex[base]')
class Complex(object):
    layout = [('real', 'base'), ('imag', 'base')]

    @jit('a -> a -> a')
    def __add__(self, other):
        return Complex(self.real + other.real, self.imag + other.imag)

    @jit('a -> a -> a')
    def __sub__(self, other):
        return Complex(self.real - other.real, self.imag - other.imag)

    @jit('a -> a -> a')
    def __mul__(self, other):
        real = (self.real * other.real) - (self.imag * other.imag)
        imag = (self.imag * other.real) + (self.real * other.imag)
        return Complex(real, imag)

    @jit('a -> a -> a')
    def __div__(self, other):
        real = (self.real * other.real) - (self.imag * other.imag)
        imag = (self.imag * other.real) + (self.real * other.imag)
        return Complex(real, imag)

    @jit('a -> a -> bool')
    def __eq__(self, other):
        return self.real == other.real and self.imag == other.imag

    @jit('a -> b -> bool')
    def __eq__(self, other):
        return False

    @jit('a -> bool')
    def __nonzero__(self):
        if bool(self.real):
            return True
        elif bool(self.imag):
            return bool(self.imag)
        else:
            return False

        # <- make this work in translation.py
        #return bool(self.real) or bool(self.imag)

    # __________________________________________________________________

    @staticmethod
    def fromobject(c, type):
        return Complex(c.real, c.imag)

    @staticmethod
    def toobject(c, type):
        return builtins.complex(c.real, c.imag)


@jit('a -> a -> Complex[a]')
def complex(real, imag=0.0):
    return Complex(real, imag)

@typeof.case(builtins.complex)
def typeof(pyval):
    return Complex[numba2.float64]

# ____________________________________________________________

overlay(builtins.complex, complex)
