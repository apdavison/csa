#
#  This file is part of the Connection-Set Algebra (CSA).
#  Copyright (C) 2010 Mikael Djurfeldt
#
#  CSA is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  CSA is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import copy

import intervalset
import valueset

# This is the fundamental connection-set class
# which is also the base class for masks
#
class CSet (object):
    def __init__ (self, mask, *valueSets):
        self._mask = mask
        self.valueSets = list (valueSets)
        self.arity = len (self.valueSets)

    def mask (self):
        #*fixme* remove this condition?
        if self._mask == None:
            self._mask = self.makeMask ()
        return self._mask

    def value (self, k):
        if self.valueSets[k] == None:
            self.valueSets[k] = self.makeValueSet (k)
        return self.valueSets[k]

    def makeValueSet (self, k):
        if isFinite (self.mask ()):
            return self.makeFiniteValueSet (k, self.mask ().bounds ())
        raise RuntimeError, "don't know how to return value set for this connection-set"

    def makeFiniteValueSet (self, k, bounds):
        raise RuntimeError, "don't know how to return value set for this connection-set"

    def __len__ (self):
        return len (self.mask ())

    def __iter__ (self):
        # this code is used for full connection sets
        if isFinite (self.mask ()):
            state = State ()
            obj = self.startIteration (state)
            (low0, high0, low1, high1) = self.bounds ()
            return obj.iterator (low0, high0, low1, high1, state)
        else:
            raise RuntimeError, 'attempt to retrieve iterator over infinite connection-set'

    def bounds (self):
        return self.mask ().bounds ()

    def startIteration (self, state):
        obj = copy.copy (self)
        obj._mask = self.mask ().startIteration (state)
        return obj

    def iterator (self, low0, high0, low1, high1, state):
        for (i, j) in self._mask.iterator (low0, high0, low1, high1, state):
            yield (i, j, [ v (i, j) for v in self.valueSets ])

    def multisetSum (self, other):
        return CSetMultisetSum (self, other)

    def intersection (self, other):
        assert isinstance (other, Mask), 'expected Mask operand'
        return SubCSet (self,
                        self.mask ().intersection (other), *self.valueSets)

    def difference (self, other):
        assert isinstance (other, Mask), 'expected Mask operand'
        return SubCSet (self, self.mask ().difference (other), *self.valueSets)


# This is the connection-set wrapper class which has as its only purpose
# to wrap non mask connection-sets so that the same code can implement
# connection-sets of different arity.  Some type dispatch is also done here.
#
class ConnectionSet (object):
    def __init__ (self, c):
        self.c = c
        
    def __len__ (self):
        return len (c)

    def __iter__ (self):
        return ConnectionSet.iterators[self.c.arity] (self)

    def iter0 (self):
        assert False, 'Should not have executed ConnectionSet.iter0'

    def iter1 (self):
        for (i, j, vs) in iter (self.c):
            (v0,) = vs
            yield (i, j, v0)

    def iter2 (self):
        for (i, j, vs) in iter (self.c):
            (v0, v1) = vs
            yield (i, j, v0, v1)

    def iter3 (self):
        for (i, j, vs) in iter (self.c):
            (v0, v1, v2) = vs
            yield (i, j, v0, v1, v2)

    def __add__ (self, other):
        if isNumber (other):
            return ConnectionSet (self.c.addScalar (other))
        else:
            return ConnectionSet (self.c.multisetSum (coerceCSet (other)))

    def __radd__ (self, other):
        return self.__add__ (other)

    def __sub__ (self, other):
        if isNumber (other):
            return ConnectionSet (self.c.addScalar (- other))
        else:
            return ConnectionSet (self.c.difference (coerceCSet (other)))

    def __rsub__ (self, other):
        return ConnectionSet (self.c.__neg__ ().addScalar (other))
    
    def __mul__ (self, other):
        if isNumber (other):
            return ConnectionSet (self.c.mulScalar (other))
        else:
            return ConnectionSet (self.c.intersection (coerceCSet (other)))

    def __rmul__ (self, other):
        return self.__mul__ (other)

