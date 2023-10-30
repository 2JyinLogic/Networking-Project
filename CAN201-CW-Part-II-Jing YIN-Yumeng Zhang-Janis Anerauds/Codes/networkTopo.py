#/usr/bin/python
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.node import Host
from mininet.node import OVSKernelSwitch
from mininet.log import setLogLevel, info
from mininet.node import RemoteController
from mininet.term import makeTerm

def myTopo():
    net = Mininet(topo=None, autoSetMacs=True, build=False, ipBase='10.0.1.0/24')

    # add controller
    SDN_Controller = net.addController('c0', RemoteController)

    # add Host
    client = net.addHost('client', cls=Host, defaultRoute=None)
    Server1 = net.addHost('server1', cls=Host, defaultRoute=None)
    Server2 = net.addHost('server2', cls=Host, defaultRoute=None)

    # add Switch
    SDN_Switch = net.addSwitch('s1', cls=OVSKernelSwitch, failMode='secure')

    # add Links
    net.addLink(client,SDN_Switch)
    net.addLink(Server1,SDN_Switch)
    net.addLink(Server2,SDN_Switch)

    # net build
    net.build()

    # set MAC to interface
    client.setMAC(intf="client-eth0", mac="00:00:00:00:00:03")
    Server1.setMAC(intf="server1-eth0", mac="00:00:00:00:00:01")
    Server2.setMAC(intf="server2-eth0", mac="00:00:00:00:00:02")

    # set IP address to interface
    client.setIP(intf="client-eth0", ip='10.0.1.5/24')
    Server1.setIP(intf="server1-eth0", ip='10.0.1.2/24')
    Server2.setIP(intf="server2-eth0", ip='10.0.1.3/24')
    
    # Network start
    net.start()

    # start nterms
    net.terms += makeTerm(SDN_Controller)
    net.terms += makeTerm(client)
    net.terms += makeTerm(Server1)
    net.terms += makeTerm(Server2)

    # CLI mode running 
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myTopo()