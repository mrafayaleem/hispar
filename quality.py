from pyretic.core.language import match, IP, ARP_TYPE, fwd
from pyretic.lib.corelib import parallel
from pyretic.lib.query import count_packets

from echo_sender import EchoSender, dummyhostip, IP_TYPE, ICMP, BURST_SIZE
from echo_receiver import EchoReciever
from database import DBManager

from threading import Thread
import time
import numpy


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