# coding=utf-8
# Copyright (C) Duncan Macleod (2013)
#
# This file is part of GWSumm
#
# GWSumm is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GWSumm is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GWSumm.  If not, see <http://www.gnu.org/licenses/>

"""Custom `SummaryTab` for the output of the FScan algorithm.
"""

import os
import re
import glob

from dateutil import parser

from numpy import loadtxt

from .registry import (get_tab, register_tab)

from .. import (html, version, globalv)
from .. plot import get_plot
from ..mode import SUMMARY_MODE_DAY
from ..config import (GWSummConfigParser, NoOptionError)
from ..state import (ALLSTATE, SummaryState)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__version__ = version.version

base = get_tab('default')
SummaryPlot = get_plot(None)


class StampPEMTab(base):
    """Custom tab displaying a summary of StampPEM results.
    """
    type = 'archived-stamp'

    def __init__(self, *args, **kwargs):
        if globalv.MODE != SUMMARY_MODE_DAY:
            raise RuntimeError("StampPEMTab is only available in 'DAY' mode.")
        super(StampPEMTab, self).__init__(*args, **kwargs)

    @classmethod
    def from_ini(cls, config, section, **kwargs):
        """Define a new `StampPEMTab` from a `ConfigParser`.
        """
        # parse generic configuration
        new = super(StampPEMTab, cls).from_ini(config, section, **kwargs)
        new.layout = [2]

        # work out day directory and url
        new.directory = os.path.normpath(config.get(section, 'base-directory'))
        return new

    def process(self, config=GWSummConfigParser(), **kwargs):
        # find all plots
        self.plots = []
        if isinstance(self.directory, str):
            plots = sorted(
                glob.glob(os.path.join(self.directory, 'DAY_*.png')),
                key=lambda p: float(re.split('[-_]', os.path.basename(p))[1]))
            for p in plots:
                home_, postbase = p.split('/public_html/', 1)
                user = os.path.split(home_)[1]
                self.plots.append(SummaryPlot(
                    src='/~%s/%s' % (user, postbase),
                    href='/~%s/%s' % (user, postbase.replace('.png', '.html'))))

    def write_state_html(self, state):
        """Write the '#main' HTML content for this `StampPEMTab`.
        """
        page = html.markup.page()

        if not(os.path.isdir(self.directory)):
            page.div(class_='alert alert-warning')
            page.p("No analysis was performed for this period, "
                   "please try again later.")
            page.p("If you believe these data should have been found, please "
                   "contact %s."
                   % html.markup.oneliner.a('the DetChar group',
                                            class_='alert-link',
                                            href='mailto:detchar@ligo.org'))
            page.div.close()

        elif not self.plots:
            page.div(class_='alert alert-warning')
            page.p("This analysis produced no plots.")
            page.p("If you believe these data should have been found, please "
                   "contact %s."
                   % html.markup.oneliner.a('the DetChar group',
                                            class_='alert-link',
                                            href='mailto:detchar@ligo.org'))
            page.div.close()

        else:
            page.add(str(self.scaffold_plots(
                aclass='fancybox fancybox-stamp plot',
                **{'data-fancybox-type': 'iframe'})))
            page.hr(class_='row-divider')

            # link full results
            home_, postbase = self.directory.split('/public_html/', 1)
            user = os.path.split(home_)[1]
            index = '/~%s/%s/' % (user, postbase.rstrip('/'))
            page.hr(class_='row-divider')
            page.div(class_='btn-group')
            page.a('Click here for the full Stamp PEM results',
                   href=index, rel='external', target='_blank',
                   class_='btn btn-default btn-info btn-xl')
            page.div.close()

        # write to file
        idx = self.states.index(state)
        with open(self.frames[idx], 'w') as fobj:
            fobj.write(str(page))
        return self.frames[idx]

register_tab(StampPEMTab)
