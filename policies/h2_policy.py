from pyretic.lib.corelib import *
from pyretic.lib.std import *
from sdx.common import *
from hispar.extensions import HRange

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
    k = drop
    
    j = if_((match(dstip=IPPrefix("98.138.0.0/16"), time=HRange(0,5))), fwd(participant.peers["C"]), k)
    
    i = if_((match(dstip=IPPrefix("173.194.0.0/16"), time=HRange(3,5))), fwd(participant.peers["A"]), j)
    
    h = if_((match(dstip=IPPrefix("173.194.0.0/16"), time=HRange(1,2))), fwd(participant.peers["B"]), i)
    
    g = if_((match(dstip=IPPrefix("173.194.0.0/16"), time=HRange(0,0))), fwd(participant.peers["A"]), h)
    
    f = if_((match(dstip=IPPrefix("173.252.0.0/16"), time=HRange(4,5))), fwd(participant.peers["B"]), g)
    
    e = if_((match(dstip=IPPrefix("173.252.0.0/16"), time=HRange(1,3))), fwd(participant.peers["A"]), f)
    
    d = if_((match(dstip=IPPrefix("173.252.0.0/16"), time=HRange(0,0))), fwd(participant.peers["B"]), e)

    c = if_((match(dstip=IP("10.0.0.7"))), fwd(participant.peers["C"]), d)

    b = if_((match(dstip=IP("10.0.0.8"))), fwd(participant.peers["B"]), c)

    a = if_((match(dstip=IP("10.0.0.6"))), fwd(participant.peers["A"]), b)
    

    participants = parse_config(cwd + "/policies/local.cfg")
    
    return (
        (parallel([match(dstip=participants["h2"]["IPP"][i]) for i in range(len(participants["h2"]["IPP"]))]) >> fwd(participant.phys_ports[0]))

        +
        a

    )