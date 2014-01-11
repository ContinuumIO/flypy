# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest

from flypy import jit

class TestCallingConventionFromPython(unittest.TestCase):

    def test_varargs(self):
        @jit
        def f(a, b, *args):
            return [a, b, args[1]]

        self.assertEqual(f(1, 2, 0, 3, 0), [1, 2, 3])

@jit
def f(a, b, *args):
    return [a, b, args[1]]

f(1, 2, 0, 3, 0)

#if __name__ == '__main__':
#    unittest.main()