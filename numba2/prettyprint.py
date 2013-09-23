# -*- coding: utf-8 -*-

"""
Pretty printing of numba IRs.
"""

from __future__ import print_function, division, absolute_import

import os
import sys
import dis
import types
from functools import wraps, partial

from numba2.lexing import lex_source
from numba2 import viz, pipeline

import pykit.ir
from pykit.analysis import cfa

import networkx as nx

#===------------------------------------------------------------------===
# Passes
#===------------------------------------------------------------------===

def dumppass(option):
    """Apply `option` if it is active in the cmdops of the environment."""
    def decorator(f):
        @wraps(f)
        def wrapper(func, env):
            cmdopts = env['numba.cmdopts']
            if cmdopts.get(option):
                return f(func, env, cmdopts.get("fancy"))
        return wrapper
    return decorator

# ______________________________________________________________________

@dumppass("dump")
def dump(func, env, fancy):
    print(func)

@dumppass("dump-cfg")
def dump_cfg(func, env, fancy):
    CFG = cfa.cfg(func)
    viz.dump(CFG.nx, os.path.expanduser("~/cfg.dot"))

@dumppass("dump-llvm")
def dump_llvm(func, env, fancy):
    print(lex_source(str(func), "llvm", "console"))

@dumppass("dump-optimized")
def dump_optimized(func, env, fancy):
    print(lex_source(str(func), "llvm", "console"))

#===------------------------------------------------------------------===
# Verbose
#===------------------------------------------------------------------===

def augment_pipeline(passes):
    return [partial(verbose, p) for p in passes]

def verbose(p, func, env):
    print(_passname(p).center(60).center(90, "-"))
    if isinstance(func, types.FunctionType):
        dis.dis(func)
        func, env = pipeline.apply_transform(p, func, env)
        print()
        print(func)
        return func, env

    before = _formatfunc(func)
    func, env = pipeline.apply_transform(p, func, env)
    after = _formatfunc(func)

    if before != after:
        print(pykit.ir.diff(before, after))

    return func, env

# ______________________________________________________________________

def _passname(transform):
    if isinstance(transform, types.ModuleType):
        return transform.__name__
    else:
        return ".".join([transform.__module__, transform.__name__])

def _formatfunc(func):
    if isinstance(func, types.FunctionType):
        dis.dis(func)
        return ""
    else:
        return str(func)