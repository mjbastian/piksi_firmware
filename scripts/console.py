#!/usr/bin/env python

import serial_link
import sbp_messages as ids

import argparse
parser = argparse.ArgumentParser(description='Swift Nav Console.')
parser.add_argument('-p', '--port', nargs=1, default=[serial_link.DEFAULT_PORT],
                   help='specify the serial port to use.')
parser.add_argument("-f", "--ftdi",
                  help="use pylibftdi instead of pyserial.",
                  action="store_true")
parser.add_argument('-t', '--toolkit', nargs=1, default=[None],
                   help="specify the TraitsUI toolkit to use, either 'wx' or 'qt4'.")
args = parser.parse_args()
serial_port = args.port[0]

if args.toolkit[0] is not None:
  from traits.etsconfig.api import ETSConfig
  ETSConfig.toolkit = args.toolkit[0]

import logging
logging.basicConfig()

# Fix default font issue on Linux
import os
#from kiva.fonttools.font_manager import fontManager, FontProperties
#if os.name == "posix":
  #font = FontProperties()
  #font.set_name("Arial")
  #fontManager.defaultFont = fontManager.findfont(font)

from traits.api import Str, Instance, Dict, HasTraits, Int
from traitsui.api import Item, ShellEditor, View, VSplit, HSplit, Tabbed, InstanceEditor

import struct

from output_stream import OutputStream
from tracking_view import TrackingView
from almanac_view import AlmanacView
from solution_view import SolutionView

class SwiftConsole(HasTraits):
  link = Instance(serial_link.SerialLink)
  console_output = Instance(OutputStream)
  python_console_env = Dict
  a = Int
  b = Int
  tracking_view = Instance(TrackingView)
  almanac_view = Instance(AlmanacView)
  solution_view = Instance(SolutionView)

  view = View(
    VSplit(
      Tabbed(
        Item('tracking_view', style='custom', label='Tracking'),
        Item('almanac_view', style='custom', label='Almanac'),
        Item('solution_view', style='custom', label='Solution'),
        Item(
          'python_console_env', style='custom',
          label='Python Console', editor=ShellEditor()
        ),
        show_labels=False
      ),
      Item(
        'console_output',
        style='custom',
        editor=InstanceEditor(),
        height=0.3,
        show_label=False,
      ),
    ),
    resizable = True,
    width = 1000,
    height = 1000,
    title = 'Piksi console'
  )

  def print_message_callback(self, data):
    try:
      self.console_output.write(data.encode('ascii', 'ignore'))
    except UnicodeDecodeError:
      print "Oh crap!"

  def __init__(self, *args, **kwargs):
    self.console_output = OutputStream()

    self.link = serial_link.SerialLink(*args, **kwargs)
    self.link.add_callback(ids.PRINT, self.print_message_callback)

    self.tracking_view = TrackingView(self.link)
    self.almanac_view = AlmanacView(self.link)
    self.solution_view = SolutionView(self.link)

    self.python_console_env = {
        'send_message': self.link.send_message,
        'link': self.link,
    }
    self.python_console_env.update(self.tracking_view.python_console_cmds)
    self.python_console_env.update(self.almanac_view.python_console_cmds)
    self.python_console_env.update(self.solution_view.python_console_cmds)

  def stop(self):
    self.link.close()

console = SwiftConsole(serial_port, use_ftdi=args.ftdi)

console.configure_traits()
console.stop()
