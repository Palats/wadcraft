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
import random
import sys

from wadcraft import bresenham
from wadcraft import minecraft
from wadcraft import thingdics


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

  def _resolve_texture(self, raw):
    if raw == '-\x00\x00\x00\x00\x00\x00\x00':
      return None
    # We should cross reference texture object when they are converted really.
    return raw

  def __init__(self, level, raw):
    self.level = level
    self.raw = raw
    self.texture_x = self.raw[0]
    self.texture_y = self.raw[1]

    self.upper_texture = self._resolve_texture(self.raw[2])
    self.lower_texture = self._resolve_texture(self.raw[3])
    self.middle_texture = self._resolve_texture(self.raw[4])
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
  
  def __str__(self):
    return 'S(%s,%s)' % (self.vertex_start, self.vertex_end)

  def __repr__(self):
    return str(self)


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
    # floor texture
    # ceiling texture
    self.light = raw[4]
    # light level
    # type
    # tag


class Thing(object):
  """A Doom Thing description"""

  def __init__(self, level, raw):
    self.level = level
    self.raw = raw

    self.x = raw[0]
    self.y = raw[1]
    self.angle = raw[2]
    self.thingtype = raw[3]
    self.flags = raw[4]

    self.sprite = thingdics.doomdic[self.thingtype]


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
    self._get_vertices()
    self._get_sectors()
    self._get_sidedefs()
    self._get_linedefs()
    self._get_segments()
    self._get_subsectors()
    self._get_things()
    self._boundingbox()

  def _get_vertices(self):
    # Create a unique dict of all vertices. We use a dict, so we can have direct
    # access for both regular and gl vertices.
    self.verts = {}
    for i, v in enumerate(self.rawlevel.getvertices()):
      self.verts[i] = Vertex(v[0], v[1])

    for i, v in enumerate(self.rawlevel.getglvertices()):
      v_idx = i | (1<<31)
      self.verts[v_idx] = Vertex(v[1], v[3])
  
  def _get_sectors(self):
    self.sectors = []
    for sector in self.rawlevel.getsectors():
      self.sectors.append(Sector(self, sector))

  def _get_sidedefs(self):
    self.sidedefs = []
    for sidedef in self.rawlevel.getsidedefs():
      self.sidedefs.append(Sidedef(self, sidedef))

  def _get_linedefs(self):
    self.linedefs = []
    for linedef in self.rawlevel.getlinedefs():
      self.linedefs.append(Linedef(self, linedef))

  def _get_segments(self):
    self.segments = []
    for seg in self.rawlevel.getglsegs():
      self.segments.append(Segment(self, seg))

    for seg in self.segments:
      seg.link()

  def _get_subsectors(self):
    self.subsectors = []
    for s in self.rawlevel.getglsubsectors():
      self.subsectors.append(Subsector(self, s))

  def _get_things(self):
    self.things = []
    for t in self.rawlevel.getthings():
      self.things.append(Thing(self, t))

  def _boundingbox(self):
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


class Pixel(object):
  def __init__(self, x, z):
    self.x = x
    self.z = z
    self.sectors = set()
    self.sidedefs = set()
    self.floor = None


class Raster(dict):
  def __getitem__(self, key):
    return self.setdefault(key, Pixel(*key))


