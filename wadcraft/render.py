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

"""Implement transformation from WAD levels to proper minecraft object."""


import math


class MinecraftMap(object):
  """Store a rendered Doom level."""
  

  def __init__(self, sizex, sizey):
    self.sizex = int(sizex)
    self.sizey = int(sizey)

    self._data = {}

  def _convkey(self, key):
    """Convert a key (vertex or x,y tuple) to a map coordinate."""

    if isinstance(key, Vertice):
      x = key.x
      y = key.y
    else:
      x = key[0]
      y = key[1]

    x = int(x)
    y = int(y)
    assert x >= 0 and x < self.sizex
    assert y >= 0 and y < self.sizex
    return x, y

  def __getitem__(self, key):
    return self._data[self._convkey(key)]

  def __setitem__(self, key, value):
    self._data[self._convkey(key)] = value

  def dump(self):
    """Generate a string representing the level."""
    s = ''
    for y in xrange(0, self.sizey):
      for x in xrange(0, self.sizex):
        key = self._convkey((x, y))
        if key in self._data:
          c = '#'
        else:
          c = ' '
        s += c
      s += '\n'
    return s


class Transform(object):
  """Helper to resize/translate coordinates."""

  def __init__(self, transx, transy, scalex, scaley):
    self.transx = transx
    self.transy = transy
    self.scalex = scalex
    self.scaley = scaley

  def __call__(self, v):
    return Vertice((v.x + self.transx) * self.scalex,
                   (v.y + self.transy) * self.scaley)


class Vertice(object):
  """Store a 2D vertex."""
  def __init__(self, x, y):
    self.x = x
    self.y = y

  def __str__(self):
    return 'V(%s,%s)' % (self.x, self.y)

  def __repr__(self):
    return str(self)


def renderlevel(level):
  """From a basic WAD level, generate a minecraft map fragment."""

  # Create a unique dict of all vertices. We use a dict, so we can have direct
  # access for both regular and gl vertices.
  verts = {}
  for i, v in enumerate(level.getvertices()):
    verts[i] = Vertice(v[0], v[1])

  for i, v in enumerate(level.getglvertices()):
    v_idx = i | (1<<31)
    verts[v_idx] = Vertice(v[1], v[3])

  # Build a bounding box so we have an idea where we're going
  bbox1 = Vertice(verts[0].x, verts[0].y)
  bbox2 = Vertice(verts[0].x, verts[0].y)
  for v in verts.itervalues():
    bbox1.x = min(bbox1.x, v.x)
    bbox1.y = min(bbox1.y, v.y)

    bbox2.x = max(bbox2.x, v.x)
    bbox2.y = max(bbox2.y, v.y)


  # Converter to adapt doom coordinate to output coordinate
  # We want something with max dim 100, so we calculate both scale factor, and
  # pick the smallest one.
  scalex = 60.0/(bbox2.x - bbox1.x)
  scaley = 60.0/(bbox2.y - bbox1.y)
  scale = min(scalex, scaley)

  tr = Transform(-bbox1.x, -bbox1.y, scale, scale)

  # Create the map. The +1 for the size is because we're actually actually
  # calculating the coordinates of the most extreme point.
  assert tr(bbox1).x >= 0.0
  assert tr(bbox1).y >= 0.0
  mcmap = MinecraftMap(math.ceil(tr(bbox2).x)+1, math.ceil(tr(bbox2).y)+1)

  
  # Now, render each subsector
  segs = level.getglsegs()
  linedefs = level.getlinedefs()
  sidedefs = level.getsidedefs()
  for segcount, segidx in level.getglsubsectors():
    ssector_verts = []
    sector_idx = None
    for seg in segs[segidx:segidx+segcount]:
      start_v = verts[seg[0]]
      end_v = verts[seg[1]]

      if seg[2] != 0xFFFF:
        linedef = linedefs[seg[2]]
        if not seg[3]:
          # Right side def
          sidedef_idx = linedef[5]
        else:
          # Left side def
          sidedef_idx = linedef[6]
        sidedef = sidedefs[sidedef_idx]
        if not sector_idx:
          sector_idx = sidedef[5]
        assert sector_idx == sidedef[5]

      if not ssector_verts:
        ssector_verts.append(start_v)
      else:
        assert ssector_verts[-1] == start_v

      ssector_verts.append(end_v)

    assert ssector_verts[0] == ssector_verts[-1]
    assert sector_idx is not None
    print ssector_verts, sector_idx
  
  #print mcmap.dump()
