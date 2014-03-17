from pyretic.sdx.lib.common import *

from hispar.extensions import HRange, UpdatePolicy
from hispar.database import DBManager

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

    UpdatePolicy.set_fwd(fwd)
    UpdatePolicy.set_participant(participant)
    UpdatePolicy.set_dbmanager(DBManager())

    participants = parse_config(cwd + "/pyretic/sdx/policies/simple_ip_prefixes/local.cfg")

    e = UpdatePolicy("130.0.0.0/24", match(dstip=IPPrefix("130.0.0.0/24")), drop, ["A", "B"], [], 15, 10, 120)
    d = UpdatePolicy("130.0.0.0/24", (match(dstip=IPPrefix("130.0.0.0/24")) & match(dstport=80) & match(srcport=80) & match(time=HRange(6, 6))), e, ["B"], [], 15, 10, 60)
    c = UpdatePolicy("120.0.0.0/24", match(dstip=IPPrefix("120.0.0.0/24")), d, ["A", "C"], [], 15, 10, 20)
    b = UpdatePolicy("110.0.0.0/24", match(dstip=IPPrefix("110.0.0.0/24")), c, ["B"], ["C"], 12, 7, 15)
    a = UpdatePolicy("110.0.0.0/24", (match(dstip=IPPrefix("110.0.0.0/24")) & match(protocol=1) & match(time=HRange(6, 7))), b, ["B", "C"], ["E"], 10, 5, 30)

    return (
        (parallel([match(dstip=participants["A"]["IPP"][i]) for i in range(len(participants["A"]["IPP"]))]) >> fwd(participant.phys_ports[0]))
        +
        a
    )



