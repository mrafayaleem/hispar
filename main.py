## Pyretic-specific imports
from pyretic.modules.arp import ARP, arp, mac_learner
from pyretic.lib.corelib import match, if_, identity
from quality import quality_mod

## SDX-specific imports
from sdx.core import sdx_parse_config, sdx_parse_policies, sdx_platform
## General imports
import os

cwd = os.getcwd()

## Globals
BGP_PORT = 179
BGP = match(srcport=BGP_PORT) | match(dstport=BGP_PORT)

base = None
### SDX Platform ###
def sdx():
    sdx_topology_file = cwd + '/mininet.topo'
    (base, participants) = sdx_parse_config(sdx_topology_file)
    sdx_parse_policies(cwd + '/sdx_policies.cfg', base, participants)
    
    return (sdx_platform(base), base)

### Main ###
    
def main():
    """Handle ARPs, BGPs, SDX and then do MAC learning"""
    (sdx_policy, base) = sdx()
    print sdx_policy
    q = quality_mod(base)
    return if_(BGP, identity, sdx_policy)
