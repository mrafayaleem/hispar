"""
Created on Feb 6, 2014

@author: root
"""
from pyretic.core.network import IP_TYPE, IP
from pyretic.core.packet import Packet
from threading import Thread, Lock
import time
from pox.lib.packet import icmp, echo, ipv4, ethernet
from pox.lib.addresses import IPAddr
import random

ICMP = 0x01
TCP = 0x06
UDP = 0x11

dummyhostip = "10.0.0.1"
dummyhostmac = "00:00:00:00:00:08"
excl_list = [IP('10.0.0.6'), IP('10.0.0.7'), IP('10.0.0.8'), IP('10.1.0.2'), IP('10.0.0.1')]
BURST_SIZE = 4


class EchoSender():
    """Observes packets to decide which targets to measure quality against
    and sends icmp echo requests to those IPs"""

    net = None

    def __init__(self, sdx):
        self.sdx = sdx

        self.sent_echos_lock = Lock()
        self.targets_lock = Lock()
        self.target_list = []
        self.target_dict = {}
        self.sent_echos = {}

        send_burst_thread = Thread(target=self.send_burst)
        send_burst_thread.start()

    def delete_target(self, endhost, participant):
        with self.targets_lock:
            del self.target_dict[(endhost, participant)]
            self.target_list.remove({"endhost": endhost, "participant": participant})

    def del_sent_echo(self, endhost, burstid):
        with self.sent_echos_lock:
            del self.sent_echos[(endhost, burstid)]

    def take_targets(self, counts):
        """Takes packet counts grouped by srcip and inport and decides which IP
        addresses to send icmp echo requests to"""

        for k, v in counts.items():
            if k.map['srcip'] in excl_list or v <= 1:
                continue

            srcip = str(k.map['srcip'])

            #just need portid to port object mapping. having to iterate all over
            for p in self.sdx.participants:
                #check if target is not already added
                if p.phys_ports[0].id_ == k.map['inport'] and not (srcip, p) in self.target_dict:
                    with self.targets_lock:
                        self.target_list.append({"endhost": srcip, "participant": p})
                        self.target_dict[(srcip, p)] = 1

    def send_burst(self):
        """Method to be run in a separate thread. Wakes up after certain time to send
        bursts of icmp echo requests to target IP addresses. Time configured so that every
        target recieves 4 bursts per minute"""

        current_target = 0
        while True:
            if len(self.target_list) > 0:
                time.sleep(1)
                #time.sleep(60 / (4 * len(self.target_list)))

                burstid = random.randint(1, 65535)
                key = (self.target_list[current_target]["endhost"], burstid)
                self.sent_echos[key] = range(BURST_SIZE)
                for burstseq in range(0, BURST_SIZE):
                    time.sleep(0.5)
                    EchoSender.__echo_request(srcip=dummyhostip,
                                              dstip=self.target_list[current_target]["endhost"],
                                              srcmac=dummyhostmac,
                                              participant=self.target_list[current_target]["participant"],
                                              idseq=burstid,
                                              seq=burstseq)
                    with self.sent_echos_lock:
                        self.sent_echos[key][burstseq] = {'sent_at': time.time(),
                                                          'through': self.target_list[current_target][
                                                              "participant"],
                                                          'rtt': None}

                current_target = (current_target + 1) % len(self.target_list)
            else:
                time.sleep(5)

    def get_sent_at(self, srcip, burstid, burstseq):
        if (srcip, burstid) in self.sent_echos:
            return self.sent_echos[(srcip, burstid)][burstseq]['sent_at']

    def set_rtt(self, srcip, burstid, burstseq, rtt):
        if (srcip, burstid) in self.sent_echos:
            with self.sent_echos_lock:
                self.sent_echos[(srcip, burstid)][burstseq]['rtt'] = rtt

    @staticmethod
    def __echo_request(srcip, dstip, srcmac, participant, idseq, seq, switch=1, payload="dummy payload"):
        """Constructs an icmp echo request packet and injects into network"""

        pport = participant.phys_ports[0]

        r = echo(id=idseq, seq=seq)
        r.set_payload(payload)
        i = icmp(type=8, code=0)
        i.set_payload(r)
        ip = ipv4(protocol=ICMP,
                  srcip=IPAddr(srcip),
                  dstip=IPAddr(dstip))
        ip.set_payload(i)
        e = ethernet(type=IP_TYPE,
                     src=srcmac,
                     dst=str(pport.mac))
        e.set_payload(ip)

        pkt = Packet()
        d = dict(protocol=ICMP, ethtype=IP_TYPE, switch=switch, inport=-1, outport=pport.id_, srcport=8, dstport=0,
                 srcip=srcip, srcmac=srcmac, dstip=dstip, dstmac=str(pport.mac), tos=0, raw=e.pack())
        pkt = pkt.modifymany(d)

        EchoSender.net.inject_packet(pkt)