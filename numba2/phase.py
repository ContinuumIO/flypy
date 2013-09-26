# -*- coding: utf-8 -*-

"""
Numba compiler phases (groupings of passes).
"""

from __future__ import print_function, division, absolute_import

from functools import partial, wraps

from .pipeline import run_pipeline
from .passes import frontend, typing, lower, optimize, backend

from pykit.analysis import callgraph

#===------------------------------------------------------------------===
# Phases
#===------------------------------------------------------------------===

def cached(cache_name, passes):
    """Helper to perform caching for a phase"""
    def decorator(f):
        @wraps(f)
        def wrapper(func, env, passes=passes):
            cache = env[cache_name]
            if cache.lookup(func):
                return cache.lookup(func)

            new_func, new_env = f(func, env, passes)
            cache.insert(func, (new_func, new_env))
            return new_func, new_env

        return wrapper
    return decorator

def starcompose(f, g):
    """Helper to compose functions in a pipeline"""
    return lambda *args: f(*g(*args))

# ______________________________________________________________________
# Individual phases

@cached('numba.frontend.cache', frontend)
def translation_phase(func, env, passes):
    return run_pipeline(func, env, passes)

@cached('numba.typing.cache', typing + lower)
def typing_phase(func, env, passes):
    return run_pipeline(func, env, passes)

@cached('numba.opt.cache', optimize)
def optimization_phase(func, env, passes):
    return apply_and_resolve(partial(run_pipeline, passes=passes), func, env)

@cached('numba.codegen.cache', backend)
def codegen_phase(func, env, passes):
    return run_pipeline(func, env, passes)

# ______________________________________________________________________
# Phase application

def apply_and_resolve(phase, func, env):
    """Apply a phase to a function and its dependences"""
    graph = env['numba.state.callgraph'] or callgraph.callgraph(func)
    for f in graph.node:
        phase(f, None)

dep_resolving = lambda phase: partial(apply_and_resolve, phase)

# ______________________________________________________________________
# Combined phases

translation = translation_phase
typing = starcompose(typing_phase, translation_phase)
opt = starcompose(optimization_phase, typing)
codegen = starcompose(codegen_phase, opt)