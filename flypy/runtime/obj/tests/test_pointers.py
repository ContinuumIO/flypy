# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

import ctypes
import cffi
import unittest

from flypy import jit, typeof, int32, float64, NULL

ffi = cffi.FFI()
arr = ffi.new('int[3]')
arr[0] = 5
arr[1] = 6
p = ffi.cast('int *', arr)

class TestPointers(unittest.TestCase):

    def test_pointer_getitem(self):
        @jit
        def f(p):
            return p[1]
        self.assertEqual(f(p), 6)

    def test_pointer_setitem(self):
        @jit
        def f(p):
            p[2] = 14
            return p[2]
        self.assertEqual(f(p), 14)

    def test_pointer_compare(self):
        @jit
        def f(p):
            return p == NULL

        p1 = ffi.new('int *')
        p2 = ffi.new('float *')
        p3 = ffi.cast('void *', p1)

        self.assertFalse(f(p1))
        self.assertFalse(f(p2))
        self.assertFalse(f(p3))

        self.assertTrue(f(ctypes.c_void_p(0)))

    def test_nonzero(self):
        @jit
        def f(p):
            return bool(p)
        self.assertTrue(f(ffi.new('int *')))
        self.assertFalse(f(ctypes.c_void_p(0)), False)

    def test_tostr(self):
        @jit
        def f(x):
            return str(x)

        p0 = ctypes.pointer(ctypes.c_int(10))
        p1 = ctypes.c_void_p(0)

        p0_addr = ctypes.cast(p0, ctypes.c_void_p).value

        self.assertEqual(f(p0), hex(p0_addr))
        self.assertIn(f(p1), ("0x0", "(nil)"))


if __name__ == '__main__':
    unittest.main()