ConnectionSet.iterators = [ ConnectionSet.iter0, \
                            ConnectionSet.iter1, \
                            ConnectionSet.iter2, \
                            ConnectionSet.iter3 ]


# Some helper functions

def source (x):
    return x[0]

def target (x):
    return x[1]

def isNumber (x):
    return isinstance (x, (int, long, float, complex))

def coerceCSet (obj):
    if isinstance (obj, list):
        return ExplicitMask (obj)
    elif isinstance (obj, ConnectionSet):
        return obj.c
    assert isinstance (obj, Mask), 'expected connection-set'
    return obj

def valueSet (obj):
    return valueset.QuotedValueSet (obj)

def coerceValueSet (obj):
    if callable (obj):
        return obj
    else:
        return valueSet (obj)

def isFinite (x):
    return isinstance (x, Finite)

def isEmpty (x):
    iterator = iter (x.mask ())
    try:
        iterator.next ()
        return False
    except StopIteration:
        return True

def transpose (obj):
    return obj.transpose ()


# This is the fundamental mask class
#
class Mask (CSet):
    def __init__ (self):
        CSet.__init__ (self, self)

    def __len__ (self):
        N = 0
        for c in self:
            N += 1
        return N

    def __iter__ (self):
        raise RuntimeError, 'attempt to retrieve iterator over infinite mask'

    def __add__ (self, other):
        return self.multisetSum (other)

    def __sub__ (self, other):
        return self.difference (other)

    def __mul__ (self, other):
        if isinstance (other, Mask):
            return self.intersection (other)
        elif isinstance (other, list):
            return self.intersection (ExplicitMask (other))
        elif isinstance (other, ConnectionSet):
            return other.__mul__ (self)
        else:
            return NotImplemented

    def __rmul__ (self, other):
        if isinstance (other, list):
            return self.intersection (ExplicitMask (other))
        else:
            return NotImplemented

    def __invert__ (self):
        return self.complement ()

    def transpose (self):
        assert isFinite (self), \
               'transpose currently only supports finite masks'
        return TransposedMask (self)

    def startIteration (self, state):
        # default action:
        return self

    def iterator (self, low0, high0, low1, high1, state):
        return NotImplemented

    def multisetSum (self, other):
        if isFinite (self) and isFinite (other):
            return FiniteMaskMultisetSum (self, other)
        else:
            return MaskMultisetSum (self, other)

    def intersection (self, other):
        # IntervalSetMask implements a specialized version of intersection
        if isinstance (other, IntervalSetMask):
            return other.intersection (self)
        # Generate Finite instances if either operand is finite
        elif isFinite (self):
            return FiniteMaskIntersection (self, other)
        elif isFinite (other):
            return FiniteMaskIntersection (other, self)
        else:
            return MaskIntersection (self, other)

    def complement (self):
        return MaskComplement (self)

    def difference (self, other):
        return MaskDifference (self, other)


class Finite (object):
    def bounds (self):
        return NotImplemented

    def maxBounds (self, b1, b2):
        return (min (b1[0], b2[0]), max (b1[1], b2[1]),
                min (b1[2], b2[2]), max (b1[3], b2[3]))

    def __iter__ (self):
        state = State ()
        obj = self.startIteration (state)
        (low0, high0, low1, high1) = self.bounds ()
        return obj.iterator (low0, high0, low1, high1, state)


class FiniteMask (Finite, Mask):
    def __init__ (self):
        Mask.__init__ (self)
        self.low0 = 0
        self.high0 = 0
        self.low1 = 0
        self.high1 = 0

    def bounds (self):
        return (self.low0, self.high0, self.low1, self.high1)

    def isBoundedBy (self, low0, high0, low1, high1):
        return low0 > self.low0 or high0 < self.high0 \
               or low1 > self.low1 or high1 < self.high1

