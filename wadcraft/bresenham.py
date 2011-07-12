"""Simple bresenham line drawing."""


def line(x1, y1, x2, y2):
  """Draw a line, yield each (x, y) points."""

  xdiff = abs(x2-x1)
  ydiff = abs(y2-y1)

  if xdiff == ydiff == 0:
    yield (x1, y1)
  elif xdiff >= ydiff:
    if x1 > x2:
      x1, x2, y1, y2 = x2, x1, y2, y1
    ratio = float(y2 - y1) / xdiff
  
    for x in xrange(x1, x2+1):
      y = y1 + (x - x1) * ratio
      yield (x, int(y))
  else:
    if y1 > y2:
      x1, x2, y1, y2 = x2, x1, y2, y1
    ratio = float(x2 - x1) / ydiff
  
    for y in xrange(y1, y2+1):
      x = x1 + (y - y1) * ratio
      yield (int(x), y)



if __name__ == '__main__':
  # Basic testing
  print list(line(42, 43, 44, 45))
  print list(line(10, 42, 11, 42))
  print list(line(10, 42, 19, 42))
  print list(line(10, 42, 10, 38))
  print list(line(10, 10, 14, 14))
