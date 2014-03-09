## Pyretic-specific imports
from pyretic.core.language import DynamicPolicy
from pyretic.lib.corelib import match, if_, identity
from quality import quality_mod
from threading import Thread
import time

## SDX-specific imports
from sdx.core import sdx_parse_config, sdx_parse_policies, sdx_platform
## General imports
import os

cwd = os.getcwd()

## Globals
BGP_PORT = 179
BGP = match(srcport=BGP_PORT) | match(dstport=BGP_PORT)


### SDX Platform ###
def sdx():
    sdx_topology_file = cwd + '/mininet.topo'
    (base, participants) = sdx_parse_config(sdx_topology_file)
    sdx_parse_policies(cwd + '/sdx_policies.cfg', base, participants)

    return sdx_platform(base), base


### Main ###
class Timely(DynamicPolicy):
    def __init__(self, sdx_policy):
        self.sdx_policy = sdx_policy
        super(Timely, self).__init__(sdx_policy)
        tlooper = Thread(target=self.looper)
        tlooper.start()

    def looper(self):
        while True:
            time.sleep(60)
            self.update_policy()

    def update_policy(self):
        self.policy = self.sdx_policy


def main():
    """Handle ARPs, BGPs, SDX and then do MAC learning"""
    (sdx_policy, base) = sdx()

    p = quality_mod(base) + if_(BGP, identity, Timely(sdx_policy))
    print p
    return p
