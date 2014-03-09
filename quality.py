from pyretic.core.language import match, IP, ARP_TYPE, fwd
from pyretic.lib.corelib import parallel
from echo_sender import EchoSender, dummyhostip, IP_TYPE, ICMP, BURST_SIZE
from echo_receiver import EchoReciever
from pyretic.lib.query import count_packets
from threading import Thread
from database import DBManager
import time
import numpy


class HRange:
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


def start_aggregator(es):
    aggregator_thread = Thread(target=aggregator, args=(es,))
    aggregator_thread.start()


def valid_burst(burst):
    for packet in burst:
        if not isinstance(packet, dict):
            return False

    if time.time() - burst[BURST_SIZE - 1]['sent_at'] < 15:
        return False

    return True


def aggregator(es):
    db = DBManager()
    while True:
        time.sleep(1)
        for (endhost, burstid), burst in es.sent_echos.items():
            try:
                #check for a valid burst with time expired
                if not valid_burst(burst):
                    continue

                rtt = [packet['rtt'] for packet in burst if packet['rtt'] is not None]
                es.del_sent_echo(endhost, burstid)

                #100% loss. end host is probably dead
                if len(rtt) == 0:
                    es.delete_targets(endhost, burst[0]['through'])
                    continue

                latency = numpy.average(rtt)
                jitter = numpy.std(rtt)
                loss = float((BURST_SIZE - len(rtt)) / BURST_SIZE) * 100
                db.store_rtt(endhost, str(burst[0]['through'].id_), latency, jitter, loss,
                             time.gmtime(burst[0]['sent_at']))
            except Exception, e:
                print e


def dum_policy(sdx, es):
    return (match(dstip=IP(dummyhostip), ethtype=ARP_TYPE) >> fwd(5)) + \
           (match(inport=5) >> parallel(
               [match(dstmac=mac) >> fwd(port.id_) for mac, port in sdx.mac_to_port.items()])
           ) + (match(dstip=IP(dummyhostip), ethtype=IP_TYPE, protocol=ICMP) >> EchoReciever(es))


### Main ###
def quality_mod(sdx):
    es = EchoSender(sdx)
    q = count_packets(1, ['srcip', 'inport'])
    q.register_callback(es.take_targets)
    start_aggregator(es)
    return q + dum_policy(sdx, es)