## Pyretic-specific imports
from pyretic.lib.corelib import parallel, match
from pyretic.core.network import IPPrefix

## SDX-specific imports
## General imports
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
    '''
        Specify participant policy
    '''
    participants = parse_config(cwd + "/policies/local.cfg")
    
    return (
        (parallel([match(dstip=participants["A"]["IPP"][i]) for i in range(len(participants["A"]["IPP"]))]) >> fwd(participant.phys_ports[0])) +
        (parallel([match(dstip=participants["h2"]["IPP"][i]) for i in range(len(participants["h2"]["IPP"]))]) >> fwd(participant.peers['h2']))
    )