# not used
class NoParIterator ():
    def __init__ (self):
        self.subIterator = False

    def iterator (self, low0, high0, low1, high1, state):
        print low0, high0, low1, high1
        if not self.subIterator:
            self.subIterator = self.noParIterator (state)
            self.lastC = self.subIterator.next ()
        c = self.lastC
        while c[1] < low1:
            c = self.subIterator.next ()
        while c[1] < high1:
            j = c[1]
            while c[1] == j and c[0] < low0:
                c = self.subIterator.next ()
            while c[1] == j and c[0] < high0:
                yield c
                c = self.subIterator.next ()
            while c[1] == j:
                c = self.subIterator.next ()
        self.lastC = c


class BinaryMask (Mask):
    def __init__ (self, c1, c2):
        Mask.__init__ (self)
        self.c1 = c1
        self.c2 = c2

    def startIteration (self, state):
        obj = copy.copy (self)
        obj.c1 = self.c1.startIteration (state)
        obj.c2 = self.c2.startIteration (state)
        return obj


class MaskIntersection (BinaryMask):
    def __init__ (self, c1, c2):
        BinaryMask.__init__ (self, c1, c2)

    def iterator (self, low0, high0, low1, high1, state):
        iter1 = self.c1.iterator (low0, high0, low1, high1, state)
        iter2 = self.c2.iterator (low0, high0, low1, high1, state)
        (i1, j1) = iter1.next ()
        (i2, j2) = iter2.next ()
        while True:
            if (j1, i1) < (j2, i2):
                (i1, j1) = iter1.next ()
            elif (j2, i2) < (j1, i1):
                (i2, j2) = iter2.next ()
            else:
                yield (i1, j1)
                (i1, j1) = iter1.next ()
                (i2, j2) = iter2.next ()


class FiniteMaskIntersection (Finite, MaskIntersection):
    def __init__ (self, c1, c2):
        assert isFinite (c1)
        MaskIntersection.__init__ (self, c1, c2)

    def bounds (self):
        return self.c1.bounds ()


class MaskMultisetSum (BinaryMask):
    def __init__ (self, c1, c2):
        BinaryMask.__init__ (self, c1, c2)

    def iterator (self, low0, high0, low1, high1, state):
        iter1 = self.c1.iterator (low0, high0, low1, high1, state)
        iter2 = self.c2.iterator (low0, high0, low1, high1, state)
        try:
            (i1, j1) = iter1.next ()
        except StopIteration:
            (i2, j2) = iter2.next ()
            while True:
                yield (i2, j2)
                (i2, j2) = iter2.next ()
        try:
            (i2, j2) = iter2.next ()
        except StopIteration:
            while True:
                yield (i1, j1)
                (i1, j1) = iter1.next ()
        while True:
            i1s = i1
            j1s = j1
            while (j1, i1) <= (j2, i2):
                yield (i1, j1)
                try:
                    (i1, j1) = iter1.next ()
                except StopIteration:
                    while True:
                        yield (i2, j2)
                        (i2, j2) = iter2.next ()
            while (j2, i2) <= (j1s, i1s):
                yield (i2, j2)
                try:
                    (i2, j2) = iter2.next ()
                except StopIteration:
                    while True:
                        yield (i1, j1)
                        (i1, j1) = iter1.next ()


class FiniteMaskMultisetSum (Finite, MaskMultisetSum):
    def __init__ (self, c1, c2):
        assert isFinite (c1) and isFinite (c2)
        MaskMultisetSum.__init__ (self, c1, c2)

    def bounds (self):
        return self.maxBounds (self.c1.bounds (), self.c2.bounds ())


