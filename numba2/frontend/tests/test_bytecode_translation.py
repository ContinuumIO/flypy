# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import dis
import unittest
from pykit.ir.interp import UncaughtException

from numba2.frontend import translate, interpret

def run(f, expected, args):
    code = translate(f)
    result = interpret(code, args=args)
    assert result == expected, "Got %s, expected %s" % (result, expected)

class TestBytecodeTranslation(unittest.TestCase):

    def test_compare(self):
        def f(a, b):
            return a < b
        run(f, True, [5, 6])

    def test_binop(self):
        def f(a, b):
            return a + b
        run(f, 11, [5, 6])

    def test_while(self):
        def f(a, b):
            while a < b:
                a = a + 1
            return a + b

        # print(translate(f))
        run(f, 20, [0, 10])

    def test_for(self):
        def f(a, b):
            sum = 0
            for i in range(a, b):
                sum += i
            return sum

        # dis.dis(f)
        # print(translate(f))
        run(f, 45, [0, 10])

    def test_raise(self):
        def f(a, b):
            sum = 0
            for i in range(a, b):
                sum += i
                if i >= 5:
                    raise ValueError(sum)
            return sum

        # dis.dis(f)
        # print(translate(f))
        try:
            run(f, 15, [0, 10])
        except UncaughtException, e:
            exc = e.args[0]
            assert isinstance(exc, ValueError)
            self.assertEqual(exc.args[0], 15)
        else:
            raise Exception("Expected 'UncaughtException'")

    def test_catch(self):
        def f(a, b):
            try:
                for i in range(a, b):
                    raise ValueError(a)
            except ValueError:
                return 12
            except Exception:
                pass
            else:
                return -1

        dis.dis(f)
        # print(translate(f))
        try:
            run(f, 15, [0, 10])
        except UncaughtException, e:
            exc = e.args[0]
            assert isinstance(exc, ValueError)
            self.assertEqual(exc.args[0], 15)
        else:
            raise Exception("Expected 'UncaughtException'")


if __name__ == '__main__':
    TestBytecodeTranslation('test_catch').debug()
    # unittest.main()