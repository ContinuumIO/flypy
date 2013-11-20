# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import unittest
from numba2 import jit

class TestControlFlow(unittest.TestCase):

    def test_loop_carried_dep_promotion(self):
        @jit
        def f(n):
            sum = 0
            for i in range(n):
                sum += float(i)
            return sum

        self.assertEqual(f(10), 45.0)


if __name__ == '__main__':
    #TestControlFlow('test_reduction').debug()
    unittest.main()