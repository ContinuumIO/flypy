# -*- coding: utf-8 -*-

"""
Handle constants.
"""

from __future__ import print_function, division, absolute_import

from numba2.types import Bool, Int, Float, NoneType
from numba2.runtime.obj import NoneValue

from pykit.ir import Const, Struct, Builder, collect_constants, substitute_args

#===------------------------------------------------------------------===
# Constant mapping
#===------------------------------------------------------------------===

# Builtin Type -> (pyval -> Value)
builtin_types = {
    NoneType[()]: lambda x: NoneValue,
}

def resolve_builtin(ty, const):
    ctor = builtin_types.get(ty)
    if ctor:
        value = ctor(const.const)
        return Const(value, const.type)
    return const

# -----------------------------------------------------------------------
# Layout

def build_struct_value(ty, value, seen=None):
    """
    Build a constant struct value from the given runtime Python
    user-defined object.
    """
    seen = seen or set()
    if id(value) in seen:
        raise TypeError("Cannot use recursive value as a numba constant")
    seen.add(id(value))

    names, types = zip(*ty.layout) or [(), ()]
    values = [getattr(value, name) for name in names]
    return Struct(names, values)

def resolve_layout(ty, const):
    py_class = type(ty).impl
    if not is_builtin(py_class):
        #assert isinstance(const.const, py_class), (const.const, str(ty))
        value = build_struct_value(ty, const.const)
        const = Const(value, const.type)
    return const

is_builtin = lambda cls: cls in (Bool, Int, Float)

#===------------------------------------------------------------------===
# Pass
#===------------------------------------------------------------------===

def rewrite_constants(func, env):
    """
    Rewrite constants with user-defined types to IR constants. Also rewrite
    constants of builtins to instances of numba classes.

        e.g. constant(None)  -> constant(NoneValue)
             constant("foo") -> constant(Bytes("foo"))
    """
    context = env['numba.typing.context']

    for op in func.ops:
        constants = collect_constants(op)
        new_constants = []
        for c in constants:
            ty = context[c]
            c = resolve_builtin(ty, c)
            c = resolve_layout(ty, c)

            context[c] = ty
            new_constants.append(c)

        substitute_args(op, constants, new_constants)