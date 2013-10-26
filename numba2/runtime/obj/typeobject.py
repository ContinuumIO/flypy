# -*- coding: utf-8 -*-

"""
Number interfaces.
"""

from __future__ import print_function, division, absolute_import
from numba2 import jit

__all__ = ['Type']

#===------------------------------------------------------------------===
# Inference
#===------------------------------------------------------------------===

def index_type(argtypes):
    """
    Infer result type for Constructor.__getitem__. This is needed because
    we express type constructor application where the type constructor itself
    is variable.
    """
    ctor, ty = argtypes
    ctor = type(ctor.parameters[0]).impl # Constructor[Foo[T]]
    ty = ty.parameters[0] # Type[T]
    return Type[ctor[ty]]

#===------------------------------------------------------------------===
# Type and Type Constructors
#===------------------------------------------------------------------===

@jit('Type[a]')
class Type(object):
    layout = []

    @staticmethod
    def toobject(obj, type):
        return type.parameters[0]


@jit('Constructor[a]')
class Constructor(object):
    layout = [] #('ctor', 'a')]

    @jit('Constructor[a] -> Type[b] -> void',
         opaque=True, infer_restype=index_type)
    def __getitem__(self, item):
        raise NotImplementedError
