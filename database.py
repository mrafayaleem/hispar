from sqlalchemy import create_engine, MetaData, Table, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from threading import Lock
from pyretic.core.network import IPPrefix, IP
from hispar.extensions import HRange
import quality
import time
from threading import Thread

engine = create_engine("mysql://root:root@localhost:5432/hispar")
metadata = MetaData(bind=engine)
Base = declarative_base()
Session = sessionmaker(bind=engine)


#ORM Classes!
class Route(Base):
    __table__ = Table('route', metadata, autoload=True)


class Quality(Base):
    __table__ = Table('quality', metadata, autoload=True)


class QualityDaily(Base):
    __table__ = Table('quality_daily', metadata, autoload=True)


class Traffic(Base):
    __table__ = Table('traffic', metadata, autoload=True)


class DBManager(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # noinspection PyArgumentList
            cls._instance = super(DBManager, cls).__new__(cls, *args, **kwargs)
            cls._instance.lock = Lock()
            cls._instance._pending_entries = []
            cls._instance.routes = {}
            cls._instance.take_routes()
            Thread(target=cls._instance._loop_commit).start()

        return cls._instance

    def take_routes(self):
        session = Session()
        results = session.query(Route).all()
        for r in results:
            if r.AS not in self.routes:
                self.routes[r.AS] = []
            self.routes[r.AS].append(r)

    def _loop_commit(self):
        while True:
            time.sleep(1)
            self._commit()

    def _commit(self):
        if len(self._pending_entries) > 0:
            session = Session()
            with self.lock:
                session.add_all(self._pending_entries)
                self._pending_entries = []
            session.commit()

    def store_rtt(self, endhost, participant, latency, jitter, loss, m_time):
        hour_of_day = m_time.tm_hour
        route_id = -1
        for r in self.routes[participant]:
            if IPPrefix(r.subnet) == IP(endhost) and HRange.from_range(r.HRange) == hour_of_day:
                route_id = r.idroute
                break

        with self.lock:
            self._pending_entries.append(
                Quality(route_id=route_id, hour_of_day=hour_of_day, latency=latency, jitter=jitter, loss=loss,
                        m_time=time.strftime("%Y-%m-%d %H:%M:%S", m_time)))

    def _get_routeids(self, participant, subnet):
        return [int(r.idroute) for r in self.routes[participant] if r.subnet == subnet]

    def get_qos(self, participants, subnet, period):
        routeids = []
        for p in participants:
            routeids.extend(self._get_routeids(p, subnet))

        session = Session()
        rows = session.query(Route.AS, func.avg(Quality.latency).label('latency'),
                             func.avg(Quality.jitter).label('jitter'), func.avg(Quality.loss).label('loss')).\
            filter(Route.idroute == Quality.route_id). \
            filter(Quality.route_id.in_(routeids)). \
            filter(Quality.m_time >= (time.time() - period * 120)).\
            group_by(Route.AS).all()

        qos = {}
        for r in rows:
            qos[r[0]] = r[1:]
        return qos


if __name__ == '__main__':
    db = DBManager()
    db.get_qos(['A', 'B', 'C'], "173.194.0.0/16", 60)