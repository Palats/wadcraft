# Wadcraft is a program converting Doom WAD levels to minecraft format.
# (C) 2011 Pierre Palatin
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


"""Minecraft data manipulation library."""


import array
import nbt


class Coord(object):
  def __init__(self, x, y, z):
    self.x = x
    self.y = y
    self.z = z


class Schematic(object):
  """Manipulate a minecraft schematic"""
  

  def __init__(self, sizex, sizey, sizez):
    # In Minecraft coordinates, y being vertical one.
    self.sizex = int(sizex)
    self.sizey = int(sizey)
    self.sizez = int(sizez)

    # Ordered y,z,x - the x coordinate varies the fastest.
    self._blocks = array.array('c', '\x00' * self.sizex * self.sizey * self.sizez)
    self._data = array.array('c', '\x00' * self.sizex * self.sizey * self.sizez)

  def _conv_key(self, key):
    """Convert a key (x,y,z tuple) to a block index."""
    
    if isinstance(key, Coord):
      x = key.x
      y = key.y
      z = key.z
    else:
      x, y, z = key
      x = int(x)
      y = int(y)
      z = int(z)
    assert x >= 0 and x < self.sizex
    assert y >= 0 and y < self.sizey
    assert z >= 0 and z < self.sizez

    return ((y * self.sizez) + z) * self.sizex + x

  def __getitem__(self, key):
    idx = self._conv_key(key)
    return self._blocks[idx], self._data[idx]

  def __setitem__(self, key, value):
    idx = self._conv_key(key)

    if isinstance(value, int):
      block = value
      data = None
    else:
      block, data = value

    if block is not None:
      self._blocks[idx] = chr(block)
    if data is not None:
      self._data[idx] = chr(data)

  def build_nbt(self):
    nbtfile = nbt.NBTFile()
    nbtfile.name = "Schematic"

    nbtfile.tags.append(nbt.TAG_String(name="Materials", value="Alpha"))
    
    nbtfile.tags.append(nbt.TAG_List(name="Entities", type=nbt.TAG_Compound))
    nbtfile.tags.append(nbt.TAG_List(name="TileEntities", type=nbt.TAG_Compound))

    nbtfile.tags.append(nbt.TAG_Short(name="Height", value=self.sizey))
    nbtfile.tags.append(nbt.TAG_Short(name="Width", value=self.sizex))
    nbtfile.tags.append(nbt.TAG_Short(name="Length", value=self.sizez))
   
    blocks = nbt.TAG_Byte_Array()
    blocks.name = "Blocks"
    blocks.value = self._blocks.tostring()
    nbtfile.tags.append(blocks)
    
    data = nbt.TAG_Byte_Array()
    data.name = "Data"
    data.value = self._data.tostring()
    nbtfile.tags.append(data)

    return nbtfile
