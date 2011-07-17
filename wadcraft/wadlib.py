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

"""High level pythonic classes to manipulate WAD data."""


from wadcraft import waddecode
from wadcraft import waddata


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
    raw = raw.rstrip('\x00')
    if raw == '-':
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

    self.sector.sidedefs.append(self)
    self.linedef = None
    self.partner = None


class Linedef(object):
  """A Doom linedef description"""

  def __init__(self, level, raw):
    self.level = level
    self.raw = raw

    self.vertex_start = self.level.verts[raw[0]]
    self.vertex_end = self.level.verts[raw[1]]

    self.flags = raw[2]
    self.flag_block_player = bool(self.flags & 1)
    # Many more flags exists obviously.

    self.special_type = raw[3]
    self.sector_tag = raw[4]
    
    self.right = None
    if raw[5] != -1:
      self.right = self.level.sidedefs[raw[5]]
      self.right.linedef = self

    self.left = None
    if raw[6] != -1:
      self.left = self.level.sidedefs[raw[6]]
      self.left.linedef = self

    if self.left and self.right:
      self.left.partner = self.right
      self.right.partner = self.left

    # If None, double faced linedef. Otherwise, point to the corresponding
    # sidedef.
    self.onesided = None
    if not (self.left and self.right):
      self.onesided = self.left or self.right


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

      #assert seg.vertex_start == self.verts[-1]
      self.verts.append(seg.vertex_end)
      
      if seg.sector:
        if not self.sector:
          self.sector = seg.sector
        assert self.sector == seg.sector

    #assert self.verts[0] == self.verts[-1]
    self.verts.pop()


class Sector(object):
  """A Doom sector description"""

  def __init__(self, level, raw):
    self.level = level
    self.raw = raw
    self.floor = raw[0]
    self.ceiling = raw[1]

    self.floor_flat = self.level.wad.flats[raw[2]]
    self.ceil_flat = self.level.wad.flats[raw[3]]
    self.light = raw[4]
    # type
    # tag

    self.sidedefs = []


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

    self.sprite = waddata.doomdic[self.thingtype]


class Level(object):
  """Help manipulating a Doom level.
  
  Vars:
    verts: {int: Vertex}, dict of all the vertices, both regular and gl ones.
    bbox1: Vertex
  """

  def __init__(self, wad, rawlevel):
    self.wad = wad
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


class Wad(object):
  def __init__(self, rawwad):
    self.rawwad = rawwad
    
    self.flats = dict([(f.name, f) for f in self.rawwad.flats])
    self.playpal = self.rawwad.playpal
    self.patchdict = waddecode.buildpatchdict([self.rawwad])

    self.textures = {}
    texdefs = self.rawwad.texture1.definitions+self.rawwad.texture2.definitions
    for texdef in texdefs:
      self.textures[texdef[0]] = texdef
