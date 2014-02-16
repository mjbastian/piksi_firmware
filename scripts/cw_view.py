from traits.api import Str, Instance, Dict, HasTraits, Array, Float, on_trait_change, Button, Int
from traitsui.api import Item, View, HGroup, VGroup
from chaco.api import ArrayPlotData, Plot
from enable.component_editor import ComponentEditor
from numpy import cos, linspace, sin
from numpy import arange

import threading
import time
import struct
import math
import numpy as np

import sbp_messages as ids
from almanac import Almanac

class CwView(HasTraits):
  python_console_cmds = Dict()
#  download_almanac = Button(label='Download latest alamanc')
#  load_almanac = Button(label='Load alamanc from file')
#  send_alm = Button(label='Send almanac to Piksi')
#  send_time = Button(label='Send time to Piksi')
  send_cw = Button(label='Scan CW')
  alm = Instance(Almanac)
  alm_txt = Str
  plot = Instance(Plot)
  plot_data = Instance(ArrayPlotData)

  traits_view = View(
        VGroup(
                VGroup(
                        Item('send_cw')
                ),
                Item('plot',
                        show_label = False,
          editor = ComponentEditor(bgcolor = (0.8,0.8,0.8)))
        )
  )

  def _send_cw_fired(self):
    buff = struct.pack("<fff", 0, 4600, 0.1)
    self.plot_data.set_data("x", arange(0))
    self.plot_data.set_data("y", arange(0,1,1))
    self.link.send_message(ids.CW_START, buff)

  def _cw_callback(self, data):
    freq,power = struct.unpack('fQ', data)
    pwr = 20 * math.log10(power)
    print 'cw callback ', freq, pwr
    self.freqs[int(freq)] = pwr
    self.plot_data.set_data("x", arange(0, 300, 1))
    self.plot_data.set_data("y", self.freqs)

  def __init__(self, link):
    super(CwView, self).__init__()

    x = arange(0,300,1)
    y = arange(0,300,0.01)
    self.plot_data = ArrayPlotData(x=x, y=y)
    plot = Plot(self.plot_data)
    plot.plot(("x", "y"), type="scatter", color="blue")
    self.plot = plot
    self.freqs = arange(0, 300, 1)
    self.link = link
    self.link.add_callback(ids.CW_RESULTS, self._cw_callback)

    self.python_console_cmds = {
      'cw': self.plot_data
    }


