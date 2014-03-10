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

    
    d = drop
    
    c = if_((match(dstip=IPPrefix("110.0.0.0/24")) & match(time=HRange(3,5))), fwd(participant.peers["A"]), d)
    
    b = if_((match(dstip=IPPrefix("110.0.0.0/24")) & match(dstport=80) & match(time=HRange(7,10))), fwd(participant.peers["A"]), c)
    
    a = if_(match(dstip=IPPrefix("110.0.0.0/24")), fwd(participant.peers["A"]), b)
    

    participants = parse_config(cwd + "/pyretic/sdx/policies/simple_ip_prefixes/local.cfg")
    
    return (
        (parallel([match(dstip=participants["A"]["IPP"][i]) for i in range(len(participants["A"]["IPP"]))]) >> fwd(participant.phys_ports[0]))
        
        +
        a
        
    )