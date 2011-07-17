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


import optparse
import random
import sys

from wadcraft import waddecode
from wadcraft import wadutils
from wadcraft import wadlib
from wadcraft import render


def main():
  """Convert all specified levels."""

  print 'WadCraft by Pierre Palatin (parts based on Wad2PDF by Jussi Pakkanen)'
  print

  # Set a fixed seed to always have the same results
  random.seed(42)

  parser = optparse.OptionParser()

  parser.add_option('-i', '--iwad', help='Specify iwad file to use.')
  parser.add_option('-l', '--level', help='Specify level to convert.')
  parser.add_option('-o', '--output', 
                    default='level.schematic',
                    help='Target schematic file.')

  (opts, args) = parser.parse_args()

  if opts.iwad is None:
    print 'Please specifiy which iwad to use.'
    print
    parser.print_help()
    sys.exit(1)

  rawwad = waddecode.wad()
  print 'Loading iwad %s ...' % opts.iwad 
  rawwad.load(opts.iwad)
  if rawwad.type != 'IWAD':
    print 'This is not an iwad file (such as doom.wad or doom2.wad).'
    sys.exit(2)
  
  for fname in args:
    print 'Loading pwad %s ...' % fname
    newrawwad = waddecode.wad()
    newrawwad.load(fname)
    wadutils.mergewad(rawwad, newrawwad)

  wad = wadlib.Wad(rawwad)

  print

  level = None
  if opts.level:
    for level in rawwad.levels:
      if level.header.name.lower() == opts.level.lower():
        break
    else:
      print 'Unable to find level %s' % opts.level
      print
      level = None

  if not level:
    print 'Existing levels:'
    for level in rawwad.levels:
      print '    %s' % level.header.name
    sys.exit(3)


  print 'Converting level %s ...' % level.header.name
  nbtfile = render.render_level(wad, level)

  print 'Writing schematic to %s ...' % opts.output
  nbtfile.write_file(opts.output)