class MaskDifference (BinaryMask):
    def __init__ (self, c1, c2):
        BinaryMask.__init__ (self, c1, c2)

    def iterator (self, low0, high0, low1, high1, state):
        iter1 = self.c1.iterator (low0, high0, low1, high1, state)
        iter2 = self.c2.iterator (low0, high0, low1, high1, state)
        (i1, j1) = iter1.next ()
        (i2, j2) = iter2.next ()
        while True:
            if (j1, i1) < (j2, i2):
                yield (i1, j1)
                (i1, j1) = iter1.next ()
                continue
            elif (i1, j1) == (i2, j2):
                (i1, j1) = iter1.next ()
            try:
                (i2, j2) = iter2.next ()
            except StopIteration:
                while True:
                    yield (i1, j1)
                    (i1, j1) = iter1.next ()


def cmpPostOrder (c0, c1):
    return cmp ((c0[1], c0[0]), (c1[1], c1[0]))


class ExplicitMask (FiniteMask):
    def __init__ (self, connections):
        FiniteMask.__init__ (self)
        self.connections = list (connections)
        self.connections.sort (cmpPostOrder)
        if connections:
            self.low0 = min ((i for (i, j) in self.connections))
            self.high0 = max ((i for (i, j) in self.connections)) + 1
            self.low1 = self.connections[0][1]
            self.high1 = self.connections[-1][1] + 1

    def __len__ (self):
        return len (self.connections)

    def iterator (self, low0, high0, low1, high1, state):
        if not self.isBoundedBy (low0, high0, low1, high1):
            return iter (self.connections)
        else:
            return self.boundedIterator (low0, high0, low1, high1, state)

    def boundedIterator (self, low0, high0, low1, high1, state):
        iterator = iter (self.connections)
        (i, j) = iterator.next ()
        while j < low1:
            (i, j) = iterator.next ()
        while j < high1:
            if low0 <= i and i < high0:
                yield (i, j)
            (i, j) = iterator.next ()


class IntervalSetMask (Mask):
    def __init__ (self, set0, set1):
        Mask.__init__ (self)
        self.set0 = set0
        self.set1 = set1

    def __repr__ (self):
        return 'cross(%r, %r)' % (self.set0, self.set1)

    def __contains__ (self, c):
        return c[0] in self.set0 and c[1] in self.set1

    def transpose (self):
        return IntervalSetMask (self.set1, self.set0)

    def iterator (self, low0, high0, low1, high1, state):
        iterator1 = self.set1.intervalIterator ()
        i1 = iterator1.next ()
        while i1[1] < low1:
            i1 = iterator1.next ()
        while i1[0] < high1:
            for j in xrange (max (i1[0], low1), min (i1[1] + 1, high1)):
                iterator0 = self.set0.intervalIterator ()
                try:
                    i0 = iterator0.next ()
                    while i0[1] < low0:
                        i0 = iterator0.next ()
                    if i0[1] < high0:
                        for i in xrange (max (i0[0], low0), i0[1] + 1):
                            yield (i, j)
                        i0 = iterator0.next ()
                        while i0[1] < high0:
                            for i in xrange (i0[0], i0[1] + 1):
                                yield (i, j)
                            i0 = iterator0.next ()
                        for i in xrange (i0[0], min (i0[1] + 1, high0)):
                            yield (i, j)
                    else:
                        for i in xrange (max (i0[0], low0), min (i0[1] + 1, high0)):
                            yield (i, j)
                except StopIteration:
                    pass
            i1 = iterator1.next ()

    def intersection (self, other):
        if isinstance (other, IntervalSetMask):
            set0 = self.set0.intersection (other.set0)
            set1 = self.set1.intersection (other.set1)
            return intervalSetMask (set0, set1)
        else:
            return ISetBoundedMask (self.set0, self.set1, other)

    def multisetSum (self, other):
        if isinstance (other, IntervalSetMask):
            if not self.set0.intersection (other.set0) \
               or not self.set1.intersection (other.set1):
                set0 = self.set0.union (other.set0)
                set1 = self.set1.union (other.set1)
                return intervalSetMask (set0, set1)
            else:
                raise RuntimeError, \
                      'sums of overlapping IntervalSetMask:s not yet supported'
        else:
            return FiniteMask.multisetSum (self, other)


