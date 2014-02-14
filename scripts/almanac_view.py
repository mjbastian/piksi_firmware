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

class AlmanacView(HasTraits):
  python_console_cmds = Dict()
  download_almanac = Button(label='Download latest alamanc')
  load_almanac = Button(label='Load alamanc from file')
  send_alm = Button(label='Send almanac to Piksi')
  send_time = Button(label='Send time to Piksi')
  send_cw = Button(label='Scan CW')
  alm = Instance(Almanac)
  alm_txt = Str
  plot = Instance(Plot)
  plot_data = Instance(ArrayPlotData)

  traits_view = View(
	VGroup(
		VGroup(
			Item('alm_txt', label='PRNs visible'),
			Item('download_almanac'),
			Item('load_almanac'),
			Item('send_alm'),
			Item('send_time'),
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
    self.plot_data.set_data("y", arange(0))
    self.link.send_message(ids.CW_START, buff)

  def _send_time_fired(self):
    gps_secs = time.time() - (315964800 - 16)
    gps_week = int(gps_secs / (7*24*3600))
    gps_tow = gps_secs % (7*24*3600)
    print gps_week, gps_tow
    buff = struct.pack("<dH", gps_tow, gps_week)
    self.link.send_message(ids.SET_TIME, buff)

  def _send_alm_fired(self):
    self.update_alamanc_view()

    for sat in self.alm.sats:
      self.link.send_message(ids.ALMANAC, sat.packed())

  def update_alamanc_view(self):
    #prns, dopps = zip(*self.alm.get_dopps())
    self.alm_txt = str(self.alm.get_dopps())

  def _download_almanac_fired(self):
    self.alm.download_almanac()
    self.update_alamanc_view()

  def _load_almanac_fired(self):
    self.alm.load_almanac_file('current.alm')
    self.update_alamanc_view()
	
  def _cw_callback(self, data):
    freq,power = struct.unpack('fQ', data)
    pwr = 20 * math.log10(power)
    print 'cw callback ', freq, pwr
    self.freqs[int(freq)] = pwr
    self.plot_data.set_data("x", arange(0, 300, 1))
    self.plot_data.set_data("y", self.freqs)

  def __init__(self, link):
    super(AlmanacView, self).__init__()

    x = arange(0,300,1)
    y = x/2 * sin(x)
    self.plot_data = ArrayPlotData(x=x, y=y)
    plot = Plot(self.plot_data)
    plot.plot(("x", "y"), type="scatter", color="blue")
    self.plot = plot
    self.freqs = arange(0, 300, 1)
    self.link = link
    self.link.add_callback(ids.CW_RESULTS, self._cw_callback)

    self.alm = Almanac()

    self.python_console_cmds = {
      'alm': self.alm
    }

