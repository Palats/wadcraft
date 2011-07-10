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


"""A Doom level to Minecraft converter."""


import sys

from wadcraft import wadformat
from wadcraft import wadutils
from wadcraft import render


def main():
  """Convert all specified levels."""

  print 'WadCraft by Pierre Palatin'
  print
  print 'Parts based on Wad2PDF by Jussi Pakkanen'
  print 'Wad2PDF/Wadcraft comes with ABSOLUTELY NO WARRANTY.'
  print 'This is free software, and you are welcome to redistribute it'
  print 'under the GPL. See included file LICENSE for further info.'
  print
  
  if len(sys.argv) == 1:
    print 'No parameters defined. Usage'
    print sys.argv[0], '<IWAD file> <optional wads>'
    sys.exit(1)
 
  wad = wadformat.wad()
  firstwad = True
  for fname in sys.argv[1:]:
    print 'Loading', fname
    newwad = wadformat.wad()
    newwad.load(fname)
    if firstwad:
      firstwad = False
      if newwad.type != 'IWAD':
        print 'First argument', fname, 'is not an IWAD file. Exiting.'
        sys.exit(1)
    wadutils.mergewad(wad, newwad)

  for level in wad.levels:
    if level.header.name not in ['MAP01']:
      continue

    print 'Level', level.header.name
    render.renderlevel(level)
