# --------------------------------------------------------------------------
# FileFormat.Bases.Array
# Implements class for arrays.
# --------------------------------------------------------------------------
# ***** BEGIN LICENSE BLOCK *****
#
# Copyright (c) 2007, NIF File Format Library and Tools.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENCE BLOCK *****
# --------------------------------------------------------------------------

from Basic import BasicBase
from Expression import Expression

class _ListWrap(list):
    """A wrapper for list, which uses getValue and setValue for
    getting and setting items of the basic type."""
    def __init__(self, element_type):
        list.__init__(self)
        if issubclass(element_type, BasicBase):
            self._getitem_hook = self.getBasicItem
            self._setitem_hook = self.setBasicItem
        else:
            self._getitem_hook = self.getItem
            self._setitem_hook = self._notimplemented_hook

    def __getitem__(self, index):
        return self._getitem_hook(index)

    def __setitem__(self, index, value):
        return self._setitem_hook(index, value)

    def _notimplemented_hook(self, *args):
        raise NotImplementedError

    def getBasicItem(self, index):
        return list.__getitem__(self, index).getValue()

    def setBasicItem(self, index, value):
        return list.__getitem__(self, index).setValue(value)

    def getItem(self, index):
        return list.__getitem__(self, index)

class Array(_ListWrap):
    # initialize the array
    def __init__(self, parent, element_type, element_type_template, element_type_argument, count1, count2 = None):
        if count2 == None:
            _ListWrap.__init__(self, element_type)
        else:
            _ListWrap.__init__(self, _ListWrap)
        self._elementType = element_type
        self._parent = parent
        self._elementTypeTemplate = element_type_template
        self._elementTypeArgument = element_type_argument
        self._count1 = count1
        self._count2 = count2
        
        if self._count2 == None:
            for i in xrange(self._len1()):
                self.append(self._elementType(self._elementTypeTemplate, self._elementTypeArgument))
        else:
            for i in xrange(self._len1()):
                el = _ListWrap(element_type)
                for j in xrange(self._len2(i)):
                    el.append(self._elementType(self._elementTypeTemplate, self._elementTypeArgument))
                self.append(el)

    def _len1(self):
        """The length the array *should* have, obtained by evaluating
        the count1 expression."""
	return self._count1.eval(self._parent)

    def _len2(self, index1):
        """The length the array *should* have, obtained by evaluating
        the count2 expression."""
        if self._count2 == None:
            raise ValueError('single array treated as double array (bug?)')
        e = self._count2.eval(self._parent)
        #if isinstance(e, BasicBase):
        #    return e.getValue()
        if isinstance(e, (int, long)):
            return e
        else:
            return e[index1]

    # string of the array
    def __str__(self):
        s = '%s instance at 0x%08X\n'%(self.__class__, id(self))
        if self._count2 == None:
            for i, element in enumerate(self):
                if i > 16:
                    s += "etc...\n"
                    break
                s += "%i: %s\n"%(i, element)
        else:
            k = 0
            for i, el in enumerate(self):
                for j, e in enumerate(el):
                    if k > 16:
                        s += "etc...\n"
                        break
                    s += "%i, %i: %s\n"%(i, j, e)
                    k += 1
                if k > 16: break
        return s

    def updateSize(self):
        if self._count2 != None:
            raise NotImplementedError('updating size of double array not implemented yet')
        old_size = len(self)
        new_size = self._len1()
        if new_size < old_size:
            self.__delslice__(new_size, old_size)
        else:
            for i in xrange(new_size-old_size):
                e = self._elementType(self._elementTypeTemplate, self._elementTypeArgument)
                self.append(e)
        
    def read(self, version, user_version, f, link_stack, argument):
        len1 = self._len1()
        if len1 > 1000000: raise ValueError('array too long')
        self._elementTypeArgument = argument
        self.__delslice__(0, self.__len__())
        if self._count2 == None:
            for i in xrange(len1):
                e = self._elementType(self._elementTypeTemplate, self._elementTypeArgument)
                e.read(version, user_version, f, link_stack, self._elementTypeArgument)
                self.append(e)
        else:
            for i in xrange(len1):
                len2i = self._len2(i)
                if len2i > 1000000: raise ValueError('array too long')
                el = _ListWrap(self._elementType)
                for j in xrange(len2i):
                    e = self._elementType(self._elementTypeTemplate, self._elementTypeArgument)
                    e.read(version, user_version, f, link_stack, self._elementTypeArgument)
                    el.append(e)
                self.append(el)

    def write(self, version, user_version, f):
        if not self._len1() == self.__len__():
            raise ValueError('array size different from to field describing number of elements')
        for e in self:
            e.write(version, user_version, f)

    def fixLinks(self, version, user_version, block_dct, link_stack):
        if self._count2 == None:
            for e in self:
                e.fixLinks(version, user_version, block_dct, link_stack)
        else:
            for el in self:
                for e in el:
                    e.fixLinks(version, user_version, block_dct, link_stack)

#    def getBasicItem(self, index):
#        return self._elements[index].getValue()

#    def setBasicItem(self, index, value):
#        return self._elements[index].setValue(value)

#    def getItem(self, index):
#        return self._elements[index]
