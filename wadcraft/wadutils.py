# This file is parts extracted from Wad2PDF

# Wad2PDF is a program that converts Doom levels into PDF files.
# (C) 2005-2008 Jussi Pakkanen
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


from wadcraft import wadformat


def mergearray(target, source, levels=False):
  """Adds and overwrites graphics from the source to target arrays."""
  for sgra in source:
    overwritten = 0
    for i in range(len(target)):
      tgra = target[i]

      # If the lump exists, overwrite it.
      if levels: # Are we dealing with levels?
        tname = tgra.header.name
        sname = sgra.header.name
      else:
        tname = tgra.name
        sname = sgra.name
      if tname == sname:
        overwritten = 1
        target[i] = sgra
        break

    # If graphic was not overwritten, append it.
    if overwritten == 0:
      target.append(sgra)


def mergewad(target, source):
  """Joins graphics, levels, palettes etc from the source to target.
  Does not do a perfect join: sounds, texture definitions etc are
  ignored."""

  # Only display levels from the lastest wad file.
  if source.levels is not None:
    mergearray(target.levels, source.levels, True)
    target.levels.sort(wadformat.levelsorter)

  if source.playpal is not None:
    target.playpal = source.playpal

  # Careful! Since this program does not save anything, no potential
  # lossage.
  #target.fname = os.path.basename(source.fname)

  mergearray(target.sprites, source.sprites)
  mergearray(target.flats, source.flats)