class Render(Level):
  def __init__(self, rawlevel):
    super(Render, self).__init__(rawlevel)

    self._compute_transform()
    self._init_schematic()
  
    self.raster = Raster()
    for subsector in self.subsectors:
      self._rasterize_subsector(subsector)

    self._render_raster()

    self._set_center()

    self.schematic.mirrorz()
  
  def tr(self, value):
    if isinstance(value, Vertex):
      # Do not return a Vertex. Vertex are doom specific, so to reduce
      # confusion and mistake, just return a triple (x, y, z).
      return minecraft.Coord(
              int((float(value.x) + self.transx) * self.scalex),
              None,
              int((float(value.y) + self.transz) * self.scalez))
    else:
      return minecraft.Coord(
              None,
              (float(value) + self.transy) * self.scaley,
              None)


  def _compute_transform(self):
    # Converter to adapt doom coordinate to minecraft coordinates
    self.scalex = 100.0/(self.bbox2.x - self.bbox1.x)
    self.scalez = 100.0/(self.bbox2.y - self.bbox1.y)
    # Height scale is not completely true, as we can add extra block for floor/ceiling
    self.scaley = 100.0/(self.max_height - self.min_height)
   
    # We want something with max dim 60, so we calculate all scale factors, and
    # pick the smallest one.
    scale = min(self.scalex, self.scaley, self.scalez)
    #scale = 0.5/24
    scale = 1.0/24

    self.scalex = self.scaley = self.scalez = scale

    self.transx = -self.bbox1.x
    self.transy = -self.min_height
    self.transz = -self.bbox1.y

    assert self.tr(self.bbox1).x >= 0.0
    assert self.tr(self.bbox1).z >= 0.0
    assert self.tr(self.min_height).y >= 0.0
    
  def _init_schematic(self):
    # Create the map. The +1 for the size is because we're actually actually
    # calculating the coordinates of the most extreme point.
    sizex = math.ceil(self.tr(self.bbox2).x)+1
    sizey = math.ceil(self.tr(self.max_height).y)+2
    sizez = math.ceil(self.tr(self.bbox2).z)+1

    self.schematic = minecraft.Schematic(sizex, sizey, sizez)

    print 'Size:', sizex, sizey, sizez

  def _rasterize_subsector(self, ssector):
    z_top = {}
    z_bottom = {}
    border = {}

    for seg in ssector.segments:
      # Shamelessly modify segments data to add our own coordinates
      seg.coord_start = self.tr(seg.vertex_start)
      seg.coord_end = self.tr(seg.vertex_end)

      # Segments are clockwise, so we know if this is a top or bottom segment.
      top_seg = (seg.vertex_end.x >= seg.vertex_start.x)

      # And then draw the segment
      gen_line = bresenham.line(seg.coord_start.x, seg.coord_start.z,
                                seg.coord_end.x, seg.coord_end.z)
      for x, z in gen_line:
        if seg.sidedef:
          self.raster[x, z].sidedefs.add(seg.sidedef)
        
        # Keep track of the segment to fill the surface afterwards
        if top_seg:
          z_top[x] = max(z_top.get(x, z), z)
        else:
          z_bottom[x] = min(z_bottom.get(x, z), z)

    # We're done with all segment, so we now know the limits of the surface, so
    # draw it.
    assert len(z_top) == len(z_bottom)
    for x in sorted(z_top.iterkeys()):
      for z in xrange(z_bottom[x], z_top[x]+1):
        self.raster[x, z].sectors.add(ssector.sector)

  def _render_raster(self):
    for pixel in self.raster.itervalues():
      wall = False
      if pixel.sidedefs:
        solid = [s for s in pixel.sidedefs if s.middle_texture]
        if solid:
          wall = True
          # Render wall
          for y in xrange(0, self.schematic.sizey):
            self.schematic[pixel.x, y, pixel.z] = 0x1

      if not wall and pixel.sectors:
        # Render floor
        lightlevel = max([s.light for s in pixel.sectors])
        has_light = random.random() < ((lightlevel / 255.0) / 10.0)

        lowest = min([s.floor for s in pixel.sectors])
        sector_y = self.tr(lowest).y
        int_y = int(math.floor(sector_y))
        for y in xrange(0, int_y+1):
          self.schematic[pixel.x, y, pixel.z] = 0x2B

        #if (sector_y - int_y) >= 0.5:
        #  int_y += 1
        #  self.schematic[pixel.x, int_y, pixel.z] = 0x2C

        pixel.floor = int_y

        if has_light:
          int_y += 1
          self.schematic[pixel.x, int_y, pixel.z] = 0x32

        # Render ceiling
        highest = max([s.ceiling for s in pixel.sectors])
        int_y = int(math.ceil(self.tr(highest).y))
        for y in xrange(int_y, self.schematic.sizey):
          self.schematic[pixel.x, y, pixel.z] = 0x1  #0x14

  def _set_center(self):
    player = None
    for t in self.things:
      if t.thingtype == 0x1:
        player = t

    coords = self.tr(Vertex(player.x, player.y))
    pixel = self.raster[coords.x, coords.z]
    self.schematic.center = minecraft.Coord(coords.x, pixel.floor+1, coords.z)


def render_level(rawlevel):
  renderer = Render(rawlevel)
  nbtfile = renderer.schematic.build_nbt()
  nbtfile.write_file("level.schematic")
