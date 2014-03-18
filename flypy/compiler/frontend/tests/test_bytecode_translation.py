# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from pykit.ir.interp import UncaughtException

from flypy import typeof, jit
from flypy.pipeline import environment, phase
from flypy.compiler import interpreter

#===------------------------------------------------------------------===
# Helpers
#===------------------------------------------------------------------===

def run(f, expected, args):
    interpreter.expect(jit(f), phase.frontend, args, expected)

#===------------------------------------------------------------------===
# Tests
#===------------------------------------------------------------------===

class TestBytecodeTranslation(unittest.TestCase):

    #===------------------------------------------------------------------===
    # Ops
    #===------------------------------------------------------------------===

    def test_compare(self):
        def f(a, b):
            return a < b
        run(f, True, [5, 6])

    def test_binop(self):
        def f(a, b):
            return a + b
        run(f, 11, [5, 6])

    #===------------------------------------------------------------------===
    # Calls
    #===------------------------------------------------------------------===

    def test_call(self):
        def f(a, b):
            return g(a + b)

        def g(x):
            return x * x

        run(f, 100, [4, 6])

    def test_recursion(self):
        def fact(n):
            if n > 1:
                return n * fact(n - 1)
            return 1

        run(fact, 120, [5])

    #===------------------------------------------------------------------===
    # Control Flow
    #===------------------------------------------------------------------===

    def test_while(self):
        def f(a, b):
            while a < b:
                a = a + 1
            return a + b

        # print(translate(f))
        run(f, 20, [0, 10])

    def test_for(self):
        # NOTE: the raise stems from 'next', which is not yet inlined, since
        # we interpret the result of bytecode translation
        raise unittest.SkipTest("Exception throwing")

        def f(a, b):
            sum = 0
            for i in range(a, b):
                sum += i
            return sum

        # dis.dis(f)
        # print(translate(f)[0])
        run(f, 45, [0, 10])

    #===------------------------------------------------------------------===
    # Exceptions
    #===------------------------------------------------------------------===

    def test_raise(self):
        raise unittest.SkipTest("Exception throwing")

        def f(a, b):
            sum = 0
            for i in range(a, b):
                sum += i
                if i >= 5:
                    raise ValueError(sum)
            return sum

        # dis.dis(f)
        #print(translate(f)[0])
        try:
            run(f, 15, [0, 10]) # TODO: exc_throw
        except UncaughtException as e:
            exc = e.args[0]
            assert isinstance(exc, ValueError)
            self.assertEqual(exc.args[0], 15)
        else:
            raise Exception("Expected 'UncaughtException'")

    def test_catch_noerror(self):
        raise unittest.SkipTest("Exception throwing")

        def f(a, b):
            try:
                a + b
            except ValueError:
                return 1
            except Exception:
                return 2
            else:
                return 3

        # dis.dis(f)
        # print(translate(f))
        run(f, 3, [0, 10])

    def test_catch_error(self):
        raise unittest.SkipTest("Exception throwing")

        def f(a, b):
            try:
                raise ValueError(a)
            except ValueError:
                return 1
            except Exception:
                return 2
            else:
                return 3

        # dis.dis(f)
        # print(translate(f))
        run(f, 1, [0, 10]) # TODO: exc_throw


if __name__ == '__main__':
    #TestBytecodeTranslation('test_for').debug()
    unittest.main()