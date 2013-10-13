# -*- coding: utf-8 -*-

"""
Numba function wrapper.
"""

from __future__ import print_function, division, absolute_import
import types
from functools import partial

from numba2.rules import typeof
from numba2.compiler.overloading import (lookup_previous, overload, Dispatcher,
                                         flatargs)

# TODO: Reuse numba.numbawrapper.pyx for autojit Python entry points

class FunctionWrapper(object):
    """
    Result of @jit for functions.
    """

    def __init__(self, dispatcher, py_func, abstract=False, opaque=False):
        self.dispatcher = dispatcher
        self.py_func = py_func
        # self.signature = signature
        self.abstract = abstract

        self.llvm_funcs = {}
        self.ctypes_funcs = {}
        self.envs = {}

        self.opaque = opaque
        self.implementor = None

    def __call__(self, *args, **kwargs):
        args = flatargs(self.dispatcher.f, args, kwargs)
        argtypes = [typeof(x) for x in args]
        cfunc = self.translate(argtypes)
        return cfunc(*args)

    def translate(self, argtypes):
        from . import phase, environment

        key = tuple(argtypes)
        if key in self.ctypes_funcs:
            return self.ctypes_funcs[key]

        # Translate
        env = environment.fresh_env(self, argtypes)
        llvm_func, env = phase.codegen(self, env)
        cfunc = env["codegen.llvm.ctypes"]

        # Cache
        self.llvm_funcs[key] = llvm_func
        self.ctypes_funcs[key] = cfunc
        self.envs[key] = env

        return cfunc

    @property
    def signatures(self):
        return [signature for func, signature, _ in self.overloads]

    @property
    def overloads(self):
        return self.dispatcher.overloads

    def __str__(self):
        return "<numba function (%s)>" % str(self.dispatcher)

    def __get__(self, instance, owner=None):
        if instance is not None:
            return partial(self.py_func, instance)
        return self


def wrap(py_func, signature, inline=False, **kwds):
    """
    Wrap a function in a FunctionWrapper. Take care of overloading.
    """
    func = lookup_previous(py_func)

    if isinstance(func, FunctionWrapper):
        func = func.dispatcher
    elif isinstance(func, types.FunctionType):
        raise TypeError(
            "Function %s in current scope is not overloadable" % (func,))
    else:
        func = Dispatcher()

    dispatcher = overload(signature, func=func, inline=inline, **kwds)(py_func)

    if isinstance(py_func, types.FunctionType):
        return FunctionWrapper(dispatcher, py_func, **kwds)
    else:
        assert isinstance(py_func, FunctionWrapper), py_func
        return py_func