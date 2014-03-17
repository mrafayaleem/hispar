"""
Created on Mar 17, 2014

@author: Mohammad Rafay Aleem
"""
from pyretic.sdx.lib.common import *

import random
from threading import Thread


class HRange(object):
    """Models an hour range to serve for match policy. The range
    is from hr_from to hr_to both inclusive"""

    def __init__(self, hr_from, hr_to):
        self.hr_from = hr_from
        self.hr_to = hr_to

    @classmethod
    def from_range(cls, str_range):
        split = str_range.split(",")
        hr_from = int(split[0])
        hr_to = int(split[1])
        return cls(hr_from, hr_to)

    def __eq__(self, other):
        """Overrides the == operator to check if other falls within range.
        Comparison of two HRange objects not supported"""
        #print "comparing " + str(other) + " to range " + self.__str__()
        if self.hr_from <= other <= self.hr_to:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "(" + str(self.hr_from) + ", " + str(self.hr_to) + ")"


class UpdatePolicy(DynamicPolicy):
    POLICY_TYPE = ('strict', 'loose',)
    fwd = None
    participant = None
    dbmanager = None

    def __init__(self, ip, pred, f_branch, routes, default_routes, latency, loss, update_interval, check_interval,
                 policy_type):
        assert(UpdatePolicy.fwd is not None)
        assert(UpdatePolicy.participant is not None)
        assert(UpdatePolicy.dbmanager is not None)

        self.ip = ip
        self.routes = routes
        self.default_routes = default_routes
        self.latency = latency
        self.loss = loss
        self.update_interval = update_interval
        self.check_interval = check_interval
        self.policy_type = policy_type
        self.pred = pred
        self.t_branch = UpdatePolicy.get_fwd_policy(ip, routes, default_routes, latency, loss, update_interval,
                                                    policy_type)
        self.f_branch = f_branch
        self.update_policy = if_(pred, self.t_branch, f_branch)
        super(UpdatePolicy, self).__init__(self.update_policy)

        tlooper = Thread(target=self.looper)
        qos_looper = Thread(target=self.qos_guaranteer)
        tlooper.start()
        qos_looper.start()

    def looper(self):
        while True:
            time.sleep(self.update_interval)
            self.update_policy()

    def qos_guaranteer(self):
        while True:
            time.sleep(self.check_interval)
            self.update_policy()

    def update_policy(self):
        self.t_branch = UpdatePolicy.get_fwd_policy(self.ip, self.routes, self.default_routes, self.latency,
                                                    self.loss, self.update_interval, self.policy_type)
        self.update_policy = if_(self.pred, self.t_branch, self.f_branch)
        self.policy = self.update_policy

    @property
    def update_interval(self):
        return self.update_interval

    @classmethod
    def get_fwd_policy(cls, ip, routes, default_routes, latency, loss, update_interval, policy_type):
        """
        Generates a fwd policy based on the parameters
        """
        peer_qos_data = UpdatePolicy.dbmanager.get_qos(routes, ip, update_interval)

        candidate_routes = [peer for peer, data in peer_qos_data.iteritems() if data[0] <= latency and data[1] <= loss]

        if candidate_routes is not None:
            return UpdatePolicy.fwd(UpdatePolicy.participant.peers[random.choice(candidate_routes)])

        if default_routes is not None and policy_type == UpdatePolicy.POLICY_TYPE[1]:
            return UpdatePolicy.fwd(UpdatePolicy.participant.peers[random.choice(default_routes)])
        else:
            print 'STRICT POLICY APPLIED: Dropping packets now from this participant'
            return drop

    @classmethod
    def set_fwd(cls, fwd):
        cls.fwd = fwd

    @classmethod
    def set_participant(cls, particpant):
        cls.participant = particpant

    @classmethod
    def set_dbmanager(cls, dbmanager):
        cls.dbmanager = dbmanager
