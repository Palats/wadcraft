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
from wadcraft import wadlib


class Pixel(object):
  def __init__(self, x, z):
    self.x = x
    self.z = z
    self.sectors = set()
    self.linedefs = set()
    self.floor = None


class Raster(dict):
  def __getitem__(self, key):
    return self.setdefault(key, Pixel(*key))


class Render(wadlib.Level):
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
    if isinstance(value, wadlib.Vertex):
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
          self.raster[x, z].linedefs.add(seg.linedef)
        
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
      self._render_pixel(pixel)

  def _render_pixel(self, pixel):
    wall = False

    floor_low = math.floor(self.tr(min([s.floor for s in pixel.sectors])).y)
    floor_high = math.floor(self.tr(max([s.floor for s in pixel.sectors])).y)
    ceil_low = math.ceil(self.tr(min([s.ceiling for s in pixel.sectors])).y)
    ceil_high = math.ceil(self.tr(max([s.ceiling for s in pixel.sectors])).y)

    sectors = [l.onesided.sector for l in pixel.linedefs if l.onesided]
    if sectors:
      # Render wall
      for y in xrange(int(floor_low), int(ceil_high)+1):
        self.schematic[pixel.x, y, pixel.z] = (0x23, 0x5)
    else:
      lightlevel = max([s.light for s in pixel.sectors])
      has_light = random.random() < ((lightlevel / 255.0) / 10.0)

      pixel.floor = int(floor_high)
      pixel.ceiling = int(ceil_low)

      if has_light:
        self.schematic[pixel.x, pixel.floor+1, pixel.z] = 0x32

      # Render floor
      self.schematic[pixel.x, pixel.floor, pixel.z] = (0x23, 0x0)
      for y in xrange(int(floor_low), pixel.floor):
        self.schematic[pixel.x, y, pixel.z] = (0x23, 0x9)

      # Render ceiling
      self.schematic[pixel.x, pixel.ceiling, pixel.z] = (0x23, 0x8)
      for y in xrange(pixel.ceiling+1, int(ceil_high)+1):
        self.schematic[pixel.x, y, pixel.z] = (0x23, 0x4)

  def _set_center(self):
    player = None
    for t in self.things:
      # 0x1 is player1 start, mandatory in levels
      if t.thingtype == 0x1:
        player = t

    coords = self.tr(wadlib.Vertex(player.x, player.y))
    pixel = self.raster[coords.x, coords.z]
    self.schematic.center = minecraft.Coord(coords.x, pixel.floor+1, coords.z)


def render_level(rawlevel):
  renderer = Render(rawlevel)
  nbtfile = renderer.schematic.build_nbt()
  return nbtfile
