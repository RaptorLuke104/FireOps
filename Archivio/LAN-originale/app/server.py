"""Private LAN/VPN only. No external dependencies. TCP NDJSON, authoritative mission state."""
import argparse, asyncio, json, secrets, time
from engine import Mission

class Server:
    def __init__(self,token,admin):
        self.token=token; self.admin=admin; self.mission=Mission(); self.peers={}
    async def send(self,w,obj):
        w.write((json.dumps(obj,allow_nan=False)+'\n').encode())
        await asyncio.wait_for(w.drain(),2)
    async def peer(self,r,w):
        pid=None
        try:
            if len(self.peers)>=16: return
            hello=json.loads(await asyncio.wait_for(r.readline(),10))
            if hello.get('type')!='hello' or not secrets.compare_digest(str(hello.get('token','')),self.token): return
            pid=secrets.token_hex(8); name=str(hello.get('name','Pilot'))[:32]
            is_admin=secrets.compare_digest(str(hello.get('admin','')),self.admin)
            self.mission.join(pid,name); self.peers[pid]=w
            await self.send(w,{'type':'welcome','id':pid,'admin':is_admin})
            last=0
            while True:
                raw=await asyncio.wait_for(r.readline(),15)
                if not raw: break
                msg=json.loads(raw)
                if not isinstance(msg,dict): break
                try:
                    kind=msg.get('type')
                    if kind=='telemetry': self.mission.telemetry(pid,msg.get('data'))
                    elif kind=='command':
                        now=time.monotonic()
                        if now-last<0.25: raise ValueError('Comandi troppo frequenti')
                        last=now; cmd=msg.get('command')
                        if cmd in ('here','cancel') and not is_admin: raise ValueError('Comando riservato al dispatcher host')
                        if cmd=='here': self.mission.create(pid)
                        elif cmd=='cancel': self.mission.cancel()
                        elif cmd=='drop': self.mission.drop(pid)
                        elif cmd=='refill': self.mission.refill(pid)
                        else: raise ValueError('Comando sconosciuto')
                except ValueError as e: await self.send(w,{'type':'error','text':str(e)})
        except (ConnectionError,TimeoutError,ValueError,KeyError,TypeError,asyncio.LimitOverrunError): pass
        finally:
            if pid:
                self.peers.pop(pid,None); self.mission.players.pop(pid,None)
            w.close()
    async def broadcast(self):
        while True:
            for pid,w in list(self.peers.items()):
                try: await self.send(w,self.mission.snapshot())
                except (ConnectionError,TimeoutError): w.close()
            await asyncio.sleep(0.5)
    async def run(self,host,port):
        server=await asyncio.start_server(self.peer,host,port,limit=16384)
        print(f'FireOps LAN: {host}:{port}. Ctrl+C per terminare.',flush=True)
        async with server: await asyncio.gather(server.serve_forever(),self.broadcast())

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--bind',default='0.0.0.0'); p.add_argument('--port',type=int,default=8765)
    p.add_argument('--token',required=True); p.add_argument('--admin',required=True); a=p.parse_args()
    if len(a.token)<12 or len(a.admin)<12 or a.token==a.admin: p.error('Usa due chiavi diverse, almeno 12 caratteri ciascuna')
    try: asyncio.run(Server(a.token,a.admin).run(a.bind,a.port))
    except KeyboardInterrupt: pass
