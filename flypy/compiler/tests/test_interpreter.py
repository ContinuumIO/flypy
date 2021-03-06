# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from flypy import jit
from flypy.pipeline import phase
from flypy.compiler import interpreter

@jit
def f(x, start, stop, step):
    for i in range(start, stop, step):
        x += i
    return x

args1   = (5, 2, 10, 3)
result1 = f.py_func(*args1)

args2   = (5.0, 2, 10, 3)
result2 = f.py_func(*args2)

#===------------------------------------------------------------------===
# Tests
#===------------------------------------------------------------------===

class TestInterpreter(unittest.TestCase):

    def interp(self, phase):
        result = interpreter.interpret(f, phase, args1)
        self.assertEqual(result, result1)

        #result = interpreter.interpret(f, phase, args2)
        #self.assertEqual(result, result2)

    def test_interp_frontend(self):
        self.interp(phase.frontend)

    def test_interp_typed(self):
        self.interp(phase.typing)

    def test_interp_optimized(self):
        raise unittest.SkipTest # TODO:
        self.interp(phase.opt)

    def test_interp_lowered(self):
        raise unittest.SkipTest # TODO:
        self.interp(phase.ll_lower)


if __name__ == '__main__':
    unittest.main()