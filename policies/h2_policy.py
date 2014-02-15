from pyretic.lib.corelib import *
from pyretic.lib.std import *
from pyretic.sdx.lib.common import *
from quality import HRange

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

    
    h = drop
    
    g = if_((match(dstip=IPPrefix("98.138.0.0/16"), time=HRange(1,5))), fwd(participant.peers["C"]), h)
    
    f = if_((match(dstip=IPPrefix("173.194.0.0/16"), time=HRange(3,5))), fwd(participant.peers["A"]), g)
    
    e = if_((match(dstip=IPPrefix("173.194.0.0/16"), time=HRange(2,2))), fwd(participant.peers["B"]), f)
    
    d = if_((match(dstip=IPPrefix("173.194.0.0/16"), time=HRange(1,1))), fwd(participant.peers["A"]), e)
    
    c = if_((match(dstip=IPPrefix("173.252.0.0/16"), time=HRange(4,5))), fwd(participant.peers["B"]), d)
    
    b = if_((match(dstip=IPPrefix("173.252.0.0/16"), time=HRange(2,3))), fwd(participant.peers["A"]), c)
    
    a = if_((match(dstip=IPPrefix("173.252.0.0/16"), time=HRange(1,1))), fwd(participant.peers["B"]), b)
    

    participants = parse_config(cwd + "/policies/local.cfg")
    
    return (
        (parallel([match(dstip=participants["h2"]["IPP"][i]) for i in range(len(participants["h2"]["IPP"]))]) >> fwd(participant.phys_ports[0]))
        
        +
        a
        
    )