class FiniteISetMask (FiniteMask, IntervalSetMask):
    def __init__ (self, set0, set1):
        FiniteMask.__init__ (self)
        IntervalSetMask.__init__ (self, set0, set1)
        if self.set0 and self.set1:
            self.low0 = self.set0.min ()
            self.high0 = self.set0.max () + 1
            self.low1 = self.set1.min ()
            self.high1 = self.set1.max () + 1

    def __len__ (self):
        return len (self.set0) * len (self.set1)

    def transpose (self):
        return FiniteISetMask (self.set1, self.set0)

    def iterator (self, low0, high0, low1, high1, state):
        if not self.isBoundedBy (low0, high0, low1, high1):
            return self.simpleIterator ()
        else:
            return IntervalSetMask.iterator (self, low0, high0, low1, high1, state)

    def simpleIterator (self):
        for j in self.set1:
            for i in self.set0:
                yield (i, j)


class FiniteSourcesISetMask (IntervalSetMask):
    def __init__ (self, set0, set1):
        IntervalSetMask.__init__ (self, set0, set1)

    def transpose (self):
        return FiniteTargetsISetMask (self.set1, self.set0)


class FiniteTargetsISetMask (IntervalSetMask):
    def __init__ (self, set0, set1):
        IntervalSetMask.__init__ (self, set0, set1)

    def transpose (self):
        return FiniteSourcesISetMask (self.set1, self.set0)


def intervalSetMask (set0, set1):
    set0 = set0 if isinstance (set0, intervalset.IntervalSet) \
           else intervalset.IntervalSet (set0)
    set1 = set1 if isinstance (set1, intervalset.IntervalSet) \
           else intervalset.IntervalSet (set1)
    if set0.finite ():
        if set1.finite ():
            return FiniteISetMask (set0, set1)
        else:
            return FiniteSourcesISetMask (set0, set1)
    else:
        if set1.finite ():
            return FiniteTargetsISetMask (set0, set1)
        else:
            return IntervalSetMask (set0, set1)


class ISetBoundedMask (FiniteMask):
    def __init__ (self, set0, set1, mask):
        FiniteMask.__init__ (self)
        self.set0 = set0
        self.set1 = set1
        self.subMask = mask
        inf = intervalset.infinity
        if isFinite (mask):
            (low0, high0, low1, high1) = mask.bounds ()
        else:
            (low0, high0, low1, high1) = (0, inf, 0, inf)
        if self.set0 and self.set1:
            self.low0 = max (self.set0.min (), low0)
            if self.set0.finite ():
                self.high0 = min (self.set0.max () + 1, high0)
            else:
                self.high0 = high0
            self.low1 = max (self.set1.min (), low1)
            if self.set1.finite ():
                self.high1 = min (self.set1.max () + 1, high1)
            else:
                self.high1 = high1
        assert self.high0 != inf and self.high1 != inf, 'infinite ISetBoundedMask:s currently not supported'

    def startIteration (self, state):
        obj = copy.copy (self)
        obj.subMask = self.subMask.startIteration (state)
        return obj

    def iterator (self, low0, high0, low1, high1, state):
        if not self.isBoundedBy (low0, high0, low1, high1):
            return self.simpleIterator (state)
        else:
            return self.boundedIterator (low0, high0, low1, high1, state)

    def simpleIterator (self, state):
        for i1 in self.set1.intervalIterator ():
            for i0 in self.set0.intervalIterator ():
                for e in self.subMask.iterator (i0[0], i0[1] + 1,
                                                i1[0], i1[1] + 1,
                                                state):
                    yield e

    def boundedIterator (self, low0, high0, low1, high1, state):
        iterator1 = self.set1.intervalIterator ()
        i1 = iterator1.next ()
        while i1[1] < low1:
            i1 = iterator1.next ()
        while i1[0] < high1:
            i1 = (max (i1[0], low1), min (i1[1], high1 - 1))
            iterator0 = self.set0.intervalIterator ()
            try:
                i0 = iterator0.next ()
                while i0[1] < low0:
                    i0 = iterator0.next ()
                if i0[1] < high0:
                    for e in self.subMask.iterator (max (i0[0], low0),
                                                    i0[1] + 1,
                                                    i1[0], i1[1] + 1,
                                                    state):
                        yield e
                    i0 = iterator0.next ()
                    while i0[1] < high0:
                        for e in self.subMask.iterator (i0[0], i0[1] + 1,
                                                        i1[0], i1[1] + 1,
                                                        state):
                            yield e
                        i0 = iterator0.next ()
                        for e in self.subMask.iterator (i0[0],
                                                        min (i0[1] + 1, high0),
                                                        i1[0], i1[1] + 1,
                                                        state):
                            yield e
                else:
                        for e in self.subMask.iterator (max (i0[0], low0),
                                                        min (i0[1] + 1, high0),
                                                        i1[0], i1[1] + 1,
                                                        state):
                            yield e
            except StopIteration:
                pass
            i1 = iterator1.next ()


