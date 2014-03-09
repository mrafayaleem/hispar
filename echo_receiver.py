from pyretic.core.language import DynamicFilter
from pox.lib.packet import ethernet
from echo_sender import EchoSender
import time


class EchoReciever(DynamicFilter):
    """Recieves icmp packets destined for dummy hostip and matches them to pending
    icmp echo requests sent out by EchoSender to calculate rtt"""

    def __init__(self, es):
        self.recieved_echos = {}
        self.es = es
        super(EchoReciever, self).__init__()

    def __eq__(self, other):
        #incorrect implementation
        return isinstance(other, EchoReciever)

    def set_network(self, network):
        EchoSender.net = network

    def eval(self, pkt):
        now = time.time()

        p = ethernet(raw=pkt['raw'])
        p = p.next.next
        burstid = p.next.id
        burstseq = p.next.seq
        srcip = str(pkt['srcip'])
        if p.type == 0:
            rtt = (now - self.es.get_sent_at(srcip, burstid, burstseq)) * 1000.0
            self.es.set_rtt(srcip, burstid, burstseq, rtt)

        return set()
