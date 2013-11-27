# -*- coding: utf-8 -*-

"""
IR interpreter. Run a series of translation phases on a numba function, and
interpreter the IR with the arguments.
"""

from __future__ import print_function, division, absolute_import
import dis
import inspect
from functools import partial
from collections import namedtuple

from numba2 import typeof, jit, functionwrapper
from numba2.rules import is_numba_type
from numba2.pipeline import environment, phase
from numba2.compiler.opaque import implement
from numba2.compiler.overloading import flatargs

from pykit.ir import interp, tracing, Function

#===------------------------------------------------------------------===
# Handlers
#===------------------------------------------------------------------===

Method = namedtuple('Method', ['func', 'self'])

def op_call(run_phase, typeof_func, interp, func, args):
    """
    Called by the interpreter to interpret IR function calls.
    """
    if isinstance(func, Method):
        func, self = func
        args = [self] + list(args)

    if isinstance(func, functionwrapper.FunctionWrapper):
        wrapper = func
        op = interp.op

        try:
            # Flatten args (consider default values)
            args = flatargs(func.dispatcher.f, tuple(args), {})
        except TypeError:
            pass

        # Determine argument types
        argtypes = [typeof_func(arg, val) for arg, val in zip(op.args[1], args)]

        # Use regular typeof() for remaining arguments (default values)
        remaining_args = args[len(argtypes):]
        for arg in remaining_args:
            argtypes.append(typeof(arg))

        # Compile function
        env = environment.fresh_env(func, argtypes)

        if wrapper.opaque and run_phase == phase.translation:
            func = implement(wrapper, wrapper.py_func, tuple(argtypes), env)
        else:
            func, env = run_phase(func, env)

    elif is_numba_type(func):
        obj = func(*args)
        return obj
        #layout = type(obj).layout
        #return { 'value': dict((name, getattr(obj, name)) for name in layout) }

    return interp.call(func, args)


def op_untyped_getfield(typeof_func, interp, obj, attr):
    """
    Retrieve an attribute/method from an object.
    """
    op = interp.op
    arg = op.args[0]
    obj_type = typeof_func(arg, obj)

    if attr in obj_type.fields:
        # Method access
        return Method(obj_type.fields[attr], obj)
    else:
        # Attribute access
        if attr not in obj_type.layout:
            raise AttributeError(
                "Object of type %s has no attribute %r" % (obj_type, attr))
        return getattr(obj, attr)


def op_untyped_setfield(interp, obj, attr, value):
    setattr(obj, attr, value)

#===------------------------------------------------------------------===
# Typing
#===------------------------------------------------------------------===

class Typer(object):
    """
    Determine argument types for function calls during interpretation.
    """

    def __init__(self, context, run_phase):
        self.context = context

        phases = {
            phase.setup:        self.typeof_untyped,
            phase.translation:  self.typeof_untyped,
            phase.typing:       self.typeof_typed,
            phase.opt:          self.typeof_lltyped,
            phase.lower:        self.typeof_lltyped,
            phase.codegen:      self.typeof_lltyped,
        }
        self.typeof = phases[run_phase]

    def typeof_untyped(self, arg, argval):
        return typeof(argval)

    def typeof_typed(self, arg, argval):
        return self.context[arg]

    def typeof_lltyped(self, arg, argval):
        raise Exception("All function calls should have been resolved before "
                        "low-level typing...")

#===------------------------------------------------------------------===
# Helpers
#===------------------------------------------------------------------===

def header(f):
    print("---------------- Interpreting function %s ----------------" % (
                                                                     f.name,))
    print(f)
    print("----------------------- End of %s ------------------------" % (
                                                                     f.name,))

def handlers(run_phase, env):
    """
    Create interpreter handlers.
    """
    typeof_arg = Typer(env['numba.typing.context'], run_phase).typeof
    handlers = {
        'call': partial(op_call, run_phase, typeof_arg),
    }

    if run_phase in (phase.translation, phase.typing):
        # Add getfield/setfield handlers for untyped code
        handlers.update({
            'getfield': partial(op_untyped_getfield, typeof_arg),
            'setfield': op_untyped_setfield,
        })

    return handlers

#===------------------------------------------------------------------===
# Interpret
#===------------------------------------------------------------------===

def expect(nb_func, phase, args, expected, debug=False):
    """Interpret and expect a result"""
    result = interpret(nb_func, phase, args, debug)
    assert result == expected, "Got %s, expected %s" % (result, expected)

def interpret(nb_func, run_phase, args, debug=False, tracer=None):
    """Interpret and return result"""
    # Translate numba function
    argtypes = [typeof(arg) for arg in args]
    env = environment.fresh_env(nb_func, argtypes)
    f, env = run_phase(nb_func, env)

    if debug:
        header(f)

    if tracer is None:
        # Set up tracer to trace interpretation
        if debug:
            tracer = tracing.Tracer()
        else:
            tracer = tracing.DummyTracer()

    # Interpret function
    env.setdefault('interp.handlers', handlers(run_phase, env))
    return interp.run(f, env, args=args, tracer=tracer)