# The ExplicitCSet captures the original value sets before coercion.
# It is used in the implementation of the "cset" constructor.
#
class ExplicitCSet (CSet):
    def __init__ (self, mask, *valueSets):
        if isinstance (mask, list):
            mask = ExplicitMask (mask)
        self.originalValueSets = valueSets
        CSet.__init__ (self, mask, *map (coerceValueSet, valueSets))

    def value (self, k):
        return self.originalValueSets[k]


# SubCSet is used in the cases where a new CSet can be created by
# an operation on the mask.
#
class SubCSet (CSet):
    def __init__ (self, cset, mask, *valueSets):
        CSet.__init__ (self, mask, *valueSets)
        self.subCSet = cset

    def value (self, k):
        if self.valueSets[k] == None:
            self.valueSets[k] = self.makeValueSet (k)
        # defer to subCSet in case it is an ExplicitCSet
        return self.subCSet.value (k)

    def makeValueSet (self, k):
        if isFinite (self.mask ()):
            bounds = self.mask ().bounds ()
            return self.subCSet.makeFiniteValueSet (k, bounds)
        else:
            return self.subCSet.makeValueSet (k)


class BinaryCSet (CSet):
    def __init__ (self, c1, c2):
        CSet.__init__ (self, None, *[ None for v in c1.valueSets ])
        self.c1 = c1
        self.c2 = c2
        self.valueSetMap = None

    def makeFiniteValueSet (self, k, bounds):
        if self.valueSetMap == None:
            self.valueSetMap = self.makeValueSetMap (bounds)
        return lambda i, j: self.valueSetMap[(i, j)][k]

    def makeValueSetMap (self, bounds):
        m = {}
        state = State ()
        obj = self.startIteration (state)
        (low0, high0, low1, high1) = bounds
        for (i, j, v) in obj.iterator (low0, high0, low1, high1, state):
            m[(i, j)] = v
        return m


class BinaryCSets (BinaryCSet):
    def __init__ (self, c1, c2):
        assert c1.arity == c2.arity, 'binary operation on connection-sets with different arity'
        BinaryCSet.__init__ (self, c1, c2)


class CSetIntersection (BinaryCSet):
    def __init__ (self, c1, c2):
        assert isinstance (c2, Mask), 'expected Mask operand'
        BinaryCSet.__init__ (self, c1, c2)
        self._mask = c1.mask ().intersection (c2)

    def iterator (self, low0, high0, low1, high1, state):
        iter1 = self.c1.iterator (low0, high0, low1, high1, state)
        iter2 = self.c2.iterator (low0, high0, low1, high1, state)
        (i1, j1, v1) = iter1.next ()
        (i2, j2) = iter2.next ()
        while True:
            if (j1, i1) < (j2, i2):
                (i1, j1, v1) = iter1.next ()
            elif (j2, i2) < (j1, i1):
                (i2, j2) = iter2.next ()
            else:
                yield (i1, j1, v1)
                (i1, j1, v1) = iter1.next ()
                (i2, j2) = iter2.next ()


