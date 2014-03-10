"""
Created on Dec 16, 2013

@author: M. Rafay Aleem
"""
from pyretic.lib.corelib import *
from pyretic.lib.std import *
from pyretic.sdx.lib.common import *

import random
from threading import Thread
import json
import os

class HRange(object):
    def __init__(self, hr_from, hr_to):
        self.hr_from = hr_from
        self.hr_to = hr_to

    def __eq__(self, other):
        if other <= self.hr_to and other >= self.hr_from:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
