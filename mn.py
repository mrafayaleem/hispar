#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.node import RemoteController, Controller
from mininet.link import TCLink
import threading

def myNetwork():
    net=Mininet(topo=None, autoSetMacs=True, link=TCLink)
    c0 = net.addController('c0', controller=RemoteController)
    c1 = net.addController('c1', controller=Controller, port=6634)
    
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    f_gate = net.addSwitch('f_gate', cls=OVSKernelSwitch, dpid='5')
    y_gate = net.addSwitch('y_gate', cls=OVSKernelSwitch, dpid='7')
    g_gate = net.addSwitch('g_gate', cls=OVSKernelSwitch, dpid='6')

    info( '*** Add hosts\n')
    A = net.addHost('A', ip='10.0.0.6', defaultRoute=None)
    B = net.addHost('B', ip='10.0.0.8', defaultRoute=None)
    C = net.addHost('C', ip='10.0.0.7', defaultRoute=None)
    h2 = net.addHost('h2', ip='10.0.0.2', defaultRoute=None)
    google = net.addHost('google', ip='173.194.39.41', defaultRoute=None)
    facebook = net.addHost('facebook', ip='173.252.110.27', defaultRoute=None)
    yahoo = net.addHost('yahoo', ip='98.138.253.109', defaultRoute=None)
    dum = net.addHost('dum', ip='10.0.0.1', defaultRoute=None)

    info( '*** Add links\n')
    net.addLink(facebook, f_gate)
    net.addLink(y_gate, yahoo)
    net.addLink(google, g_gate)
    net.addLink(A, s1)
    net.addLink(A, g_gate, delay='50ms', jitter='5ms', loss=10)
    net.addLink(A, f_gate, delay='120ms', jitter='5ms', loss=10)
    net.addLink(A, y_gate, delay='120ms', jitter='5ms', loss=10)
    
    net.addLink(B, s1)
    net.addLink(B, g_gate, delay='150ms', jitter='5ms', loss=10)
    net.addLink(B, f_gate, delay='100ms', jitter='5ms', loss=10)
    net.addLink(B, y_gate, delay='150ms', jitter='5ms', loss=10)
    
    net.addLink(C, s1)
    net.addLink(C, g_gate, delay='150ms', jitter='5ms', loss=10)
    net.addLink(C, f_gate, delay='150ms', jitter='5ms', loss=10)
    net.addLink(C, y_gate, delay='100ms', jitter='5ms', loss=10)
    net.addLink(h2, s1)
    net.addLink(dum, s1)
    
    net.build()
    c0.start()
    c1.start()
    s1.start([c0])
    f_gate.start([c1])
    y_gate.start([c1])
    g_gate.start([c1])
        
    for host in net.hosts:
        if host.name in ['google', 'yahoo', 'facebook']:
            host.cmd('route add -net 10.0.0.0 netmask 255.0.0.0 ' + host.name + '-eth0')
        elif host.name in ['A', 'B', 'C']:
            host.cmd('sysctl net.ipv4.ip_forward=1')
            host.cmd('ifconfig ' + host.name + '-th1 ' + host.IP())
            for i in range(0, 4):
                host.cmd('echo 1 > /proc/sys/net/ipv4/conf/' + host.name + '-eth' + str(i) + '/proxy_arp')
            host.cmd('route add -net 173.194.0.0 netmask 255.255.0.0 ' + host.name + '-eth1')
            host.cmd('route add -net 173.252.0.0 netmask 255.255.0.0 ' + host.name + '-eth2')
            host.cmd('route add -net 98.138.0.0 netmask 255.255.0.0 ' + host.name + '-eth3')
        else:
            host.cmd('route add -net 0.0.0.0 netmask 0.0.0.0 ' + host.name + '-eth0')
            
        #if host.name == 'C':
        #   for i in range(0, 4):
                #host.cmd('echo 1 > /proc/sys/net/ipv4/conf/' + host.name + '-eth' + str(i) + '/proxy_arp') 
                
    def change_delay(host, dif):
        inflist = host.cmd("ifconfig -a | sed 's/[ \t].*//;/^\(lo\|\)$/d' | awk 'NR>2'").split('\n')[:3]
        for inf in inflist:
            old = float(host.cmd("tc -s qdisc ls dev " + inf + " | awk 'NR==2{print $10}'")[:-3])
            host.cmd("tc qdisc change dev " + inf + " root netem delay " + str(old+dif) + "ms")
            
    post_task(1*60, change_delay, [A, 150])
    post_task(3*60, change_delay, [A, -150])
    post_task(2*60, change_delay, [B, 80])
    post_task(4*60, change_delay, [B, -80])
    post_task(3*60, change_delay, [C, 80])
    post_task(5*60, change_delay, [C, -80])
    
    CLI(net)
    net.stop()

def post_task(interval, callback, args):
    t = threading.Timer(interval, callback, args)
    t.start()
    
if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

