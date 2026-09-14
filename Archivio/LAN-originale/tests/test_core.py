import unittest,sys,pathlib,struct,time,asyncio,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'app'))
from engine import Mission,distance
from protocol import *
from server import Server
T={'lat':41.1,'lon':16.8,'alt':30.,'ground':28.,'agl':2.,'speed':0.,'on_ground':1.}
class Core(unittest.TestCase):
    def setUp(self):
        self.m=Mission();self.m.join('a','Alpha');self.m.telemetry('a',T.copy())
    def test_packet_abi(self):
        self.m.create('a'); b=pack_snapshot(self.m.snapshot(),'12345678-1234-1234-1234-123456789ABC','',9)
        self.assertEqual(len(b),1120);self.assertEqual(HEADER.unpack_from(b)[:4],(1,9,1,0));self.assertEqual(CELL.unpack_from(b,96)[0],1)
    def test_invalid_guid(self):
        with self.assertRaises(ValueError): guid_bytes('bogus')
    def test_completion(self):
        self.m.create('a'); t=T|{'alt':78.,'agl':50.,'speed':40.,'on_ground':0.}
        for _ in range(4):
            self.m.telemetry('a',t);self.m.players['a']['last_drop']=0;self.m.drop('a')
        self.assertEqual(self.m.phase,'COMPLETATA');self.assertEqual(self.m.players['a']['water'],0)
    def test_miss_consumes(self):
        self.m.create('a');self.m.telemetry('a',T|{'lat':42.,'agl':50.,'on_ground':0.});self.m.drop('a')
        self.assertEqual(self.m.fires[0]['hp'],100);self.assertEqual(self.m.players['a']['water'],1500)
    def test_stale(self):
        self.m.players['a']['seen']-=10
        with self.assertRaises(ValueError):self.m.create('a')
    def test_refill_air_rejected(self):
        self.m.telemetry('a',T|{'on_ground':0.})
        with self.assertRaises(ValueError):self.m.refill('a')
    def test_nan(self):
        with self.assertRaises(ValueError):self.m.telemetry('a',T|{'lat':float('nan')})
    def test_cooldown(self):
        self.m.create('a');self.m.telemetry('a',T|{'agl':50.,'on_ground':0.});self.m.drop('a')
        with self.assertRaises(ValueError):self.m.drop('a')
    def test_cancel(self):
        self.m.create('a');self.m.cancel();self.assertEqual(self.m.fires,[])
    def test_distance(self):self.assertAlmostEqual(distance(T,T),0)

class Network(unittest.IsolatedAsyncioTestCase):
    async def test_two_clients_late_join_and_authority(self):
        srv=Server('shared-secret','admin-secret'); listener=await asyncio.start_server(srv.peer,'127.0.0.1',0)
        port=listener.sockets[0].getsockname()[1]; bg=asyncio.create_task(srv.broadcast());ws=[]
        async def connect(admin=''):
            r,w=await asyncio.open_connection('127.0.0.1',port);ws.append(w)
            w.write((json.dumps({'type':'hello','name':'Test','token':'shared-secret','admin':admin})+'\n').encode());await w.drain()
            msg=json.loads(await r.readline());self.assertEqual(msg['type'],'welcome');return r,w,msg['id']
        async def until(r,kind):
            for _ in range(10):
                m=json.loads(await asyncio.wait_for(r.readline(),2))
                if m['type']==kind:return m
            self.fail('missing message')
        try:
            r,w,pid=await connect('admin-secret')
            for m in ({'type':'telemetry','data':T},{'type':'command','command':'here'}):w.write((json.dumps(m)+'\n').encode())
            await w.drain(); a=await until(r,'state');self.assertEqual(a['phase'],'ATTIVA')
            r2,w2,_=await connect();b=await until(r2,'state');self.assertEqual(a['fires'],b['fires'])
            w2.write(b'{"type":"command","command":"cancel"}\n');await w2.drain()
            e=await until(r2,'error');self.assertIn('host',e['text']);self.assertEqual(srv.mission.phase,'ATTIVA')
        finally:
            for w in ws:w.close();await w.wait_closed()
            bg.cancel();await asyncio.gather(bg,return_exceptions=True);listener.close();await listener.wait_closed()
if __name__=='__main__':unittest.main()
