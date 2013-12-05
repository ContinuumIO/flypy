# -*- coding: utf-8 -*-

"""
Numba function wrapper.
"""

from __future__ import print_function, division, absolute_import
import types
import ctypes
from functools import partial
from itertools import starmap
import copy

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
        from numba2.representation import byref, stack_allocate
        from numba2.conversion import (
            toctypes, fromctypes, toobject, fromobject, ctype)
        #from numba2.support.ctypes_support import CTypesStruct
        #from numba2.types import Function

        # Keep this alive for the duration of the call
        keepalive = list(args) + list(kwargs.values())

        # Order arguments
        args = flatargs(self.dispatcher.f, args, kwargs)
        argtypes = [typeof(x) for x in args]

        # Translate
        cfunc, restype = self.translate(argtypes)

        # Construct numba values
        arg_objs = list(starmap(fromobject, zip(args, argtypes)))

        # Map numba values to a ctypes representation
        args = []
        for arg, argtype in zip(arg_objs, argtypes):
            c_arg = toctypes(arg, argtype, keepalive)
            if byref(argtype) and stack_allocate(argtype):
                c_arg = ctypes.pointer(c_arg)
            args.append(c_arg)

        # We need this cast since the ctypes function constructed from LLVM
        # IR has different structs (which are structurally equivalent)
        c_restype = ctype(restype)
        if byref(restype):
            c_result = c_restype() # dummy result value
            args.append(ctypes.pointer(c_result))
            c_restype = None # void

        c_signature = ctypes.PYFUNCTYPE(c_restype, *[type(arg) for arg in args])
        cfunc = ctypes.cast(cfunc, c_signature)

        # Handle calling convention
        if byref(restype):
            cfunc(*args)
        else:
            c_result = cfunc(*args)

        # Map ctypes result back to a python value
        result = fromctypes(c_result, restype)
        result_obj = toobject(result, restype)

        return result_obj

    def translate(self, argtypes):
        from .pipeline import phase, environment

        key = tuple(argtypes)
        if key in self.ctypes_funcs:
            env = self.envs[key]
            return self.ctypes_funcs[key], env["numba.typing.restype"]

        # Translate
        env = environment.fresh_env(self, argtypes)
        llvm_func, env = phase.codegen(self, env)
        cfunc = env["codegen.llvm.ctypes"]

        # Cache
        self.llvm_funcs[key] = llvm_func
        self.ctypes_funcs[key] = cfunc
        self.envs[key] = env

        return cfunc, env["numba.typing.restype"]

    def overload(self, py_func, signature, **kwds):
        overload(signature, dispatcher=self.dispatcher, **kwds)(py_func)

    def get_llvm_func(self, argtypes):
        """Get the LLVM function object for the argtypes.
        """
        return self.llvm_funcs[tuple(argtypes)]

    @property
    def signatures(self):
        return [signature for func, signature, _ in self.overloads]

    @property
    def overloads(self):
        return self.dispatcher.overloads

    def __str__(self):
        return "<numba function (%s)>" % str(self.dispatcher)

    __repr__ = __str__

    def __get__(self, instance, owner=None):
        if instance is not None:
            # TODO: return partial(self, instance)
            return partial(self.py_func, instance)
        return self

    def copy(self):
        fw = FunctionWrapper(copy.deepcopy(self.dispatcher), self.py_func,
                             abstract=self.abstract, opaque=self.opaque)
        fw.implementor = self.implementor
        return fw

def wrap(py_func, signature, scope, inline=False, opaque=False, abstract=False, **kwds):
    """
    Wrap a function in a FunctionWrapper. Take care of overloading.
    """
    func = lookup_previous(py_func, [scope])

    if isinstance(func, FunctionWrapper):
        pass
    elif isinstance(func, types.FunctionType) and func != py_func:
        raise TypeError(
            "Function %s in current scope is not overloadable" % (func,))
    else:
        dispatcher = Dispatcher()
        func = FunctionWrapper(dispatcher, py_func,
                               abstract=abstract, opaque=opaque)

    func.overload(py_func, signature, inline=inline, opaque=opaque,
                  abstract=abstract, **kwds)
    return func
