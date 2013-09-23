# -*- coding: utf-8 -*-

"""
Numba passes that perform translation, type inference, code generation, etc.
"""

from __future__ import print_function, division, absolute_import

from .environment import root_env
from numba2.compiler.backend import preparation, backend
from .pipeline import run_pipeline
from .compiler.frontend import translate
from .compiler import simplification
from .compiler.typing import inference
from .compiler.typing.resolution import resolve_context, resolve_restype, rewrite_methods

#===------------------------------------------------------------------===
# Utils
#===------------------------------------------------------------------===

def dump(func, env):
    print(func)

#===------------------------------------------------------------------===
# Passes
#===------------------------------------------------------------------===

frontend = [
    translate,
]

typing = [
    simplification,
    inference,
]

resolution = [
    resolve_context,
    resolve_restype,
    rewrite_methods,
]

backend = [
    preparation,
    dump,
    backend,
]

passes = frontend + typing + resolution + backend

#===------------------------------------------------------------------===
# Translation
#===------------------------------------------------------------------===

def translate(py_func, argtypes, restype=None, env=None, passes=passes):
    if env is None:
        env = dict(root_env)

    # Types
    env['numba.typing.argtypes'] = argtypes
    env.setdefault('numba.typing.restype', restype)

    # State
    env['numba.state.py_func'] = py_func
    env['numba.state.func_globals'] = py_func.__globals__
    env['numba.state.func_code'] = py_func.__code__

    return run_pipeline(py_func, env, passes)