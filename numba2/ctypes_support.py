# -*- coding: utf-8 -*-

"""
Support for ctypes.
"""

from __future__ import print_function, division, absolute_import

import ctypes.util

from numba2 import types
from pykit.utils import hashable

#===------------------------------------------------------------------===
# CTypes Types for Type Checking
#===------------------------------------------------------------------===

libc = ctypes.CDLL(ctypes.util.find_library('c'))

_ctypes_scalar_type = type(ctypes.c_int)
_ctypes_func_type = (type(ctypes.CFUNCTYPE(ctypes.c_int)), type(libc.printf))
_ctypes_pointer_type = type(ctypes.POINTER(ctypes.c_int))
_ctypes_array_type = type(ctypes.c_int * 2)

CData = type(ctypes.c_int(10)).__mro__[-2]

#===------------------------------------------------------------------===
# Check Whether values are ctypes values
#===------------------------------------------------------------------===

def is_ctypes_function_type(value):
    return isinstance(value, _ctypes_func_type)

def is_ctypes_function(value):
    return is_ctypes_function_type(type(value))

def is_ctypes_value(ctypes_value):
    return isinstance(ctypes_value, CData)

def is_ctypes_struct_type(ctypes_type):
    return (isinstance(ctypes_type, type) and
            issubclass(ctypes_type, ctypes.Structure))

def is_ctypes_pointer_type(ctypes_type):
    return isinstance(ctypes_type, _ctypes_pointer_type)

def is_ctypes_type(ctypes_type):
    return (
       (isinstance(ctypes_type, _ctypes_scalar_type)) or
       is_ctypes_struct_type(ctypes_type)
    )

def is_ctypes(value):
    "Check whether the given value is a ctypes value"
    return is_ctypes_value(value) or is_ctypes_type(value)

ptrval = lambda val: ctypes.cast(val, ctypes.c_void_p).value

#===------------------------------------------------------------------===
# Type mapping (ctypes -> numba)
#===------------------------------------------------------------------===

ctypes_map = {
    ctypes.c_bool :  types.bool_,
    ctypes.c_char :  types.int8,
    ctypes.c_int8 :  types.int8,
    ctypes.c_int16:  types.int16,
    ctypes.c_int32:  types.int32,
    ctypes.c_int64:  types.int64,
    ctypes.c_uint8 : types.uint8,
    ctypes.c_uint16: types.uint16,
    ctypes.c_uint32: types.uint32,
    ctypes.c_uint64: types.uint64,
    ctypes.c_float:  types.float32,
    ctypes.c_double: types.float64,
    None:            types.void,
}

def from_ctypes_type(cty, ctypes_value=None):
    """
    Convert a ctypes type to a numba type.

    Supported are structs, unit types (int/float)
    """
    if hashable(cty) and cty in ctypes_map:
        return ctypes_map[cty]
    elif cty is ctypes.c_void_p or cty is ctypes.py_object:
        return types.Pointer[types.void]
    elif is_ctypes_pointer_type(cty):
        return types.Pointer[from_ctypes_type(cty._type_)]
    elif is_ctypes_struct_type(cty):
        fields = [(name, from_ctypes_type(field_type))
                      for name, field_type in cty._fields_]
        fieldnames, fieldtypes = zip(*fields) or (('dummy',), (types.Int8,))
        return types.struct_(fieldnames, fieldtypes)
    elif is_ctypes_function_type(cty):
        # from_ctypes_type(cty._restype_) # <- this value is arbitrary,
        # it's always a c_int
        restype = from_ctypes_type(ctypes_value.restype)
        argtypes = tuple(from_ctypes_type(argty) for argty in ctypes_value.argtypes)
        return types.ForeignFunction[argtypes + (restype,)]
    else:
        raise NotImplementedError(cty)
