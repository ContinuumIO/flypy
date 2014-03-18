# -*- coding: utf-8 -*-

"""
Convert between objects and flypy representations.
"""

from __future__ import print_function, division, absolute_import
import ctypes

import flypy as nb
from flypy import typing
from .representation import stack_allocate, byref, c_primitive

#===------------------------------------------------------------------===
# Object Conversion
#===------------------------------------------------------------------===

ctypes_type_memo = {}

def fromobject(value, type, keepalive):
    """
    Convert a Python value to a flypy representation according to `type`
    (e.g. list -> List)
    """
    cls = type.impl
    if hasattr(cls, 'fromobject') and not isinstance(value, cls):
        return cls.fromobject(value, type, keepalive)
    return value


def toobject(value, type):
    """
    Convert a flypy value to a Python representation (e.g. List -> list)
    """
    cls = type.impl
    if hasattr(cls, 'toobject'):
        return cls.toobject(value, type)
    return value


def toctypes(value, type, keepalive, valmemo=None, typememo=None):
    """
    Convert a flypy object given as a Python value to a low-level ctypes
    representation.

    Returns (ctypes_value, keep_alive)
    """
    from flypy.types import int8

    if hasattr(type, 'type'):
        type = type.type

    strtype = str(type)
    if valmemo is None:
        valmemo = {}
        typememo = ctypes_type_memo
    if (id(value), strtype) in valmemo:
        return valmemo[id(value), strtype]

    cls = type.impl
    if hasattr(cls, 'toctypes'):
        result = cls.toctypes(value, type)
    else:
        cty = ctype(type, typememo)
        if not stack_allocate(type):
            cty = cty._type_ # Get the base type

        # Resolve types
        layout = type.resolved_layout
        if not layout:
            types = [int8]
        else:
            types = [layout[name] for name, _ in cty._fields_]

        # Dereference pointer to aggregate
        if hasattr(value, 'contents'):
            value = value.contents

        # Resolve values
        values = []
        for (name, cty_field), ty in zip(cty._fields_, types):
            if hasattr(value, name):
                val = getattr(value, name)
            else:
                assert name == 'dummy', (name, value, value.__class__)
                val = 0

            cval = toctypes(val, ty, keepalive, valmemo, typememo)
            values.append(cval)

        # Construct value from ctypes struct
        result = cty(*values)

        if not stack_allocate(type):
            keepalive.append(result)
            result = ctypes.pointer(result)

    valmemo[id(value), strtype] = result
    return result


def fromctypes(value, ty, memo=None):
    """
    Construct a flypy object from a ctypes representation.
    """
    from flypy.support.ctypes_support import is_ctypes_pointer_type, CTypesStruct

    if hasattr(ty, 'type'):
        ty = ty.type

    if memo is None:
        memo = {}

    # NOTE: This cache doesn't work by hashing on ids, since ctypes values
    # are transient.

    #if id(value) in memo:
    #    return memo[id(value)]

    cls = ty.impl
    if hasattr(cls, 'fromctypes'):
        result = cls.fromctypes(value, ty)
    else:
        cls = ty.impl
        layout = ty.resolved_layout
        values = {}

        if is_ctypes_pointer_type(type(value)):
            # TODO: stack jit
            # Recover original names from the type
            cty = ctype(ty)
            value = ctypes.cast(value, cty)

        for name, ty in ty.resolved_layout.items():
            if is_ctypes_pointer_type(type(value)):
                value = value[0]
            cval = getattr(value, name)
            pyval = fromctypes(cval, ty, memo)
            values[name] = pyval

        result = cls(**values)

    #memo[id(value)] = result
    return result


def ctype(type, memo=None):
    """
    Return the low-level ctypes type representation for a flypy type instance.
    """
    # -------------------------------------------------
    # Setup cache

    if hasattr(type, 'type'):
        type = type.type

    if memo is None:
        memo = ctypes_type_memo
    if type in memo:
        return memo[type]

    # -------------------------------------------------
    # Handle custom ctype methods

    cls = type.impl
    if hasattr(cls, 'ctype'):
        result = cls.ctype(type)
        memo[type] = result
        return result

    # -------------------------------------------------
    # Build dummy struct and cache result

    class result(ctypes.Structure):
        def __repr__(self):
            return "{ %s }" % (", ".join("%s:%s" % (name, getattr(self, name))
                                             for name in names))

    struct = result
    if not stack_allocate(type):
        result = ctypes.POINTER(result)

    memo[type] = result

    # -------------------------------------------------
    # Determine field ctypes

    names, types = unzip2(type.resolved_layout.items())
    types = [ctype(ty, memo) for ty in types]
    if not types:
        names = ['dummy']
        types = [ctypes.c_int8]

    struct._fields_ = list(zip(names, types))
    struct.__name__ = 'CTypes' + type.__class__.__name__

    return result

def unzip2(xs):
    return list(zip(*xs)) or [(), ()]

def make_coercers(type):
    """
    Build coercion functions that reconstruct the values.
    """

    cls = type.impl
    pycls = lambda *args: cls(*args)
    layout = cls.layout

    @jit('%s -> Type[Object] -> Object' % (type,))
    def topy(obj, _):
        args = []
        for name, type in unroll(layout):
            args.append(coerce(getattr(obj, name), Object))
        return pycls(*args)

    @jit('Object -> Type[%s] -> %s' % (type, type))
    def frompy(obj, _):
        args = []
        for name, type in unroll(layout):
            args.append(coerce(getattr(obj, name), type))
        return cls(*args)

    return topy, frompy

#===------------------------------------------------------------------===
# General Type Conversion
#===------------------------------------------------------------------===

# TODO:
