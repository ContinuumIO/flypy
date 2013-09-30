# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from pykit.ir.interp import UncaughtException
from numba2 import jit, int32

#===------------------------------------------------------------------===
# Test code
#===------------------------------------------------------------------===

@jit
class C(object):
    layout = {'x': int32}

    @jit
    def __init__(self, x):
        self.x = x

    @jit
    def __add__(self, other):
        return self.x * other.x

    @jit
    def method(self, other):
        return self.x * other.x

@jit
def call_special(x):
    return C(x) + C(2)

@jit
def call_method(x):
    return C(x).method(C(2))

#===------------------------------------------------------------------===
# Tests
#===------------------------------------------------------------------===

class TestClasses(unittest.TestCase):

    def test_special_method(self):
        self.assertEqual(call_special(5), 10)

    def test_methods(self):
        self.assertEqual(call_method(5), 10)

if __name__ == '__main__':
    unittest.main()
