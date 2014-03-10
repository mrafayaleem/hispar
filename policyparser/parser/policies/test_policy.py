from pyretic.lib.corelib import *
from pyretic.lib.std import *
from pyretic.sdx.lib.common import *

import random
from threading import Thread
import json
import os

from policyparser.parser.utils import HRange

cwd = os.getcwd()

participant_ref = None
fwd_ref = None

class UpdatePolicy(DynamicPolicy):
    def __init__(self, ip, pred, f_branch, routes, default_routes, latency, loss, update_interval):
        self._ip = ip
        self._routes = routes
        self._default_routes = default_routes
        self._latency = latency
        self._loss = loss
        self._update_interval = update_interval
        self._pred = pred
        self._t_branch = get_fwd_policy(ip, routes, default_routes, latency, loss, update_interval)
        self._f_branch = f_branch
        self._update_policy = if_(pred, self.t_branch, f_branch)
        super(UpdatePolicy, self).__init__(self._update_policy)
        tlooper = Thread(target=self.looper)
        tlooper.start()

    def looper(self):
        while True:
            time.sleep(self._update_interval)
            self.update_policy()

    def update_policy(self):
        self._t_branch = get_fwd_policy(self._ip, self._routes, self._latency, self._loss,
                                        self._update_interval)
        self._update_policy = if_(self._pred, self.t_branch, self.f_branch)
        self.policy = self._update_policy

    @property
    def update_interval(self):
        return self._update_interval


def parse_config(config_file):
    participants = json.load(open(config_file, 'r'))
    
    for participant_name in participants:
        for i in range(len(participants[participant_name]["IPP"])):
            participants[participant_name]["IPP"][i] = IPPrefix(participants[participant_name]["IPP"][i])
    
    return participants


def policy(participant, fwd):

    global participant_ref
    participant_ref = participant

    global fwd_ref
    fwd_ref = fwd

    participants = parse_config(cwd + "/pyretic/sdx/policies/simple_ip_prefixes/local.cfg")

    d = UpdatePolicy("130.0.0.0/24", match(dstip=IPPrefix("130.0.0.0/24")), drop, ["A", "B"], [], 15, 10, 120)
    c = UpdatePolicy("120.0.0.0/24", match(dstip=IPPrefix("120.0.0.0/24")), d, ["A", "C"], [], 15, 10, 20)
    b = UpdatePolicy("110.0.0.0/24", match(dstip=IPPrefix("110.0.0.0/24")), c, ["B"], ["C"], 12, 7, 15)
    a = UpdatePolicy("110.0.0.0/24", (match(dstip=IPPrefix("110.0.0.0/24")) & match(protocol=1) & match(time=HRange(6, 7))), b, ["B", "C"], ["E"], 10, 5, 30)

    return (
        (parallel([match(dstip=participants["A"]["IPP"][i]) for i in range(len(participants["A"]["IPP"]))]) >> fwd(participant.phys_ports[0]))
        +
        a
    )


def get_fwd_policy(ip, routes, default_routes, latency, loss, update_interval):
    """
    if latecny and loss satisfied for N routes:
        create a list of those N routes
        select any random route from these N routes
        write a timed dynamic policy and return

    else if default route is not none
        write a timed dynamic policy and return

    else
        return drop
    """
    peer_qos_data = get_qos_data(ip, routes, None, update_interval)

    candidate_routes = [peer for peer, data in peer_qos_data.iteritems() if data[0] <= latency and data[1] <= loss]

    if candidate_routes is not None:
        return fwd_ref(participant_ref.peers[random.choice(candidate_routes)])

    if default_routes is not None:
        return fwd_ref(participant_ref.peers[random.choice(default_routes)])
    else:
        return drop


def get_qos_data(ip, routes, update_interval):
    return {}
