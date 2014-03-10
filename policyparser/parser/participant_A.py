from pyretic.lib.corelib import *
from pyretic.lib.std import *

from pyretic.sdx.lib.common import *

from policyparser.parser.utils import HRange

import json
import os

cwd = os.getcwd()


def parse_config(config_file):
    participants = json.load(open(config_file, 'r'))
    
    for participant_name in participants:
        for i in range(len(participants[participant_name]["IPP"])):
            participants[participant_name]["IPP"][i] = IPPrefix(participants[participant_name]["IPP"][i])
    
    return participants


def policy(participant, fwd):

    
    e = drop
    
    d = if_(match(dstip=IPPrefix("120.0.0.0/24")), fwd(participant.peers["C"]), e)
    
    c = if_(match(dstip=IPPrefix("130.0.0.0/24")), fwd(participant.peers["C"]), d)
    
    b = if_((match(dstip=IPPrefix("130.0.0.0/24")) & match(time=HRange(6, 6))), fwd(participant.peers["B"]), c)
    
    a = if_((match(dstip=IPPrefix("110.0.0.0/24")) & match(protocol=1)), fwd(participant.peers["C"]), b)
    

    participants = parse_config(cwd + "/pyretic/sdx/policies/simple_ip_prefixes/local.cfg")
    
    return (
        (parallel([match(dstip=participants["A"]["IPP"][i]) for i in range(len(participants["A"]["IPP"]))]) >> fwd(participant.phys_ports[0]))
        
        +
        a
        
    )