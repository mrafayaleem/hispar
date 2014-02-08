from pyretic.core.language import DynamicFilter, match, IP_TYPE, IP, IPPrefix
from pox.lib.packet import ethernet
from pinger import Pinger, lock, hostip, ICMP
from pyretic.lib.query import count_packets
from threading import Thread
import MySQLdb
import time

launch = time.time()

class HRange:
    def __init__(self, hr_from, hr_to):
        self.hr_from = hr_from
        self.hr_to = hr_to

    def __eq__(self, other):
        if other <= self.hr_to and other >= self.hr_from:
            return True
        return False

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return "(" + str(self.hr_from) + ", " + str(self.hr_to) + ")"

class Reciever(DynamicFilter):
    def __init__(self):
        self.pending_db = []
        
        tdbman = Thread(target=self.dbman)
        tdbman.start()
        
        super(Reciever, self).__init__()
    
    def __getconn(self):
        db = MySQLdb.connect(host="localhost",
                                         user="root",
                                         passwd="root",
                                         db="hispar")
        return db
    
    def dbman(self):
        ASroutes = {}
        
        db = self.__getconn()
        cur = db.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM route")
        rows = cur.fetchall()
        for row in rows:
            if not ASroutes.has_key(row['AS']):
                ASroutes[row['AS']] = []
            ASroutes[row['AS']].append( { "idroute": row['idroute'],
                                          "IPP": IPPrefix(row['netid'] + '/' + row['netmask']) } )
        while(True):
            time.sleep(10)
            if len(self.pending_db) > 0:
                db = self.__getconn()
                cur = db.cursor(MySQLdb.cursors.DictCursor)
                idroute = None
                for e in self.pending_db:
                    endip = IP(e['endip'])
                    for r in ASroutes[str(e['part'].id_)]:
                        if  r['IPP'] == endip:
                            idroute = r['idroute']
                            break
                    if idroute == None:
                        continue
                    
                    cur.execute("SELECT * FROM quality WHERE route_id=" + str(idroute) + " AND hour_of_day=" + str(e['hour']))
                    row = cur.fetchone()
                    ts = time.gmtime(e['taken_at'])
                    taken_at = time.strftime('%Y-%m-%d %H:%M:%S', ts)
                    
                    if row is None:
                        q = "INSERT INTO quality (route_id, avg_latency, hour_of_day, m_time) VALUES (" + \
                                    str(idroute) + ", " + str(e['rtt']) + ", " + str(e['hour']) + ", '" + taken_at + "')"
                        cur.execute(q)
                    else:
                        avg = 0.7*float(row['avg_latency']) + 0.3*e['rtt']
                        count = int(row['m_count']) + 1
                        q = "UPDATE quality SET avg_latency=" + str(avg) + \
                            ", m_count=" + str(count) + \
                            ", m_time='" + taken_at + "' WHERE route_id=" + str(idroute) + " AND hour_of_day=" + str(e['hour'])
                        cur.execute(q)
                db.commit()
                self.pending_db = []
                        
    def __eq__(self, other):
        return isinstance(other, Reciever)
    
    def set_network(self, network):
        Pinger.net = network
    
    def eval(self, pkt):
        now = time.time()
        try:
            p = ethernet(raw=pkt['raw'])
            p = p.next.next
            idseq = p.next.id
            seq = p.next.seq
            srcip = str(pkt['srcip'])
            if p.type==0:
                if (srcip,idseq,seq) in Pinger.pending_echo:
                    with(lock):
                        #queue results to database
                        rtt = (now - Pinger.pending_echo[(srcip,idseq,seq)][0]) * 1000.0
                        self.pending_db.append( {"endip":srcip,
                                                 "part":Pinger.pending_echo[(srcip,idseq,seq)][1],
                                                 #taking in minutes since launch instead of hours since midnight
                                                 "hour":int( (time.time() - launch) / 60), #time.strftime('%H'),
                                                 "rtt":rtt,
                                                 "taken_at":now } )
                        Pinger.pending_echo.pop((srcip,idseq,seq))
        except Exception as e:
            print e
        return set()

### Main ###

def quality_mod(sdx):
    p = Pinger(sdx)
    q = count_packets(10, ['srcip', 'inport'])
    q.register_callback(p.take_targets)
    return q + ( match(dstip=IP(hostip), ethtype=IP_TYPE, protocol=ICMP) >> Reciever() )
    #return parallel([dpi(), mac_learner()])

