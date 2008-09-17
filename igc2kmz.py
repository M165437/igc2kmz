#!/usr/bin/python

import datetime
import fileinput
import optparse
import sys

from bounds import Bounds, BoundsSet
import gradient
import igc
import kml
import kmz
from OpenStruct import OpenStruct
import scale
from track import Hints, Stock

def add_track(option, opt_str, value, parser, make_track, **kwargs):
  track = make_track(value)
  hints = Hints()
  for attr in 'color glider_type pilot_name'.split(' '):
    if not getattr(parser.values, attr) is None:
      setattr(hints, attr, getattr(parser.values, attr))
      setattr(parser.values, attr, None)
  if parser.values.tracks_and_hints is None:
    parser.values.tracks_and_hints = []
  parser.values.tracks_and_hints.append((track, hints))


def main(argv):
  parser = optparse.OptionParser(usage='Usage: %prog [options]')
  parser.add_option('-o', '--output', metavar='FILENAME')
  parser.add_option('-z', '--timezone-offset', metavar='INTEGER', type='int')
  group = optparse.OptionGroup(parser, 'Per-track options')
  group.add_option('-c', '--color', dest='color', metavar='COLOR')
  group.add_option('-i', '--igc', action='callback', callback=add_track, dest='tracks_and_hints', metavar='FILENAME', nargs=1, type='string', callback_args=(lambda value: igc.IGC(value).track(),))
  group.add_option('-g', '--glider-type', dest='glider_type', metavar='STRING')
  group.add_option('-p', '--pilot-name', dest='pilot_name', metavar='STRING')
  group.add_option('-w', '--width', dest='width', metavar='INTEGER', type='int')
  parser.add_option_group(group)
  parser.set_defaults(output='igc2kmz.kmz')
  parser.set_defaults(timezone_offset=0)
  options, args = parser.parse_args(argv)
  if options.tracks_and_hints is None:
    raise RuntimeError # FIXME
  if len(args) != 1:
    raise RuntimeError # FIXME
  bounds = BoundsSet()
  for track, hints in options.tracks_and_hints:
    track.analyse()
    bounds.merge(track.bounds)
  globals = OpenStruct()
  globals.stock = Stock()
  globals.timezone_offset = datetime.timedelta(0, 3600 * options.timezone_offset)
  globals.altitude_scale = scale.Scale(bounds.ele.tuple(), title='altitude', gradient=gradient.default)
  globals.altitude_styles = []
  for color in globals.altitude_scale.colors():
    balloon_style = kml.BalloonStyle(text='$[description]')
    icon_style = kml.IconStyle(kml.Icon.palette(4, 24), scale=0.5)
    label_style = kml.LabelStyle(color=color)
    globals.altitude_styles.append(kml.Style(balloon_style, icon_style, label_style))
  globals.stock.kmz.add_roots(*globals.altitude_styles)
  globals.climb_scale = scale.ZeroCenteredScale(bounds.climb.tuple(), title='climb', step=0.1, gradient=gradient.bilinear)
  globals.speed_scale = scale.Scale(bounds.speed.tuple(), title='ground speed', gradient=gradient.default)
  globals.time_scale = scale.TimeScale(bounds.time.tuple(), timezone_offset=globals.timezone_offset)
  globals.progress_scale = scale.Scale((0.0, 1.0), title='progress', gradient=gradient.default)
  globals.graph_width = 600
  globals.graph_height = 300
  result = kmz.kmz()
  result.add_siblings(globals.stock.kmz)
  for track, hints in options.tracks_and_hints:
    hints.globals = globals
    result.add_siblings(track.kmz(hints))
  result.write(options.output)

if __name__ == '__main__':
  main(sys.argv)
