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

"""Implement transformation from WAD levels to proper minecraft object.

Keep in mind the following mapping for coordinates
   Doom X      -> Minecraft X
   Doom Y      -> Minecraft Z
   Doom height -> Minecraft Y
"""


import math

from wadcraft import minecraft


class Vertex(object):
  """Store a Doom/glbsp 2D vertex."""
  def __init__(self, x, y):
    self.x = x
    self.y = y

  def __str__(self):
    return 'V(%s,%s)' % (self.x, self.y)

  def __repr__(self):
    return str(self)


class Sidedef(object):
  """A Doom sidedef description"""

  def __init__(self, level, raw):
    self.level = level
    self.raw = raw
    self.texture_x = self.raw[0]
    self.texture_y = self.raw[1]
    # upper texture
    # lower texture
    # middle texture
    self.sector = self.level.sectors[self.raw[5]]


class Linedef(object):
  """A Doom linedef description"""

  def __init__(self, level, raw):
    self.level = level
    self.raw = raw

    self.vertex_start = self.level.verts[raw[0]]
    self.vertex_end = self.level.verts[raw[1]]
    # flags
    # special type
    # sector tag
    self.right = None
    if raw[5] != -1:
      self.right = self.level.sidedefs[raw[5]]

    self.left = None
    if raw[6] != -1:
      self.left = self.level.sidedefs[raw[6]]


class Segment(object):
  """A glbsp segment"""

  def __init__(self, level, raw):
    self.level = level
    self.raw = raw

    self.vertex_start = self.level.verts[raw[0]]
    self.vertex_end = self.level.verts[raw[1]]

    self.side = raw[3]
    if raw[2] == 0xffff:
      self.linedef = None
      self.sidedef = None
      self.sector = None
    else:
      self.linedef = self.level.linedefs[raw[2]]
  
      if self.side == 0:
        self.sidedef = self.linedef.right
      else:
        self.sidedef = self.linedef.left

      self.sector = self.sidedef.sector

  def link(self):
    if self.raw[4] == 0xffffffff:
      self.partner = None
    else:
      self.partner = self.level.segments[self.raw[4]]


class Subsector(object):
  """A glbsp subsector description"""

  def __init__(self, level, raw):
    self.level = level
    self.raw = raw

    count, firstidx = raw
    self.segments = self.level.segments[firstidx:firstidx+count]

    self.sector = None
    self.verts = []
    for seg in self.segments:
      if not self.verts:
        self.verts.append(seg.vertex_start)

      assert seg.vertex_start == self.verts[-1]
      self.verts.append(seg.vertex_end)
      
      if seg.sector:
        if not self.sector:
          self.sector = seg.sector
        assert self.sector == seg.sector

    assert self.verts[0] == self.verts[-1]
    self.verts.pop()


class Sector(object):
  """A Doom sector description"""

  def __init__(self, level, raw):
    self.level = level
    self.raw = raw
    self.floor = raw[0]
    self.ceiling = raw[1]
    # floor texture, ceiling texture, light level, type, tag


