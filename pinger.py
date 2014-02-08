'''
Created on Feb 6, 2014

@author: root
'''
from pyretic.core.network import IP_TYPE, Packet
from threading import Thread, Lock
import time
from pox.lib.packet import icmp, echo, ipv4, ethernet
from pox.lib.addresses import IPAddr

ICMP=0x01
TCP=0x06
UDP=0x11
IP=0x0800
hostip = "10.0.0.2"
hostmac = "00:00:00:00:00:00"
lock = Lock()

class Pinger():
    '''
    Observes packets to decide which targets to measure quality against
    and sends icmp requests to those IPs
    '''
    net = None
    pending_echo = {}

    def __init__(self, sdx):
        self.tid = 0
        self.sdx = sdx
        self.idseq = 1
        self.seq = 1
        self.targets = []
        self.tdone = {}
        
        tstarter = Thread(target=self.starter)
        tstarter.start()
        
        tdiscarder = Thread(target=self.discarder)
        tdiscarder.start()
    
    def take_targets(self, counts):
        for k, v in counts.items():
            srcip = str(k.map['srcip'])
            if  srcip != hostip and v > 1:
                for p in self.sdx.participants:
                    if p.phys_ports[0].id_ == k.map['inport']:
                        with(lock): 
                            if not self.tdone.has_key(srcip + str(p)):
                                self.targets.append({"endip": srcip, "part": p})
                                self.tdone[srcip + str(p)] = 1                
                
    def starter(self):
        while(True):
            if len(self.targets) > 0:
                time.sleep(60/ (4*len(self.targets)))
                for i in range(0, 10):
                    time.sleep(0.2)
                    self.__echo_request(srcip = hostip,
                                        dstip = self.targets[self.tid]["endip"],
                                        srcmac = hostmac,
                                        participant = self.targets[self.tid]["part"],
                                        idseq = self.idseq,
                                        seq = self.seq)
                    with(lock):
                        Pinger.pending_echo[(self.targets[self.tid]["endip"], self.idseq, self.seq)] = [time.time(), self.targets[self.tid]["part"]]
                    self.idseq = (self.idseq + 1) % 256
                    self.seq = (self.seq + 1) % 256
                    self.tid = (self.tid + 1) % len(self.targets)
            else:
                time.sleep(1)
                
    def discarder(self):
        while(True):
            time.sleep(2)
            with(lock):
                now = time.time()
                for key,val in self.pending_echo.items():
                    if (now - val[0]) > 10:
                        self.pending_echo.pop(key)
    
    def set_network(self, network):
        self.network = network
        
    def __echo_request(self, srcip, dstip, srcmac, participant, idseq, seq, switch=1):
        pport = participant.phys_ports[0]
        
        r = echo(id=idseq, seq=seq)
        r.set_payload("dummy payload")
        i = icmp(type=8, code=0)
        i.set_payload(r)
        ip = ipv4(protocol=ICMP,
                  srcip=IPAddr(srcip),
                  dstip=IPAddr(dstip))
        ip.set_payload(i)
        e = ethernet(type=IP,
                 src=srcmac,
                 dst=str(pport.mac))
        e.set_payload(ip)
        
        rp = Packet()
        rp = rp.modify(protocol=ICMP)
        rp = rp.modify(ethtype=IP_TYPE)
        rp = rp.modify(switch=switch)
        rp = rp.modify(inport=-1)
        rp = rp.modify(outport=pport.id_)
        rp = rp.modify(srcport=8)
        rp = rp.modify(dstport=0)
        rp = rp.modify(srcip=srcip)
        rp = rp.modify(srcmac=srcmac)
        rp = rp.modify(dstip=dstip)
        rp = rp.modify(dstmac=str(pport.mac))
        
        rp = rp.modify(tos=0)
        rp = rp.modify(raw=e.pack())
    
        Pinger.net.inject_packet(rp)