class CSetMultisetSum (BinaryCSets):
    def __init__ (self, c1, c2):
        BinaryCSet.__init__ (self, c1, c2)
        self._mask = c1.mask ().multisetSum (c2.mask ())
        
    def iterator (self, low0, high0, low1, high1, state):
        iter1 = self.c1.iterator (low0, high0, low1, high1, state)
        iter2 = self.c2.iterator (low0, high0, low1, high1, state)
        try:
            (i1, j1, v1) = iter1.next ()
        except StopIteration:
            (i2, j2, v2) = iter2.next ()
            while True:
                yield (i2, j2, v2)
                (i2, j2, v2) = iter2.next ()
        try:
            (i2, j2, v2) = iter2.next ()
        except StopIteration:
            while True:
                yield (i1, j1, v1)
                (i1, j1, v1) = iter1.next ()
        while True:
            i1s = i1
            j1s = j1
            while (j1, i1) <= (j2, i2):
                yield (i1, j1, v1)
                try:
                    (i1, j1, v1) = iter1.next ()
                except StopIteration:
                    while True:
                        yield (i2, j2, v2)
                        (i2, j2, v2) = iter2.next ()
            while (j2, i2) <= (j1s, i1s):
                yield (i2, j2, v2)
                try:
                    (i2, j2, v2) = iter2.next ()
                except StopIteration:
                    while True:
                        yield (i1, j1, v1)
                        (i1, j1, v1) = iter1.next ()

    def intersection (self, other):
        assert isinstance (other, Mask), 'expected Mask operand'
        if isFinite (self) or isFinite (other):
            # since operands are finite we are allowed to use isEmpty
            if isEmpty (self.c2.mask ().intersection (other)):
                return self.c1.intersection (other)
            if isEmpty (self.c1.mask ().intersection (other)):
                return self.c2.intersection (other)
        return CSetIntersection (self, other)


class Operator (object):
    pass


class TransposedMask (Finite, Mask):
    def __init__ (self, mask):
        self.subMask = mask

    def transpose (self):
        return self.subMask

    def bounds (self):
        (low0, high0, low1, high1) = self.subMask.bounds ()
        return (low1, high1, low0, high0)

    def startIteration (self, state):
        obj = copy.copy (self)
        obj.transposedState = state.transpose ()
        obj.subMask = self.subMask.startIteration (obj.transposedState)
        return obj

    def iterator (self, low0, high0, low1, high1, state):
        ls = []
        for c in self.subMask.iterator (low1, high1, low0, high0, \
                                        self.transposedState):
            ls.append ((c[1], c[0]))
        ls.sort (cmpPostOrder)
        return iter (ls)


class State (dict):
    def transpose (self):
        if 'partitions' in self:
            s = State (self)
            s['partitions'] = map (transpose, s['partitions'])
            return s
        else:
            return self


class MaskPartition (Finite, Mask):
    def __init__ (self, mask, partitions, selected, seed):
        #*fixme* How can we know when this is not necessary?
        self.subMask = partitions[selected] * mask

        #domain = IntervalSetMask ([], [])
        #for m in partitions:
        #    assert isFinite (m), 'partitions must be finite'
        #    domain = domain.multisetSum (m)
        
        self.state = { #'domain' : domain,
                       'partitions' : partitions,
                       'selected' : selected }
        if seed != None:
            self.state['seed'] = seed

    def bounds (self):
        return self.subMask.bounds ()

    def startIteration (self, state):
        for key in self.state:
            state[key] = self.state[key]
        return self.subMask.startIteration (state)

    def iterator (self, low0, high0, low1, high1, state):
        raise RuntimeError, 'iterator called on wrong object'