class Level(object):
  """Help manipulating a Doom level.
  
  Vars:
    verts: {int: Vertex}, dict of all the vertices, both regular and gl ones.
    bbox1: Vertex
  """

  def __init__(self, rawlevel):
    self.rawlevel = rawlevel

    # Many objects have dependencies, so we need to parse that in the correct
    # order.
    self._GetVertices()
    self._GetSectors()
    self._GetSidedefs()
    self._GetLinedefs()
    self._GetSegments()
    self._GetSubsectors()
    self._BoundingBox()

  def _GetVertices(self):
    # Create a unique dict of all vertices. We use a dict, so we can have direct
    # access for both regular and gl vertices.
    self.verts = {}
    for i, v in enumerate(self.rawlevel.getvertices()):
      self.verts[i] = Vertex(v[0], v[1])

    for i, v in enumerate(self.rawlevel.getglvertices()):
      v_idx = i | (1<<31)
      self.verts[v_idx] = Vertex(v[1], v[3])
  
  def _GetSectors(self):
    self.sectors = []
    for sector in self.rawlevel.getsectors():
      self.sectors.append(Sector(self, sector))

  def _GetSidedefs(self):
    self.sidedefs = []
    for sidedef in self.rawlevel.getsidedefs():
      self.sidedefs.append(Sidedef(self, sidedef))

  def _GetLinedefs(self):
    self.linedefs = []
    for linedef in self.rawlevel.getlinedefs():
      self.linedefs.append(Linedef(self, linedef))

  def _GetSegments(self):
    self.segments = []
    for seg in self.rawlevel.getglsegs():
      self.segments.append(Segment(self, seg))

    for seg in self.segments:
      seg.link()

  def _GetSubsectors(self):
    self.subsectors = []
    for s in self.rawlevel.getglsubsectors():
      self.subsectors.append(Subsector(self, s))

  def _BoundingBox(self):
    # Build a bounding box so we have an idea where we're going
    self.bbox1 = Vertex(self.verts[0].x, self.verts[0].y)
    self.bbox2 = Vertex(self.verts[0].x, self.verts[0].y)
    for v in self.verts.itervalues():
      self.bbox1.x = min(self.bbox1.x, v.x)
      self.bbox1.y = min(self.bbox1.y, v.y)

      self.bbox2.x = max(self.bbox2.x, v.x)
      self.bbox2.y = max(self.bbox2.y, v.y)

    # Check min/max height
    self.min_height = self.sectors[0].floor
    self.max_height = self.sectors[0].ceiling
    for s in self.sectors:
      self.min_height = min(self.min_height, s.floor)
      self.max_height = max(self.max_height, s.ceiling)


class Render(Level):
  def __init__(self, rawlevel):
    super(Render, self).__init__(rawlevel)

    self._ComputeTransform()
    self._InitSchematic()
    
    for v in self.verts.itervalues():
      self.schematic[self.tr(v).x, 0, self.tr(v).z] = 0x14
    
  
  def tr(self, value):
    if isinstance(value, Vertex):
      # Do not return a Vertex. Vertex are doom specific, so to reduce
      # confusion and mistake, just return a triple (x, y, z).
      return minecraft.Coord(
              (value.x + self.transx) * self.scalex,
              None,
              (value.y + self.transz) * self.scalez)
    else:
      return minecraft.Coord(
              None,
              (value + self.transy) * self.scaley,
              None)


  def _ComputeTransform(self):
    # Converter to adapt doom coordinate to minecraft coordinates
    self.scalex = 60.0/(self.bbox2.x - self.bbox1.x)
    self.scalez = 60.0/(self.bbox2.y - self.bbox1.y)
    # Height scale is not completely true, as we can add extra block for floor/ceiling
    self.scaley = 60.0/(self.max_height - self.min_height)
   
    # We want something with max dim 60, so we calculate all scale factors, and
    # pick the smallest one.
    scale = min(self.scalex, self.scaley, self.scalez)
    self.scalex = self.scaley = self.scalez = scale

    self.transx = -self.bbox1.x
    # We take a bit of margin vertically
    self.transy = -self.min_height + 2 / scale
    self.transz = -self.bbox1.y

    assert self.tr(self.bbox1).x >= 0.0
    assert self.tr(self.bbox1).z >= 0.0
    assert self.tr(self.min_height).y >= 1.0
    
  def _InitSchematic(self):
    # Create the map. The +1 for the size is because we're actually actually
    # calculating the coordinates of the most extreme point.
    sizex = math.ceil(self.tr(self.bbox2).x)+1
    sizey = math.ceil(self.tr(self.max_height).y)+2
    sizez = math.ceil(self.tr(self.bbox2).z)+1

    self.schematic = minecraft.Schematic(sizex, sizey, sizez)
   
  def _RenderSubsectors(self):
    # Now, render each subsector
    segs = level.getglsegs()
    linedefs = level.getlinedefs()
    sidedefs = level.getsidedefs()
    for segcount, segidx in level.getglsubsectors():
      ssector_verts = []
      sector_idx = None
      for seg in segs[segidx:segidx+segcount]:
        start_v = self.verts[seg[0]]
        end_v = self.verts[seg[1]]

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
      #print ssector_verts, sector_idx
  

def renderlevel(rawlevel):
  renderer = Render(rawlevel)
  nbtfile = renderer.schematic.build_nbt()
  nbtfile.write_file("level.schematic")
