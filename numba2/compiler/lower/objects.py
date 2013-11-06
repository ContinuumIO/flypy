# -*- coding: utf-8 -*-

"""
Handle calling conventions for objections.
"""

from __future__ import print_function, division, absolute_import

import ctypes

from numba2 import jit, void
from numba2.types import Pointer
from numba2.compiler import is_numba_cc
from numba2.runtime import conversion

from pykit import types
from pykit.ir import OpBuilder, Builder

#===------------------------------------------------------------------===
# Return Objects
#===------------------------------------------------------------------===

opaque_t = types.Pointer(types.Opaque)

@jit('StackVar[a]')
class StackVar(object):
    """
    Represent the loaded stack layout of a value.
    """

    layout = []

    @classmethod
    def ctype(cls, ty):
        cty = conversion.ctype(ty.parameters[0])
        # Get the base type if a pointer
        if hasattr(cty, '_type_'):
            return cty._type_
        return cty


def rewrite_obj_return(func, env):
    """
    Handle returning stack-allocated objects.
    """
    if env['numba.state.opaque']:
        return

    context = env['numba.typing.context']
    restype = env['numba.typing.restype']
    envs =  env['numba.state.envs']

    builder = Builder(func)

    stack_alloc = conversion.byref(restype)

    if stack_alloc:
        out = func.add_arg(func.temp("out"), opaque_t)
        context[out] = Pointer[restype]
        func.type = types.Function(types.Void, func.type.argtypes)

    for arg in func.args:
        arg.type = opaque_t
    func.type = types.Function(func.type.restype, (opaque_t,) * len(func.args))

    for op in func.ops:
        if op.opcode == 'ret' and op.args[0] is not None and stack_alloc:
            # ret val =>
            #     store (load val) out ; ret void
            [val] = op.args
            builder.position_before(op)
            newval = builder.load(val)
            builder.store(newval, out)
            op.set_args([None])

            # Update context
            context[newval] = StackVar[context[val]]

        elif op.opcode == 'call' and op.type != types.Void:
            # result = call(f, ...) =>
            #     alloca result ; call(f, ..., &result)
            ty = context[op]
            if conversion.byref(ty):
                f, args = op.args
                if not is_numba_cc(f) or envs[f]['numba.state.opaque']:
                    continue

                builder.position_before(op)
                retval = builder.alloca(opaque_t)
                builder.position_after(op)
                op.replace_uses(retval)

                newargs = args + [retval]
                op.set_args([f, newargs])

                # Update context
                context[retval] = context[op]
                context[op] = void
