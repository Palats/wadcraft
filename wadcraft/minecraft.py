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
from colormath import color_objects


wool_colors = {
  0x0: color_objects.RGBColor(0xdc, 0xdc, 0xdc),   # white
  0x1: color_objects.RGBColor(0xe9, 0x7f, 0x36),   # orange
  0x2: color_objects.RGBColor(0xbe, 0x4b, 0xc8),   # magenta
  0x3: color_objects.RGBColor(0x67, 0x8a, 0xd3),   # light blue
  0x4: color_objects.RGBColor(0xc2, 0xb4, 0x1b),   # yellow
  0x5: color_objects.RGBColor(0x3a, 0xbc, 0x2f),   # light green
  0x6: color_objects.RGBColor(0xd9, 0x83, 0x9a),   # pink
  0x7: color_objects.RGBColor(0x42, 0x42, 0x42),   # gray
  0x8: color_objects.RGBColor(0x9c, 0xa4, 0xa4),   # light gray
  0x9: color_objects.RGBColor(0x27, 0x74, 0x95),   # cyan
  0xa: color_objects.RGBColor(0x80, 0x34, 0xc2),   # purple
  0xb: color_objects.RGBColor(0x26, 0x32, 0x98),   # blue
  0xc: color_objects.RGBColor(0x55, 0x32, 0x1b),   # brown
  0xd: color_objects.RGBColor(0x37, 0x4c, 0x18),   # dark green
  0xe: color_objects.RGBColor(0xa2, 0x2c, 0x28),   # red
  0xf: color_objects.RGBColor(0x1a, 0x16, 0x16),   # black
}


class Coord(object):
  def __init__(self, x, y, z):
    self.x = x
    self.y = y
    self.z = z
  
  def __str__(self):
    return 'C(%s,%s,%s)' % (self.x, self.y, self.z)

  def __repr__(self):
    return str(self)


class Schematic(object):
  """Manipulate a minecraft schematic"""
  

  def __init__(self, sizex, sizey, sizez):
    # In Minecraft coordinates, y being vertical one.
    self.sizex = int(sizex)
    self.sizey = int(sizey)
    self.sizez = int(sizez)

    self.center = None

    # Ordered y,z,x - the x coordinate varies the fastest.
    self._blocks = array.array('c', '\x00' * self.sizex * self.sizey * self.sizez)
    self._data = array.array('c', '\x00' * self.sizex * self.sizey * self.sizez)

  def _conv_key(self, key):
    """Convert a key (x,y,z tuple) to a block index."""
    
    if isinstance(key, Coord):
      x = int(key.x)
      y = int(key.y)
      z = int(key.z)
    else:
      x, y, z = key
      x = int(x)
      y = int(y)
      z = int(z)
    assert x >= 0 and x < self.sizex
    assert y >= 0 and y < self.sizey
    assert z >= 0 and z < self.sizez, str(z)

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

  def mirrorz(self):
    new_blocks = array.array('c')
    new_data = array.array('c')

    # Ordered y,z,x - the x coordinate varies the fastest.
    for y in xrange(self.sizey):
      for z in xrange(self.sizez-1, -1, -1):
        idx = ((y * self.sizez) + z) * self.sizex
        new_blocks.extend(self._blocks[idx:idx+self.sizex])
        new_data.extend(self._data[idx:idx+self.sizex])

    self._blocks = new_blocks
    self._data = new_data

    if self.center:
      self.center = Coord(self.center.x, self.center.y, self.sizez - self.center.z)
    
  def build_nbt(self):
    nbtfile = nbt.NBTFile()
    nbtfile.name = "Schematic"

    nbtfile.tags.append(nbt.TAG_String(name="Materials", value="Alpha"))
    
    nbtfile.tags.append(nbt.TAG_List(name="Entities", type=nbt.TAG_Compound))
    nbtfile.tags.append(nbt.TAG_List(name="TileEntities", type=nbt.TAG_Compound))

    nbtfile.tags.append(nbt.TAG_Short(name="Height", value=self.sizey))
    nbtfile.tags.append(nbt.TAG_Short(name="Width", value=self.sizex))
    nbtfile.tags.append(nbt.TAG_Short(name="Length", value=self.sizez))
    
    if self.center:
      #nbtfile.tags.append(nbt.TAG_Int(name="WEOriginX", value=0))
      #nbtfile.tags.append(nbt.TAG_Int(name="WEOriginY", value=0))
      #nbtfile.tags.append(nbt.TAG_Int(name="WEOriginZ", value=0))
      nbtfile.tags.append(nbt.TAG_Int(name="WEOffsetX", value=-self.center.x))
      nbtfile.tags.append(nbt.TAG_Int(name="WEOffsetY", value=-self.center.y))
      nbtfile.tags.append(nbt.TAG_Int(name="WEOffsetZ", value=-self.center.z))
   
    blocks = nbt.TAG_Byte_Array()
    blocks.name = "Blocks"
    blocks.value = self._blocks.tostring()
    nbtfile.tags.append(blocks)
    
    data = nbt.TAG_Byte_Array()
    data.name = "Data"
    data.value = self._data.tostring()
    nbtfile.tags.append(data)

    return nbtfile
