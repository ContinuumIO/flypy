# -*- coding: utf-8 -*-

"""
Numba passes that perform translation, type inference, code generation, etc.
"""

from __future__ import print_function, division, absolute_import

from .environment import root_env
from .pipeline import run_pipeline
from .frontend import translate
from .compiler import inference
from .backend import backend

#===------------------------------------------------------------------===
# Utils
#===------------------------------------------------------------------===

def dump(func, env):
    print(func)

#===------------------------------------------------------------------===
# Passes
#===------------------------------------------------------------------===

passes = [
    translate,
    inference,
    backend,
]

#===------------------------------------------------------------------===
# Translation
#===------------------------------------------------------------------===

def translate(py_func, argtypes, restype=None, env=None, passes=passes):
    if env is None:
        env = dict(root_env)

    env['numba.typing.argtypes'] = argtypes
    env.setdefault('numba.typing.restype', restype)

    run_pipeline(py_func, env, passes)